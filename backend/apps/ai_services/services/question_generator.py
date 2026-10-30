import os
import torch

from django.conf import settings

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


# Global variables — model ek baar load hoga
_tokenizer = None
_model = None
_device = None


def load_model():
    """Load the interview question model (once)."""
    global _tokenizer, _model, _device

    if _model is not None:
        return  # Already loaded

    model_path = os.path.join(
        settings.BASE_DIR, "ai_models", "qs_model"
    )

    print(f"Loading interview question model from {model_path}...")

    _tokenizer = AutoTokenizer.from_pretrained(model_path)
    _model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _model = _model.to(_device)
    _model.eval()

    print(f"✅ Interview question model loaded on {_device}")


def generate_question(
    job_title: str,
    job_description: str,
    required_experience: str,
    skills: str,
    question_type: str = "Scenario",
) -> str:
    """Generate an interview question from job details."""
    load_model()

    input_text = (
        "Generate an interview question.\n"
        f"Job Title: {job_title}\n"
        f"Job Description: {job_description}\n"
        f"Required Experience: {required_experience}\n"
        f"Skills: {skills}\n"
        f"Question Type: {question_type}"
    )

    inputs = _tokenizer(
        input_text,
        return_tensors="pt",
        max_length=512,
        truncation=True,
    )
    inputs = {k: v.to(_device) for k, v in inputs.items()}

    with torch.no_grad():
        generated_ids = _model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_length=128,
            do_sample=True,
            temperature=0.8,
            top_p=0.9,
        )

    return _tokenizer.decode(generated_ids[0], skip_special_tokens=True)