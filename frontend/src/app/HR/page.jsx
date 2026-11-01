"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";

// ============================================================
// CONFIG
// ============================================================
const API_BASE_URL = "http://localhost:8000";

const SECTIONS = [
  { id: "overview", label: "Overview", num: "01" },
  { id: "profile", label: "Profile", num: "02" },
  { id: "jobs", label: "My Jobs", num: "03" },
  { id: "applicants", label: "Applicants", num: "04" },
  { id: "interviews", label: "Interviews", num: "05" },
  { id: "decisions", label: "Decisions", num: "06" },
];

const SECTION_TITLES = {
  overview: "Overview.",
  profile: "Profile.",
  jobs: "Your Jobs.",
  applicants: "Applicants.",
  interviews: "Interviews.",
  decisions: "Decisions.",
};

const APP_STATUS_COLORS = {
  applied: "bg-blue-50 text-blue-700 ring-1 ring-blue-200",
  shortlisted: "bg-amber-50 text-amber-700 ring-1 ring-amber-200",
  rejected: "bg-red-50 text-red-700 ring-1 ring-red-200",
  hired: "bg-green-50 text-green-700 ring-1 ring-green-200",
};

const INTERVIEW_STATUS_COLORS = {
  pending: "bg-blue-50 text-blue-700 ring-1 ring-blue-200",
  in_progress: "bg-amber-50 text-amber-700 ring-1 ring-amber-200",
  completed: "bg-green-50 text-green-700 ring-1 ring-green-200",
  cancelled: "bg-red-50 text-red-700 ring-1 ring-red-200",
};

const SELECTION_COLORS = {
  selected: "bg-green-50 text-green-700 ring-1 ring-green-200",
  shortlisted: "bg-amber-50 text-amber-700 ring-1 ring-amber-200",
  rejected: "bg-red-50 text-red-700 ring-1 ring-red-200",
  on_hold: "bg-neutral-100 text-neutral-700 ring-1 ring-neutral-200",
};

// ============================================================
// ICONS
// ============================================================
const Icon = ({ name, size = 18 }) => {
  const common = {
    width: size, height: size, viewBox: "0 0 24 24",
    fill: "none", stroke: "currentColor", strokeWidth: 1.8,
    strokeLinecap: "round", strokeLinejoin: "round",
  };
  const paths = {
    overview: <><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></>,
    jobs: <><rect x="2" y="7" width="20" height="14" rx="2" /><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" /></>,
    users: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></>,
    calendar: <><rect x="3" y="4" width="18" height="18" rx="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" /></>,
    check: <><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></>,
    user: <><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></>,
    clock: <><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></>,
    logout: <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></>,
    plus: <><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></>,
    arrow: <><line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" /></>,
  };
  return <svg {...common}>{paths[name]}</svg>;
};

// ============================================================
// API
// ============================================================
async function apiRequest(path, { method = "GET", body } = {}) {
  const url = `${API_BASE_URL}${path}`;
  const options = { method, credentials: "include" };
  if (body !== undefined) {
    options.headers = { "Content-Type": "application/json" };
    options.body = JSON.stringify(body);
  }
  let response;
  try { response = await fetch(url, options); }
  catch { throw new Error("Server se connect nahi ho saka"); }
  let payload = null;
  try { payload = await response.json(); } catch {}
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
  } catch { return null; }
}
function getInitials(name) {
  if (!name) return "U";
  return name.trim().split(/\s+/).map((w) => w[0]).slice(0, 2).join("").toUpperCase();
}
function formatDate(d) {
  if (!d) return "—";
  try { return new Date(d).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }); }
  catch { return d; }
}
function formatDateTime(d) {
  if (!d) return "—";
  try { return new Date(d).toLocaleString("en-GB", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }); }
  catch { return d; }
}

