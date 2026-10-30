#!/usr/bin/env python3
"""
Hybrid CV/Resume Parser - single-file, local-only implementation.

Required packages:
    pip install pdfplumber PyMuPDF python-docx rapidfuzz
Recommended:
    pip install spacy fastapi "uvicorn[standard]" python-multipart
    python -m spacy download en_core_web_sm

CHANGELOG
---------
1.2.0
  - [Provenance]  metadata.parser_file and metadata.parser_version added so the
                  JSON itself proves which file is running.
  - [Skills]      _join_continuations fixes PDF-wrapped skill lines like
                  "…, Facial" / "& Body Landmark Tracking".
  - [Headings]    "additional" section requires: seen_first_section, ALL-CAPS,
                  2+ words, no dash separator, no job keywords, no digits/@.
                  Prevents tagline-style first lines from being swallowed.
  - [Diagnostics] /parser-info endpoint.
1.1.0
  - DATE_TOKEN month name restricted to real months.
  - Preamble is first-class; candidate name / job titles never become sections.
  - Multi-word skills preserved; OpenAI / Groq / LangChain / ChromaDB etc.
    classified as tools.
  - Project splitter using bullet-block boundaries.
  - Certifications split one bullet per entry; issuers only from explicit
    wording or known providers.
  - Education: degree / field / institution cleanly separated.
  - Experience: "Title — Company" parsed deterministically.
  - Location: preamble only, technology blacklist applied.
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import logging
import math
import os
import re
import tempfile
import unicodedata
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence
from urllib.parse import urlparse


VERSION = "1.2.0"
LOGGER = logging.getLogger("cv_parser")
LOGGER.info("Loading cv_parser %s from %s", VERSION, __file__)


# ============================================================================
# Data model
# ============================================================================

@dataclass
class LineHint:
    text: str
    page: int = 1
    order: int = 0
    bold: bool = False
    font_size: Optional[float] = None
    x0: Optional[float] = None
    y0: Optional[float] = None
    source: str = "body"


@dataclass
class LoadedDocument:
    lines: list[LineHint] = field(default_factory=list)
    file_type: Optional[str] = None
    page_count: Optional[int] = None
    methods: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    ocr_used: bool = False

    @property
    def text(self) -> str:
        return "\n".join(line.text for line in self.lines if line.text.strip())


# ============================================================================
# Document loader
# ============================================================================

class DocumentLoader:
    PDF_MAGIC = b"%PDF-"
    DOCX_REQUIRED = {"[Content_Types].xml", "word/document.xml"}

    def validate(self, file_path: Path) -> tuple[Optional[str], Optional[str]]:
        if not file_path.exists() or not file_path.is_file():
            return None, "File does not exist or is not a regular file"
        if file_path.stat().st_size == 0:
            return None, "File is empty"
        suffix = file_path.suffix.lower()
        if suffix not in {".pdf", ".docx"}:
            return None, "Unsupported file type; only PDF and DOCX are accepted"
        try:
            with file_path.open("rb") as handle:
                magic = handle.read(8)
            if suffix == ".pdf":
                if not magic.startswith(self.PDF_MAGIC):
                    return None, "Extension is .pdf but file content is not a PDF"
                return "pdf", None
            if not zipfile.is_zipfile(file_path):
                return None, "Extension is .docx but file content is not a valid DOCX container"
            with zipfile.ZipFile(file_path) as archive:
                if not self.DOCX_REQUIRED.issubset(set(archive.namelist())):
                    return None, "DOCX is missing required document components"
            return "docx", None
        except (OSError, zipfile.BadZipFile) as exc:
            return None, f"Could not validate file: {exc}"

    def load(self, file_path: str | Path) -> LoadedDocument:
        path = Path(file_path)
        result = LoadedDocument()
        file_type, error = self.validate(path)
        result.file_type = file_type or path.suffix.lower().lstrip(".") or None
        if error:
            result.errors.append(error)
            return result
        try:
            return self._load_pdf(path) if file_type == "pdf" else self._load_docx(path)
        except PermissionError:
            result.errors.append("Permission denied while reading file")
        except Exception as exc:
            LOGGER.exception("Document extraction failed")
            if "password" in str(exc).lower() or "encrypt" in str(exc).lower():
                result.errors.append("Document is password-protected or encrypted")
            else:
                result.errors.append(f"Document is corrupted or unreadable: {exc}")
        return result

    def _load_pdf(self, path: Path) -> LoadedDocument:
        result = LoadedDocument(file_type="pdf")
        extraction_errors: list[str] = []
        try:
            import pdfplumber  # type: ignore
            with pdfplumber.open(str(path)) as pdf:
                result.page_count = len(pdf.pages)
                for page_no, page in enumerate(pdf.pages, 1):
                    words = page.extract_words(
                        use_text_flow=False, keep_blank_chars=False,
                        extra_attrs=["fontname", "size"],
                    )
                    if words:
                        result.lines.extend(self._pdf_words_to_lines(words, page_no, page.width))
                    else:
                        text = page.extract_text(x_tolerance=2, y_tolerance=3) or ""
                        for index, line in enumerate(text.splitlines()):
                            result.lines.append(LineHint(line, page_no, index))
            result.methods.append("pdfplumber")
        except ImportError:
            extraction_errors.append("pdfplumber is not installed")
        except Exception as exc:
            extraction_errors.append(f"pdfplumber failed: {exc}")

        if len(result.text.strip()) < 40:
            try:
                import fitz  # type: ignore
                fitz_lines: list[LineHint] = []
                document = fitz.open(str(path))
                if document.needs_pass:
                    result.errors.append("PDF is password-protected")
                    return result
                result.page_count = document.page_count
                for page_no, page in enumerate(document, 1):
                    blocks = sorted(page.get_text("blocks"), key=lambda b: (round(b[1], 1), b[0]))
                    order = 0
                    for block in blocks:
                        for line in str(block[4]).splitlines():
                            if line.strip():
                                fitz_lines.append(LineHint(line, page_no, order, x0=block[0], y0=block[1]))
                                order += 1
                if len("\n".join(x.text for x in fitz_lines)) > len(result.text):
                    result.lines = fitz_lines
                result.methods.append("PyMuPDF")
            except ImportError:
                extraction_errors.append("PyMuPDF is not installed")
            except Exception as exc:
                extraction_errors.append(f"PyMuPDF failed: {exc}")

        if len(result.text.strip()) < 40:
            self._ocr_pdf(path, result)
        if not result.lines and not result.errors:
            result.errors.append("No extractable text found in PDF")
        result.warnings.extend(extraction_errors)
        return result

    @staticmethod
    def _pdf_words_to_lines(words: list[dict[str, Any]], page: int, width: float) -> list[LineHint]:
        if not words:
            return []
        mid = width / 2
        left = [w for w in words if float(w.get("x0", 0)) < mid and float(w.get("x1", 0)) < mid + 20]
        right = [w for w in words if float(w.get("x0", 0)) >= mid - 20]
        overlap = len({id(x) for x in left} & {id(x) for x in right})
        column_mode = len(left) > 8 and len(right) > 8 and overlap == 0
        groups = [left, right] if column_mode else [words]
        output: list[LineHint] = []
        order = 0
        for group in groups:
            rows: list[list[dict[str, Any]]] = []
            for word in sorted(group, key=lambda w: (round(float(w.get("top", 0)) / 3) * 3, float(w.get("x0", 0)))):
                top = float(word.get("top", 0))
                target = next((row for row in rows if abs(float(row[0].get("top", 0)) - top) <= 3), None)
                if target is None:
                    target = []
                    rows.append(target)
                target.append(word)
            for row in sorted(rows, key=lambda r: float(r[0].get("top", 0))):
                row.sort(key=lambda w: float(w.get("x0", 0)))
                text = " ".join(str(w.get("text", "")) for w in row).strip()
                if not text:
                    continue
                fonts = [float(w.get("size", 0) or 0) for w in row]
                bold = any("bold" in str(w.get("fontname", "")).lower() for w in row)
                output.append(LineHint(
                    text, page, order, bold,
                    max(fonts) if fonts else None,
                    float(row[0].get("x0", 0)),
                    float(row[0].get("top", 0)),
                ))
                order += 1
        return output

    def _ocr_pdf(self, path: Path, result: LoadedDocument) -> None:
        try:
            import pytesseract  # type: ignore
            from pdf2image import convert_from_path  # type: ignore
            images = convert_from_path(str(path), dpi=250)
            ocr_lines: list[LineHint] = []
            for page_no, image in enumerate(images, 1):
                for order, line in enumerate(pytesseract.image_to_string(image).splitlines()):
                    if line.strip():
                        ocr_lines.append(LineHint(line, page_no, order, source="ocr"))
            if ocr_lines:
                result.lines = ocr_lines
                result.page_count = len(images)
                result.ocr_used = True
                result.methods.append("OCR:pytesseract")
                result.warnings.append("Scanned PDF detected; OCR used")
            else:
                result.errors.append("Scanned PDF detected but OCR produced no text")
        except ImportError:
            result.errors.append(
                "PDF has little or no extractable text; install pytesseract, pdf2image, "
                "Tesseract, and Poppler to enable OCR"
            )
        except Exception as exc:
            result.errors.append(f"Scanned PDF detected but OCR failed: {exc}")

    def _load_docx(self, path: Path) -> LoadedDocument:
        result = LoadedDocument(file_type="docx")
        try:
            from docx import Document  # type: ignore
            from docx.table import Table  # type: ignore
            from docx.text.paragraph import Paragraph  # type: ignore
        except ImportError:
            result.errors.append("python-docx is required to parse DOCX files")
            return result
        try:
            document = Document(str(path))
        except Exception as exc:
            result.errors.append(
                "DOCX is password-protected" if "password" in str(exc).lower()
                else f"DOCX is corrupted: {exc}"
            )
            return result

        order = 0
        for child in document.element.body.iterchildren():
            if child.tag.endswith("}p"):
                paragraph = Paragraph(child, document)
                hint = self._paragraph_hint(paragraph, order)
                if hint.text.strip():
                    result.lines.append(hint)
                    order += 1
            elif child.tag.endswith("}tbl"):
                table = Table(child, document)
                for row in table.rows:
                    text = " | ".join(
                        self._cell_text(c) for c in row.cells if self._cell_text(c)
                    )
                    if text.strip():
                        result.lines.append(LineHint(text, order=order, source="table"))
                        order += 1

        for section in document.sections:
            for source_name, part in (("header", section.header), ("footer", section.footer)):
                for paragraph in part.paragraphs:
                    if paragraph.text.strip():
                        hint = self._paragraph_hint(paragraph, order)
                        hint.source = source_name
                        result.lines.append(hint)
                        order += 1

        seen: set[str] = set()
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        for node in document.element.xpath(".//w:txbxContent"):
            text = " ".join(t.text or "" for t in node.findall(".//w:t", ns) if (t.text or "").strip()).strip()
            if text and text not in seen:
                seen.add(text)
                result.lines.append(LineHint(text, order=order, source="textbox"))
                order += 1
        result.methods.append("python-docx")
        if not result.lines:
            result.errors.append("No text found in DOCX")
        return result

    @staticmethod
    def _cell_text(cell: Any) -> str:
        return " ".join(p.text.strip() for p in cell.paragraphs if p.text.strip())

    @staticmethod
    def _paragraph_hint(paragraph: Any, order: int) -> LineHint:
        runs = [r for r in paragraph.runs if r.text.strip()]
        bold = bool(runs) and sum(1 for r in runs if r.bold) >= max(1, math.ceil(len(runs) / 2))
        sizes = [r.font.size.pt for r in runs if r.font.size is not None]
        return LineHint(paragraph.text, order=order, bold=bold,
                        font_size=max(sizes) if sizes else None)


# ============================================================================
# Text cleaner
# ============================================================================

class TextCleaner:
    LIGATURES = str.maketrans({"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"})
    BULLETS = re.compile(r"^[\s\u2022\u2023\u25E6\u2043\u2219\u25AA\u25CF\u00B7\uf0b7●▪◦]+")
    PAGE_NUMBER = re.compile(r"^(?:page\s*)?\d+(?:\s*(?:/|of)\s*\d+)?$", re.I)

    def clean(self, document: LoadedDocument) -> list[LineHint]:
        lines: list[LineHint] = []
        for hint in document.lines:
            text = unicodedata.normalize("NFKC", hint.text.translate(self.LIGATURES))
            text = text.replace("\u200b", "").replace("\xa0", " ")
            text = re.sub(r"[\t\r ]+", " ", text).strip()
            text = self.BULLETS.sub("- ", text)
            if not text or self.PAGE_NUMBER.fullmatch(text):
                continue
            lines.append(LineHint(text, hint.page, hint.order, hint.bold,
                                  hint.font_size, hint.x0, hint.y0, hint.source))

        page_count = max((line.page for line in lines), default=1)
        if page_count > 1:
            counts = Counter(self._repeat_key(line.text) for line in lines)
            threshold = max(2, math.ceil(page_count * 0.6))
            repeated = {k for k, c in counts.items() if c >= threshold and len(k) < 100}
            lines = [line for line in lines if self._repeat_key(line.text) not in repeated]

        joined: list[LineHint] = []
        for line in lines:
            if (joined and joined[-1].page == line.page and joined[-1].text.endswith("-")
                    and re.match(r"^[a-z]", line.text)):
                joined[-1].text = joined[-1].text[:-1] + line.text
            else:
                joined.append(line)
        for i, line in enumerate(joined):
            line.order = i
        return joined

    @staticmethod
    def _repeat_key(text: str) -> str:
        return re.sub(r"\d+", "#", text.casefold()).strip()


# ============================================================================
# Date parser
# ============================================================================

class DateParser:
    MONTHS = {name.casefold(): i for i, name in enumerate(calendar.month_name) if name}
    MONTHS.update({name.casefold(): i for i, name in enumerate(calendar.month_abbr) if name})
    MONTHS.update({"sept": 9})
    CURRENT = {"present", "current", "now", "till date", "ongoing", "to date"}

    _MONTH_WORD = (
        r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    )
    DATE_TOKEN = (
        rf"(?:{_MONTH_WORD}[,.]?\s+\d{{4}}"
        rf"|(?:0?[1-9]|1[0-2])[/-]\d{{4}}"
        rf"|\d{{4}}(?:[/-](?:0?[1-9]|1[0-2]))?"
        rf"|(?:Spring|Summer|Fall|Autumn|Winter)\s+\d{{4}}"
        rf"|Present|Current|Now|Till\s+date|Ongoing|To\s+date)"
    )
    RANGE_RE = re.compile(
        rf"(?P<start>{DATE_TOKEN})\s*(?:-|–|—|to|until|through)\s*(?P<end>{DATE_TOKEN})", re.I
    )
    SINGLE_RE = re.compile(DATE_TOKEN, re.I)

    @classmethod
    def normalize(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        clean = re.sub(r"[,\s]+", " ", value.strip()).casefold()
        if clean in cls.CURRENT:
            return "present"
        year_match = re.search(r"\b(19|20)\d{2}\b", clean)
        if not year_match:
            return None
        year = int(year_match.group())
        numeric = re.search(r"\b(0?[1-9]|1[0-2])[/-](?:19|20)\d{2}\b", clean)
        if numeric:
            return f"{year:04d}-{int(numeric.group(1)):02d}"
        for month, number in cls.MONTHS.items():
            if re.search(rf"\b{re.escape(month)}\b", clean):
                return f"{year:04d}-{number:02d}"
        for season, number in (("spring", 3), ("summer", 6), ("fall", 9),
                               ("autumn", 9), ("winter", 12)):
            if season in clean:
                return f"{year:04d}-{number:02d}"
        return str(year)

    @classmethod
    def extract_range(cls, text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        match = cls.RANGE_RE.search(text)
        if match:
            raw = match.group(0)
            return cls.normalize(match.group("start")), cls.normalize(match.group("end")), raw
        matches = cls.SINGLE_RE.findall(text)
        if matches:
            raw = str(matches[0])
            normalized = cls.normalize(raw)
            return normalized, normalized, raw
        return None, None, None


# ============================================================================
# Rule-based extractor
# ============================================================================

class RuleBasedExtractor:
    EMAIL_RE = re.compile(r"(?<![\w.+-])([\w.+-]+@[\w-]+(?:\.[\w-]+)+)", re.I)
    URL_RE = re.compile(
        r"(?:(?:https?://|www\.)[^\s<>{}\[\]]+|(?:linkedin\.com|github\.com)/[^\s<>{}\[\]]+)", re.I
    )
    PHONE_RE = re.compile(r"(?<!\w)(?:\+|00)?\d{1,3}[\s.-]?(?:\(?\d{2,4}\)?[\s.-]?){1,3}\d{3,5}(?!\w)")
    GPA_RE = re.compile(
        r"\b(?:GPA|CGPA)\s*[:=-]?\s*([0-9](?:\.[0-9]{1,2})?(?:\s*/\s*[0-9](?:\.0)?)?)|\b(\d{1,3}(?:\.\d+)?)\s*%",
        re.I,
    )
    CREDENTIAL_RE = re.compile(
        r"\b(?:credential|certificate|license)\s*(?:id|no\.?|number)?\s*[:#-]\s*([\w.-]+)", re.I
    )
    LABEL_RE = re.compile(
        r"^(date of birth|dob|nationality|gender|marital status)\s*[:|-]\s*(.+)$", re.I
    )

    TECHNICAL = {
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "PHP", "Ruby", "Swift",
        "Kotlin", "Scala", "Rust", "Go", "R", "MATLAB", "SQL", "HTML", "CSS", "Bash",
        "PowerShell", "Dart",
        "React", "React.js", "Angular", "Vue.js", "Next.js", "Node.js", "Express.js",
        "Django", "Flask", "FastAPI", "Spring Boot", ".NET", "Laravel", "Ruby on Rails",
        "Flutter", "React Native", "Tailwind CSS",
        "PostgreSQL", "MySQL", "SQL Server", "Oracle", "MongoDB", "Redis", "SQLite",
        "Elasticsearch", "DynamoDB", "Firebase", "Snowflake", "BigQuery", "Databricks",
        "AWS", "Azure", "Google Cloud",
        "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins", "GitHub Actions",
        "GitLab CI", "Linux", "Git", "REST API", "REST APIs", "GraphQL", "Microservices",
        "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
        "TensorFlow", "PyTorch", "scikit-learn", "Keras", "Pandas", "NumPy",
        "Spark", "Hadoop", "Airflow", "Kafka", "MLOps", "Data Analysis",
        "Data Engineering", "Data Science", "ETL", "Statistics",
        "RNN", "CNN", "LSTM", "Transformer", "Neural Network Design",
        "Model Training", "Model Evaluation", "Model Training & Evaluation",
        "Text Preprocessing", "Tokenization", "Sequence Modeling",
        "CNN-based Classification", "Facial & Body Landmark Tracking",
        "Generative AI", "Agentic AI", "Autonomous AI Agents",
        "LLM", "LLM API Integration", "Prompt Engineering", "Fine-tuning",
        "Retrieval-Augmented Generation", "RAG",
        "Vector Databases", "Embeddings",
        "Cybersecurity", "Penetration Testing", "Network Security", "DevOps",
        "CI/CD", "Agile", "Scrum", "SEO", "SEM", "Google Analytics",
        "Content Marketing", "Performance Marketing", "A/B Testing",
        "Financial Analysis", "Forecasting", "Risk Management", "Supply Chain",
        "CRM", "ERP", "SAP", "Dynamics 365", "Salesforce",
        "Figma", "UI/UX", "Graphic Design", "AutoCAD", "SolidWorks",
    }
    TOOLS = {
        "Microsoft Excel", "Microsoft Word", "PowerPoint", "Power BI", "Tableau",
        "Looker", "Jira", "Confluence", "Trello", "Asana", "Notion", "Slack",
        "Google Workspace", "Microsoft Office",
        "Adobe Photoshop", "Adobe Illustrator", "Adobe XD", "Canva", "Figma",
        "Postman", "Visual Studio Code", "IntelliJ IDEA", "Eclipse", "Jupyter",
        "HubSpot", "Mailchimp", "Google Ads", "Meta Ads",
        "OpenAI", "Groq", "Anthropic", "LangChain", "LlamaIndex",
        "ChromaDB", "Pinecone", "Weaviate", "FAISS",
        "Hugging Face", "Transformers", "PyPDF", "Mistral",
    }
    SOFT = {
        "Communication", "Leadership", "Teamwork", "Problem Solving",
        "Critical Thinking", "Creativity", "Time Management", "Adaptability",
        "Collaboration", "Negotiation", "Presentation", "Decision Making",
        "Attention to Detail", "Conflict Resolution", "Project Management",
        "Stakeholder Management", "Customer Service", "Analytical Thinking",
        "Interpersonal Skills", "Mentoring", "Strategic Planning",
    }
    SKILL_LOOKUP = {s.casefold(): s for s in TECHNICAL | TOOLS | SOFT}
    SHORT_SKILLS = {"c", "r", "go"}

    DEGREE_RE = re.compile(
        r"\b(?:Ph\.?D|Doctorate|M\.?Phil|MBA|MSc|M\.S\.?|Master(?:'s)?|BSc|B\.S\.?|"
        r"B\.Tech|B\.E\.?|Bachelor(?:'s)?|Associate(?:'s)?|Diploma|FSc|FA|ICS|ICom|"
        r"Intermediate|A[- ]Levels?|O[- ]Levels?|Matric(?:ulation)?)\b",
        re.I,
    )
    JOB_RE = re.compile(
        r"\b(?:intern|trainee|assistant|associate|specialist|analyst|consultant|"
        r"coordinator|officer|engineer|developer|designer|administrator|executive|"
        r"manager|director|head|lead|supervisor|architect|scientist|teacher|lecturer|"
        r"professor|accountant|recruiter|writer|editor|founder|president|salesperson)\b",
        re.I,
    )
    CERT_PROVIDER_RE = re.compile(
        r"\b(?:Microsoft|Google|Amazon|AWS|Cisco|Oracle|IBM|Coursera|Udemy|edX|PMI|CompTIA|Meta)\b",
        re.I,
    )

    # ---------- contacts ----------

    def extract_contacts(self, text: str) -> dict[str, Any]:
        emails = self._dedupe(self.EMAIL_RE.findall(text))
        urls = self._dedupe(self._clean_url(x) for x in self.URL_RE.findall(text))
        phones: list[str] = []
        for match in self.PHONE_RE.finditer(text):
            value = match.group().strip(" .,-")
            digits = re.sub(r"\D", "", value)
            if 7 <= len(digits) <= 15 and not re.fullmatch(r"(?:19|20)\d{2}(?:\D.*)?", value):
                phones.append(value)
        phones = self._dedupe(phones)
        links: dict[str, Any] = {"linkedin": None, "github": None, "portfolio": None, "other": []}
        for url in urls:
            host = urlparse(url).netloc.casefold()
            if "linkedin.com" in host and links["linkedin"] is None:
                links["linkedin"] = url
            elif "github.com" in host and links["github"] is None:
                links["github"] = url
            elif links["portfolio"] is None and not any(
                x in host for x in ("facebook.com", "twitter.com", "x.com", "instagram.com")
            ):
                links["portfolio"] = url
            else:
                links["other"].append(url)
        return {"emails": emails, "phones": phones, "links": links}

    @staticmethod
    def _clean_url(value: str) -> str:
        value = value.rstrip(".,;:)")
        return value if value.startswith(("http://", "https://")) else "https://" + value

    def extract_sensitive_labels(self, lines: Sequence[LineHint]) -> dict[str, Optional[str]]:
        values = {"date_of_birth": None, "nationality": None,
                  "gender": None, "marital_status": None}
        mapping = {"date of birth": "date_of_birth", "dob": "date_of_birth",
                   "nationality": "nationality", "gender": "gender",
                   "marital status": "marital_status"}
        for line in lines:
            m = self.LABEL_RE.match(line.text)
            if m:
                values[mapping[m.group(1).casefold()]] = m.group(2).strip()
        return values

    # ---------- skills ----------

    @staticmethod
    def _split_skill_chunks(line: str) -> list[str]:
        out, buf, depth = [], "", 0
        for ch in line:
            if ch == "(":
                depth += 1
                buf += ch
            elif ch == ")":
                depth = max(0, depth - 1)
                buf += ch
            elif ch in ",;|·•" and depth == 0:
                out.append(buf)
                buf = ""
            else:
                buf += ch
        if buf:
            out.append(buf)
        return [c.strip() for c in out if c.strip()]

    @staticmethod
    def _join_continuations(lines: list[str]) -> list[str]:
        """Join lines that PDF extraction has wrapped mid-phrase.

        Trigger rules (conservative):
          - previous line ends with a comma, or
          - current line starts with '&' (e.g. "& Body Landmark Tracking"), or
          - previous line has unbalanced parentheses.
        Bullets ("- ...") are never merged backwards.
        """
        joined: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if joined and not stripped.startswith("- "):
                prev = joined[-1].rstrip()
                prev_unbalanced_parens = prev.count("(") > prev.count(")")
                if prev.endswith(",") or stripped.startswith("&") or prev_unbalanced_parens:
                    joined[-1] = prev + " " + stripped
                    continue
            joined.append(stripped)
        return joined

    def extract_skills(self, text: str, in_skill_section: bool = False) -> dict[str, list[str]]:
        lower = text.casefold()
        found: set[str] = set()

        for key, display in self.SKILL_LOOKUP.items():
            if key in self.SHORT_SKILLS and not in_skill_section:
                continue
            if re.search(rf"(?<![\w+#.]){re.escape(key)}(?![\w+#.])", lower):
                found.add(display)

        if in_skill_section:
            raw_lines = [re.sub(r"^-\s*", "", x).strip() for x in text.splitlines()]
            raw_lines = self._join_continuations(raw_lines)
            for line in raw_lines:
                if not line:
                    continue
                if ":" in line:
                    _, line = line.split(":", 1)
                for chunk in self._split_skill_chunks(line):
                    m = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", chunk)
                    pieces: list[str] = []
                    if m:
                        pieces.append(m.group(1).strip())
                        pieces.extend(p.strip() for p in m.group(2).split(","))
                    else:
                        pieces.append(chunk.strip(" .,:;"))
                    for piece in pieces:
                        if (
                            2 < len(piece) < 70
                            and len(piece.split()) <= 8
                            and not DateParser.SINGLE_RE.search(piece)
                            and not re.search(r"@|https?:", piece)
                        ):
                            found.add(piece)

        technical, tools, soft = [], [], []
        for item in found:
            if item in self.SOFT:
                soft.append(item)
            elif item in self.TOOLS:
                tools.append(item)
            elif item in self.TECHNICAL:
                technical.append(item)
            else:
                technical.append(item)
        return {
            "technical_skills": self._dedupe(technical),
            "soft_skills": self._dedupe(soft),
            "tools_and_technologies": self._dedupe(tools),
            "all_skills": self._dedupe(technical + tools + soft),
        }

    @staticmethod
    def _dedupe(values: Iterable[str]) -> list[str]:
        seen, out = set(), []
        for v in values:
            clean = re.sub(r"\s+", " ", str(v)).strip()
            key = clean.casefold()
            if clean and key not in seen:
                seen.add(key)
                out.append(clean)
        return out


# ============================================================================
# NER
# ============================================================================

class NERExtractor:
    def __init__(self, warnings: list[str], methods: list[str]) -> None:
        self.spacy_nlp = None
        self.hf_pipeline = None
        try:
            import spacy  # type: ignore
            model = "en_core_web_trf" if spacy.util.is_package("en_core_web_trf") else "en_core_web_sm"
            try:
                self.spacy_nlp = spacy.load(model)
                methods.append(f"spaCy:{model}")
            except OSError:
                warnings.append("spaCy is installed but no English model is available; rules-only NER used")
        except ImportError:
            warnings.append("spaCy is unavailable; rules-only NER used")

        local_model = os.getenv("CV_PARSER_HF_MODEL")
        if local_model:
            try:
                from transformers import pipeline  # type: ignore
                self.hf_pipeline = pipeline("token-classification", model=local_model,
                                            aggregation_strategy="simple", local_files_only=True)
                methods.append("HuggingFaceNER:local")
            except Exception as exc:
                warnings.append(f"Local Hugging Face NER model could not be loaded: {exc}")

    def entities(self, text: str) -> dict[str, list[str]]:
        output: dict[str, list[str]] = {"PERSON": [], "ORG": [], "GPE": [], "LOC": [], "DATE": []}
        if self.spacy_nlp and text.strip():
            doc = self.spacy_nlp(text[:100_000])
            for entity in doc.ents:
                if entity.label_ in output:
                    output[entity.label_].append(entity.text.strip())
        if self.hf_pipeline and text.strip():
            try:
                for entity in self.hf_pipeline(text[:20_000]):
                    label = str(entity.get("entity_group", "")).upper()
                    mapped = {"PER": "PERSON", "PERSON": "PERSON", "ORG": "ORG",
                              "LOC": "LOC", "GPE": "GPE", "DATE": "DATE"}.get(label)
                    if mapped:
                        output[mapped].append(str(entity.get("word", "")).strip())
            except Exception as exc:
                LOGGER.warning("HF inference failed: %s", exc)
        for k, v in output.items():
            output[k] = RuleBasedExtractor._dedupe(v)
        return output


# ============================================================================
# Section detector
# ============================================================================

class SectionDetector:
    ALIASES: dict[str, set[str]] = {
        "summary": {"summary", "professional summary", "profile", "professional profile",
                    "objective", "career objective", "about me", "executive summary",
                    "personal statement"},
        "skills": {"skills", "key skills", "core skills", "competencies",
                   "core competencies", "technical skills", "technical expertise",
                   "expertise", "areas of expertise", "tools", "technologies"},
        "education": {"education", "academic background", "academic qualifications",
                      "education history", "educational background", "academics",
                      "educational qualifications"},
        "qualifications": {"qualifications", "professional qualifications", "licenses",
                           "memberships", "licenses and memberships",
                           "professional memberships"},
        "experience": {"experience", "work experience", "professional experience",
                       "employment history", "career history", "work history",
                       "employment", "career experience"},
        "projects": {"projects", "key projects", "personal projects",
                     "academic projects", "selected projects"},
        "certifications": {"certifications", "certificates", "certification",
                           "courses and certifications", "courses & certifications",
                           "licenses & certifications", "training",
                           "professional development"},
        "languages": {"languages", "language skills", "linguistic skills"},
        "awards_and_achievements": {"awards", "achievements", "honors", "honours",
                                    "awards and achievements", "accomplishments"},
        "publications": {"publications", "research", "papers", "articles"},
        "volunteer_experience": {"volunteer experience", "volunteering",
                                 "community service", "voluntary work"},
        "interests": {"interests", "hobbies", "hobbies and interests",
                      "personal interests"},
        "references": {"references", "referees"},
    }
    REVERSE = {alias: key for key, aliases in ALIASES.items() for alias in aliases}

    def __init__(self) -> None:
        try:
            from rapidfuzz import fuzz  # type: ignore
            self._fuzz = fuzz
        except ImportError:
            self._fuzz = None

    @staticmethod
    def _heading_text(text: str) -> str:
        text = re.sub(r"[:|\-–—]+$", "", text.strip())
        return re.sub(r"[^a-z0-9& ]", "", text.casefold()).strip()

    def classify_heading(
        self,
        line: LineHint,
        median_font: float,
        current_section: str = "preamble",
        seen_first_section: bool = False,
    ) -> tuple[Optional[str], float, Optional[str]]:
        raw = line.text.strip()
        clean = self._heading_text(raw)
        word_count = len(clean.split())
        if not clean or word_count > 7 or len(clean) > 65:
            return None, 0.0, None

        if clean in self.REVERSE:
            return self.REVERSE[clean], 0.99, raw

        is_all_caps = raw.isupper() and len(raw) > 2 and any(c.isalpha() for c in raw)
        has_dash_sep = bool(re.search(r"\s[—–-]\s|\s\|\s", raw))
        candidate_heading = (
            line.bold or raw.endswith(":") or is_all_caps
            or (line.font_size is not None and line.font_size >= median_font * 1.12)
        )

        best_key, best_score = None, 0.0
        if self._fuzz:
            for alias, key in self.REVERSE.items():
                score = float(self._fuzz.ratio(clean, alias)) / 100
                if score > best_score:
                    best_key, best_score = key, score
        if best_score >= 0.88 and (candidate_heading or best_score >= 0.94):
            return best_key, best_score, raw

        # "additional" only after a real section has started, only ALL-CAPS,
        # no dash separator, no job keywords, no digits/@.
        if (
            seen_first_section
            and is_all_caps
            and 2 <= word_count <= 5
            and not has_dash_sep
            and not self._looks_like_content(raw)
            and not RuleBasedExtractor.JOB_RE.search(raw)
            and not re.search(r"\d", raw)
        ):
            return "additional", 0.60, raw.rstrip(":")

        return None, 0.0, None

    @staticmethod
    def _looks_like_content(text: str) -> bool:
        return bool(re.search(r"@|https?://|\b\d{4}\b|\+?\d[\d ()-]{6,}", text))

    def split(self, lines: list[LineHint]) -> tuple[dict[str, list[LineHint]],
                                                     dict[str, list[LineHint]],
                                                     dict[str, float]]:
        sizes = sorted(x.font_size for x in lines if x.font_size)
        median = sizes[len(sizes) // 2] if sizes else 10.0
        sections: dict[str, list[LineHint]] = defaultdict(list)
        additional: dict[str, list[LineHint]] = defaultdict(list)
        scores: dict[str, float] = {}
        current, current_extra = "preamble", None
        seen_first_section = False
        for line in lines:
            category, score, heading = self.classify_heading(
                line, median, current, seen_first_section
            )
            if category:
                if category == "additional":
                    current, current_extra = "additional", heading
                    scores[f"additional:{heading}"] = score
                else:
                    current, current_extra = category, None
                    scores[category] = max(scores.get(category, 0), score)
                seen_first_section = True
                continue
            if current == "additional" and current_extra:
                additional[current_extra].append(line)
            else:
                sections[current].append(line)
        return dict(sections), dict(additional), scores


# ============================================================================
# Entry parser
# ============================================================================

class EntryParser:
    _FIELD_KEYWORDS = re.compile(
        r"\b(computer|science|engineering|arts|commerce|business|economics|"
        r"physics|chemistry|biology|mathematics|math|management|technology|"
        r"information|data|software|electrical|mechanical|civil|chemical|"
        r"philosophy|history|literature|education|law|medicine|nursing|"
        r"psychology|accounting|finance)\b",
        re.I,
    )

    def __init__(self, rules: RuleBasedExtractor, ner: NERExtractor) -> None:
        self.rules, self.ner = rules, ner

    # ---------- splitting ----------

    @staticmethod
    def split_entries(lines: Sequence[LineHint], kind: str) -> list[list[str]]:
        clean = [x.text.strip() for x in lines if x.text.strip()]
        if not clean:
            return []

        if kind == "certifications":
            bullets = [x for x in clean if x.startswith("- ")]
            if len(bullets) >= 2:
                return [[b] for b in bullets]

        if kind == "projects":
            return EntryParser._split_projects(clean)

        entries, current = [], []
        for line in clean:
            date_range = bool(DateParser.RANGE_RE.search(line))
            cue = bool(
                RuleBasedExtractor.DEGREE_RE.search(line) if kind == "education"
                else RuleBasedExtractor.JOB_RE.search(line) if kind == "experience"
                else False
            )
            if re.fullmatch(r"[-–—_ ]{3,}", line):
                if current:
                    entries.append(current)
                    current = []
                continue
            if current:
                if cue and not date_range:
                    if any(DateParser.RANGE_RE.search(x) for x in current) or any(
                        x.startswith("- ") for x in current
                    ):
                        entries.append(current)
                        current = []
                elif date_range and any(DateParser.RANGE_RE.search(x) for x in current):
                    entries.append(current)
                    current = []
            current.append(line)
        if current:
            entries.append(current)
        return entries

    @staticmethod
    def _is_tech_line(line: str) -> bool:
        return bool(re.search(r"[·|]", line))

    @staticmethod
    def _split_projects(clean: list[str]) -> list[list[str]]:
        entries, current, seen_bullet = [], [], False
        for line in clean:
            if line.startswith("- "):
                current.append(line)
                seen_bullet = True
                continue
            has_content = seen_bullet or any(EntryParser._is_tech_line(x) for x in current)
            if has_content and not EntryParser._is_tech_line(line):
                entries.append(current)
                current = [line]
                seen_bullet = False
            else:
                current.append(line)
        if current:
            entries.append(current)
        return entries

    # ---------- education ----------

    @staticmethod
    def _parse_degree_line(line: Optional[str]) -> tuple[Optional[str], Optional[str], Optional[str]]:
        if not line:
            return None, None, None
        m = RuleBasedExtractor.DEGREE_RE.search(line)
        if not m:
            return None, None, None
        degree = m.group(0)
        remainder = line[m.end():].strip(" ,:-—–|")
        remainder = re.sub(r"^(?:in|of|in\s+the\s+field\s+of)\s+", "", remainder, flags=re.I)
        if not remainder:
            return degree, None, None
        parts = re.split(r"\s*[—–|]\s*|,\s*|\s+at\s+|\s+from\s+", remainder)
        field_, institution = None, None
        for part in (p.strip() for p in parts if p.strip()):
            if re.search(r"\b(university|college|institute|school|academy|polytechnic)\b", part, re.I):
                institution = part
            elif field_ is None and EntryParser._FIELD_KEYWORDS.search(part):
                field_ = part
            elif institution is None and not EntryParser._FIELD_KEYWORDS.search(part):
                institution = part
            elif field_ is None:
                field_ = part
        return degree, field_, institution

    def education(self, lines: Sequence[LineHint]) -> list[dict[str, Any]]:
        out = []
        for chunk in self.split_entries(lines, "education"):
            raw = "\n".join(chunk)
            start, end, date_raw = DateParser.extract_range(raw)
            degree_line = next((x for x in chunk if self.rules.DEGREE_RE.search(x)), None)
            degree, field_, institution = self._parse_degree_line(degree_line)

            if not institution:
                institution = next(iter(self.ner.entities(raw)["ORG"]), None)
            if not institution:
                for x in chunk:
                    m = re.search(
                        r"\b(?:[A-Z][\w&.'-]*\s+){1,4}"
                        r"(?:University|College|Institute|School|Academy|Polytechnic)\b",
                        x, re.I,
                    )
                    if m:
                        institution = m.group(0)
                        break

            grade_match = self.rules.GPA_RE.search(raw)
            grade = grade_match.group(0) if grade_match else None
            location = next(iter(self.ner.entities(raw)["GPE"]), None)
            description = "\n".join(
                x for x in chunk if x != degree_line and not DateParser.RANGE_RE.search(x)
            ) or None
            out.append({
                "degree": degree,
                "field_of_study": field_,
                "institution": institution,
                "location": location,
                "start_date": start,
                "end_date": end,
                "date_raw": date_raw,
                "grade": grade,
                "description": description,
                "raw_text": raw,
            })
        return self._nonempty(out, ("degree", "institution", "raw_text"))

    # ---------- experience ----------

    def experience(self, lines: Sequence[LineHint]) -> list[dict[str, Any]]:
        out = []
        for chunk in self.split_entries(lines, "experience"):
            raw = "\n".join(chunk)
            start, end, date_raw = DateParser.extract_range(raw)

            title_line = next(
                (x for x in chunk if self.rules.JOB_RE.search(self._without_dates(x))),
                None,
            )
            title: Optional[str] = None
            company: Optional[str] = None
            if title_line:
                title_clean = self._without_dates(title_line).strip(" |-—–,")
                m = re.match(r"^(.+?)\s*(?:—|–|\||\s-\s)\s*(.+)$", title_clean)
                if m:
                    left, right = m.group(1).strip(), m.group(2).strip()
                    if self.rules.JOB_RE.search(left) and not self.rules.JOB_RE.search(right):
                        title, company = left, right
                    elif self.rules.JOB_RE.search(right) and not self.rules.JOB_RE.search(left):
                        title, company = right, left
                    else:
                        title = title_clean
                else:
                    title = title_clean

            if not company:
                orgs = [x for x in self.ner.entities(raw)["ORG"]
                        if x.casefold() != (title or "").casefold()]
                if orgs:
                    company = orgs[0]
            if not company:
                company = self._company_heuristic(
                    [c for c in chunk if c != title_line], title
                )

            location = next(iter(self.ner.entities(raw)["GPE"]), None)
            responsibilities = [re.sub(r"^-\s*", "", x).strip()
                                for x in chunk if x.startswith("- ")]
            if not responsibilities:
                excluded = {x for x in (title_line, title, company) if x}
                responsibilities = [x for x in chunk[1:]
                                    if x not in excluded and not DateParser.RANGE_RE.search(x)]

            skills = self.rules.extract_skills(raw)
            out.append({
                "job_title": title,
                "position": title,
                "company": company,
                "location": location,
                "employment_type": self._employment_type(raw),
                "start_date": start,
                "end_date": end,
                "date_raw": date_raw,
                "is_current": end == "present",
                "duration_months": self._duration_months(start, end),
                "responsibilities": RuleBasedExtractor._dedupe(responsibilities),
                "technologies": skills["technical_skills"] + skills["tools_and_technologies"],
                "raw_text": raw,
            })
        return self._nonempty(out, ("job_title", "company", "date_raw"))

    # ---------- projects ----------

    def projects(self, lines: Sequence[LineHint]) -> list[dict[str, Any]]:
        out = []
        for chunk in self.split_entries(lines, "projects"):
            raw = "\n".join(chunk)
            start, end, _ = DateParser.extract_range(raw)
            urls = self.rules.extract_contacts(raw)["links"]
            all_urls = [x for x in [urls["github"], urls["portfolio"], *urls["other"]] if x]

            non_bullets = [x for x in chunk if not x.startswith("- ")]
            title = non_bullets[0].strip() if non_bullets else None
            tech_line = None
            for line in non_bullets[1:]:
                if self._is_tech_line(line):
                    tech_line = line.strip()
                    break

            tech_items: list[str] = []
            if tech_line:
                for item in re.split(r"\s*[·|]\s*", tech_line):
                    item = item.strip()
                    if item and len(item) < 60:
                        tech_items.append(item)

            skills = self.rules.extract_skills(raw)
            technologies = RuleBasedExtractor._dedupe(
                tech_items + skills["technical_skills"] + skills["tools_and_technologies"]
            )
            out.append({
                "name": title,
                "description": "\n".join(chunk[1:]) or None,
                "role": None,
                "technologies": technologies,
                "start_date": start,
                "end_date": end,
                "url": all_urls[0] if all_urls else None,
                "raw_text": raw,
            })
        return self._nonempty(out, ("name", "description"))

    # ---------- certifications ----------

    def certifications(self, lines: Sequence[LineHint]) -> list[dict[str, Any]]:
        out = []
        for chunk in self.split_entries(lines, "certifications"):
            raw = "\n".join(chunk)
            start, end, _ = DateParser.extract_range(raw)
            cred = self.rules.CREDENTIAL_RE.search(raw)

            issuer: Optional[str] = None
            explicit = re.search(r"(?:issued\s+by|issuer|by)\s*[:|-]\s*(.+)", raw, re.I)
            if explicit:
                issuer = explicit.group(1).strip(" .,:;")
            else:
                provider = self.rules.CERT_PROVIDER_RE.search(raw)
                if provider:
                    issuer = provider.group(0)

            first = re.sub(r"^-\s*", "", chunk[0]).strip() if chunk else ""
            name = re.sub(DateParser.RANGE_RE, "", first).strip(" |-—–,") or None

            contacts = self.rules.extract_contacts(raw)["links"]
            urls = [x for x in [contacts["portfolio"], contacts["linkedin"],
                                *contacts["other"]] if x]
            out.append({
                "name": name,
                "issuer": issuer,
                "issue_date": start,
                "expiry_date": end if end != start else None,
                "credential_id": cred.group(1) if cred else None,
                "url": urls[0] if urls else None,
                "raw_text": raw,
            })
        return self._nonempty(out, ("name", "issuer", "credential_id"))

    # ---------- helpers ----------

    @staticmethod
    def list_section(lines: Sequence[LineHint]) -> list[str]:
        values: list[str] = []
        for line in lines:
            parts = re.split(r"\s*[;|•·]\s*|,\s+(?=[A-Z])",
                             re.sub(r"^-\s*", "", line.text))
            values.extend(x.strip() for x in parts if x.strip())
        return RuleBasedExtractor._dedupe(values)

    @staticmethod
    def languages(lines: Sequence[LineHint]) -> list[dict[str, Optional[str]]]:
        levels = (r"native|fluent|professional|advanced|intermediate|basic|"
                  r"elementary|beginner|conversational|proficient")
        out = []
        for value in EntryParser.list_section(lines):
            m = re.match(rf"(.+?)(?:\s*[-:|(]\s*({levels})\)?)?$", value, re.I)
            if m:
                out.append({
                    "language": m.group(1).strip(),
                    "proficiency": m.group(2).title() if m.group(2) else None,
                })
        return out

    @staticmethod
    def _company_heuristic(lines: Sequence[str], title: Optional[str]) -> Optional[str]:
        for line in lines[:4]:
            if line.startswith("- "):
                continue
            clean = re.sub(DateParser.RANGE_RE, "", line).strip(" |-—–,")
            if clean and clean != title and not RuleBasedExtractor.JOB_RE.search(clean) \
                    and len(clean.split()) <= 10:
                return clean
        return None

    @staticmethod
    def _employment_type(text: str) -> Optional[str]:
        types = {"full time": "Full-time", "full-time": "Full-time",
                 "part time": "Part-time", "part-time": "Part-time",
                 "internship": "Internship", "intern": "Internship",
                 "freelance": "Freelance", "contract": "Contract",
                 "temporary": "Temporary", "volunteer": "Volunteer",
                 "self-employed": "Self-employed"}
        lower = text.casefold()
        return next((v for k, v in types.items()
                     if re.search(rf"\b{re.escape(k)}\b", lower)), None)

    @staticmethod
    def _without_dates(text: str) -> str:
        return DateParser.RANGE_RE.sub("", text)

    @staticmethod
    def _duration_months(start: Optional[str], end: Optional[str]) -> Optional[int]:
        interval = HybridMerger.to_month_interval(start, end)
        return interval[1] - interval[0] + 1 if interval else None

    @staticmethod
    def _nonempty(items: list[dict[str, Any]],
                  fields: Sequence[str]) -> list[dict[str, Any]]:
        return [x for x in items if any(x.get(f) for f in fields)]


# ============================================================================
# Hybrid merger
# ============================================================================

class HybridMerger:
    @staticmethod
    def to_month_interval(start: Optional[str], end: Optional[str]) -> Optional[tuple[int, int]]:
        def month_index(value: Optional[str], is_end: bool = False) -> Optional[int]:
            if not value:
                return None
            if value == "present":
                now = datetime.now()
                return now.year * 12 + now.month - 1
            m = re.fullmatch(r"(\d{4})(?:-(\d{2}))?", value)
            if not m:
                return None
            year = int(m.group(1))
            month = int(m.group(2) or (12 if is_end else 1))
            return year * 12 + month - 1
        s, e = month_index(start), month_index(end, True)
        return (s, e) if s is not None and e is not None and e >= s else None

    @classmethod
    def total_experience(cls, experience: Sequence[dict[str, Any]]) -> Optional[float]:
        intervals = [cls.to_month_interval(x.get("start_date"), x.get("end_date"))
                     for x in experience]
        valid = sorted(x for x in intervals if x)
        if not valid:
            return None
        merged: list[list[int]] = []
        for start, end in valid:
            if not merged or start > merged[-1][1] + 1:
                merged.append([start, end])
            else:
                merged[-1][1] = max(merged[-1][1], end)
        months = sum(end - start + 1 for start, end in merged)
        return round(months / 12, 2)


# ============================================================================
# Result shape & orchestrator
# ============================================================================

def empty_result(file_path: str | Path) -> dict[str, Any]:
    path = Path(file_path)
    return {
        "personal_information": {
            "full_name": None, "first_name": None, "last_name": None,
            "emails": [], "phones": [],
            "location": {"city": None, "state": None, "country": None, "raw": None},
            "links": {"linkedin": None, "github": None, "portfolio": None, "other": []},
            "date_of_birth": None, "nationality": None, "gender": None,
            "marital_status": None,
        },
        "summary": None,
        "skills": {"technical_skills": [], "soft_skills": [],
                   "tools_and_technologies": [], "all_skills": []},
        "education": [], "qualifications": [], "experience": [],
        "total_experience_years": None, "projects": [], "certifications": [],
        "languages": [], "awards_and_achievements": [], "publications": [],
        "volunteer_experience": [], "interests": [], "references": [],
        "additional_sections": {},
        "metadata": {
            "file_name": path.name or None,
            "file_type": path.suffix.lower().lstrip(".") or None,
            "page_count": None,
            "parsed_at": datetime.now().astimezone().isoformat(),
            "parser_version": VERSION,
            "parser_file": __file__,
            "methods_used": [], "ocr_used": False,
            "confidence_scores": {}, "warnings": [], "errors": [],
        },
    }


class CVParser:
    _TECH_LOCATION_BLACKLIST = {
        "openai", "google", "microsoft", "amazon", "aws", "meta", "apple", "ibm",
        "oracle", "sap", "salesforce", "adobe", "groq", "anthropic", "hugging face",
        "langchain", "chromadb", "pinecone", "weaviate", "faiss", "tensorflow",
        "pytorch", "keras", "python", "java", "javascript", "react", "node",
        "django", "flask", "next.js",
    }

    def __init__(self) -> None:
        self.loader = DocumentLoader()
        self.cleaner = TextCleaner()
        self.detector = SectionDetector()
        self.rules = RuleBasedExtractor()

    def parse(self, file_path: str | Path) -> dict[str, Any]:
        result = empty_result(file_path)
        loaded = self.loader.load(file_path)
        md = result["metadata"]
        md.update({
            "file_type": loaded.file_type,
            "page_count": loaded.page_count,
            "methods_used": loaded.methods,
            "ocr_used": loaded.ocr_used,
            "warnings": loaded.warnings,
            "errors": loaded.errors,
        })
        if loaded.errors and not loaded.lines:
            return result

        lines = self.cleaner.clean(loaded)
        if not lines:
            md["errors"].append("No usable text remained after normalization")
            return result

        md["methods_used"].append("rules")
        ner = NERExtractor(md["warnings"], md["methods_used"])
        entry_parser = EntryParser(self.rules, ner)

        sections, additional, section_scores = self.detector.split(lines)
        full_text = "\n".join(x.text for x in lines)
        contacts = self.rules.extract_contacts(full_text)

        pi = result["personal_information"]
        pi["emails"] = contacts["emails"]
        pi["phones"] = contacts["phones"]
        pi["links"] = contacts["links"]
        pi.update(self.rules.extract_sensitive_labels(lines))

        self._extract_identity(result, lines, sections.get("preamble", []), ner)
        result["summary"] = self._section_text(sections.get("summary", []))

        skill_text = self._section_text(sections.get("skills", [])) or ""
        result["skills"] = self.rules.extract_skills(skill_text, in_skill_section=True)
        ctx = self.rules.extract_skills(full_text, in_skill_section=False)
        for key in result["skills"]:
            result["skills"][key] = self.rules._dedupe(result["skills"][key] + ctx[key])

        result["education"] = entry_parser.education(sections.get("education", []))
        result["qualifications"] = entry_parser.list_section(sections.get("qualifications", []))
        result["experience"] = entry_parser.experience(sections.get("experience", []))
        result["projects"] = entry_parser.projects(sections.get("projects", []))
        result["certifications"] = entry_parser.certifications(sections.get("certifications", []))
        result["languages"] = entry_parser.languages(sections.get("languages", []))
        for key in ("awards_and_achievements", "publications", "volunteer_experience",
                    "interests", "references"):
            result[key] = entry_parser.list_section(sections.get(key, []))

        result["additional_sections"] = {
            heading: {
                "content": self._section_text(body),
                "raw_text": "\n".join(x.text for x in body),
            }
            for heading, body in additional.items()
        }
        for heading in additional:
            md["warnings"].append(
                f"Section '{heading}' not recognized; stored in additional_sections"
            )

        result["total_experience_years"] = HybridMerger.total_experience(result["experience"])
        md["confidence_scores"] = self._confidence(result, section_scores)
        self._warnings(result)
        md["warnings"] = self.rules._dedupe(md["warnings"])
        md["methods_used"] = self.rules._dedupe(md["methods_used"])
        return result

    def _extract_identity(self, result, lines, preamble, ner):
        top = list(preamble[:12])
        if not top:
            sizes = sorted(x.font_size for x in lines if x.font_size)
            mf = sizes[len(sizes) // 2] if sizes else 10.0
            top = [
                x for x in lines[:6]
                if not self.detector.classify_heading(x, mf, "preamble", False)[0]
            ]
        top_text = "\n".join(x.text for x in top)
        entities = ner.entities(top_text)
        rejected = re.compile(
            r"\b(?:curriculum vitae|resume|cv|profile|summary|engineer|manager|"
            r"developer|specialist|consultant|director|designer|analyst|address|"
            r"phone|email)\b", re.I,
        )
        candidates = [x for x in entities["PERSON"]
                      if 1 < len(x.split()) <= 5 and not rejected.search(x)]
        for line in top[:6]:
            text = line.text.strip()
            if (
                2 <= len(text.split()) <= 5
                and re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ' .-]+", text)
                and not rejected.search(text)
                and not self.rules.DEGREE_RE.search(text)
            ):
                candidates.append(text)

        email_user = (result["personal_information"]["emails"][0].split("@")[0]
                      if result["personal_information"]["emails"] else "")

        def score(name: str) -> float:
            words = [x.casefold() for x in re.findall(r"[A-Za-z]+", name)]
            email_score = sum(1 for x in words if len(x) > 2
                              and x in email_user.casefold()) * 0.2
            line_score = 0.2 if any(
                x.text.strip().casefold() == name.casefold() and (x.bold or x.font_size)
                for x in top) else 0.0
            return 0.55 + email_score + line_score

        name = max(self.rules._dedupe(candidates), key=score, default=None)
        pi = result["personal_information"]
        pi["full_name"] = name
        if name:
            parts = name.split()
            pi["first_name"] = parts[0]
            pi["last_name"] = parts[-1] if len(parts) > 1 else None

        location_raw: Optional[str] = None
        for line in top:
            if re.search(r"@|https?://", line.text):
                continue
            for loc in entities["GPE"] + entities["LOC"]:
                if loc.casefold() in self._TECH_LOCATION_BLACKLIST:
                    continue
                if name and loc.casefold() == name.casefold():
                    continue
                if loc in line.text:
                    location_raw = loc
                    break
            if location_raw:
                break

        if location_raw:
            parts = [p.strip() for p in location_raw.split(",")]
            pi["location"] = {
                "city": parts[0] or None,
                "state": parts[1] if len(parts) > 2 else None,
                "country": parts[-1] if len(parts) > 1 else None,
                "raw": location_raw,
            }

    @staticmethod
    def _section_text(lines: Sequence[LineHint]) -> Optional[str]:
        text = "\n".join(re.sub(r"^-\s*", "", x.text) for x in lines).strip()
        return text or None

    @staticmethod
    def _confidence(result, heading_scores):
        pi = result["personal_information"]
        personal = (0.2 + (0.3 if pi["full_name"] else 0)
                    + (0.25 if pi["emails"] else 0) + (0.15 if pi["phones"] else 0))
        return {
            "personal_information": round(min(personal, 1), 2),
            "summary": round(heading_scores.get("summary", 0.35 if result["summary"] else 0), 2),
            "skills": round(max(heading_scores.get("skills", 0),
                                0.65 if result["skills"]["all_skills"] else 0), 2),
            "education": round(max(heading_scores.get("education", 0),
                                   0.55 if result["education"] else 0), 2),
            "experience": round(max(heading_scores.get("experience", 0),
                                    0.55 if result["experience"] else 0), 2),
            "projects": round(max(heading_scores.get("projects", 0),
                                  0.55 if result["projects"] else 0), 2),
            "certifications": round(max(heading_scores.get("certifications", 0),
                                        0.55 if result["certifications"] else 0), 2),
        }

    @staticmethod
    def _warnings(result):
        w = result["metadata"]["warnings"]
        pi = result["personal_information"]
        if not pi["emails"]:
            w.append("No email found")
        if not pi["full_name"]:
            w.append("Candidate name could not be identified confidently")
        if not result["education"]:
            w.append("No structured education entries found")
        if not result["experience"]:
            w.append("No structured work experience entries found")


# ============================================================================
# Public API
# ============================================================================

def parse_cv(file_path: str | Path) -> dict[str, Any]:
    try:
        return CVParser().parse(file_path)
    except Exception as exc:
        LOGGER.exception("Unexpected parser failure")
        result = empty_result(file_path)
        result["metadata"]["errors"].append(f"Unexpected parser error: {exc}")
        return result


# ============================================================================
# FastAPI app + CLI (unchanged except /parser-info)
# ============================================================================

UPLOAD_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hybrid CV Parser</title><style>
body{font-family:system-ui,sans-serif;max-width:760px;margin:4rem auto;padding:0 1rem;color:#172033}
.card{border:1px solid #d7dce5;border-radius:14px;padding:2rem;box-shadow:0 8px 28px #15213b12}
h1{margin-top:0}input,button{font:inherit}input{display:block;margin:1rem 0;width:100%}
button{background:#2457d6;color:white;border:0;border-radius:8px;padding:.75rem 1rem;cursor:pointer}
small{color:#5d687c}</style></head><body><div class="card"><h1>Hybrid CV Parser</h1>
<p>Upload a PDF or DOCX resume.</p>
<form action="/parse" method="post" enctype="multipart/form-data">
<input type="file" name="file" accept=".pdf,.docx" required>
<button type="submit">Parse CV</button></form></div></body></html>"""


