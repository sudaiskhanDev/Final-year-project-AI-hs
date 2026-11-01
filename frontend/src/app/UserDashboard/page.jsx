"use client";

/* ==========================================================================
   HireAI — Candidate Dashboard · "Glass" redesign

   Design language taken from the Loman reference image:
   - Light, monochrome canvas (soft #ebebeb + white glows, black / grey text)
   - Frosted-glass cards with white edges and soft shadows
   - Huge bold uppercase headlines, last line in grey
   - Tiny tracked-out tag pill above every headline ("NEXT GENERATION" style)
   - Black pill buttons with a white arrow circle, round glass icon buttons
   - Thin line + arrow divider, big concentric ring visual with vertical stripes
   - Glass feature strip with icon tiles and dividers
   - Fixed numbered side index (01 / 02 / 03 …) with an animated line
   - Top glass nav pill with a dot under the active item

   Notes
   - Drop-in replacement for your current UserDashboard page file.
   - No new packages. Same API endpoints, payloads and response fields.
   - The page is LIGHT now. If your global NavBar uses white text, give it
     dark text (or a glass background) on this route so it stays readable.
   - For the closest match to the reference typography, load a geometric
     grotesk (e.g. "Inter Tight" / "Plus Jakarta Sans" via next/font) and
     apply it to the app; the layout works fine with the default font too.
   ========================================================================== */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useRouter } from "next/navigation";

// ============================================================
// CONFIG
// ============================================================
const API_BASE_URL = "http://localhost:8000";
const MAX_FILE_MB = 10;

const SECTIONS = [
  { id: "overview", label: "Overview", icon: "overview" },
  { id: "profile", label: "Profile", icon: "user" },
  { id: "resume", label: "Resume", icon: "document" },
  { id: "experience", label: "Experience", icon: "briefcase" },
  { id: "skills", label: "Skills", icon: "sparkles" },
  { id: "qualifications", label: "Qualifications", icon: "cap" },
  { id: "languages", label: "Languages", icon: "language" },
  { id: "applications", label: "Applications", icon: "send" },
];

const STATUS_ORDER = ["applied", "shortlisted", "rejected", "hired"];

const STATUS_STYLES = {
  applied: { label: "Applied", badge: "bg-blue-500/10 text-blue-700", dot: "bg-blue-500", bar: "bg-blue-500" },
  shortlisted: { label: "Shortlisted", badge: "bg-amber-500/15 text-amber-700", dot: "bg-amber-500", bar: "bg-amber-500" },
  rejected: { label: "Rejected", badge: "bg-red-500/10 text-red-600", dot: "bg-red-500", bar: "bg-red-500" },
  hired: { label: "Hired", badge: "bg-emerald-500/10 text-emerald-700", dot: "bg-emerald-500", bar: "bg-emerald-500" },
};

const PROFICIENCY = ["basic", "intermediate", "fluent", "native"];

const PAGE_BG = {
  background:
    "radial-gradient(60% 50% at 78% 10%, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0) 70%), radial-gradient(45% 40% at 6% 90%, rgba(255,255,255,0.85) 0%, rgba(255,255,255,0) 70%), #ebebeb",
};

// ============================================================
// SHARED CLASS STRINGS
// ============================================================
const baseInput =
  "rounded-2xl border border-black/10 bg-white/70 px-4 py-2.5 text-sm text-neutral-900 placeholder-neutral-400 outline-none transition focus:border-black/30 focus:bg-white focus:ring-4 focus:ring-black/5 disabled:opacity-50 [&>option]:bg-white [&>option]:text-neutral-900";
const inputCls = `w-full ${baseInput}`;
const btnSmall =
  "inline-flex items-center justify-center gap-1.5 rounded-full border border-black/10 bg-white/70 px-3.5 py-1.5 text-xs font-semibold text-neutral-800 transition hover:bg-white active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-50";
const btnDanger =
  "inline-flex items-center justify-center gap-1.5 rounded-full border border-red-500/20 bg-red-500/5 px-3.5 py-1.5 text-xs font-semibold text-red-600 transition hover:bg-red-500/10 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-50";
const cardCls = "glass glass-hover rounded-3xl";

// ============================================================
// ICONS (inline SVG, no dependency)
// ============================================================
const ICONS = {
  overview:
    "M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z",
  user:
    "M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z",
  document:
    "M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z",
  briefcase:
    "M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0112 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 01-.673-.38m0 0A2.18 2.18 0 013 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 013.413-.387m7.5 0V5.25A2.25 2.25 0 0013.5 3h-3a2.25 2.25 0 00-2.25 2.25v.894m7.5 0a48.667 48.667 0 00-7.5 0M12 12.75h.008v.008H12v-.008z",
  sparkles:
    "M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z",
  cap:
    "M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5",
  language:
    "M10.5 21l5.25-11.25L21 21m-9-3h7.5M3 5.621a48.474 48.474 0 016-.371m0 0c1.12 0 2.233.038 3.334.114M9 5.25V3m3.334 2.364C11.176 10.658 7.69 15.08 3 17.502m9.334-12.138c.896.061 1.785.147 2.666.257m-4.589 8.495a18.023 18.023 0 01-3.827-5.802",
  send:
    "M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5",
  plus: "M12 4.5v15m7.5-7.5h-15",
  trash:
    "M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0",
  pencil:
    "M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10",
  check: "M4.5 12.75l6 6 9-13.5",
  x: "M6 18L18 6M6 6l12 12",
  upload:
    "M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5",
  calendar:
    "M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5",
  search:
    "M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z",
  mail:
    "M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75",
  phone:
    "M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z",
  pin:
    "M15 10.5a3 3 0 11-6 0 3 3 0 016 0zM19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z",
  building:
    "M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z",
  alert:
    "M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z",
  arrowRight: "M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3",
  arrowUpRight: "M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25",
  refresh:
    "M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99",
};

function Icon({ name, className = "h-4 w-4", strokeWidth = 1.7 }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d={ICONS[name]} />
    </svg>
  );
}

// ============================================================
// API HELPERS
// ============================================================
async function apiRequest(path, { method = "GET", body, isFormData = false } = {}) {
  const url = `${API_BASE_URL}${path}`;
  const options = { method, credentials: "include" };

  if (body !== undefined) {
    if (isFormData) {
      options.body = body;
    } else {
      options.headers = { "Content-Type": "application/json" };
      options.body = JSON.stringify(body);
    }
  }

  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new Error("Could not connect to the server");
  }

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    /* ignore */
  }

  if (!response.ok || payload?.success === false) {
    throw new Error(payload?.message || `Request failed (${response.status})`);
  }
  return payload;
}