// ============================================================
// MAIN
// ============================================================
export default function HRDashboard() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [activeSection, setActiveSection] = useState("overview");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const [hrProfile, setHrProfile] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [jobSkills, setJobSkills] = useState([]);
  const [jobQuals, setJobQuals] = useState([]);
  const [applications, setApplications] = useState([]);
  const [matchings, setMatchings] = useState([]);
  const [interviews, setInterviews] = useState([]);
  const [hiringResults, setHiringResults] = useState([]);
  const [candidateProfiles, setCandidateProfiles] = useState([]);
  const [resumes, setResumes] = useState([]);
  const [masterSkills, setMasterSkills] = useState([]);
  const [masterQuals, setMasterQuals] = useState([]);

  const loadAll = useCallback(async (hrId) => {
    const safe = (p) => p.catch(() => ({ data: [] }));
    const [p, j, js, jq, a, m, i, h, c, r, ms, mq] = await Promise.all([
      apiRequest(`/api/hr-profiles/${hrId}/`).catch(() => null),
      safe(apiRequest("/api/jobs/")),
      safe(apiRequest("/api/job-skills/")),
      safe(apiRequest("/api/job-qualifications/")),
      safe(apiRequest("/api/applications/")),
      safe(apiRequest("/api/resume-matchings/")),
      safe(apiRequest("/api/ai-interviews/")),
      safe(apiRequest("/api/hiring-results/")),
      safe(apiRequest("/api/candidate-profiles/")),
      safe(apiRequest("/api/resumes/")),
      safe(apiRequest("/api/skills/")),
      safe(apiRequest("/api/qualifications/")),
    ]);
    setHrProfile(p?.data || null);
    const myJobs = (j.data || []).filter((x) => x.hr_id === hrId);
    setJobs(myJobs);
    const myJobIds = new Set(myJobs.map((x) => x.job_id));
    setJobSkills((js.data || []).filter((x) => myJobIds.has(x.job_id)));
    setJobQuals((jq.data || []).filter((x) => myJobIds.has(x.job_id)));
    const myApps = (a.data || []).filter((x) => myJobIds.has(x.job_id));
    setApplications(myApps);
    const myAppIds = new Set(myApps.map((x) => x.application_id));
    setMatchings((m.data || []).filter((x) => myAppIds.has(x.application_id)));
    setInterviews((i.data || []).filter((x) => myAppIds.has(x.application_id)));
    setHiringResults((h.data || []).filter((x) => myAppIds.has(x.application_id)));
    setCandidateProfiles(c.data || []);
    setResumes(r.data || []);
    setMasterSkills(ms.data || []);
    setMasterQuals(mq.data || []);
  }, []);

  useEffect(() => {
    const storedUser = getStoredUser();
    if (!storedUser) { router.push("/Auth/Login"); return; }
    if (storedUser.role !== "hr") { setError("This dashboard is only for HR users."); setIsLoading(false); return; }
    setUser(storedUser);
    loadAll(storedUser.hr_id).catch((e) => setError(e.message)).finally(() => setIsLoading(false));
  }, [router, loadAll]);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try { await fetch(`${API_BASE_URL}/api/auth/logout/`, { method: "POST", credentials: "include" }); } catch {}
    localStorage.removeItem("auth_user");
    router.push("/");
    router.refresh();
  };

  // Derived
  const appsByJob = useMemo(() => { const m = {}; applications.forEach((a) => { (m[a.job_id] ||= []).push(a); }); return m; }, [applications]);
  const matchingByApp = useMemo(() => { const m = {}; matchings.forEach((x) => { m[x.application_id] = x; }); return m; }, [matchings]);
  const interviewByApp = useMemo(() => { const m = {}; interviews.forEach((x) => { m[x.application_id] = x; }); return m; }, [interviews]);
  const candidateById = useMemo(() => { const m = {}; candidateProfiles.forEach((x) => { m[x.candidate_id] = x; }); return m; }, [candidateProfiles]);
  const resumeById = useMemo(() => { const m = {}; resumes.forEach((x) => { m[x.resume_id] = x; }); return m; }, [resumes]);
  const jobsById = useMemo(() => { const m = {}; jobs.forEach((j) => { m[j.job_id] = j; }); return m; }, [jobs]);

  if (isLoading) {
    return <div className="flex min-h-screen items-center justify-center bg-[#f7f6f3] text-sm text-neutral-500">Loading HR workspace…</div>;
  }
  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f7f6f3] px-4">
        <div className="max-w-md rounded-3xl bg-white p-8 text-center ring-1 ring-neutral-200">
          <p className="text-[10px] font-semibold uppercase tracking-[0.25em] text-red-500">Error</p>
          <p className="mt-3 text-sm text-neutral-700">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f7f6f3] pt-32 pb-20 text-neutral-900">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        {/* HERO */}
        <div className="mb-10 flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.25em] text-neutral-500">
              HR Workspace
            </p>
            <h1 className="mt-3 text-5xl font-bold tracking-tight text-black sm:text-6xl">
              {SECTION_TITLES[activeSection]}
            </h1>
            <p className="mt-3 max-w-md text-sm text-neutral-500">
              Manage your job postings, review applicants, run interviews, and make final hiring decisions.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-xs font-semibold text-black">{hrProfile?.full_name || user?.full_name}</p>
              <p className="text-[11px] text-neutral-500">{user?.email}</p>
            </div>
            <div className="flex h-11 w-11 items-center justify-center rounded-full bg-black text-sm font-bold text-white">
              {getInitials(hrProfile?.full_name || user?.full_name)}
            </div>
            <button
              onClick={handleLogout}
              disabled={isLoggingOut}
              className="flex items-center gap-2 rounded-full border border-neutral-300 bg-white px-5 py-2.5 text-xs font-semibold text-black transition hover:bg-neutral-100 disabled:opacity-60"
            >
              <Icon name="logout" size={14} />
              {isLoggingOut ? "Logging out…" : "Logout"}
            </button>
          </div>
        </div>

        {/* MAIN GRID */}
        <div className="flex flex-col gap-6 lg:flex-row">
          {/* SIDEBAR */}
          <aside className="w-full flex-shrink-0 lg:w-64">
            <div className="rounded-3xl bg-white p-3 ring-1 ring-neutral-200">
              <nav className="flex flex-col gap-1">
                {SECTIONS.map((s) => {
                  const active = activeSection === s.id;
                  return (
                    <button
                      key={s.id}
                      onClick={() => setActiveSection(s.id)}
                      className={`flex items-center gap-3 rounded-full px-4 py-3 text-left text-[13px] font-medium transition ${
                        active
                          ? "bg-black text-white"
                          : "text-neutral-700 hover:bg-neutral-100"
                      }`}
                    >
                      <span className={`font-mono text-[10px] ${active ? "text-white/60" : "text-neutral-400"}`}>
                        {s.num}
                      </span>
                      {s.label}
                    </button>
                  );
                })}
              </nav>
            </div>
          </aside>

          {/* CONTENT */}
          <main className="min-w-0 flex-1">
            {activeSection === "overview" && (
              <Overview
                jobs={jobs} applications={applications} interviews={interviews}
                hiringResults={hiringResults} candidateById={candidateById} matchingByApp={matchingByApp}
              />
            )}
            {activeSection === "profile" && (
              <ProfileCard profile={hrProfile} hrId={user.hr_id} onUpdate={setHrProfile} />
            )}
            {activeSection === "jobs" && (
              <JobsPanel
                jobs={jobs} setJobs={setJobs}
                jobSkills={jobSkills} setJobSkills={setJobSkills}
                jobQuals={jobQuals} setJobQuals={setJobQuals}
                masterSkills={masterSkills} masterQuals={masterQuals}
                hrId={user.hr_id} appsByJob={appsByJob}
              />
            )}
            {activeSection === "applicants" && (
              <ApplicantsPanel
                jobs={jobs} appsByJob={appsByJob} candidateById={candidateById}
                matchingByApp={matchingByApp} resumeById={resumeById}
                applications={applications} setApplications={setApplications}
                interviews={interviews} setInterviews={setInterviews}
              />
            )}
            {activeSection === "interviews" && (
              <InterviewsPanel
                interviews={interviews} setInterviews={setInterviews}
                applications={applications} candidateById={candidateById} jobsById={jobsById}
              />
            )}
            {activeSection === "decisions" && (
              <DecisionsPanel
                applications={applications} candidateById={candidateById}
                jobsById={jobsById} matchingByApp={matchingByApp}
                interviewByApp={interviewByApp} hiringResults={hiringResults}
                setHiringResults={setHiringResults}
              />
            )}
          </main>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// OVERVIEW