def create_app() -> Any:
    try:
        from fastapi import FastAPI, File, HTTPException, UploadFile  # type: ignore
        from fastapi.responses import HTMLResponse, JSONResponse  # type: ignore
    except ImportError as exc:
        raise RuntimeError("FastAPI mode requires: pip install fastapi uvicorn python-multipart") from exc

    app = FastAPI(title="Hybrid CV Parser", version=VERSION)

    @app.get("/", response_class=HTMLResponse)
    async def upload_page() -> str:
        return UPLOAD_HTML

    @app.get("/parser-info")
    async def parser_info() -> dict[str, Any]:
        return {
            "file": __file__,
            "version": VERSION,
            "has_blacklist": hasattr(CVParser, "_TECH_LOCATION_BLACKLIST"),
            "has_project_splitter": hasattr(EntryParser, "_split_projects"),
            "has_continuation_joiner": hasattr(RuleBasedExtractor, "_join_continuations"),
        }

    @app.post("/parse")
    async def parse_endpoint(file: UploadFile = File(...)) -> Any:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in {".pdf", ".docx"}:
            raise HTTPException(status_code=415, detail="Only PDF and DOCX files are supported")
        max_size = 20 * 1024 * 1024
        content = await file.read(max_size + 1)
        if len(content) > max_size:
            raise HTTPException(status_code=413, detail="File exceeds the 20 MB limit")
        with tempfile.TemporaryDirectory(prefix="cv-parser-") as tmp:
            safe = re.sub(r"[^A-Za-z0-9_.-]", "_", Path(file.filename or f"u{suffix}").name)
            path = Path(tmp) / safe
            path.write_bytes(content)
            parsed = parse_cv(path)
        return JSONResponse(content=parsed,
                            status_code=422 if parsed["metadata"]["errors"] else 200)

    return app