// ============================================================
// UTILS
// ============================================================
function getStoredUser() {
  try {
    const raw = localStorage.getItem("auth_user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function getInitials(name) {
  if (!name) return "U";
  return name
    .trim()
    .split(/\s+/)
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : "";
}

function formatDate(dateStr) {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

function monthsBetween(start, end) {
  const s = new Date(start);
  const e = end ? new Date(end) : new Date();
  if (isNaN(s.getTime()) || isNaN(e.getTime())) return 0;
  return Math.max(0, (e.getFullYear() - s.getFullYear()) * 12 + (e.getMonth() - s.getMonth()));
}

function formatMonths(m) {
  if (m < 1) return "Less than a month";
  const y = Math.floor(m / 12);
  const mo = m % 12;
  const parts = [];
  if (y) parts.push(`${y} yr${y > 1 ? "s" : ""}`);
  if (mo) parts.push(`${mo} mo${mo > 1 ? "s" : ""}`);
  return parts.join(" ");
}

function calcAge(dob) {
  if (!dob) return null;
  const d = new Date(dob);
  if (isNaN(d.getTime())) return null;
  const now = new Date();
  let age = now.getFullYear() - d.getFullYear();
  const m = now.getMonth() - d.getMonth();
  if (m < 0 || (m === 0 && now.getDate() < d.getDate())) age--;
  return age >= 0 ? age : null;
}

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function fileExt(name) {
  return (name || "").split(".").pop().toLowerCase();
}

function todayStr() {
  return new Date().toISOString().split("T")[0];
}

// ============================================================
// HOOKS
// ============================================================
function useCountUp(target, duration = 900) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    let raf;
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setValue(Math.round(target * eased));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return value;
}

// ============================================================
// GLOBAL STYLES (glass + keyframes)
// ============================================================
function GlobalStyles() {
  return (
    <style>{`
      @keyframes dashFadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; } }
      @keyframes dashFadeIn { from { opacity: 0; } to { opacity: 1; } }
      @keyframes dashScaleIn { from { opacity: 0; transform: scale(.95); } to { opacity: 1; transform: none; } }
      @keyframes dashSlideIn { from { opacity: 0; transform: translateX(24px); } to { opacity: 1; transform: none; } }
      @keyframes dashPop { 0% { opacity: 0; transform: scale(.7); } 60% { transform: scale(1.06); } 100% { opacity: 1; transform: scale(1); } }
      @keyframes dashShimmer { from { background-position: 200% 0; } to { background-position: -200% 0; } }
      @keyframes dashFloat { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
      @keyframes dashIndeterminate { 0% { transform: translateX(-100%); } 100% { transform: translateX(350%); } }
      @keyframes dashSpinSlow { to { transform: rotate(360deg); } }

      /* "backwards" so hover transforms still work after the entrance finishes */
      .anim-fade-up { animation: dashFadeUp .7s cubic-bezier(.22,1,.36,1) backwards; }
      .anim-fade-in { animation: dashFadeIn .35s ease backwards; }
      .anim-scale-in { animation: dashScaleIn .3s cubic-bezier(.22,1,.36,1) backwards; }
      .anim-slide-in { animation: dashSlideIn .45s cubic-bezier(.22,1,.36,1) backwards; }
      .anim-pop { animation: dashPop .45s cubic-bezier(.22,1,.36,1) backwards; }
      .anim-float { animation: dashFloat 5s ease-in-out infinite; }
      .anim-indeterminate { animation: dashIndeterminate 1.2s ease-in-out infinite; }
      .anim-spin-slow { animation: dashSpinSlow 60s linear infinite; }

      .glass {
        background: rgba(255,255,255,.58);
        -webkit-backdrop-filter: blur(20px) saturate(150%);
        backdrop-filter: blur(20px) saturate(150%);
        border: 1px solid rgba(255,255,255,.85);
        box-shadow: inset 0 1px 0 rgba(255,255,255,.9), 0 12px 40px -14px rgba(0,0,0,.14);
      }
      .glass-hover { transition: background .25s ease, transform .25s ease, box-shadow .25s ease; }
      .glass-hover:hover {
        background: rgba(255,255,255,.82);
        transform: translateY(-2px);
        box-shadow: inset 0 1px 0 rgba(255,255,255,.95), 0 20px 48px -16px rgba(0,0,0,.2);
      }

      .skeleton {
        background: linear-gradient(90deg, rgba(0,0,0,.04) 25%, rgba(0,0,0,.09) 50%, rgba(0,0,0,.04) 75%);
        background-size: 200% 100%;
        animation: dashShimmer 1.6s linear infinite;
      }
      .no-scrollbar { scrollbar-width: none; -ms-overflow-style: none; }
      .no-scrollbar::-webkit-scrollbar { display: none; }

      @media (prefers-reduced-motion: reduce) {
        .anim-fade-up, .anim-fade-in, .anim-scale-in, .anim-slide-in, .anim-pop, .anim-float,
        .anim-indeterminate, .anim-spin-slow, .skeleton { animation: none !important; }
      }
    `}</style>
  );
}

// ============================================================
// UI PROVIDER (toasts + confirm dialog)
// ============================================================
const UIContext = createContext(null);

function useUI() {
  return useContext(UIContext);
}

function UIProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const [dialog, setDialog] = useState(null);
  const idRef = useRef(0);

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    (message, type = "success") => {
      const id = ++idRef.current;
      setToasts((prev) => [...prev, { id, message, type }]);
      setTimeout(() => dismiss(id), 3500);
    },
    [dismiss]
  );

  const confirm = useCallback(
    (opts) => new Promise((resolve) => setDialog({ ...opts, resolve })),
    []
  );

  const closeDialog = useCallback(
    (result) => {
      if (dialog) dialog.resolve(result);
      setDialog(null);
    },
    [dialog]
  );

  useEffect(() => {
    if (!dialog) return;
    const onKey = (e) => {
      if (e.key === "Escape") closeDialog(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [dialog, closeDialog]);

  const value = useMemo(() => ({ toast, confirm }), [toast, confirm]);

  return (
    <UIContext.Provider value={value}>
      {children}

      {/* Toasts — black pills */}
      <div className="pointer-events-none fixed right-4 top-24 z-[100] flex w-[min(92vw,22rem)] flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            className="anim-slide-in pointer-events-auto flex items-center gap-3 rounded-3xl bg-black py-2 pl-2 pr-4 text-white shadow-2xl"
          >
            <span
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
                t.type === "error" ? "bg-red-500 text-white" : "bg-white text-black"
              }`}
            >
              <Icon name={t.type === "error" ? "x" : "check"} className="h-3.5 w-3.5" strokeWidth={2.6} />
            </span>
            <p className="flex-1 py-1 text-sm">{t.message}</p>
            <button
              onClick={() => dismiss(t.id)}
              className="text-white/50 transition hover:text-white"
              aria-label="Dismiss"
            >
              <Icon name="x" className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>

      {/* Confirm dialog */}
      {dialog && (
        <div className="fixed inset-0 z-[110] flex items-center justify-center p-4">
          <div
            className="anim-fade-in absolute inset-0 bg-black/30 backdrop-blur-sm"
            onClick={() => closeDialog(false)}
          />
          <div
            role="alertdialog"
            aria-modal="true"
            className="glass anim-scale-in relative w-full max-w-sm rounded-[2rem] bg-white/90 p-7"
            style={{ background: "rgba(255,255,255,.92)" }}
          >
            <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-2xl bg-red-500/10 text-red-600">
              <Icon name="alert" className="h-5 w-5" />
            </div>
            <h3 className="text-xl font-bold uppercase tracking-tight text-neutral-950">{dialog.title}</h3>
            <p className="mt-2 text-sm text-neutral-500">{dialog.message}</p>
            <div className="mt-7 flex justify-end gap-3">
              <PillButton variant="light" icon={null} onClick={() => closeDialog(false)}>
                Cancel
              </PillButton>
              <button
                className="inline-flex items-center justify-center rounded-full bg-red-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-red-500 active:scale-[0.97]"
                onClick={() => closeDialog(true)}
              >
                {dialog.confirmLabel || "Confirm"}
              </button>
            </div>
          </div>
        </div>
      )}
    </UIContext.Provider>
  );
}

// ============================================================
// MAIN EXPORT
// ============================================================
export default function UserDashboard() {
  return (
    <UIProvider>
      <GlobalStyles />
      <Dashboard />
    </UIProvider>
  );
}

// ============================================================
// DASHBOARD SHELL
// ============================================================
function Dashboard() {
  const router = useRouter();

  const [user, setUser] = useState(null);
  const [activeSection, setActiveSection] = useState("overview");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [loadKey, setLoadKey] = useState(0);

  // Data
  const [profile, setProfile] = useState(null);
  const [resumes, setResumes] = useState([]);
  const [experiences, setExperiences] = useState([]);
  const [candSkills, setCandSkills] = useState([]);
  const [candQuals, setCandQuals] = useState([]);
  const [candLangs, setCandLangs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [jobsMap, setJobsMap] = useState({});

  // Master lists
  const [masterSkills, setMasterSkills] = useState([]);
  const [masterQuals, setMasterQuals] = useState([]);
  const [masterLangs, setMasterLangs] = useState([]);

  // -------- Loaders --------
  const loadAll = useCallback(async (candidateId) => {
    const safe = (p) => p.catch(() => ({ data: [] }));
    const [
      profileRes, resumesRes, expRes, skillsRes, qualsRes, langsRes,
      appsRes, jobsRes, msRes, mqRes, mlRes,
    ] = await Promise.all([
      apiRequest(`/api/candidate-profiles/${candidateId}/`).catch(() => null),
      safe(apiRequest("/api/resumes/")),
      safe(apiRequest("/api/experiences/")),
      safe(apiRequest("/api/candidate-skills/")),
      safe(apiRequest("/api/candidate-qualifications/")),
      safe(apiRequest("/api/candidate-languages/")),
      safe(apiRequest("/api/applications/")),
      safe(apiRequest("/api/jobs/")),
      safe(apiRequest("/api/skills/")),
      safe(apiRequest("/api/qualifications/")),
      safe(apiRequest("/api/languages/")),
    ]);

    setProfile(profileRes?.data || null);
    setResumes((resumesRes.data || []).filter((r) => r.candidate_id === candidateId));
    setExperiences((expRes.data || []).filter((r) => r.candidate_id === candidateId));
    setCandSkills((skillsRes.data || []).filter((r) => r.candidate_id === candidateId));
    setCandQuals((qualsRes.data || []).filter((r) => r.candidate_id === candidateId));
    setCandLangs((langsRes.data || []).filter((r) => r.candidate_id === candidateId));
    setApplications((appsRes.data || []).filter((r) => r.candidate_id === candidateId));

    const jMap = {};
    (jobsRes.data || []).forEach((j) => { jMap[j.job_id] = j; });
    setJobsMap(jMap);

    setMasterSkills(msRes.data || []);
    setMasterQuals(mqRes.data || []);
    setMasterLangs(mlRes.data || []);
  }, []);

  useEffect(() => {
    const storedUser = getStoredUser();
    if (!storedUser) {
      router.push("/Auth/Login");
      return;
    }
    if (storedUser.role !== "candidate") {
      setError("This dashboard is only for candidates.");
      setIsLoading(false);
      return;
    }
    setUser(storedUser);
    setError("");
    setIsLoading(true);
    loadAll(storedUser.candidate_id)
      .catch((err) => setError(err.message))
      .finally(() => setIsLoading(false));
  }, [router, loadAll, loadKey]);

  // -------- Derived --------
  const counts = {
    resume: resumes.length,
    experience: experiences.length,
    skills: candSkills.length,
    qualifications: candQuals.length,
    languages: candLangs.length,
    applications: applications.length,
  };

  const checklist = useMemo(
    () => [
      {
        id: "profile",
        label: "Complete personal details",
        hint: "Add your date of birth, gender and address",
        done: Boolean(profile?.date_of_birth && profile?.gender && profile?.address),
      },
      { id: "resume", label: "Upload a resume", hint: "Recruiters look for a PDF or DOCX resume", done: resumes.length > 0 },
      { id: "experience", label: "Add work experience", hint: "List at least one role you've held", done: experiences.length > 0 },
      { id: "skills", label: "Add your skills", hint: "Pick skills that match the jobs you want", done: candSkills.length > 0 },
      { id: "qualifications", label: "Add qualifications", hint: "Degrees, diplomas or certifications", done: candQuals.length > 0 },
      { id: "languages", label: "Add languages", hint: "Languages you speak and how well", done: candLangs.length > 0 },
    ],
    [profile, resumes, experiences, candSkills, candQuals, candLangs]
  );
  const percent = Math.round((checklist.filter((c) => c.done).length / checklist.length) * 100);

  // -------- Loading / Error --------
  if (isLoading) return <DashboardSkeleton />;

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4" style={PAGE_BG}>
        <div className="glass anim-scale-in max-w-md rounded-[2rem] p-9 text-center">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/10 text-red-600">
            <Icon name="alert" className="h-6 w-6" />
          </div>
          <h2 className="text-2xl font-bold uppercase tracking-tight text-neutral-950">
            Something<br />
            <span className="text-neutral-400">went wrong.</span>
          </h2>
          <p className="mt-3 text-sm text-neutral-500">{error}</p>
          <div className="mt-7 flex flex-wrap justify-center gap-3">
            {user && (
              <PillButton onClick={() => setLoadKey((k) => k + 1)} icon="refresh">
                Try again
              </PillButton>
            )}
            <PillButton variant="light" icon={null} onClick={() => router.push("/Auth/Login")}>
              Back to login
            </PillButton>
          </div>
        </div>
      </div>
    );
  }

  // -------- Layout --------
  return (
    <div className="relative min-h-screen overflow-hidden pb-24 pt-24 text-neutral-900" style={PAGE_BG}>
      <BackgroundRings />
      <SideIndex sections={SECTIONS} active={activeSection} onSelect={setActiveSection} />

      <div className="relative mx-auto max-w-6xl px-4">
        <TopBar
          sections={SECTIONS}
          active={activeSection}
          onSelect={setActiveSection}
          counts={counts}
          profile={profile}
          onRefresh={() => setLoadKey((k) => k + 1)}
        />

        <main key={activeSection} className="anim-fade-up mt-12 min-w-0">
          {activeSection === "overview" && (
            <OverviewSection
              profile={profile}
              counts={counts}
              experiences={experiences}
              checklist={checklist}
              percent={percent}
              applications={applications}
              jobsMap={jobsMap}
              onNavigate={setActiveSection}
            />
          )}
          {activeSection === "profile" && (
            <ProfileSection profile={profile} candidateId={user.candidate_id} onUpdate={setProfile} />
          )}
          {activeSection === "resume" && (
            <ResumeSection resumes={resumes} setResumes={setResumes} candidateId={user.candidate_id} />
          )}
          {activeSection === "experience" && (
            <ExperienceSection experiences={experiences} setExperiences={setExperiences} candidateId={user.candidate_id} />
          )}
          {activeSection === "skills" && (
            <SkillsSection
              skills={candSkills}
              setSkills={setCandSkills}
              masterSkills={masterSkills}
              candidateId={user.candidate_id}
            />
          )}
          {activeSection === "qualifications" && (
            <QualificationsSection
              quals={candQuals}
              setQuals={setCandQuals}
              masterQuals={masterQuals}
              candidateId={user.candidate_id}
            />
          )}
          {activeSection === "languages" && (
            <LanguagesSection
              langs={candLangs}
              setLangs={setCandLangs}
              masterLangs={masterLangs}
              candidateId={user.candidate_id}
            />
          )}
          {activeSection === "applications" && (
            <ApplicationsSection applications={applications} jobsMap={jobsMap} />
          )}
        </main>
      </div>
    </div>
  );
}

// ============================================================
// SHELL PIECES
// ============================================================
function BackgroundRings() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      <div className="absolute -right-48 top-8 h-[48rem] w-[48rem] rounded-full border border-black/[0.05]" />
      <div className="absolute -right-24 top-32 h-[36rem] w-[36rem] rounded-full border border-black/[0.04]" />
      <div className="absolute -left-40 bottom-0 h-[34rem] w-[34rem] rounded-full border border-black/[0.04]" />
    </div>
  );
}

function TopBar({ sections, active, onSelect, counts, profile, onRefresh }) {
  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <nav className="glass no-scrollbar flex max-w-full items-center gap-0.5 overflow-x-auto rounded-full p-1.5">
        {sections.map((s) => {
          const isActive = active === s.id;
          const c = counts[s.id];
          return (
            <button
              key={s.id}
              onClick={() => onSelect(s.id)}
              className={`relative shrink-0 whitespace-nowrap rounded-full px-3.5 pb-3.5 pt-2.5 text-[13px] transition-colors ${
                isActive ? "font-semibold text-black" : "text-neutral-500 hover:text-black"
              }`}
            >
              {s.label}
              {c > 0 && <sup className="ml-0.5 text-[9px] font-semibold text-neutral-400">{c}</sup>}
              <span
                className={`absolute bottom-2 left-1/2 h-1 w-1 -translate-x-1/2 rounded-full bg-black transition-all duration-300 ${
                  isActive ? "scale-100 opacity-100" : "scale-0 opacity-0"
                }`}
              />
            </button>
          );
        })}
      </nav>

      <div className="flex items-center gap-2 self-end lg:self-auto">
        <button
          onClick={onRefresh}
          aria-label="Refresh data"
          className="glass flex h-11 w-11 items-center justify-center rounded-full text-neutral-600 transition hover:text-black active:scale-95"
        >
          <Icon name="refresh" className="h-4 w-4" />
        </button>
        <div className="glass flex items-center gap-2.5 rounded-full py-1.5 pl-1.5 pr-5">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-black text-[11px] font-bold text-white">
            {getInitials(profile?.full_name)}
          </span>
          <span className="hidden min-w-0 sm:block">
            <span className="block max-w-[10rem] truncate text-xs font-semibold text-neutral-900">
              {profile?.full_name || "Candidate"}
            </span>
            <span className="block max-w-[10rem] truncate text-[10px] text-neutral-500">{profile?.email}</span>
          </span>
        </div>
      </div>
    </div>
  );
}

function SideIndex({ sections, active, onSelect }) {
  return (
    <div className="fixed right-6 top-1/2 z-30 hidden -translate-y-1/2 flex-col items-center xl:flex">
      {sections.map((s, i) => {
        const isActive = s.id === active;
        return (
          <button
            key={s.id}
            onClick={() => onSelect(s.id)}
            title={s.label}
            aria-label={s.label}
            className="group flex flex-col items-center"
          >
            <span
              className={`py-1.5 tabular-nums transition-all duration-300 ${
                isActive
                  ? "text-sm font-bold text-black"
                  : "text-[11px] text-neutral-400 group-hover:text-neutral-700"
              }`}
            >
              {String(i + 1).padStart(2, "0")}
            </span>
            <span
              className="block w-px bg-black transition-all duration-500 ease-out"
              style={{ height: isActive ? 34 : 0, opacity: isActive ? 1 : 0 }}
            />
          </button>
        );
      })}
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="min-h-screen pb-16 pt-24" style={PAGE_BG}>
      <div className="mx-auto max-w-6xl px-4">
        <div className="flex items-center justify-between">
          <div className="skeleton h-12 w-[34rem] max-w-[70%] rounded-full" />
          <div className="skeleton h-12 w-44 rounded-full" />
        </div>
        <div className="mt-14 grid items-center gap-10 lg:grid-cols-2">
          <div className="space-y-4">
            <div className="skeleton h-6 w-40 rounded-full" />
            <div className="skeleton h-16 w-4/5 rounded-2xl" />
            <div className="skeleton h-16 w-3/5 rounded-2xl" />
            <div className="skeleton h-16 w-2/5 rounded-2xl" />
            <div className="skeleton mt-6 h-12 w-56 rounded-full" />
          </div>
          <div className="skeleton mx-auto aspect-square w-full max-w-sm rounded-full" />
        </div>
        <div className="skeleton mt-12 h-28 rounded-[2rem]" />
      </div>
    </div>
  );
}

// ============================================================
// OVERVIEW SECTION
// ============================================================
function OverviewSection({
  profile, counts, experiences, checklist, percent, applications, jobsMap, onNavigate,
}) {
  const firstName = (profile?.full_name || "there").trim().split(/\s+/)[0];
  const totalMonths = experiences.reduce((sum, e) => sum + monthsBetween(e.start_date, e.end_date), 0);
  const nextStep = checklist.find((c) => !c.done);
  const remaining = checklist.filter((c) => !c.done).length;

  const statusCounts = STATUS_ORDER.reduce((acc, k) => {
    acc[k] = applications.filter((a) => a.application_status === k).length;
    return acc;
  }, {});
  const total = applications.length;

  const recent = useMemo(
    () =>
      [...applications]
        .sort((a, b) => new Date(b.applied_at) - new Date(a.applied_at))
        .slice(0, 3),
    [applications]
  );

  const stats = [
    { id: "resume", label: "Resumes", value: counts.resume, icon: "document", sub: "Uploaded files" },
    {
      id: "experience",
      label: "Experience",
      value: counts.experience,
      icon: "briefcase",
      sub: totalMonths ? `≈ ${formatMonths(totalMonths)}` : "Roles added",
    },
    { id: "skills", label: "Skills", value: counts.skills, icon: "sparkles", sub: "On your profile" },
    { id: "qualifications", label: "Qualifications", value: counts.qualifications, icon: "cap", sub: "Education" },
    { id: "languages", label: "Languages", value: counts.languages, icon: "language", sub: "Spoken" },
    { id: "applications", label: "Applications", value: counts.applications, icon: "send", sub: "Jobs applied" },
  ];

  return (
    <div>
      {/* ---------- Hero ---------- */}
      <section className="grid items-center gap-12 lg:grid-cols-[1.1fr_1fr]">
        <div>
          <Tag>{getGreeting()}</Tag>
          <h1 className="mt-6 break-words text-5xl font-bold uppercase leading-[0.92] tracking-tight text-neutral-950 sm:text-6xl lg:text-7xl">
            Welcome.
            <br />
            {firstName}.
            <br />
            <span className="text-neutral-400">{percent}% ready.</span>
          </h1>

          <div className="mt-8 text-neutral-900">
            <ArrowLine />
          </div>
          <p className="mt-5 max-w-sm text-base leading-relaxed text-neutral-500">
            {percent === 100
              ? "Your profile is complete. Recruiters can now see the full picture and keep you ahead."
              : `Finish ${remaining} more step${remaining > 1 ? "s" : ""} to stand out to recruiters and keep your profile ahead.`}
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-5">
            <PillButton onClick={() => onNavigate(nextStep ? nextStep.id : "applications")}>
              {nextStep ? "Continue setup" : "View applications"}
            </PillButton>
            <button
              onClick={() => onNavigate("profile")}
              className="group flex items-center gap-3 text-sm font-semibold text-neutral-900"
            >
              <span className="flex h-11 w-11 items-center justify-center rounded-full bg-white shadow-[0_8px_24px_-8px_rgba(0,0,0,0.25)] ring-1 ring-black/5 transition group-hover:scale-105">
                <Icon name="user" className="h-4 w-4" />
              </span>
              View profile
            </button>
          </div>
        </div>

        <HeroRing percent={percent} skills={counts.skills} applications={counts.applications} />
      </section>

      {/* ---------- Glass feature strip ---------- */}
      <section className="glass mt-14 rounded-[2rem] p-2">
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6">
          {stats.map((s, i) => (
            <StatCell key={s.id} {...s} delay={i * 70} onClick={() => onNavigate(s.id)} />
          ))}
        </div>
      </section>

      {/* ---------- Checklist + pipeline ---------- */}
      <section className="mt-6 grid gap-6 lg:grid-cols-5">
        <div className={`${cardCls} p-6 lg:col-span-3`}>
          <Tag>Getting started</Tag>
          <ul className="mt-5 space-y-1">
            {checklist.map((item, i) => (
              <li key={item.id} className="anim-fade-up" style={{ animationDelay: `${i * 60}ms` }}>
                <button
                  onClick={() => onNavigate(item.id)}
                  className="group flex w-full items-center gap-4 rounded-2xl px-3 py-3 text-left transition hover:bg-white/70"
                >
                  <span
                    className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full transition ${
                      item.done ? "bg-black text-white" : "border border-black/20 text-transparent"
                    }`}
                  >
                    <Icon name="check" className="h-3 w-3" strokeWidth={3} />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span
                      className={`block text-sm font-semibold ${
                        item.done ? "text-neutral-400 line-through" : "text-neutral-900"
                      }`}
                    >
                      {item.label}
                    </span>
                    {!item.done && <span className="block text-xs text-neutral-500">{item.hint}</span>}
                  </span>
                  <Icon
                    name="arrowUpRight"
                    className="h-4 w-4 shrink-0 text-neutral-300 transition group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-black"
                  />
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="flex flex-col gap-6 lg:col-span-2">
          <div className={`${cardCls} p-6`}>
            <Tag>Pipeline</Tag>
            {total === 0 ? (
              <p className="mt-5 text-sm text-neutral-500">You haven&apos;t applied to any jobs yet.</p>
            ) : (
              <>
                <div className="mt-5 flex h-2.5 w-full overflow-hidden rounded-full bg-black/5">
                  {STATUS_ORDER.map(
                    (k) =>
                      statusCounts[k] > 0 && (
                        <div
                          key={k}
                          className={`${STATUS_STYLES[k].bar} transition-all duration-700`}
                          style={{ width: `${(statusCounts[k] / total) * 100}%` }}
                        />
                      )
                  )}
                </div>
                <div className="mt-5 grid grid-cols-2 gap-x-6 gap-y-2.5">
                  {STATUS_ORDER.map((k) => (
                    <div key={k} className="flex items-center gap-2 text-xs text-neutral-500">
                      <span className={`h-2 w-2 rounded-full ${STATUS_STYLES[k].dot}`} />
                      <span className="flex-1">{STATUS_STYLES[k].label}</span>
                      <span className="font-bold text-neutral-900">{statusCounts[k]}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>

          <div className={`${cardCls} p-6`}>
            <div className="flex items-center justify-between">
              <Tag>Recent</Tag>
              {total > 0 && (
                <button
                  onClick={() => onNavigate("applications")}
                  className="text-xs font-semibold text-neutral-500 transition hover:text-black"
                >
                  View all
                </button>
              )}
            </div>
            {recent.length === 0 ? (
              <p className="mt-5 text-sm text-neutral-500">Nothing here yet.</p>
            ) : (
              <ul className="mt-5 space-y-3.5">
                {recent.map((a) => {
                  const st = STATUS_STYLES[a.application_status];
                  return (
                    <li key={a.application_id} className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-neutral-900">
                          {jobsMap[a.job_id]?.job_title || `Job #${a.job_id}`}
                        </p>
                        <p className="text-[11px] text-neutral-500">{formatDate(a.applied_at)}</p>
                      </div>
                      <span
                        className={`shrink-0 rounded-full px-3 py-1 text-[10px] font-semibold ${
                          st?.badge || "bg-black/5 text-neutral-600"
                        }`}
                      >
                        {st?.label || capitalize(a.application_status) || "Unknown"}
                      </span>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

function HeroRing({ percent, skills, applications }) {
  const R = 196;
  const C = 2 * Math.PI * R;
  const [offset, setOffset] = useState(C);
  const shown = useCountUp(percent, 1200);

  useEffect(() => {
    const t = setTimeout(() => setOffset(C - (percent / 100) * C), 120);
    return () => clearTimeout(t);
  }, [percent, C]);

  return (
    <div className="relative mx-auto aspect-square w-full max-w-[26rem]">
      {/* concentric rings + progress arc */}
      <svg viewBox="0 0 400 400" className="absolute inset-0 h-full w-full -rotate-90">
        <circle cx="200" cy="200" r={R} fill="none" stroke="rgba(0,0,0,0.08)" strokeWidth="1" />
        <circle cx="200" cy="200" r="172" fill="none" stroke="rgba(0,0,0,0.05)" strokeWidth="1" />
        <circle
          cx="200"
          cy="200"
          r={R}
          fill="none"
          stroke="#0a0a0a"
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray={C}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 1.4s cubic-bezier(.22,1,.36,1)" }}
        />
      </svg>

      {/* striped glass disc */}
      <div
        className="absolute inset-[13%] rounded-full"
        style={{
          background:
            "repeating-linear-gradient(90deg, rgba(0,0,0,0.05) 0px, rgba(0,0,0,0.05) 1px, transparent 1px, transparent 9px), radial-gradient(circle at 50% 30%, #ffffff 0%, #f1f1f1 70%, #e8e8e8 100%)",
          boxShadow: "inset 0 0 40px rgba(0,0,0,0.05), 0 30px 60px -30px rgba(0,0,0,0.25)",
        }}
      />

      {/* center readout */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-7xl font-bold tracking-tight text-neutral-950 sm:text-8xl">
          {shown}
          <span className="text-4xl text-neutral-400 sm:text-5xl">%</span>
        </span>
        <span className="mt-2 text-[10px] font-medium uppercase tracking-[0.25em] text-neutral-500">
          Profile strength
        </span>
      </div>

      {/* floating glass chips */}
      <div className="glass anim-float absolute left-[-2%] top-[10%] flex items-center gap-2.5 rounded-full py-1.5 pl-1.5 pr-4">
        <IconTile icon="sparkles" size="sm" />
        <span className="text-xs font-semibold text-neutral-900">{skills} skills</span>
      </div>
      <div
        className="glass anim-float absolute bottom-[10%] right-[-2%] flex items-center gap-2.5 rounded-full py-1.5 pl-1.5 pr-4"
        style={{ animationDelay: "1.4s" }}
      >
        <IconTile icon="send" size="sm" />
        <span className="text-xs font-semibold text-neutral-900">{applications} applied</span>
      </div>
    </div>
  );
}

function StatCell({ label, value, icon, sub, delay = 0, onClick }) {
  const shown = useCountUp(value);
  return (
    <button
      onClick={onClick}
      className="anim-fade-up group flex items-center gap-3.5 rounded-3xl px-4 py-5 text-left transition hover:bg-white/70 xl:rounded-none xl:border-l xl:border-black/5 xl:first:border-l-0"
      style={{ animationDelay: `${delay}ms` }}
    >
      <IconTile icon={icon} />
      <span className="min-w-0">
        <span className="block text-xs font-semibold text-neutral-900">{label}</span>
        <span className="block text-2xl font-bold leading-tight tracking-tight text-neutral-950">{shown}</span>
        <span className="block truncate text-[10px] text-neutral-500">{sub}</span>
      </span>
    </button>
  );
}

// ============================================================
// PROFILE SECTION
// ============================================================
function ProfileSection({ profile, candidateId, onUpdate }) {
  const { toast } = useUI();
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [form, setForm] = useState({ date_of_birth: "", gender: "", address: "" });

  const age = calcAge(profile?.date_of_birth);

  const handleStart = () => {
    setForm({
      date_of_birth: profile?.date_of_birth || "",
      gender: profile?.gender || "",
      address: profile?.address || "",
    });
    setSaveError("");
    setIsEditing(true);
  };

  const handleSave = async () => {
    if (form.date_of_birth && form.date_of_birth > todayStr()) {
      setSaveError("Date of birth cannot be in the future.");
      return;
    }
    setIsSaving(true);
    setSaveError("");
    try {
      await apiRequest(`/api/candidate-profiles/${candidateId}/update/`, {
        method: "PUT",
        body: form,
      });
      onUpdate((prev) => ({ ...prev, ...form }));
      setIsEditing(false);
      toast("Profile updated");
    } catch (err) {
      setSaveError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div>
      <SectionHeader
        tag="Personal details"
        title="Your"
        accent="Profile."
        subtitle="Your personal details, exactly as recruiters see them."
        action={
          !isEditing && (
            <PillButton onClick={handleStart} icon="pencil">
              Edit profile
            </PillButton>
          )
        }
      />

      {/* identity card */}
      <div className="glass relative mb-6 flex items-center gap-5 overflow-hidden rounded-[2rem] p-6">
        <div className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full border border-black/5" />
        <div className="pointer-events-none absolute -right-8 -top-8 h-40 w-40 rounded-full border border-black/5" />
        <div className="anim-float flex h-20 w-20 shrink-0 items-center justify-center rounded-full bg-black text-2xl font-bold text-white shadow-[0_16px_40px_-12px_rgba(0,0,0,0.5)]">
          {getInitials(profile?.full_name)}
        </div>
        <div className="relative min-w-0">
          <p className="truncate text-2xl font-bold uppercase tracking-tight text-neutral-950">
            {profile?.full_name || "Candidate"}
          </p>
          <p className="truncate text-sm text-neutral-500">{profile?.email}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Tag>Candidate</Tag>
            {age !== null && <Tag>{age} years old</Tag>}
          </div>
        </div>
      </div>

      <div className="glass rounded-[2rem] p-6 sm:p-8">
        <div className="grid gap-7 sm:grid-cols-2">
          <InfoField icon="user" label="Full Name" value={profile?.full_name} />
          <InfoField icon="mail" label="Email" value={profile?.email} />
          <InfoField icon="phone" label="Phone" value={profile?.phone_no} />

          {isEditing ? (
            <>
              <div className="anim-fade-up">
                <FieldLabel>Date of Birth</FieldLabel>
                <input
                  type="date"
                  max={todayStr()}
                  value={form.date_of_birth || ""}
                  onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })}
                  className={inputCls}
                />
              </div>
              <div className="anim-fade-up" style={{ animationDelay: "60ms" }}>
                <FieldLabel>Gender</FieldLabel>
                <select
                  value={form.gender || ""}
                  onChange={(e) => setForm({ ...form, gender: e.target.value })}
                  className={inputCls}
                >
                  <option value="">— Select —</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="anim-fade-up sm:col-span-2" style={{ animationDelay: "120ms" }}>
                <FieldLabel>Address</FieldLabel>
                <textarea
                  rows={3}
                  value={form.address || ""}
                  onChange={(e) => setForm({ ...form, address: e.target.value })}
                  placeholder="Street, city, country"
                  className={inputCls}
                />
              </div>
            </>
          ) : (
            <>
              <InfoField
                icon="calendar"
                label="Date of Birth"
                value={profile?.date_of_birth ? formatDate(profile.date_of_birth) : null}
              />
              <InfoField icon="user" label="Gender" value={capitalize(profile?.gender) || null} />
              <InfoField icon="pin" label="Address" value={profile?.address} fullWidth />
            </>
          )}
        </div>

        {isEditing && (
          <div className="anim-fade-up mt-8 border-t border-black/5 pt-6">
            <ErrorBanner message={saveError} />
            <div className="flex flex-wrap gap-3">
              <PillButton onClick={handleSave} loading={isSaving} icon="check">
                {isSaving ? "Saving..." : "Save changes"}
              </PillButton>
              <PillButton variant="light" icon={null} onClick={() => setIsEditing(false)} disabled={isSaving}>
                Cancel
              </PillButton>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================
// RESUME SECTION
// ============================================================
function ResumeSection({ resumes, setResumes, candidateId }) {
  const { toast, confirm } = useUI();
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [error, setError] = useState("");

  const pickFile = (f) => {
    if (!f) return;
    const ext = fileExt(f.name);
    if (!["pdf", "docx"].includes(ext)) {
      setError("Only PDF or DOCX files are supported.");
      return;
    }
    if (f.size > MAX_FILE_MB * 1024 * 1024) {
      setError(`File is too large. Maximum size is ${MAX_FILE_MB} MB.`);
      return;
    }
    setError("");
    setFile(f);
  };

  const clearFile = () => {
    setFile(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setIsUploading(true);
    setError("");
    try {
      const fd = new FormData();
      fd.append("candidate_id", candidateId);
      fd.append("file", file);

      const res = await apiRequest("/api/resumes/create/", {
        method: "POST",
        body: fd,
        isFormData: true,
      });
      setResumes((prev) => [res.data, ...prev]);
      clearFile();
      toast("Resume uploaded");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (r) => {
    const ok = await confirm({
      title: "Delete resume?",
      message: `"${r.file_name}" will be permanently removed.`,
      confirmLabel: "Delete",
    });
    if (!ok) return;
    setDeletingId(r.resume_id);
    try {
      await apiRequest(`/api/resumes/${r.resume_id}/delete/`, { method: "DELETE" });
      setResumes((prev) => prev.filter((x) => x.resume_id !== r.resume_id));
      toast("Resume deleted");
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div>
      <SectionHeader
        tag="Documents"
        title="Your"
        accent="Resume."
        subtitle={`Upload a PDF or DOCX (max ${MAX_FILE_MB} MB).`}
      />

      <form onSubmit={handleUpload} className="mb-6">
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          className="hidden"
          onChange={(e) => pickFile(e.target.files?.[0] || null)}
        />

        {!file ? (
          <div
            role="button"
            tabIndex={0}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                inputRef.current?.click();
              }
            }}
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              pickFile(e.dataTransfer.files?.[0]);
            }}
            className={`flex cursor-pointer flex-col items-center rounded-[2rem] border-2 border-dashed px-6 py-14 text-center transition duration-300 ${
              dragging
                ? "scale-[1.01] border-black/50 bg-white/90"
                : "border-black/15 bg-white/40 hover:border-black/30 hover:bg-white/70"
            }`}
          >
            <span className="anim-float mb-4 flex h-16 w-16 items-center justify-center rounded-3xl bg-black text-white shadow-[0_16px_40px_-12px_rgba(0,0,0,0.5)]">
              <Icon name="upload" className="h-7 w-7" />
            </span>
            <p className="text-lg font-bold uppercase tracking-tight text-neutral-950">
              {dragging ? "Drop it here." : "Drag & drop your resume"}
            </p>
            <p className="mt-1 text-sm text-neutral-500">or click to browse · PDF or DOCX</p>
          </div>
        ) : (
          <div className="glass anim-scale-in rounded-[2rem] p-5">
            <div className="flex items-center gap-4">
              <FileBadge name={file.name} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-neutral-900">{file.name}</p>
                <p className="text-xs text-neutral-500">{formatBytes(file.size)}</p>
              </div>
              <button
                type="button"
                onClick={clearFile}
                disabled={isUploading}
                className="flex h-9 w-9 items-center justify-center rounded-full text-neutral-500 transition hover:bg-black/5 hover:text-black disabled:opacity-50"
                aria-label="Remove selected file"
              >
                <Icon name="x" className="h-4 w-4" />
              </button>
            </div>
            {isUploading && (
              <div className="mt-4 h-1 overflow-hidden rounded-full bg-black/10">
                <div className="anim-indeterminate h-full w-1/4 rounded-full bg-black" />
              </div>
            )}
            <div className="mt-5 flex flex-wrap gap-3">
              <PillButton type="submit" loading={isUploading} icon="upload">
                {isUploading ? "Uploading..." : "Upload"}
              </PillButton>
              <PillButton variant="light" icon={null} onClick={clearFile} disabled={isUploading}>
                Cancel
              </PillButton>
            </div>
          </div>
        )}
      </form>

      <ErrorBanner message={error} />

      {resumes.length === 0 ? (
        <EmptyState
          icon="document"
          title="No resumes uploaded yet"
          text="Upload your resume so recruiters can review your background."
        />
      ) : (
        <ul className="space-y-3">
          {resumes.map((r, i) => (
            <li
              key={r.resume_id}
              className={`${cardCls} anim-fade-up flex items-center gap-4 p-4`}
              style={{ animationDelay: `${i * 60}ms` }}
            >
              <FileBadge name={r.file_name} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-neutral-900">{r.file_name}</p>
                <p className="text-xs text-neutral-500">Uploaded {formatDate(r.uploaded_at)}</p>
              </div>
              <button
                onClick={() => handleDelete(r)}
                disabled={deletingId === r.resume_id}
                className={btnDanger}
              >
                {deletingId === r.resume_id ? <Spinner /> : <Icon name="trash" className="h-3.5 w-3.5" />}
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function FileBadge({ name }) {
  const ext = fileExt(name);
  const tone =
    ext === "pdf"
      ? "bg-red-500/10 text-red-600"
      : ext === "docx"
      ? "bg-blue-500/10 text-blue-600"
      : "bg-black/5 text-neutral-600";
  return (
    <div className={`flex h-12 w-12 shrink-0 flex-col items-center justify-center gap-0.5 rounded-2xl ${tone}`}>
      <Icon name="document" className="h-4 w-4" />
      <span className="text-[8px] font-bold uppercase leading-none">{ext}</span>
    </div>
  );
}

// ============================================================
// EXPERIENCE SECTION
// ============================================================
function ExperienceSection({ experiences, setExperiences, candidateId }) {
  const { toast, confirm } = useUI();
  const emptyForm = { company_name: "", designation: "", start_date: "", end_date: "" };
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [isSaving, setIsSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [error, setError] = useState("");

  const sorted = useMemo(
    () => [...experiences].sort((a, b) => new Date(b.start_date) - new Date(a.start_date)),
    [experiences]
  );
  const totalMonths = experiences.reduce((sum, e) => sum + monthsBetween(e.start_date, e.end_date), 0);

  const resetForm = () => {
    setForm(emptyForm);
    setEditing(null);
    setShowForm(false);
    setError("");
  };

  const handleEdit = (exp) => {
    setForm({
      company_name: exp.company_name,
      designation: exp.designation,
      start_date: exp.start_date,
      end_date: exp.end_date || "",
    });
    setEditing(exp);
    setShowForm(true);
    setError("");
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (form.end_date && form.end_date < form.start_date) {
      setError("End date cannot be before the start date.");
      return;
    }
    setIsSaving(true);
    setError("");
    try {
      if (editing) {
        await apiRequest(`/api/experiences/${editing.exp_id}/update/`, { method: "PUT", body: form });
        setExperiences((prev) => prev.map((x) => (x.exp_id === editing.exp_id ? { ...x, ...form } : x)));
        toast("Experience updated");
      } else {
        const res = await apiRequest("/api/experiences/create/", {
          method: "POST",
          body: { ...form, candidate_id: candidateId },
        });
        setExperiences((prev) => [res.data, ...prev]);
        toast("Experience added");
      }
      resetForm();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (exp) => {
    const ok = await confirm({
      title: "Delete experience?",
      message: `${exp.designation} at ${exp.company_name} will be removed from your profile.`,
      confirmLabel: "Delete",
    });
    if (!ok) return;
    setDeletingId(exp.exp_id);
    try {
      await apiRequest(`/api/experiences/${exp.exp_id}/delete/`, { method: "DELETE" });
      setExperiences((prev) => prev.filter((x) => x.exp_id !== exp.exp_id));
      toast("Experience deleted");
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div>
      <SectionHeader
        tag="Work history"
        title="Work"
        accent="Experience."
        subtitle={
          experiences.length
            ? `${experiences.length} role${experiences.length > 1 ? "s" : ""} · about ${formatMonths(totalMonths)} in total`
            : "Your work history, newest first."
        }
        action={
          !showForm && (
            <PillButton onClick={() => { resetForm(); setShowForm(true); }} icon="plus">
              Add experience
            </PillButton>
          )
        }
      />

      {showForm && (
        <form
          onSubmit={handleSave}
          className="glass anim-scale-in mb-8 space-y-5 rounded-[2rem] p-6 sm:p-8"
        >
          <p className="text-lg font-bold uppercase tracking-tight text-neutral-950">
            {editing ? "Edit experience" : "New experience"}
          </p>
          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <FieldLabel>Company Name</FieldLabel>
              <input
                required
                value={form.company_name}
                onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                placeholder="e.g. Acme Corp"
                className={inputCls}
              />
            </div>
            <div>
              <FieldLabel>Designation</FieldLabel>
              <input
                required
                value={form.designation}
                onChange={(e) => setForm({ ...form, designation: e.target.value })}
                placeholder="e.g. Software Engineer"
                className={inputCls}
              />
            </div>
            <div>
              <FieldLabel>Start Date</FieldLabel>
              <input
                required
                type="date"
                max={todayStr()}
                value={form.start_date}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                className={inputCls}
              />
            </div>
            <div>
              <FieldLabel>End Date (empty = current)</FieldLabel>
              <input
                type="date"
                min={form.start_date || undefined}
                value={form.end_date || ""}
                onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                className={inputCls}
              />
            </div>
          </div>
          <ErrorBanner message={error} />
          <div className="flex flex-wrap gap-3">
            <PillButton type="submit" loading={isSaving} icon="check">
              {isSaving ? "Saving..." : editing ? "Update" : "Create"}
            </PillButton>
            <PillButton variant="light" icon={null} onClick={resetForm}>
              Cancel
            </PillButton>
          </div>
        </form>
      )}

      {experiences.length === 0 ? (
        !showForm && (
          <EmptyState
            icon="briefcase"
            title="No experience added yet"
            text="Add the roles you've held to give recruiters a fuller picture."
            action={
              <PillButton onClick={() => setShowForm(true)} icon="plus">
                Add experience
              </PillButton>
            }
          />
        )
      ) : (
        <ol className="relative ml-3 space-y-5 border-l border-black/10 pl-7">
          {sorted.map((exp, i) => {
            const current = !exp.end_date;
            return (
              <li
                key={exp.exp_id}
                className="anim-fade-up relative"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <span
                  className={`absolute -left-[35px] top-7 h-3 w-3 rounded-full ring-4 ring-[#ebebeb] ${
                    current ? "bg-emerald-500" : "bg-neutral-400"
                  }`}
                />
                <div className={`${cardCls} p-5`}>
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="truncate text-base font-bold tracking-tight text-neutral-950">
                          {exp.designation}
                        </p>
                        {current && (
                          <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-700">
                            Current
                          </span>
                        )}
                      </div>
                      <p className="mt-1 flex items-center gap-1.5 truncate text-sm text-neutral-500">
                        <Icon name="building" className="h-4 w-4 shrink-0" />
                        {exp.company_name}
                      </p>
                      <p className="mt-3 flex flex-wrap items-center gap-x-2 text-xs text-neutral-500">
                        <Icon name="calendar" className="h-3.5 w-3.5" />
                        {formatDate(exp.start_date)} – {current ? "Present" : formatDate(exp.end_date)}
                        <span className="text-neutral-300">·</span>
                        <span>{formatMonths(monthsBetween(exp.start_date, exp.end_date))}</span>
                      </p>
                    </div>
                    <div className="flex shrink-0 gap-2">
                      <button onClick={() => handleEdit(exp)} className={btnSmall}>
                        <Icon name="pencil" className="h-3.5 w-3.5" /> Edit
                      </button>
                      <button
                        onClick={() => handleDelete(exp)}
                        disabled={deletingId === exp.exp_id}
                        className={btnDanger}
                      >
                        {deletingId === exp.exp_id ? <Spinner /> : <Icon name="trash" className="h-3.5 w-3.5" />}
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}

// ============================================================
// SKILLS SECTION
// ============================================================
function SkillsSection({ skills, setSkills, masterSkills, candidateId }) {
  const { toast } = useUI();
  const [selectedSkill, setSelectedSkill] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  const [removingId, setRemovingId] = useState(null);
  const [error, setError] = useState("");

  const available = masterSkills.filter((m) => !skills.some((s) => s.skill_id === m.skill_id));
  const suggestions = available.slice(0, 10);

  const handleAdd = async (skillId) => {
    const id = skillId ?? selectedSkill;
    if (!id) return;
    setIsAdding(true);
    setError("");
    try {
      const res = await apiRequest("/api/candidate-skills/create/", {
        method: "POST",
        body: { candidate_id: candidateId, skill_id: Number(id) },
      });
      setSkills((prev) => [...prev, res.data]);
      setSelectedSkill("");
      toast("Skill added");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsAdding(false);
    }
  };

  const handleRemove = async (csId) => {
    setRemovingId(csId);
    try {
      await apiRequest(`/api/candidate-skills/${csId}/delete/`, { method: "DELETE" });
      setSkills((prev) => prev.filter((s) => s.candidate_skill_id !== csId));
      toast("Skill removed");
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <div>
      <SectionHeader
        tag="Expertise"
        title="Your"
        accent="Skills."
        subtitle={
          skills.length
            ? `${skills.length} skill${skills.length > 1 ? "s" : ""} on your profile`
            : "Show recruiters what you're good at."
        }
      />

      <div className="glass mb-6 rounded-[2rem] p-5 sm:p-6">
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={selectedSkill}
            onChange={(e) => setSelectedSkill(e.target.value)}
            className={`${baseInput} min-w-[12rem] flex-1 sm:flex-none sm:basis-72`}
          >
            <option value="">— Select skill —</option>
            {available.map((m) => (
              <option key={m.skill_id} value={m.skill_id}>{m.skill_name}</option>
            ))}
          </select>
          <PillButton onClick={() => handleAdd()} disabled={!selectedSkill} loading={isAdding} icon="plus">
            {isAdding ? "Adding..." : "Add skill"}
          </PillButton>
        </div>

        {suggestions.length > 0 && (
          <div className="mt-5 border-t border-black/5 pt-5">
            <Tag>Quick add</Tag>
            <div className="mt-3 flex flex-wrap gap-2">
              {suggestions.map((m) => (
                <button
                  key={m.skill_id}
                  onClick={() => handleAdd(m.skill_id)}
                  disabled={isAdding}
                  className="inline-flex items-center gap-1.5 rounded-full border border-dashed border-black/20 px-3.5 py-1.5 text-xs font-medium text-neutral-600 transition hover:border-black hover:bg-black hover:text-white active:scale-95 disabled:opacity-50"
                >
                  <Icon name="plus" className="h-3 w-3" strokeWidth={2.5} /> {m.skill_name}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      <ErrorBanner message={error} />

      {skills.length === 0 ? (
        <EmptyState
          icon="sparkles"
          title="No skills added yet"
          text="Pick from the list above to build your skill set."
        />
      ) : (
        <div className="flex flex-wrap gap-2.5">
          {skills.map((s, i) => (
            <span
              key={s.candidate_skill_id}
              className="glass anim-pop inline-flex items-center gap-2 rounded-full py-2 pl-4 pr-2 text-sm font-semibold text-neutral-900 transition hover:bg-white"
              style={{ animationDelay: `${Math.min(i, 20) * 35}ms` }}
            >
              {s.skill_name}
              <button
                onClick={() => handleRemove(s.candidate_skill_id)}
                disabled={removingId === s.candidate_skill_id}
                className="flex h-5 w-5 items-center justify-center rounded-full bg-black/5 text-neutral-500 transition hover:bg-red-500 hover:text-white disabled:opacity-50"
                aria-label={`Remove ${s.skill_name}`}
              >
                <Icon name="x" className="h-3 w-3" strokeWidth={2.5} />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================
// QUALIFICATIONS SECTION
// ============================================================
function QualificationsSection({ quals, setQuals, masterQuals, candidateId }) {
  const { toast, confirm } = useUI();
  const [selected, setSelected] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  const [removingId, setRemovingId] = useState(null);
  const [error, setError] = useState("");

  const available = masterQuals.filter((m) => !quals.some((q) => q.qualification_id === m.qualification_id));

  const handleAdd = async () => {
    if (!selected) return;
    setIsAdding(true);
    setError("");
    try {
      const res = await apiRequest("/api/candidate-qualifications/create/", {
        method: "POST",
        body: { candidate_id: candidateId, qualification_id: Number(selected) },
      });
      setQuals((prev) => [...prev, res.data]);
      setSelected("");
      toast("Qualification added");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsAdding(false);
    }
  };

  const handleRemove = async (q) => {
    const ok = await confirm({
      title: "Remove qualification?",
      message: `"${q.qualification_name}" will be removed from your profile.`,
      confirmLabel: "Remove",
    });
    if (!ok) return;
    setRemovingId(q.cq_id);
    try {
      await apiRequest(`/api/candidate-qualifications/${q.cq_id}/delete/`, { method: "DELETE" });
      setQuals((prev) => prev.filter((x) => x.cq_id !== q.cq_id));
      toast("Qualification removed");
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <div>
      <SectionHeader
        tag="Education"
        title="Your"
        accent="Qualifications."
        subtitle="Degrees, diplomas and certifications."
      />

      <div className="glass mb-6 flex flex-wrap items-center gap-3 rounded-[2rem] p-5 sm:p-6">
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className={`${baseInput} min-w-[12rem] flex-1 sm:flex-none sm:basis-80`}
        >
          <option value="">— Select qualification —</option>
          {available.map((m) => (
            <option key={m.qualification_id} value={m.qualification_id}>{m.qualification_name}</option>
          ))}
        </select>
        <PillButton onClick={handleAdd} disabled={!selected} loading={isAdding} icon="plus">
          {isAdding ? "Adding..." : "Add"}
        </PillButton>
      </div>

      <ErrorBanner message={error} />

      {quals.length === 0 ? (
        <EmptyState
          icon="cap"
          title="No qualifications added yet"
          text="Add your education to strengthen your profile."
        />
      ) : (
        <ul className="space-y-3">
          {quals.map((q, i) => (
            <li
              key={q.cq_id}
              className={`${cardCls} group anim-fade-up flex items-center gap-4 p-4`}
              style={{ animationDelay: `${i * 60}ms` }}
            >
              <IconTile icon="cap" />
              <span className="min-w-0 flex-1 truncate text-sm font-semibold text-neutral-900">
                {q.qualification_name}
              </span>
              <button onClick={() => handleRemove(q)} disabled={removingId === q.cq_id} className={btnDanger}>
                {removingId === q.cq_id ? <Spinner /> : <Icon name="trash" className="h-3.5 w-3.5" />}
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ============================================================
// LANGUAGES SECTION
// ============================================================
function LanguagesSection({ langs, setLangs, masterLangs, candidateId }) {
  const { toast, confirm } = useUI();
  const [selected, setSelected] = useState("");
  const [proficiency, setProficiency] = useState("intermediate");
  const [isAdding, setIsAdding] = useState(false);
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState("");

  const available = masterLangs.filter((m) => !langs.some((l) => l.lang_id === m.lang_id));

  const handleAdd = async () => {
    if (!selected) return;
    setIsAdding(true);
    setError("");
    try {
      const res = await apiRequest("/api/candidate-languages/create/", {
        method: "POST",
        body: { candidate_id: candidateId, lang_id: Number(selected), proficiency_lvl: proficiency },
      });
      setLangs((prev) => [...prev, res.data]);
      setSelected("");
      setProficiency("intermediate");
      toast("Language added");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsAdding(false);
    }
  };

  const handleRemove = async (l) => {
    const ok = await confirm({
      title: "Remove language?",
      message: `"${l.language_name}" will be removed from your profile.`,
      confirmLabel: "Remove",
    });
    if (!ok) return;
    setBusyId(l.cand_lang_id);
    try {
      await apiRequest(`/api/candidate-languages/${l.cand_lang_id}/delete/`, { method: "DELETE" });
      setLangs((prev) => prev.filter((x) => x.cand_lang_id !== l.cand_lang_id));
      toast("Language removed");
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setBusyId(null);
    }
  };

  const handleUpdateProficiency = async (id, newLevel) => {
    setBusyId(id);
    try {
      await apiRequest(`/api/candidate-languages/${id}/update/`, {
        method: "PUT",
        body: { proficiency_lvl: newLevel },
      });
      setLangs((prev) => prev.map((l) => (l.cand_lang_id === id ? { ...l, proficiency_lvl: newLevel } : l)));
      toast("Proficiency updated");
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div>
      <SectionHeader
        tag="Communication"
        title="Spoken"
        accent="Languages."
        subtitle="Languages you speak and how well."
      />

      <div className="glass mb-6 flex flex-wrap items-center gap-3 rounded-[2rem] p-5 sm:p-6">
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className={`${baseInput} min-w-[12rem] flex-1 sm:flex-none sm:basis-64`}
        >
          <option value="">— Select language —</option>
          {available.map((m) => (
            <option key={m.lang_id} value={m.lang_id}>{m.language_name}</option>
          ))}
        </select>
        <select value={proficiency} onChange={(e) => setProficiency(e.target.value)} className={baseInput}>
          {PROFICIENCY.map((p) => (
            <option key={p} value={p}>{capitalize(p)}</option>
          ))}
        </select>
        <PillButton onClick={handleAdd} disabled={!selected} loading={isAdding} icon="plus">
          {isAdding ? "Adding..." : "Add"}
        </PillButton>
      </div>

      <ErrorBanner message={error} />

      {langs.length === 0 ? (
        <EmptyState
          icon="language"
          title="No languages added yet"
          text="Add the languages you can work in."
        />
      ) : (
        <ul className="space-y-3">
          {langs.map((l, i) => {
            const level = PROFICIENCY.indexOf(l.proficiency_lvl) + 1;
            return (
              <li
                key={l.cand_lang_id}
                className={`${cardCls} group anim-fade-up flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between`}
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <div className="flex min-w-0 items-center gap-4">
                  <IconTile icon="language" />
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-neutral-900">{l.language_name}</p>
                    <div className="mt-2 flex items-center gap-1" aria-label={`Proficiency: ${l.proficiency_lvl}`}>
                      {PROFICIENCY.map((p, idx) => (
                        <span
                          key={p}
                          className={`h-1.5 w-8 rounded-full transition-colors duration-500 ${
                            idx < level ? "bg-black" : "bg-black/10"
                          }`}
                        />
                      ))}
                      <span className="ml-2 text-[11px] text-neutral-500">{capitalize(l.proficiency_lvl)}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={l.proficiency_lvl}
                    disabled={busyId === l.cand_lang_id}
                    onChange={(e) => handleUpdateProficiency(l.cand_lang_id, e.target.value)}
                    className="rounded-full border border-black/10 bg-white/70 px-3.5 py-1.5 text-xs font-medium text-neutral-800 outline-none transition focus:border-black/30 disabled:opacity-50 [&>option]:bg-white"
                  >
                    {PROFICIENCY.map((p) => (
                      <option key={p} value={p}>{capitalize(p)}</option>
                    ))}
                  </select>
                  <button onClick={() => handleRemove(l)} disabled={busyId === l.cand_lang_id} className={btnDanger}>
                    <Icon name="trash" className="h-3.5 w-3.5" /> Remove
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

// ============================================================
// APPLICATIONS SECTION
// ============================================================
function ApplicationsSection({ applications, jobsMap }) {
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");

  const jobTitle = useCallback(
    (a) => jobsMap[a.job_id]?.job_title || `Job #${a.job_id}`,
    [jobsMap]
  );

  const sorted = useMemo(
    () => [...applications].sort((a, b) => new Date(b.applied_at) - new Date(a.applied_at)),
    [applications]
  );

  const filtered = sorted.filter(
    (a) =>
      (filter === "all" || a.application_status === filter) &&
      jobTitle(a).toLowerCase().includes(query.trim().toLowerCase())
  );

  const tabCount = (k) =>
    k === "all" ? applications.length : applications.filter((a) => a.application_status === k).length;

  return (
    <div>
      <SectionHeader
        tag="Job tracker"
        title="My"
        accent="Applications."
        subtitle={
          applications.length
            ? `${applications.length} application${applications.length > 1 ? "s" : ""} in total`
            : "Track every job you've applied to."
        }
      />

      {applications.length === 0 ? (
        <EmptyState
          icon="send"
          title="You haven't applied to any jobs yet"
          text="Once you apply, you can follow each application's progress here."
        />
      ) : (
        <>
          <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="no-scrollbar flex gap-2 overflow-x-auto">
              {["all", ...STATUS_ORDER].map((k) => {
                const active = filter === k;
                return (
                  <button
                    key={k}
                    onClick={() => setFilter(k)}
                    className={`inline-flex shrink-0 items-center gap-2 rounded-full px-4 py-2 text-xs font-semibold transition active:scale-95 ${
                      active
                        ? "bg-black text-white shadow-[0_8px_24px_-8px_rgba(0,0,0,0.5)]"
                        : "glass text-neutral-600 hover:text-black"
                    }`}
                  >
                    {k === "all" ? "All" : STATUS_STYLES[k].label}
                    <span
                      className={`rounded-full px-1.5 text-[10px] ${
                        active ? "bg-white/20" : "bg-black/5"
                      }`}
                    >
                      {tabCount(k)}
                    </span>
                  </button>
                );
              })}
            </div>

            <div className="relative lg:w-64">
              <Icon
                name="search"
                className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400"
              />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search jobs..."
                className={`${inputCls} !rounded-full pl-11`}
              />
            </div>
          </div>

          {filtered.length === 0 ? (
            <EmptyState
              icon="search"
              title="No matching applications"
              text="Try a different status filter or search term."
            />
          ) : (
            <ul className="space-y-3">
              {filtered.map((a, i) => {
                const st = STATUS_STYLES[a.application_status];
                return (
                  <li
                    key={a.application_id}
                    className={`${cardCls} group anim-fade-up p-5`}
                    style={{ animationDelay: `${Math.min(i, 10) * 55}ms` }}
                  >
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="flex min-w-0 items-center gap-4">
                        <IconTile icon="briefcase" />
                        <div className="min-w-0">
                          <p className="truncate text-base font-bold tracking-tight text-neutral-950">
                            {jobTitle(a)}
                          </p>
                          <p className="mt-0.5 flex items-center gap-1.5 text-xs text-neutral-500">
                            <Icon name="calendar" className="h-3.5 w-3.5" />
                            Applied on {formatDate(a.applied_at)}
                          </p>
                        </div>
                      </div>
                      <span
                        className={`inline-flex w-fit items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[11px] font-semibold ${
                          st?.badge || "bg-black/5 text-neutral-600"
                        }`}
                      >
                        <span className={`h-1.5 w-1.5 rounded-full ${st?.dot || "bg-neutral-400"}`} />
                        {st?.label || capitalize(a.application_status) || "Unknown"}
                      </span>
                    </div>
                    {st && <StatusTracker status={a.application_status} />}
                  </li>
                );
              })}
            </ul>
          )}
        </>
      )}
    </div>
  );
}

function StatusTracker({ status }) {
  const rejected = status === "rejected";
  const labels = rejected ? ["Applied", "Rejected"] : ["Applied", "Shortlisted", "Hired"];
  const current = rejected ? 1 : labels.map((l) => l.toLowerCase()).indexOf(status);

  return (
    <div className="mt-5 flex items-center gap-2 border-t border-black/5 pt-4">
      {labels.map((label, i) => {
        const done = i <= current;
        const isRejectedStep = rejected && i === current;
        return (
          <div key={label} className="flex flex-1 items-center gap-2 last:flex-none">
            <div className="flex items-center gap-2">
              <span
                className={`flex h-5 w-5 items-center justify-center rounded-full transition-colors duration-500 ${
                  isRejectedStep
                    ? "bg-red-500 text-white"
                    : done
                    ? "bg-black text-white"
                    : "bg-black/10 text-transparent"
                }`}
              >
                <Icon name={isRejectedStep ? "x" : "check"} className="h-3 w-3" strokeWidth={3.2} />
              </span>
              <span className={`text-[11px] font-semibold ${done ? "text-neutral-900" : "text-neutral-400"}`}>
                {label}
              </span>
            </div>
            {i < labels.length - 1 && (
              <span
                className={`h-px flex-1 transition-colors duration-500 ${
                  i < current ? "bg-black/60" : "bg-black/10"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ============================================================
// SHARED UI
// ============================================================
function Tag({ children }) {
  return (
    <span className="inline-flex items-center rounded-full border border-black/10 bg-white/50 px-3.5 py-1 text-[10px] font-medium uppercase tracking-[0.22em] text-neutral-500 backdrop-blur">
      {children}
    </span>
  );
}

function ArrowLine() {
  return (
    <svg width="38" height="8" viewBox="0 0 38 8" fill="none" aria-hidden="true">
      <path d="M0 4H34" stroke="currentColor" strokeWidth="1.2" />
      <path d="M31 1L37 4L31 7Z" fill="currentColor" />
    </svg>
  );
}

function SectionHeader({ tag, title, accent, subtitle, action }) {
  return (
    <div className="mb-10 flex flex-wrap items-end justify-between gap-6">
      <div className="min-w-0">
        <Tag>{tag}</Tag>
        <h2 className="mt-6 break-words text-4xl font-bold uppercase leading-[0.95] tracking-tight text-neutral-950 sm:text-5xl lg:text-6xl">
          {title}
          <br />
          <span className="text-neutral-400">{accent}</span>
        </h2>
        <div className="mt-6 text-neutral-900">
          <ArrowLine />
        </div>
        {subtitle && <p className="mt-4 max-w-md text-sm leading-relaxed text-neutral-500">{subtitle}</p>}
      </div>
      {action || null}
    </div>
  );
}

function PillButton({
  children,
  icon = "arrowUpRight",
  onClick,
  type = "button",
  disabled = false,
  loading = false,
  variant = "dark",
  className = "",
}) {
  const dark = variant === "dark";
  const hasIcon = icon !== null;
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`group inline-flex items-center rounded-full text-sm font-semibold transition-all duration-200 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-50 ${
        hasIcon ? "gap-3 py-1.5 pl-5 pr-1.5" : "px-5 py-2.5"
      } ${
        dark
          ? "bg-black text-white shadow-[0_10px_28px_-10px_rgba(0,0,0,0.55)] hover:bg-neutral-800"
          : "border border-black/10 bg-white/70 text-neutral-900 hover:bg-white"
      } ${className}`}
    >
      <span>{children}</span>
      {hasIcon && (
        <span
          className={`flex h-8 w-8 items-center justify-center rounded-full transition-transform duration-200 group-hover:scale-110 ${
            dark ? "bg-white text-black" : "bg-black text-white"
          }`}
        >
          {loading ? <Spinner /> : <Icon name={icon} className="h-3.5 w-3.5" strokeWidth={2} />}
        </span>
      )}
    </button>
  );
}

function IconTile({ icon, size = "md" }) {
  const dim = size === "sm" ? "h-8 w-8 rounded-xl" : "h-12 w-12 rounded-2xl";
  const ic = size === "sm" ? "h-4 w-4" : "h-5 w-5";
  return (
    <span
      className={`flex shrink-0 items-center justify-center bg-white/90 text-neutral-800 shadow-[0_8px_20px_-8px_rgba(0,0,0,0.22)] ring-1 ring-black/5 transition duration-200 group-hover:bg-black group-hover:text-white ${dim}`}
    >
      <Icon name={icon} className={ic} />
    </span>
  );
}

function InfoField({ label, value, icon, fullWidth = false }) {
  return (
    <div className={`flex items-start gap-4 ${fullWidth ? "sm:col-span-2" : ""}`}>
      {icon && (
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white/90 text-neutral-700 shadow-[0_6px_16px_-6px_rgba(0,0,0,0.2)] ring-1 ring-black/5">
          <Icon name={icon} className="h-4 w-4" />
        </span>
      )}
      <div className="min-w-0">
        <p className="mb-1 text-[10px] font-medium uppercase tracking-[0.2em] text-neutral-500">{label}</p>
        <p className="break-words text-sm font-semibold text-neutral-900">{value || "—"}</p>
      </div>
    </div>
  );
}

function FieldLabel({ children }) {
  return (
    <label className="mb-2 block text-[10px] font-medium uppercase tracking-[0.2em] text-neutral-500">
      {children}
    </label>
  );
}

function ErrorBanner({ message }) {
  if (!message) return null;
  return (
    <p className="anim-fade-in mb-5 flex items-start gap-2.5 rounded-2xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-600">
      <Icon name="alert" className="mt-0.5 h-4 w-4 shrink-0" />
      <span>{message}</span>
    </p>
  );
}

function EmptyState({ icon, title, text, action }) {
  return (
    <div className="anim-fade-in flex flex-col items-center rounded-[2rem] border-2 border-dashed border-black/10 bg-white/30 px-6 py-14 text-center">
      <span className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/90 text-neutral-500 shadow-[0_8px_20px_-8px_rgba(0,0,0,0.2)] ring-1 ring-black/5">
        <Icon name={icon} className="h-6 w-6" />
      </span>
      <p className="text-base font-bold uppercase tracking-tight text-neutral-900">{title}</p>
      {text && <p className="mt-1.5 max-w-xs text-sm text-neutral-500">{text}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}

function Spinner() {
  return (
    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
  );
}