// ============================================================
function Overview({ jobs, applications, interviews, hiringResults, candidateById, matchingByApp }) {
  const activeJobs = jobs.filter((j) => j.due_date && new Date(j.due_date) >= new Date()).length;
  const pending = applications.filter((a) => a.application_status === "applied").length;
  const shortlisted = applications.filter((a) => a.application_status === "shortlisted").length;
  const hired = applications.filter((a) => a.application_status === "hired").length;
  const upcomingInterviews = interviews.filter((i) => i.interview_status === "pending").length;

  const recent = [...applications]
    .sort((a, b) => new Date(b.applied_at) - new Date(a.applied_at))
    .slice(0, 5);

  return (
    <div className="space-y-6">
      {/* FEATURE CARDS (stats) */}
      <div className="rounded-3xl bg-white p-4 ring-1 ring-neutral-200 sm:p-5">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <FeatureCard icon="jobs" value={jobs.length} label="Total Jobs" sub="All postings" />
          <FeatureCard icon="clock" value={activeJobs} label="Active" sub="Within due date" />
          <FeatureCard icon="users" value={applications.length} label="Applications" sub="All received" />
          <FeatureCard icon="check" value={hired} label="Hired" sub="Confirmed" />
        </div>
        <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-4">
          <FeatureCard icon="user" value={pending} label="Pending Review" sub="Need attention" />
          <FeatureCard icon="check" value={shortlisted} label="Shortlisted" sub="In pipeline" />
          <FeatureCard icon="calendar" value={upcomingInterviews} label="Interviews" sub="Upcoming" />
          <FeatureCard icon="overview" value={hiringResults.length} label="Decisions" sub="Finalized" />
        </div>
      </div>

      {/* RECENT */}
      <div className="rounded-3xl bg-white p-6 ring-1 ring-neutral-200">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-neutral-500">Latest</p>
            <h3 className="mt-1 text-lg font-semibold text-black">Recent Applications</h3>
          </div>
        </div>
        {recent.length === 0 ? (
          <p className="text-sm text-neutral-500">No applications yet.</p>
        ) : (
          <ul className="divide-y divide-neutral-100">
            {recent.map((a) => {
              const cand = candidateById[a.candidate_id];
              const matching = matchingByApp[a.application_id];
              return (
                <li key={a.application_id} className="flex items-center justify-between gap-4 py-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-black">
                      {cand?.full_name || `Candidate #${a.candidate_id}`}
                    </p>
                    <p className="truncate text-[11px] text-neutral-500">
                      Applied {formatDate(a.applied_at)}
                    </p>
                  </div>
                  <div className="flex flex-shrink-0 items-center gap-3">
                    {matching && (
                      <span className="text-xs font-semibold text-black">
                        {Number(matching.total_score).toFixed(0)}%
                      </span>
                    )}
                    <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold capitalize ${APP_STATUS_COLORS[a.application_status]}`}>
                      {a.application_status}
                    </span>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

function FeatureCard({ icon, value, label, sub }) {
  return (
    <div className="rounded-2xl bg-[#faf9f6] p-4 ring-1 ring-neutral-200">
      <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-white text-black ring-1 ring-neutral-200">
        <Icon name={icon} size={16} />
      </div>
      <p className="text-2xl font-bold tracking-tight text-black">{value}</p>
      <p className="mt-0.5 text-[11px] font-semibold text-neutral-800">{label}</p>
      <p className="text-[10px] text-neutral-500">{sub}</p>
    </div>
  );
}

// ============================================================
// PROFILE
// ============================================================
function ProfileCard({ profile, hrId, onUpdate }) {
  const [isEditing, setIsEditing] = useState(false);
  const [form, setForm] = useState({ department: "", designation: "" });
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");

  const start = () => {
    setForm({ department: profile?.department || "", designation: profile?.designation || "" });
    setError(""); setIsEditing(true);
  };
  const save = async () => {
    setIsSaving(true); setError("");
    try {
      await apiRequest(`/api/hr-profiles/${hrId}/update/`, { method: "PUT", body: form });
      onUpdate((prev) => ({ ...prev, ...form }));
      setIsEditing(false);
    } catch (e) { setError(e.message); }
    finally { setIsSaving(false); }
  };

  return (
    <div className="rounded-3xl bg-white p-6 ring-1 ring-neutral-200 sm:p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-neutral-500">Personal</p>
          <h3 className="mt-1 text-lg font-semibold text-black">HR Profile</h3>
        </div>
        {!isEditing && (
          <button onClick={start} className="rounded-full border border-neutral-300 bg-white px-4 py-2 text-xs font-semibold text-black hover:bg-neutral-100">
            Edit
          </button>
        )}
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        <Field label="Full Name" value={profile?.full_name} />
        <Field label="Email" value={profile?.email} />

        {isEditing ? (
          <>
            <div>
              <Label>Department</Label>
              <Input value={form.department} onChange={(v) => setForm({ ...form, department: v })} />
            </div>
            <div>
              <Label>Designation</Label>
              <Input value={form.designation} onChange={(v) => setForm({ ...form, designation: v })} />
            </div>
          </>
        ) : (
          <>
            <Field label="Department" value={profile?.department} />
            <Field label="Designation" value={profile?.designation} />
          </>
        )}
      </div>

      {isEditing && (
        <div className="mt-6 flex gap-3 border-t border-neutral-100 pt-5">
          <button onClick={save} disabled={isSaving} className="rounded-full bg-black px-5 py-2.5 text-xs font-semibold text-white hover:bg-neutral-800 disabled:opacity-60">
            {isSaving ? "Saving…" : "Save Changes"}
          </button>
          <button onClick={() => setIsEditing(false)} disabled={isSaving} className="rounded-full border border-neutral-300 bg-white px-5 py-2.5 text-xs font-semibold text-black hover:bg-neutral-100 disabled:opacity-60">
            Cancel
          </button>
        </div>
      )}
      {error && <p className="mt-3 rounded-xl bg-red-50 px-3 py-2 text-xs text-red-700 ring-1 ring-red-200">{error}</p>}
    </div>
  );
}

// ============================================================
// JOBS
// ============================================================
function JobsPanel({ jobs, setJobs, jobSkills, setJobSkills, jobQuals, setJobQuals, masterSkills, masterQuals, hrId, appsByJob }) {
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ job_title: "", job_description: "", required_exp: 0, minimum_score: 0, due_date: "", skill_ids: [], qual_ids: [] });
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");

  const reset = () => {
    setForm({ job_title: "", job_description: "", required_exp: 0, minimum_score: 0, due_date: "", skill_ids: [], qual_ids: [] });
    setEditing(null); setShowForm(false); setError("");
  };
  const openEdit = (job) => {
    setForm({
      job_title: job.job_title, job_description: job.job_description,
      required_exp: Number(job.required_exp), minimum_score: Number(job.minimum_score),
      due_date: job.due_date,
      skill_ids: jobSkills.filter((js) => js.job_id === job.job_id).map((js) => js.skill_id),
      qual_ids: jobQuals.filter((jq) => jq.job_id === job.job_id).map((jq) => jq.qualification_id),
    });
    setEditing(job); setShowForm(true);
  };

  const save = async (e) => {
    e.preventDefault(); setIsSaving(true); setError("");
    try {
      let jobId;
      if (editing) {
        await apiRequest(`/api/jobs/${editing.job_id}/update/`, { method: "PUT", body: {
          job_title: form.job_title, job_description: form.job_description,
          required_exp: form.required_exp, minimum_score: form.minimum_score, due_date: form.due_date,
        }});
        jobId = editing.job_id;
        // sync skills
        const curS = jobSkills.filter((x) => x.job_id === jobId);
        for (const cs of curS) if (!form.skill_ids.includes(cs.skill_id))
          await apiRequest(`/api/job-skills/${cs.job_skill_id}/delete/`, { method: "DELETE" }).catch(() => {});
        const curIds = new Set(curS.map((x) => x.skill_id));
        for (const sid of form.skill_ids) if (!curIds.has(sid))
          await apiRequest("/api/job-skills/create/", { method: "POST", body: { job_id: jobId, skill_id: sid } }).catch(() => {});
        // sync quals
        const curQ = jobQuals.filter((x) => x.job_id === jobId);
        for (const cq of curQ) if (!form.qual_ids.includes(cq.qualification_id))
          await apiRequest(`/api/job-qualifications/${cq.job_qualification_id}/delete/`, { method: "DELETE" }).catch(() => {});
        const curQIds = new Set(curQ.map((x) => x.qualification_id));
        for (const qid of form.qual_ids) if (!curQIds.has(qid))
          await apiRequest("/api/job-qualifications/create/", { method: "POST", body: { job_id: jobId, qualification_id: qid } }).catch(() => {});
        setJobs((prev) => prev.map((j) => j.job_id === jobId ? { ...j, ...form } : j));
      } else {
        const res = await apiRequest("/api/jobs/create/", { method: "POST", body: {
          hr_id: hrId, job_title: form.job_title, job_description: form.job_description,
          required_exp: form.required_exp, minimum_score: form.minimum_score, due_date: form.due_date,
        }});
        jobId = res.data.job_id;
        for (const sid of form.skill_ids) {
          const r = await apiRequest("/api/job-skills/create/", { method: "POST", body: { job_id: jobId, skill_id: sid } });
          setJobSkills((prev) => [...prev, r.data]);
        }
        for (const qid of form.qual_ids) {
          const r = await apiRequest("/api/job-qualifications/create/", { method: "POST", body: { job_id: jobId, qualification_id: qid } });
          setJobQuals((prev) => [...prev, r.data]);
        }
        setJobs((prev) => [res.data, ...prev]);
      }
      const [js, jq] = await Promise.all([apiRequest("/api/job-skills/").catch(() => ({ data: [] })), apiRequest("/api/job-qualifications/").catch(() => ({ data: [] }))]);
      const ids = new Set([...jobs.map((j) => j.job_id), jobId]);
      setJobSkills((js.data || []).filter((x) => ids.has(x.job_id)));
      setJobQuals((jq.data || []).filter((x) => ids.has(x.job_id)));
      reset();
    } catch (err) { setError(err.message); }
    finally { setIsSaving(false); }
  };

  const remove = async (id) => {
    if (!confirm("Delete this job? All applications will be removed.")) return;
    try {
      await apiRequest(`/api/jobs/${id}/delete/`, { method: "DELETE" });
      setJobs((prev) => prev.filter((j) => j.job_id !== id));
    } catch (err) { alert(err.message); }
  };

  const toggle = (arr, id) => arr.includes(id) ? arr.filter((x) => x !== id) : [...arr, id];

  return (
    <div className="space-y-6">
      {!showForm && (
        <div className="flex items-center justify-between rounded-3xl bg-white px-6 py-5 ring-1 ring-neutral-200">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-neutral-500">Manage</p>
            <h3 className="mt-1 text-lg font-semibold text-black">Job Postings</h3>
          </div>
          <button
            onClick={() => { reset(); setShowForm(true); }}
            className="flex items-center gap-2 rounded-full bg-black px-5 py-2.5 text-xs font-semibold text-white hover:bg-neutral-800"
          >
            <Icon name="plus" size={14} />
            New Job
          </button>
        </div>
      )}

      {showForm && (
        <form onSubmit={save} className="space-y-4 rounded-3xl bg-white p-6 ring-1 ring-neutral-200 sm:p-8">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-black">{editing ? "Edit Job" : "Create Job"}</h3>
            <button type="button" onClick={reset} className="text-xs font-medium text-neutral-500 hover:text-black">Cancel</button>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <Label>Job Title</Label>
              <Input value={form.job_title} onChange={(v) => setForm({ ...form, job_title: v })} required />
            </div>
            <div className="sm:col-span-2">
              <Label>Description</Label>
              <textarea
                required rows={4} value={form.job_description}
                onChange={(e) => setForm({ ...form, job_description: e.target.value })}
                className="w-full rounded-xl border border-neutral-200 bg-[#faf9f6] px-3.5 py-2.5 text-sm text-black outline-none focus:border-black"
              />
            </div>
            <div>
              <Label>Required Experience (years)</Label>
              <Input type="number" step="0.5" min="0" value={form.required_exp} onChange={(v) => setForm({ ...form, required_exp: Number(v) })} />
            </div>
            <div>
              <Label>Minimum Score (0–100)</Label>
              <Input type="number" min="0" max="100" value={form.minimum_score} onChange={(v) => setForm({ ...form, minimum_score: Number(v) })} />
            </div>
            <div className="sm:col-span-2">
              <Label>Due Date</Label>
              <Input type="date" required value={form.due_date} onChange={(v) => setForm({ ...form, due_date: v })} />
            </div>

            <div className="sm:col-span-2">
              <Label>Required Skills</Label>
              <div className="flex flex-wrap gap-2">
                {masterSkills.map((s) => (
                  <Chip key={s.skill_id} active={form.skill_ids.includes(s.skill_id)} onClick={() => setForm({ ...form, skill_ids: toggle(form.skill_ids, s.skill_id) })}>
                    {s.skill_name}
                  </Chip>
                ))}
              </div>
            </div>
            <div className="sm:col-span-2">
              <Label>Required Qualifications</Label>
              <div className="flex flex-wrap gap-2">
                {masterQuals.map((q) => (
                  <Chip key={q.qualification_id} active={form.qual_ids.includes(q.qualification_id)} onClick={() => setForm({ ...form, qual_ids: toggle(form.qual_ids, q.qualification_id) })}>
                    {q.qualification_name}
                  </Chip>
                ))}
              </div>
            </div>
          </div>

          {error && <p className="rounded-xl bg-red-50 px-3 py-2 text-xs text-red-700 ring-1 ring-red-200">{error}</p>}

          <div className="flex gap-3 border-t border-neutral-100 pt-4">
            <button type="submit" disabled={isSaving} className="rounded-full bg-black px-5 py-2.5 text-xs font-semibold text-white hover:bg-neutral-800 disabled:opacity-60">
              {isSaving ? "Saving…" : editing ? "Update Job" : "Create Job"}
            </button>
            <button type="button" onClick={reset} className="rounded-full border border-neutral-300 bg-white px-5 py-2.5 text-xs font-semibold text-black hover:bg-neutral-100">
              Cancel
            </button>
          </div>
        </form>
      )}

      {jobs.length === 0 ? (
        <div className="rounded-3xl bg-white p-10 text-center ring-1 ring-neutral-200">
          <p className="text-sm text-neutral-500">No jobs created yet.</p>
        </div>
      ) : (
        <ul className="space-y-3">
          {jobs.map((job) => {
            const count = appsByJob[job.job_id]?.length || 0;
            const overdue = job.due_date && new Date(job.due_date) < new Date();
            return (
              <li key={job.job_id} className="rounded-3xl bg-white p-6 ring-1 ring-neutral-200">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h4 className="text-base font-semibold text-black">{job.job_title}</h4>
                      {overdue && <span className="rounded-full bg-red-50 px-2 py-0.5 text-[10px] font-semibold text-red-700 ring-1 ring-red-200">Overdue</span>}
                    </div>
                    <p className="mt-1 line-clamp-2 text-sm text-neutral-600">{job.job_description}</p>
                    <div className="mt-3 flex flex-wrap gap-4 text-[11px] text-neutral-500">
                      <span><b className="text-black">{job.required_exp}</b> yrs exp</span>
                      <span>Min score <b className="text-black">{Number(job.minimum_score).toFixed(0)}</b></span>
                      <span>Due <b className="text-black">{formatDate(job.due_date)}</b></span>
                      <span><b className="text-black">{count}</b> applicants</span>
                    </div>
                  </div>
                  <div className="flex flex-shrink-0 gap-2">
                    <button onClick={() => openEdit(job)} className="rounded-full border border-neutral-300 bg-white px-4 py-1.5 text-xs font-semibold text-black hover:bg-neutral-100">Edit</button>
                    <button onClick={() => remove(job.job_id)} className="rounded-full border border-red-200 bg-white px-4 py-1.5 text-xs font-semibold text-red-600 hover:bg-red-50">Delete</button>
                  </div>
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
// APPLICANTS
// ============================================================
function ApplicantsPanel({ jobs, appsByJob, candidateById, matchingByApp, resumeById, applications, setApplications, interviews, setInterviews }) {
  const [selectedJobId, setSelectedJobId] = useState("");
  const [busyId, setBusyId] = useState(null);

  const list = selectedJobId ? (appsByJob[Number(selectedJobId)] || []) : [];
  const sorted = [...list].sort((a, b) => {
    const sa = Number(matchingByApp[a.application_id]?.total_score || 0);
    const sb = Number(matchingByApp[b.application_id]?.total_score || 0);
    return sb - sa;
  });

  const changeStatus = async (appId, newStatus) => {
    setBusyId(appId);
    try {
      await apiRequest(`/api/applications/${appId}/update/`, { method: "PUT", body: { application_status: newStatus } });
      setApplications((prev) => prev.map((a) => a.application_id === appId ? { ...a, application_status: newStatus } : a));
    } catch (e) { alert(e.message); }
    finally { setBusyId(null); }
  };

  const schedule = async (appId) => {
    setBusyId(appId);
    try {
      if (interviews.find((i) => i.application_id === appId)) { alert("Interview already scheduled."); return; }
      const res = await apiRequest("/api/ai-interviews/create/", { method: "POST", body: {
        application_id: appId, interview_mode: "ai", interview_round: "1st Round", interview_status: "pending",
      }});
      setInterviews((prev) => [...prev, res.data]);
      alert("Interview scheduled.");
    } catch (e) { alert(e.message); }
    finally { setBusyId(null); }
  };

  return (
    <div className="space-y-5">
      <div className="rounded-3xl bg-white p-6 ring-1 ring-neutral-200">
        <Label>Select Job</Label>
        <select
          value={selectedJobId}
          onChange={(e) => setSelectedJobId(e.target.value)}
          className="mt-2 w-full max-w-md rounded-full border border-neutral-200 bg-[#faf9f6] px-4 py-2.5 text-sm text-black outline-none focus:border-black"
        >
          <option value="">— Choose a job —</option>
          {jobs.map((j) => <option key={j.job_id} value={j.job_id}>{j.job_title} ({appsByJob[j.job_id]?.length || 0})</option>)}
        </select>
      </div>

      {!selectedJobId ? (
        <div className="rounded-3xl bg-white p-10 text-center ring-1 ring-neutral-200">
          <p className="text-sm text-neutral-500">Select a job to view applicants.</p>
        </div>
      ) : sorted.length === 0 ? (
        <div className="rounded-3xl bg-white p-10 text-center ring-1 ring-neutral-200">
          <p className="text-sm text-neutral-500">No applicants for this job yet.</p>
        </div>
      ) : (
        <ul className="space-y-3">
          {sorted.map((app) => {
            const cand = candidateById[app.candidate_id];
            const matching = matchingByApp[app.application_id];
            const resume = app.resume_id ? resumeById[app.resume_id] : null;
            return (
              <li key={app.application_id} className="rounded-3xl bg-white p-6 ring-1 ring-neutral-200">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h4 className="text-base font-semibold text-black">{cand?.full_name || `Candidate #${app.candidate_id}`}</h4>
                      <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold capitalize ${APP_STATUS_COLORS[app.application_status]}`}>
                        {app.application_status}
                      </span>
                    </div>
                    <p className="mt-1 truncate text-xs text-neutral-500">
                      {cand?.email} {cand?.phone_no ? `· ${cand.phone_no}` : ""}
                    </p>
                    <p className="mt-1 text-[11px] text-neutral-500">Applied {formatDate(app.applied_at)}</p>

                    {matching && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        <Badge>Skills {Number(matching.skills_score).toFixed(0)}</Badge>
                        <Badge>Exp {Number(matching.experience_score).toFixed(0)}</Badge>
                        <Badge>Qual {Number(matching.qualification_score).toFixed(0)}</Badge>
                        <Badge dark>Total {Number(matching.total_score).toFixed(0)}</Badge>
                      </div>
                    )}

                    {resume && (
                      <a
                        href={`${API_BASE_URL}${resume.file_path}`}
                        target="_blank" rel="noreferrer"
                        className="mt-3 inline-block text-xs font-medium text-black underline underline-offset-4 hover:no-underline"
                      >
                        📄 {resume.file_name}
                      </a>
                    )}
                  </div>

                  <div className="flex flex-shrink-0 flex-wrap gap-2">
                    <SmallBtn onClick={() => changeStatus(app.application_id, "shortlisted")} disabled={busyId === app.application_id || app.application_status === "shortlisted"} tone="amber">Shortlist</SmallBtn>
                    <SmallBtn onClick={() => changeStatus(app.application_id, "rejected")} disabled={busyId === app.application_id || app.application_status === "rejected"} tone="red">Reject</SmallBtn>
                    <SmallBtn onClick={() => changeStatus(app.application_id, "hired")} disabled={busyId === app.application_id || app.application_status === "hired"} tone="green">Hire</SmallBtn>
                    <SmallBtn onClick={() => schedule(app.application_id)} disabled={busyId === app.application_id}>Schedule Interview</SmallBtn>
                  </div>
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
// INTERVIEWS
// ============================================================
function InterviewsPanel({ interviews, setInterviews, applications, candidateById, jobsById }) {
  const appById = useMemo(() => { const m = {}; applications.forEach((a) => { m[a.application_id] = a; }); return m; }, [applications]);

  const update = async (id, data) => {
    try {
      await apiRequest(`/api/ai-interviews/${id}/update/`, { method: "PUT", body: data });
      setInterviews((prev) => prev.map((i) => i.interview_id === id ? { ...i, ...data } : i));
    } catch (e) { alert(e.message); }
  };

  if (interviews.length === 0) {
    return (
      <div className="rounded-3xl bg-white p-10 text-center ring-1 ring-neutral-200">
        <p className="text-sm text-neutral-500">No interviews scheduled yet. Schedule from the Applicants section.</p>
      </div>
    );
  }

  return (
    <ul className="space-y-3">
      {interviews.map((i) => {
        const app = appById[i.application_id];
        const cand = app ? candidateById[app.candidate_id] : null;
        const job = app ? jobsById[app.job_id] : null;
        return (
          <li key={i.interview_id} className="rounded-3xl bg-white p-6 ring-1 ring-neutral-200">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <h4 className="text-base font-semibold text-black">{cand?.full_name || `Candidate #${app?.candidate_id}`}</h4>
                <p className="truncate text-xs text-neutral-500">{job?.job_title}</p>
                <p className="mt-2 text-[11px] text-neutral-500">
                  {i.interview_round} · {i.interview_mode} · Score <b className="text-black">{Number(i.overall_score).toFixed(0)}</b>
                </p>
                <p className="text-[11px] text-neutral-500">
                  {i.started_at ? `Started ${formatDateTime(i.started_at)}` : "Not started"}
                  {i.completed_at ? ` · Completed ${formatDateTime(i.completed_at)}` : ""}
                </p>
              </div>
              <div className="flex flex-shrink-0 flex-wrap items-center gap-2">
                <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold capitalize ${INTERVIEW_STATUS_COLORS[i.interview_status]}`}>
                  {i.interview_status.replace("_", " ")}
                </span>
                <select
                  value={i.interview_status}
                  onChange={(e) => update(i.interview_id, { interview_status: e.target.value })}
                  className="rounded-full border border-neutral-200 bg-white px-3 py-1.5 text-xs text-black"
                >
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
                <input
                  type="number" min="0" max="100" value={Number(i.overall_score).toFixed(0)}
                  onChange={(e) => update(i.interview_id, { overall_score: Number(e.target.value) })}
                  className="w-16 rounded-full border border-neutral-200 bg-white px-3 py-1.5 text-xs text-black"
                />
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

// ============================================================
// DECISIONS
// ============================================================
function DecisionsPanel({ applications, candidateById, jobsById, matchingByApp, interviewByApp, hiringResults, setHiringResults }) {
  const [busyId, setBusyId] = useState(null);
  const [form, setForm] = useState({ application_id: "", final_score: 0, ranking: 0, selection_status: "shortlisted", remarks: "", decision_date: "" });
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");

  const resultByApp = useMemo(() => { const m = {}; hiringResults.forEach((h) => { m[h.application_id] = h; }); return m; }, [hiringResults]);

  const open = (appId) => {
    const existing = resultByApp[appId];
    if (existing) {
      setForm({
        application_id: appId, final_score: Number(existing.final_score), ranking: existing.ranking,
        selection_status: existing.selection_status, remarks: existing.remarks || "", decision_date: existing.decision_date || "",
      });
    } else {
      const m = matchingByApp[appId];
      setForm({
        application_id: appId, final_score: m ? Number(m.total_score) : 0, ranking: 0,
        selection_status: "shortlisted", remarks: "", decision_date: new Date().toISOString().slice(0, 10),
      });
    }
    setError(""); setShowForm(true);
  };

  const save = async (e) => {
    e.preventDefault(); setBusyId(form.application_id); setError("");
    try {
      const existing = resultByApp[form.application_id];
      if (existing) {
        await apiRequest(`/api/hiring-results/${existing.result_id}/update/`, { method: "PUT", body: form });
        setHiringResults((prev) => prev.map((h) => h.result_id === existing.result_id ? { ...h, ...form } : h));
      } else {
        const res = await apiRequest("/api/hiring-results/create/", { method: "POST", body: form });
        setHiringResults((prev) => [...prev, res.data]);
      }
      setShowForm(false);
    } catch (err) { setError(err.message); }
    finally { setBusyId(null); }
  };

  return (
    <div className="space-y-4">
      {applications.length === 0 ? (
        <div className="rounded-3xl bg-white p-10 text-center ring-1 ring-neutral-200">
          <p className="text-sm text-neutral-500">No applications yet.</p>
        </div>
      ) : (
        <ul className="space-y-3">
          {applications.map((app) => {
            const cand = candidateById[app.candidate_id];
            const job = jobsById[app.job_id];
            const matching = matchingByApp[app.application_id];
            const interview = interviewByApp[app.application_id];
            const result = resultByApp[app.application_id];
            return (
              <li key={app.application_id} className="rounded-3xl bg-white p-6 ring-1 ring-neutral-200">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <h4 className="text-base font-semibold text-black">{cand?.full_name || `Candidate #${app.candidate_id}`}</h4>
                    <p className="truncate text-xs text-neutral-500">{job?.job_title}</p>
                    <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-neutral-500">
                      {matching && <span>Match <b className="text-black">{Number(matching.total_score).toFixed(0)}</b></span>}
                      {interview && <span>Interview <b className="text-black">{Number(interview.overall_score).toFixed(0)}</b></span>}
                      {result && <span>Final <b className="text-black">{Number(result.final_score).toFixed(0)}</b></span>}
                    </div>
                  </div>
                  <div className="flex flex-shrink-0 items-center gap-2">
                    {result && (
                      <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold capitalize ${SELECTION_COLORS[result.selection_status]}`}>
                        {result.selection_status.replace("_", " ")}
                      </span>
                    )}
                    <button
                      onClick={() => open(app.application_id)}
                      className="rounded-full bg-black px-4 py-1.5 text-xs font-semibold text-white hover:bg-neutral-800"
                    >
                      {result ? "Edit Decision" : "Make Decision"}
                    </button>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      {showForm && (
        <form onSubmit={save} className="space-y-4 rounded-3xl bg-white p-6 ring-1 ring-neutral-200 sm:p-8">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-black">Final Decision</h3>
            <button type="button" onClick={() => setShowForm(false)} className="text-xs font-medium text-neutral-500 hover:text-black">Cancel</button>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label>Final Score (0–100)</Label>
              <Input type="number" step="0.01" min="0" max="100" value={form.final_score} onChange={(v) => setForm({ ...form, final_score: Number(v) })} />
            </div>
            <div>
              <Label>Ranking</Label>
              <Input type="number" min="0" value={form.ranking} onChange={(v) => setForm({ ...form, ranking: Number(v) })} />
            </div>
            <div>
              <Label>Status</Label>
              <select
                value={form.selection_status}
                onChange={(e) => setForm({ ...form, selection_status: e.target.value })}
                className="w-full rounded-xl border border-neutral-200 bg-[#faf9f6] px-3.5 py-2.5 text-sm text-black outline-none focus:border-black"
              >
                <option value="selected">Selected</option>
                <option value="shortlisted">Shortlisted</option>
                <option value="rejected">Rejected</option>
                <option value="on_hold">On Hold</option>
              </select>
            </div>
            <div>
              <Label>Decision Date</Label>
              <Input type="date" value={form.decision_date} onChange={(v) => setForm({ ...form, decision_date: v })} />
            </div>
            <div className="sm:col-span-2">
              <Label>Remarks</Label>
              <textarea
                rows={3} value={form.remarks}
                onChange={(e) => setForm({ ...form, remarks: e.target.value })}
                className="w-full rounded-xl border border-neutral-200 bg-[#faf9f6] px-3.5 py-2.5 text-sm text-black outline-none focus:border-black"
              />
            </div>
          </div>

          {error && <p className="rounded-xl bg-red-50 px-3 py-2 text-xs text-red-700 ring-1 ring-red-200">{error}</p>}

          <div className="flex gap-3 border-t border-neutral-100 pt-4">
            <button type="submit" disabled={busyId === form.application_id} className="rounded-full bg-black px-5 py-2.5 text-xs font-semibold text-white hover:bg-neutral-800 disabled:opacity-60">
              {busyId === form.application_id ? "Saving…" : "Save Decision"}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="rounded-full border border-neutral-300 bg-white px-5 py-2.5 text-xs font-semibold text-black hover:bg-neutral-100">
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

// ============================================================
// SHARED UI
// ============================================================
function Field({ label, value }) {
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-neutral-500">{label}</p>
      <p className="mt-1.5 text-sm text-black">{value || "—"}</p>
    </div>
  );
}
function Label({ children }) {
  return <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-neutral-500">{children}</p>;
}
function Input({ type = "text", value, onChange, required, ...rest }) {
  return (
    <input
      type={type} value={value} required={required} {...rest}
      onChange={(e) => onChange(e.target.value)}
      className="w-full rounded-xl border border-neutral-200 bg-[#faf9f6] px-3.5 py-2.5 text-sm text-black outline-none focus:border-black"
    />
  );
}
function Chip({ active, onClick, children }) {
  return (
    <button
      type="button" onClick={onClick}
      className={`rounded-full px-3 py-1 text-[11px] font-medium transition ${
        active ? "bg-black text-white" : "bg-[#faf9f6] text-neutral-700 ring-1 ring-neutral-200 hover:bg-neutral-100"
      }`}
    >
      {children}
    </button>
  );
}
function Badge({ children, dark }) {
  return (
    <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold ${dark ? "bg-black text-white" : "bg-[#faf9f6] text-neutral-700 ring-1 ring-neutral-200"}`}>
      {children}
    </span>
  );
}
function SmallBtn({ children, onClick, disabled, tone }) {
  const tones = {
    amber: "border-amber-200 text-amber-700 hover:bg-amber-50",
    red: "border-red-200 text-red-600 hover:bg-red-50",
    green: "border-green-200 text-green-700 hover:bg-green-50",
    default: "border-neutral-300 text-black hover:bg-neutral-100",
  };
  return (
    <button
      onClick={onClick} disabled={disabled}
      className={`rounded-full border bg-white px-3.5 py-1.5 text-xs font-semibold transition disabled:opacity-40 ${tones[tone] || tones.default}`}
    >
      {children}
    </button>
  );
}