def _write_json(data: dict[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_folder(folder: Path, output: Optional[Path]) -> int:
    files = sorted(x for x in folder.rglob("*")
                   if x.is_file() and x.suffix.lower() in {".pdf", ".docx"})
    if not files:
        LOGGER.error("No PDF or DOCX files found in %s", folder)
        return 1
    target = output or folder / "parsed"
    target.mkdir(parents=True, exist_ok=True)
    failures = 0
    for source in files:
        result = parse_cv(source)
        rel = source.relative_to(folder)
        digest = hashlib.sha1(str(rel).encode()).hexdigest()[:8]
        dest = target / rel.parent / f"{source.stem}_{digest}.json"
        _write_json(result, dest)
        print(f"{source} -> {dest}")
        failures += bool(result["metadata"]["errors"])
    return 2 if failures else 0


def build_cli() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Parse PDF/DOCX resumes into structured JSON")
    p.add_argument("path", nargs="?", help="Resume file or folder")
    p.add_argument("--output", "-o", help="Output JSON file or folder")
    p.add_argument("--serve", action="store_true", help="Start the local FastAPI upload interface")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--verbose", "-v", action="store_true")
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_cli().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    if args.serve:
        try:
            import uvicorn  # type: ignore
            uvicorn.run(create_app(), host=args.host, port=args.port)
            return 0
        except Exception as exc:
            LOGGER.error("Could not start web interface: %s", exc)
            return 2
    if not args.path:
        build_cli().print_help()
        return 1
    source = Path(args.path).expanduser()
    output = Path(args.output).expanduser() if args.output else None
    if source.is_dir():
        return _parse_folder(source, output)
    result = parse_cv(source)
    if output:
        _write_json(result, output)
        print(output)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["metadata"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

# # ============================================================
# # CV PARSER SERVICE
# # ============================================================
# # Ye file Jupyter notebook (final2.ipynb) ka poora code hai,
# # Django service ke form mein. Kuch bhi change nahi kiya.
# #
# # Flow:
# #   1. CV file (PDF/DOCX) se text extract
# #   2. Text clean
# #   3. Sections detect (header, skills, experience, etc.)
# #   4. NER model (oksomu/resume-ner) run
# #   5. Rule-based extraction (regex + NER)
# #   6. Final JSON return
# # ============================================================


# import os
# import re
# import json

# from pathlib import Path

# from django.conf import settings

# from pypdf import PdfReader
# from docx import Document

# from transformers import pipeline


# # ============================================================
# # GLOBAL NER MODEL (loaded once)
# # ============================================================

# _ner_model = None


# def load_ner_model():
#     """Load NER model from local folder (once)."""
#     global _ner_model

#     if _ner_model is not None:
#         return

#     MODEL_DIR = os.path.join(
#         settings.BASE_DIR, "ai_models", "ner"
#     )

#     print(f"Loading NER model from {MODEL_DIR}...")

#     _ner_model = pipeline(
#         "token-classification",
#         model=MODEL_DIR,
#         tokenizer=MODEL_DIR,
#         aggregation_strategy="simple"
#     )

#     # Patch the model to ignore token_type_ids
#     original_forward = _ner_model._forward

#     def patched_forward(model_inputs):
#         # token_type_ids hata do agar hai toh
#         model_inputs.pop("token_type_ids", None)
#         return original_forward(model_inputs)

#     _ner_model._forward = patched_forward

#     print("✅ NER model loaded and patched successfully!")


# # ============================================================
# # CELL 7: TEXT EXTRACTION
# # ============================================================

# def extract_text(file_path):

#     extension = Path(file_path).suffix.lower()

#     # -----------------------------
#     # PDF
#     # -----------------------------
#     if extension == ".pdf":

#         reader = PdfReader(file_path)

#         pages = []

#         for page in reader.pages:

#             page_text = page.extract_text()

#             if page_text:
#                 pages.append(page_text)

#         return "\n".join(pages).strip()

#     # -----------------------------
#     # DOCX
#     # -----------------------------
#     elif extension == ".docx":

#         document = Document(file_path)

#         paragraphs = []

#         for paragraph in document.paragraphs:

#             text = paragraph.text.strip()

#             if text:
#                 paragraphs.append(text)

#         return "\n".join(paragraphs).strip()

#     else:

#         raise ValueError(
#             f"Unsupported file format: {extension}"
#         )


# # ============================================================
# # CELL 9: CLEAN CV TEXT
# # ============================================================

# def clean_cv_text(text):

#     # Normalize line endings
#     text = text.replace("\r\n", "\n")
#     text = text.replace("\r", "\n")

#     # Replace tabs
#     text = text.replace("\t", " ")

#     # Normalize spaces
#     text = re.sub(r"[ ]{2,}", " ", text)

#     # Remove excessive blank lines
#     text = re.sub(r"\n{3,}", "\n\n", text)

#     return text.strip()


# # ============================================================
# # CELL 10: SECTION ALIASES
# # ============================================================

# SECTION_ALIASES = {

#     "summary": [
#         "summary",
#         "professional summary",
#         "profile",
#         "professional profile",
#         "career summary",
#         "objective",
#         "career objective",
#         "about me",
#         "personal statement",
#         "executive summary",
#         "overview",
#         "introduction",
#         "personal profile",
#         "summary of qualifications"
#     ],

#     "skills": [
#         "skills",
#         "technical skills",
#         "key skills",
#         "core skills",
#         "core competencies",
#         "technical competencies",
#         "technologies",
#         "technical expertise",
#         "proficiencies",
#         "expertise",
#         "areas of expertise",
#         "tools & technologies",
#         "competencies",
#         "strengths",
#         "professional skills",
#         "job-related skills",
#         "skills & certifications",
#         "skills and certifications"
#     ],

#     "experience": [
#         "experience",
#         "work experience",
#         "professional experience",
#         "employment history",
#         "work history",
#         "career history",
#         "professional history",
#         "relevant experience",
#         "previous employment",
#         "job history",
#         "professional background",
#         "industry experience",
#         "work experience & projects",
#         "internship experience",
#         "internships",
#         "internship"
#     ],

#     "education": [
#         "education",
#         "educational background",
#         "academic background",
#         "academic qualifications",
#         "educational qualifications",
#         "qualifications",
#         "formal education",
#         "schooling",
#         "academic history",
#         "degrees",
#         "certificates & degrees",
#         "learning & development"
#     ],

#     "projects": [
#         "projects",
#         "personal projects",
#         "academic projects",
#         "key projects",
#         "major projects",
#         "project experience",
#         "project portfolio",
#         "notable projects",
#         "case studies",
#         "development projects",
#         "research projects",
#         "capstone projects"
#     ],

#     "certifications": [
#         "certifications",
#         "certificates",
#         "professional certifications",
#         "licenses & certifications",
#         "licenses and certifications",
#         "accreditations",
#         "professional development",
#         "training",
#         "courses",
#         "completion certificates"
#     ],

#     "publications": [
#         "publications",
#         "research publications",
#         "papers",
#         "research papers",
#         "published papers",
#         "journal publications"
#     ],

#     "languages": [
#         "languages",
#         "language skills",
#         "linguistic skills",
#         "foreign languages",
#         "language proficiency",
#         "spoken languages",
#         "multilingual skills",
#         "linguistics"
#     ],

#     "leadership": [
#         "leadership",
#         "leadership experience",
#         "leadership & campus involvement",
#         "leadership and campus involvement",
#         "campus involvement"
#     ],

#     "achievements": [
#         "achievements",
#         "awards",
#         "honors",
#         "honours",
#         "accomplishments",
#         "recognitions",
#         "notable achievements",
#         "key achievements",
#         "professional awards"
#     ],

#     "interests": [
#         "interests",
#         "hobbies",
#         "personal interests",
#         "activities",
#         "extracurriculars",
#         "extracurricular activities"
#     ]
# }


# # ============================================================
# # CELL 11: NORMALIZE HEADING
# # ============================================================

# def normalize_heading(text):

#     text = text.strip().lower()

#     # Remove bullets
#     text = re.sub(
#         r"^[•●▪◦\-*]+\s*",
#         "",
#         text
#     )

#     # Remove trailing punctuation
#     text = re.sub(
#         r"[:\|]+$",
#         "",
#         text
#     )

#     # Normalize "and" / "&"
#     text = text.replace(
#         " and ",
#         " & "
#     )

#     # Normalize spaces
#     text = re.sub(
#         r"\s+",
#         " ",
#         text
#     )

#     return text.strip()


# # ============================================================
# # CELL 12: DETECT SECTION HEADING
# # ============================================================

# def detect_section_heading(line):

#     normalized = normalize_heading(line)

#     for section_name, aliases in SECTION_ALIASES.items():

#         aliases_normalized = [
#             normalize_heading(alias)
#             for alias in aliases
#         ]

#         if normalized in aliases_normalized:
#             return section_name

#     return None


# # ============================================================
# # CELL 13: DETECT SECTIONS
# # ============================================================

# def detect_sections(text):

#     lines = text.splitlines()

#     sections = {}

#     current_section = "header"

#     sections[current_section] = []

#     for line in lines:

#         line = line.strip()

#         if not line:
#             continue

#         detected = detect_section_heading(line)

#         if detected:

#             current_section = detected

#             if current_section not in sections:
#                 sections[current_section] = []

#         else:

#             sections[current_section].append(line)

#     # Convert lists to text
#     for section_name in sections:

#         sections[section_name] = "\n".join(
#             sections[section_name]
#         )

#     return sections


# # ============================================================
# # CELL 21: EXTRACT EMAIL
# # ============================================================

# def extract_email(text):

#     pattern = (
#         r"\b[A-Za-z0-9._%+-]+"
#         r"@[A-Za-z0-9.-]+\."
#         r"[A-Za-z]{2,}\b"
#     )

#     matches = re.findall(
#         pattern,
#         text
#     )

#     return matches[0] if matches else None


# # ============================================================
# # CELL 22: EXTRACT PHONE
# # ============================================================

# def extract_phone(text):

#     pattern = (
#         r"(?<!\d)"
#         r"(?:\+?\d{1,3}[\s.-]?)?"
#         r"(?:\(?\d{2,4}\)?[\s.-]?)?"
#         r"\d{3,4}[\s.-]?\d{3,4}"
#         r"(?!\d)"
#     )

#     matches = re.findall(
#         pattern,
#         text
#     )

#     valid = []

#     for phone in matches:

#         digits = re.sub(
#             r"\D",
#             "",
#             phone
#         )

#         if len(digits) >= 7:
#             valid.append(phone.strip())

#     return valid[0] if valid else None


# # ============================================================
# # CELL 23: EXTRACT HEADER ENTITIES
# # ============================================================

# def extract_header_entities(
#     header_text,
#     ner_entities
# ):

#     result = {
#         "full_name": None,
#         "designation": None
#     }

#     # -----------------------------
#     # NER candidates
#     # -----------------------------
#     name_candidates = []

#     title_candidates = []

#     for entity in ner_entities:

#         label = entity["entity_group"]

#         text = entity["word"].strip()

#         score = entity["score"]

#         if score < 0.70:
#             continue

#         if label == "NAME":
#             name_candidates.append(text)

#         elif label == "TITLE":
#             title_candidates.append(text)

#     # -----------------------------
#     # Name
#     # -----------------------------
#     if name_candidates:

#         name = name_candidates[0]

#         # Remove obvious title contamination
#         name = re.sub(
#             r"\b(AI|ML|Machine Learning|Engineer)\b.*$",
#             "",
#             name,
#             flags=re.IGNORECASE
#         ).strip()

#         result["full_name"] = name

#     # -----------------------------
#     # Title
#     # -----------------------------
#     if title_candidates:

#         result["designation"] = (
#             title_candidates[0]
#         )

#     # -----------------------------
#     # Fallback name
#     # -----------------------------
#     if not result["full_name"]:

#         lines = [
#             line.strip()
#             for line in header_text.splitlines()
#             if line.strip()
#         ]

#         if lines:

#             result["full_name"] = lines[0]

#     # -----------------------------
#     # Fallback title
#     # -----------------------------
#     if not result["designation"]:

#         lines = [
#             line.strip()
#             for line in header_text.splitlines()
#             if line.strip()
#         ]

#         if len(lines) >= 2:

#             result["designation"] = lines[1]

#     return result


# # ============================================================
# # CELL 25: DATE PATTERNS
# # ============================================================

# MONTH_PATTERN = (
#     r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|"
#     r"Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
#     r"Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
#     r"Nov(?:ember)?|Dec(?:ember)?)"
# )

# DATE_RANGE_PATTERN = re.compile(
#     rf"({MONTH_PATTERN}\s+\d{{4}})"
#     rf"\s*[–—-]\s*"
#     rf"(Present|{MONTH_PATTERN}\s+\d{{4}}|\d{{4}})",
#     re.IGNORECASE
# )

# YEAR_RANGE_PATTERN = re.compile(
#     r"(\d{4})\s*[–—-]\s*(Present|\d{4})",
#     re.IGNORECASE
# )


# # ============================================================
# # CELL 26: EXTRACT DATE RANGE
# # ============================================================

# def extract_date_range(text):

#     match = DATE_RANGE_PATTERN.search(text)

#     if match:

#         return {
#             "start_date": match.group(1),
#             "end_date": match.group(2)
#         }

#     match = YEAR_RANGE_PATTERN.search(text)

#     if match:

#         return {
#             "start_date": match.group(1),
#             "end_date": match.group(2)
#         }

#     return {
#         "start_date": None,
#         "end_date": None
#     }


# # ============================================================
# # CELL 27: EXTRACT EXPERIENCE
# # ============================================================

# def extract_experience(
#     text,
#     ner_entities
# ):

#     lines = [
#         line.strip()
#         for line in text.splitlines()
#         if line.strip()
#     ]

#     # --------------------------------
#     # Get NER entities
#     # --------------------------------
#     titles = []
#     companies = []

#     for entity in ner_entities:

#         if entity["score"] < 0.70:
#             continue

#         label = entity["entity_group"]

#         value = entity["word"].strip()

#         if label == "TITLE":
#             titles.append(value)

#         elif label == "COMPANY":
#             companies.append(value)

#     # --------------------------------
#     # Build records
#     # --------------------------------
#     experiences = []

#     title_index = 0
#     company_index = 0

#     for i, line in enumerate(lines):

#         # Find a date range
#         date_data = extract_date_range(line)

#         if (
#             date_data["start_date"]
#             or date_data["end_date"]
#         ):

#             title = (
#                 titles[title_index]
#                 if title_index < len(titles)
#                 else None
#             )

#             company = (
#                 companies[company_index]
#                 if company_index < len(companies)
#                 else None
#             )

#             record = {

#                 "company_name": company,

#                 "designation": title,

#                 "start_date":
#                     date_data["start_date"],

#                 "end_date":
#                     date_data["end_date"]
#             }

#             experiences.append(record)

#             title_index += 1
#             company_index += 1

#     # --------------------------------
#     # Fallback
#     # --------------------------------
#     if not experiences:

#         count = max(
#             len(titles),
#             len(companies)
#         )

#         for i in range(count):

#             experiences.append({

#                 "company_name":
#                     companies[i]
#                     if i < len(companies)
#                     else None,

#                 "designation":
#                     titles[i]
#                     if i < len(titles)
#                     else None,

#                 "start_date": None,

#                 "end_date": None
#             })

#     return experiences


# # ============================================================
# # CELL 29: EXTRACT QUALIFICATION
# # ============================================================

# def extract_qualification(
#     education_text,
#     ner_entities
# ):

#     lines = [
#         line.strip()
#         for line in education_text.splitlines()
#         if line.strip()
#     ]

#     degree = None
#     field = None

#     for entity in ner_entities:

#         if entity["score"] < 0.70:
#             continue

#         label = entity["entity_group"]

#         value = entity["word"].strip()

#         if label == "DEGREE":
#             degree = value

#         elif label == "FIELD":
#             field = value

#     # --------------------------------
#     # Build qualification
#     # --------------------------------
#     if degree and field:

#         qualification = (
#             f"{degree} in {field}"
#         )

#     elif degree:

#         qualification = degree

#     elif field:

#         qualification = field

#     else:

#         qualification = (
#             lines[0]
#             if lines
#             else None
#         )

#     return {
#         "qualification_name":
#             qualification
#     }


# # ============================================================
# # CELL 31: MASTER SKILLS LIST
# # ============================================================

# MASTER_SKILLS = [

#     # ---------- Programming Languages ----------
#     "Python",
#     "C++",
#     "SQL",
#     "JavaScript",
#     "Bash",
#     "Java",
#     "Go",
#     "Rust",
#     "Ruby",
#     "PHP",
#     "Swift",
#     "Kotlin",
#     "Scala",
#     "R",
#     "MATLAB",
#     "TypeScript",
#     "Dart",
#     "Perl",
#     "Lua",
#     "Haskell",
#     "Elixir",
#     "Clojure",
#     "Julia",
#     "Shell Scripting",
#     "PowerShell",

#     # ---------- ML/DL Frameworks & Libraries ----------
#     "PyTorch",
#     "TensorFlow",
#     "Keras",
#     "scikit-learn",
#     "Hugging Face Transformers",
#     "JAX",
#     "XGBoost",
#     "Random Forest",
#     "LightGBM",
#     "CatBoost",
#     "Dask ML",
#     "RAPIDS",
#     "cuML",
#     "cuDF",
#     "Fastai",
#     "MXNet",
#     "Caffe2",
#     "Theano",
#     "Chainer",
#     "Flax",
#     "Trax",
#     "Dlib",
#     "Shogun",

#     # ---------- LLM & Generative AI ----------
#     "GPT",
#     "LLM",
#     "LLM fine-tuning",
#     "LoRA",
#     "QLoRA",
#     "RAG",
#     "RAG pipelines",
#     "LangChain",
#     "LlamaIndex",
#     "Prompt Engineering",
#     "ChatGPT API",
#     "Claude API",
#     "Gemini API",
#     "Mistral",
#     "Falcon",
#     "Llama",
#     "LLM evaluation",
#     "RLHF",
#     "DPO",
#     "Inference optimization",
#     "vLLM",
#     "TGI (Text Generation Inference)",
#     "DeepSpeed",
#     "Megatron-LM",
#     "Fugue",
#     "Guidance",
#     "LMQL",

#     # ---------- Vector Databases & Search ----------
#     "Pinecone",
#     "FAISS",
#     "ChromaDB",
#     "Weaviate",
#     "Qdrant",
#     "Milvus",
#     "Elasticsearch",
#     "OpenSearch",
#     "Vespa",
#     "Redis (Vector Search)",
#     "LanceDB",

#     # ---------- Computer Vision ----------
#     "OpenCV",
#     "YOLOv8",
#     "Detectron2",
#     "Image Segmentation",
#     "OCR",
#     "Tesseract",
#     "PaddleOCR",
#     "MMDetection",
#     "MMSegmentation",
#     "Pillow",
#     "imutils",
#     "Scikit-image",
#     "DeepFace",
#     "dlib (face detection)",
#     "MediaPipe",
#     "Albumentations",
#     "Kornia",
#     "SuperVision",
#     "SAM (Segment Anything)",
#     "CLIP",
#     "DINOv2",

#     # ---------- NLP ----------
#     "Named Entity Recognition",
#     "Text Classification",
#     "BERT",
#     "RoBERTa",
#     "Tokenization",
#     "Sentiment Analysis",
#     "spaCy",
#     "NLTK",
#     "Gensim",
#     "Stanford CoreNLP",
#     "AllenNLP",
#     "Flair",
#     "TextBlob",
#     "Transformers (library)",
#     "Sentence Transformers",
#     "Topic Modeling (LDA)",
#     "Text Summarization",
#     "Machine Translation",
#     "Speech Recognition (Whisper)",
#     "Text-to-Speech (TTS)",
#     "PyAudio",
#     "Librosa",
#     "Voice Activity Detection",

#     # ---------- MLOps & Deployment ----------
#     "Docker",
#     "Kubernetes",
#     "MLflow",
#     "Airflow",
#     "FastAPI",
#     "Flask",
#     "ONNX",
#     "ONNX Runtime",
#     "TensorRT",
#     "CI/CD",
#     "Kubeflow",
#     "TFX",
#     "Seldon Core",
#     "BentoML",
#     "Ray",
#     "Ray Tune",
#     "Optuna",
#     "Hyperopt",
#     "Kedro",
#     "DVC (Data Version Control)",
#     "Pachyderm",
#     "Great Expectations",
#     "Pytest",
#     "Prefect",
#     "ZenML",
#     "Polyaxon",
#     "ClearML",
#     "Comet",
#     "Neptune",
#     "Grafana",
#     "Prometheus",

#     # ---------- Cloud Platforms & Services ----------
#     "AWS",
#     "SageMaker",
#     "EC2",
#     "S3",
#     "Lambda",
#     "Google Cloud Platform",
#     "Vertex AI",
#     "Microsoft Azure",
#     "Azure ML",
#     "AWS ECS",
#     "AWS EKS",
#     "AWS RDS",
#     "AWS DynamoDB",
#     "AWS Redshift",
#     "AWS Glue",
#     "AWS Athena",
#     "AWS Kinesis",
#     "AWS SQS",
#     "AWS SNS",
#     "AWS Step Functions",
#     "Google BigQuery",
#     "Google Pub/Sub",
#     "Google Dataflow",
#     "Google Dataproc",
#     "Azure Data Factory",
#     "Azure Databricks",
#     "Azure Functions",
#     "Azure DevOps",
#     "Oracle Cloud",
#     "IBM Cloud",
#     "DigitalOcean",
#     "Heroku",

#     # ---------- Infrastructure as Code ----------
#     "Terraform",
#     "Ansible",
#     "Chef",
#     "Puppet",
#     "Pulumi",
#     "CloudFormation",
#     "CDK",
#     "SaltStack",

#     # ---------- Databases & Data Stores ----------
#     "PostgreSQL",
#     "MongoDB",
#     "Redis",
#     "MySQL",
#     "Cassandra",
#     "DynamoDB",
#     "Elasticsearch (as DB)",
#     "Neo4j",
#     "ArangoDB",
#     "Couchbase",
#     "InfluxDB",
#     "TimescaleDB",
#     "SQLite",
#     "MariaDB",
#     "Oracle DB",
#     "Snowflake",
#     "ClickHouse",
#     "HBase",
#     "Bigtable",
#     "RocksDB",

#     # ---------- Big Data & Data Engineering ----------
#     "Apache Spark",
#     "PySpark",
#     "Hadoop",
#     "Hive",
#     "Pig",
#     "Kafka",
#     "Flink",
#     "Storm",
#     "NiFi",
#     "Airbyte",
#     "Fivetran",
#     "Talend",
#     "Informatica",
#     "Dremio",
#     "Presto/Trino",
#     "Databricks",
#     "Delta Lake",
#     "Iceberg",
#     "Hudi",
#     "Great Expectations (data quality)",
#     "Dagster",

#     # ---------- Data Analysis & Visualization ----------
#     "Pandas",
#     "NumPy",
#     "Power BI",
#     "Tableau",
#     "Matplotlib",
#     "Seaborn",
#     "Plotly",
#     "Bokeh",
#     "Altair",
#     "ggplot2 (R)",
#     "Shiny (R)",
#     "Dash",
#     "Streamlit",
#     "Grafana (visualization)",

#     # ---------- Web Development (Backend & Frontend) ----------
#     "Django",
#     "Spring Boot",
#     "React",
#     "Angular",
#     "Vue.js",
#     "Node.js",
#     "Express.js",
#     ".NET Core",
#     "ASP.NET",
#     "Ruby on Rails",
#     "Laravel",
#     "Flask (web)",
#     "FastAPI (web)",
#     "GraphQL",
#     "REST APIs",
#     "WebSockets",
#     "gRPC",
#     "HTML5",
#     "CSS3",
#     "Sass",
#     "Bootstrap",
#     "Tailwind CSS",
#     "jQuery",
#     "Svelte",
#     "Next.js",
#     "Nuxt.js",
#     "Gatsby",
#     "D3.js",
#     "Three.js",

#     # ---------- Mobile Development ----------
#     "Android (Java/Kotlin)",
#     "iOS (Swift)",
#     "React Native",
#     "Flutter",
#     "Xamarin",
#     "Ionic",
#     "Cordova",

#     # ---------- Game Development ----------
#     "Unity",
#     "Unreal Engine",
#     "Godot",
#     "Cocos2d",
#     "Phaser",
#     "Pygame",

#     # ---------- DevOps & Monitoring ----------
#     "Git",
#     "GitHub",
#     "JIRA",
#     "Weights & Biases",
#     "Jupyter",
#     "Postman",
#     "Linux",
#     "GitLab",
#     "Bitbucket",
#     "Jenkins",
#     "CircleCI",
#     "Travis CI",
#     "GitHub Actions",
#     "Argo CD",
#     "Istio",
#     "Envoy",
#     "NGINX",
#     "Apache HTTP Server",
#     "HAProxy",
#     "Consul",
#     "Vault",
#     "Terraform (already)",
#     "Ansible (already)",
#     "Nagios",
#     "Zabbix",
#     "Splunk",
#     "ELK Stack (Elasticsearch, Logstash, Kibana)",
#     "Fluentd",
#     "Loki",
#     "Tempo",

#     # ---------- Cybersecurity & Ethical Hacking ----------
#     "OWASP Top 10",
#     "Penetration Testing",
#     "Metasploit",
#     "Burp Suite",
#     "Wireshark",
#     "Nmap",
#     "Kali Linux",
#     "Snort",
#     "Suricata",
#     "Firewall Configuration",
#     "SIEM (Security Information and Event Management)",
#     "SOC",
#     "Incident Response",
#     "Forensics",
#     "PKI",
#     "SSL/TLS",
#     "OAuth",
#     "SAML",
#     "OpenID Connect",
#     "Zero Trust",
#     "Vulnerability Scanning",
#     "CVE Analysis",
#     "Security Compliance (GDPR, HIPAA, SOC2)",

#     # ---------- Blockchain & Web3 ----------
#     "Solidity",
#     "Ethereum",
#     "Smart Contracts",
#     "Web3.js",
#     "Ethers.js",
#     "Hardhat",
#     "Truffle",
#     "Ganache",
#     "IPFS",
#     "Filecoin",
#     "Solana (Rust)",
#     "Polkadot",
#     "Chainlink",
#     "NFTs",
#     "DeFi",
#     "Cryptography (SHA, ECDSA)",

#     # ---------- Scientific Computing & Simulation ----------
#     "SimPy",
#     "SciPy",
#     "SymPy",
#     "OpenFOAM",
#     "COMSOL",
#     "ANSYS",
#     "FEniCS",

#     # ---------- Other Tools & Platforms ----------
#     "Jupyter Notebook",
#     "JupyterLab",
#     "Google Colab",
#     "Kaggle",
#     "VS Code",
#     "PyCharm",
#     "IntelliJ IDEA",
#     "Eclipse",
#     "Vim",
#     "Emacs",
#     "Slack",
#     "Teams",
#     "Zoom API",
#     "Notion",
#     "Confluence",
#     "Trello",
#     "Asana",
#     "Monday.com",
#     "ClickUp",

#     # ---------- Soft Skills ----------
#     "Agile Methodologies",
#     "Scrum",
#     "Kanban",
#     "Project Management",
#     "Technical Writing",
#     "Presentations",
#     "Team Leadership",
#     "Mentoring",
#     "Cross-functional Collaboration",
#     "Problem Solving",
#     "Critical Thinking",
#     "Time Management",
# ]


# # ============================================================
# # CELL 32: EXTRACT SKILLS
# # ============================================================

# def extract_skills(
#     skills_text,
#     master_skills
# ):

#     found = []

#     text_lower = skills_text.lower()

#     for skill in master_skills:

#         pattern = (
#             r"(?<!\w)"
#             + re.escape(skill.lower())
#             + r"(?!\w)"
#         )

#         if re.search(
#             pattern,
#             text_lower
#         ):

#             found.append(skill)

#     return found


# # ============================================================
# # CELL 40: LANGUAGE RULES
# # ============================================================

# KNOWN_LANGUAGES = [
#     "English",
#     "Urdu",
#     "Punjabi",
#     "Hindi",
#     "Arabic",
#     "French",
#     "Spanish",
#     "German",
#     "Chinese",
#     "Mandarin",
#     "Italian",
#     "Portuguese",
#     "Russian",
#     "Japanese",
#     "Korean"
# ]

# LANGUAGE_PROFICIENCY = {
#     "native": "Native",
#     "fluent": "Fluent",
#     "advanced": "Advanced",
#     "intermediate": "Intermediate",
#     "basic": "Basic",
#     "beginner": "Basic",
#     "elementary": "Basic",
#     "professional": "Professional",
#     "conversational": "Conversational"
# }


# # ============================================================
# # CELL 41: EXTRACT LANGUAGES
# # ============================================================

# def extract_languages(language_text):

#     results = []

#     if not language_text:
#         return results

#     # Split languages using | ; or newline
#     parts = re.split(r"[|;\n]+", language_text)

#     for part in parts:

#         part = part.strip()

#         if not part:
#             continue

#         detected_language = None
#         detected_proficiency = ""

#         # ----------------------------------------------------
#         # Detect language
#         # ----------------------------------------------------

#         for language in KNOWN_LANGUAGES:

#             if re.search(
#                 rf"\b{re.escape(language)}\b",
#                 part,
#                 re.IGNORECASE
#             ):
#                 detected_language = language
#                 break

#         if detected_language is None:
#             continue

#         # ----------------------------------------------------
#         # Detect proficiency
#         # ----------------------------------------------------

#         for level, normalized_level in LANGUAGE_PROFICIENCY.items():

#             if re.search(
#                 rf"\b{re.escape(level)}\b",
#                 part,
#                 re.IGNORECASE
#             ):
#                 detected_proficiency = normalized_level
#                 break

#         # ----------------------------------------------------
#         # Add result
#         # ----------------------------------------------------

#         results.append({
#             "language_name": detected_language,
#             "proficiency_lvl": detected_proficiency
#         })

#     return results


# # ============================================================
# # CELL 42: VALIDATE LANGUAGES
# # ============================================================

# def validate_languages(languages_data):

#     if not languages_data:
#         return []

#     validated = []
#     seen = set()

#     for item in languages_data:

#         if not isinstance(item, dict):
#             continue

#         language = str(
#             item.get("language_name", "")
#         ).strip()

#         proficiency = str(
#             item.get("proficiency_lvl", "")
#         ).strip()

#         if not language:
#             continue

#         # Normalize language
#         language_map = {
#             "english": "English",
#             "urdu": "Urdu",
#             "punjabi": "Punjabi",
#             "hindi": "Hindi",
#             "arabic": "Arabic",
#             "french": "French",
#             "spanish": "Spanish",
#             "german": "German",
#             "chinese": "Chinese",
#             "mandarin": "Mandarin",
#             "italian": "Italian",
#             "portuguese": "Portuguese",
#             "russian": "Russian",
#             "japanese": "Japanese",
#             "korean": "Korean"
#         }

#         normalized_language = language_map.get(
#             language.lower(),
#             language.title()
#         )

#         # Normalize proficiency
#         normalized_proficiency = ""

#         if proficiency:

#             normalized_proficiency = LANGUAGE_PROFICIENCY.get(
#                 proficiency.lower(),
#                 proficiency.title()
#             )

#         # Prevent duplicates
#         key = (
#             normalized_language.lower(),
#             normalized_proficiency.lower()
#         )

#         if key in seen:
#             continue

#         seen.add(key)

#         validated.append({
#             "language_name": normalized_language,
#             "proficiency_lvl": normalized_proficiency
#         })

#     return validated


# # ============================================================
# # CELL 37: CLEAN STRING
# # ============================================================

# def clean_string(value):

#     if value is None:
#         return None

#     value = str(value).strip()

#     value = re.sub(
#         r"\s+",
#         " ",
#         value
#     )

#     value = value.strip(
#         " ,.;:|-"
#     )

#     return value if value else None


# # ============================================================
# # CELL 38: VALIDATE EXPERIENCE
# # ============================================================

# def validate_experience(experiences):

#     validated = []

#     for item in experiences:

#         company = clean_string(
#             item.get("company_name")
#         )

#         designation = clean_string(
#             item.get("designation")
#         )

#         start_date = clean_string(
#             item.get("start_date")
#         )

#         end_date = clean_string(
#             item.get("end_date")
#         )

#         if (
#             company
#             or designation
#             or start_date
#             or end_date
#         ):

#             validated.append({

#                 "company_name": company,

#                 "designation": designation,

#                 "start_date": start_date,

#                 "end_date": end_date
#             })

#     return validated


# # ============================================================
# # MAIN FUNCTION: PARSE CV
# # ============================================================
# # Ye function notebook ke cells 7, 9, 13, 19, 23, 27, 29, 32, 41,
# # 42, 44 ko combine karta hai — bilkul same logic, ek jagah.
# # ============================================================

# def parse_cv(file_path):

#     # ----------------------------------------------------
#     # Ensure NER model is loaded
#     # ----------------------------------------------------
#     load_ner_model()

#     # ----------------------------------------------------
#     # 1. Extract text from CV
#     # ----------------------------------------------------
#     cv_text = extract_text(file_path)

#     # ----------------------------------------------------
#     # 2. Clean text
#     # ----------------------------------------------------
#     cleaned_text = clean_cv_text(cv_text)

#     # ----------------------------------------------------
#     # 3. Detect sections
#     # ----------------------------------------------------
#     sections = detect_sections(cleaned_text)

#     # ----------------------------------------------------
#     # 4. Run NER on each section
#     # ----------------------------------------------------
#     raw_ner_output = {}

#     for section_name, section_text in sections.items():

#         if not section_text.strip():
#             continue

#         entities = _ner_model(section_text)

#         raw_ner_output[section_name] = entities

#     # ----------------------------------------------------
#     # 5. Extract header
#     # ----------------------------------------------------
#     header_text = sections.get("header", "")

#     header_entities = raw_ner_output.get("header", [])

#     header_data = extract_header_entities(
#         header_text,
#         header_entities
#     )

#     header_data["email"] = extract_email(header_text)

#     header_data["phone"] = extract_phone(header_text)

#     # ----------------------------------------------------
#     # 6. Extract experience
#     # ----------------------------------------------------
#     experience_data = extract_experience(

#         sections.get("experience", ""),

#         raw_ner_output.get("experience", [])
#     )

#     # ----------------------------------------------------
#     # 7. Extract education
#     # ----------------------------------------------------
#     education_data = extract_qualification(

#         sections.get("education", ""),

#         raw_ner_output.get("education", [])
#     )

#     # ----------------------------------------------------
#     # 8. Extract skills
#     # ----------------------------------------------------
#     skills_data = extract_skills(

#         sections.get("skills", ""),

#         MASTER_SKILLS
#     )

#     # ----------------------------------------------------
#     # 9. Extract languages
#     # ----------------------------------------------------
#     languages_data = extract_languages(
#         sections.get("languages", "")
#     )

#     # ----------------------------------------------------
#     # 10. Final database-ready JSON
#     # ----------------------------------------------------
#     final_data = {

#         "full_name":
#             clean_string(
#                 header_data.get("full_name")
#             ),

#         "email":
#             clean_string(
#                 header_data.get("email")
#             ),

#         "phone":
#             clean_string(
#                 header_data.get("phone")
#             ),

#         "education": [
#             education_data
#         ] if education_data.get(
#             "qualification_name"
#         ) else [],

#         "experience":
#             validate_experience(
#                 experience_data
#             ),

#         "skills": [
#             {
#                 "skill_name": skill
#             }
#             for skill in skills_data
#         ],

#         "languages":
#             validate_languages(
#                 languages_data
#             )
#     }

#     return final_data