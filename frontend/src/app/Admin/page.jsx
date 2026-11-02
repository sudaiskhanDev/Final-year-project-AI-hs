"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";

// ============================================================
// CONFIG
// ============================================================
const API_BASE_URL = "http://localhost:8000";

const SECTIONS = [
  { id: "overview", label: "Overview", num: "01" },
  { id: "users", label: "Manage Users", num: "02" },
  { id: "profiles", label: "Profiles", num: "03" },
  { id: "masterdata", label: "Master Data", num: "04" },
  { id: "jobs", label: "All Jobs", num: "05" },
  { id: "applications", label: "Applications", num: "06" },
];

const SECTION_TITLES = {
  overview: "Overview.",
  users: "Manage Users.",
  profiles: "Profiles.",
  masterdata: "Master Data.",
  jobs: "All Jobs.",
  applications: "Applications.",
};

// ============================================================
// ICONS
// ============================================================
const Icon = ({ name, size = 18 }) => {
  const common = { width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" };
  const paths = {
    overview: <><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></>,
    users: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></>,
    jobs: <><rect x="2" y="7" width="20" height="14" rx="2" /><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" /></>,
    apps: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /><polyline points="10 9 9 9 8 9" /></>,
    settings: <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" /></>,
    user: <><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></>,
    logout: <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></>,
    trash: <><polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /></>,
    plus: <><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></>,
  };
  return <svg {...common}>{paths[name]}</svg>;
};

// ============================================================
// API & UTILS
// ============================================================
async function apiRequest(path, { method = "GET", body } = {}) {
  const options = { method, credentials: "include", headers: {} };
  if (body) { options.headers["Content-Type"] = "application/json"; options.body = JSON.stringify(body); }
  let res; try { res = await fetch(`${API_BASE_URL}${path}`, options); } catch { throw new Error("Network error"); }
  let payload = null; try { payload = await res.json(); } catch {}
  if (!res.ok || payload?.success === false) throw new Error(payload?.message || `Error ${res.status}`);
  return payload;
}
function getStoredUser() { try { return JSON.parse(localStorage.getItem("auth_user")); } catch { return null; } }
function getInitials(name) { return name ? name.trim().split(/\s+/).map(w => w[0]).slice(0,2).join("").toUpperCase() : "A"; }
function formatDate(d) { return d ? new Date(d).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }) : "—"; }

// ============================================================
// MAIN COMPONENT
// ============================================================
export default function AdminDashboard() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [activeSection, setActiveSection] = useState("overview");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  // Data
  const [users, setUsers] = useState([]);
  const [hrProfiles, setHrProfiles] = useState([]);
  const [candProfiles, setCandProfiles] = useState([]);
  const [skills, setSkills] = useState([]);
  const [quals, setQuals] = useState([]);
  const [langs, setLangs] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);

  const loadAll = useCallback(async () => {
    const safe = (p) => p.catch(() => ({ data: [] }));
    const [u, hr, c, s, q, l, j, a] = await Promise.all([
      safe(apiRequest("/api/users/")), safe(apiRequest("/api/hr-profiles/")), safe(apiRequest("/api/candidate-profiles/")),
      safe(apiRequest("/api/skills/")), safe(apiRequest("/api/qualifications/")), safe(apiRequest("/api/languages/")),
      safe(apiRequest("/api/jobs/")), safe(apiRequest("/api/applications/"))
    ]);
    setUsers(u.data || []); setHrProfiles(hr.data || []); setCandProfiles(c.data || []);
    setSkills(s.data || []); setQuals(q.data || []); setLangs(l.data || []);
    setJobs(j.data || []); setApplications(a.data || []);
  }, []);

  useEffect(() => {
    const storedUser = getStoredUser();
    if (!storedUser || storedUser.role !== "admin") { router.push("/Auth/Login"); return; }
    setUser(storedUser);
    loadAll().catch(e => setError(e.message)).finally(() => setIsLoading(false));
  }, [router, loadAll]);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try { await fetch(`${API_BASE_URL}/api/auth/logout/`, { method: "POST", credentials: "include" }); } catch {}
    localStorage.removeItem("auth_user"); router.push("/"); router.refresh();
  };

  if (isLoading) return <div className="flex min-h-screen items-center justify-center bg-[#f7f6f3] text-sm text-neutral-500">Loading Admin Workspace…</div>;
  if (error) return <div className="flex min-h-screen items-center justify-center bg-[#f7f6f3]"><div className="rounded-3xl bg-white p-8 text-center ring-1 ring-neutral-200"><p className="text-red-500 font-bold">Error</p><p className="text-sm text-neutral-700">{error}</p></div></div>;

  return (
    <div className="min-h-screen bg-[#f7f6f3] pt-32 pb-20 text-neutral-900">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        
        {/* HERO */}
        <div className="mb-10 flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.25em] text-neutral-500">Admin Control Panel</p>
            <h1 className="mt-3 text-5xl font-bold tracking-tight text-black sm:text-6xl">{SECTION_TITLES[activeSection]}</h1>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-xs font-semibold text-black">{user?.full_name}</p>
              <p className="text-[11px] text-neutral-500">{user?.email}</p>
            </div>
            <div className="flex h-11 w-11 items-center justify-center rounded-full bg-black text-sm font-bold text-white">{getInitials(user?.full_name)}</div>
            <button onClick={handleLogout} disabled={isLoggingOut} className="flex items-center gap-2 rounded-full border border-neutral-300 bg-white px-5 py-2.5 text-xs font-semibold text-black hover:bg-neutral-100 disabled:opacity-60">
              <Icon name="logout" size={14} /> {isLoggingOut ? "Logging out…" : "Logout"}
            </button>
          </div>
        </div>

        {/* MAIN GRID */}
        <div className="flex flex-col gap-6 lg:flex-row">
          {/* SIDEBAR */}
          <aside className="w-full flex-shrink-0 lg:w-64">
            <div className="rounded-3xl bg-white p-3 ring-1 ring-neutral-200 sticky top-24">
              <nav className="flex flex-col gap-1">
                {SECTIONS.map((s) => (
                  <button key={s.id} onClick={() => setActiveSection(s.id)} className={`flex items-center gap-3 rounded-full px-4 py-3 text-left text-[13px] font-medium transition ${activeSection === s.id ? "bg-black text-white" : "text-neutral-700 hover:bg-neutral-100"}`}>
                    <span className={`font-mono text-[10px] ${activeSection === s.id ? "text-white/60" : "text-neutral-400"}`}>{s.num}</span>
                    {s.label}
                  </button>
                ))}
              </nav>
            </div>
          </aside>

          {/* CONTENT */}
          <main className="min-w-0 flex-1">
            {activeSection === "overview" && <OverviewSection users={users} jobs={jobs} applications={applications} hrProfiles={hrProfiles} candProfiles={candProfiles} />}
            {activeSection === "users" && <UsersSection users={users} setUsers={setUsers} />}
            {activeSection === "profiles" && <ProfilesSection hrProfiles={hrProfiles} candProfiles={candProfiles} />}
            {activeSection === "masterdata" && <MasterDataSection skills={skills} setSkills={setSkills} quals={quals} setQuals={setQuals} langs={langs} setLangs={setLangs} />}
            {activeSection === "jobs" && <JobsSection jobs={jobs} hrProfiles={hrProfiles} />}
            {activeSection === "applications" && <ApplicationsSection applications={applications} candProfiles={candProfiles} jobs={jobs} />}
          </main>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// OVERVIEW
// ============================================================
function OverviewSection({ users, jobs, applications, hrProfiles, candProfiles }) {
  const stats = [
    { label: "Total Users", value: users.length, icon: "users" },
    { label: "HRs", value: hrProfiles.length, icon: "user" },
    { label: "Candidates", value: candProfiles.length, icon: "user" },
    { label: "Total Jobs", value: jobs.length, icon: "jobs" },
    { label: "Applications", value: applications.length, icon: "apps" },
    { label: "Hired", value: applications.filter(a => a.application_status === 'hired').length, icon: "overview" },
  ];

  return (
    <div className="space-y-6">
      <div className="rounded-3xl bg-white p-6 ring-1 ring-neutral-200">
        <h2 className="mb-4 text-lg font-bold text-black">System Stats</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {stats.map((s, i) => (
            <div key={i} className="rounded-2xl bg-[#faf9f6] p-4 ring-1 ring-neutral-200">
              <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-xl bg-white text-black ring-1 ring-neutral-200"><Icon name={s.icon} size={14} /></div>
              <p className="text-2xl font-bold text-black">{s.value}</p>
              <p className="text-[10px] font-semibold text-neutral-600">{s.label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============================================================
// USERS SECTION
// ============================================================
function UsersSection({ users, setUsers }) {
  const [search, setSearch] = useState("");
  const [busyId, setBusyId] = useState(null);

  const filtered = users.filter(u => u.full_name.toLowerCase().includes(search.toLowerCase()) || u.email.toLowerCase().includes(search.toLowerCase()));

  const handleRoleChange = async (id, newRole) => {
    setBusyId(id);
    try {
      await apiRequest(`/api/users/${id}/update/`, { method: "PUT", body: { role: newRole } });
      setUsers(prev => prev.map(u => u.user_id === id ? { ...u, role: newRole } : u));
    } catch (e) { alert(e.message); } finally { setBusyId(null); }
  };

  const handleDelete = async (id) => {
    if (!confirm("Delete this user? This action cannot be undone.")) return;
    setBusyId(id);
    try {
      await apiRequest(`/api/users/${id}/delete/`, { method: "DELETE" });
      setUsers(prev => prev.filter(u => u.user_id !== id));
    } catch (e) { alert(e.message); } finally { setBusyId(null); }
  };

  return (
    <div className="rounded-3xl bg-white p-6 ring-1 ring-neutral-200">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-lg font-bold text-black">All Users</h2>
        <input type="text" placeholder="Search users..." value={search} onChange={e => setSearch(e.target.value)} className="w-full max-w-xs rounded-full border border-neutral-200 bg-[#faf9f6] px-4 py-2 text-sm outline-none focus:border-black" />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-neutral-600">
          <thead className="border-b border-neutral-200 text-[10px] uppercase tracking-wider text-neutral-500">
            <tr>
              <th className="pb-3 font-semibold">User</th>
              <th className="pb-3 font-semibold">Role</th>
              <th className="pb-3 font-semibold">Status</th>
              <th className="pb-3 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {filtered.map(u => (
              <tr key={u.user_id} className="hover:bg-neutral-50/50">
                <td className="py-3">
                  <p className="font-semibold text-black">{u.full_name}</p>
                  <p className="text-[11px] text-neutral-500">{u.email}</p>
                </td>
                <td className="py-3">
                  <select value={u.role} onChange={e => handleRoleChange(u.user_id, e.target.value)} disabled={busyId === u.user_id} className="rounded-full border border-neutral-200 bg-white px-2 py-1 text-xs font-medium">
                    <option value="admin">Admin</option>
                    <option value="hr">HR</option>
                    <option value="candidate">Candidate</option>
                  </select>
                </td>
                <td className="py-3">
                  <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold ${u.is_active ? "bg-green-50 text-green-700 ring-1 ring-green-200" : "bg-red-50 text-red-700 ring-1 ring-red-200"}`}>{u.is_active ? "Active" : "Inactive"}</span>
                </td>
                <td className="py-3 text-right">
                  <button onClick={() => handleDelete(u.user_id)} disabled={busyId === u.user_id} className="rounded-full border border-red-200 p-2 text-red-600 hover:bg-red-50 disabled:opacity-40"><Icon name="trash" size={14} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ============================================================
// PROFILES SECTION
// ============================================================
function ProfilesSection({ hrProfiles, candProfiles }) {
  const [tab, setTab] = useState("hr");
  return (
    <div className="rounded-3xl bg-white p-6 ring-1 ring-neutral-200">
      <div className="mb-6 flex gap-2 border-b border-neutral-200 pb-4">
        <button onClick={() => setTab("hr")} className={`rounded-full px-4 py-2 text-xs font-semibold ${tab === "hr" ? "bg-black text-white" : "bg-neutral-100 text-neutral-700 hover:bg-neutral-200"}`}>HR Profiles ({hrProfiles.length})</button>
        <button onClick={() => setTab("cand")} className={`rounded-full px-4 py-2 text-xs font-semibold ${tab === "cand" ? "bg-black text-white" : "bg-neutral-100 text-neutral-700 hover:bg-neutral-200"}`}>Candidates ({candProfiles.length})</button>
      </div>

      {tab === "hr" ? (
        <ul className="divide-y divide-neutral-100">
          {hrProfiles.map(hr => (
            <li key={hr.hr_id} className="flex justify-between py-3">
              <div><p className="font-semibold text-black">{hr.department || "No Dept"}</p><p className="text-[11px] text-neutral-500">{hr.designation || "No Designation"}</p></div>
              <span className="text-[11px] text-neutral-500">ID: {hr.hr_id}</span>
            </li>
          ))}
        </ul>
      ) : (
        <ul className="divide-y divide-neutral-100">
          {candProfiles.map(c => (
            <li key={c.candidate_id} className="flex justify-between py-3">
              <div><p className="font-semibold text-black">{c.address || "No Address"}</p><p className="text-[11px] text-neutral-500">{c.gender || "N/A"} · DOB: {formatDate(c.date_of_birth)}</p></div>
              <span className="text-[11px] text-neutral-500">ID: {c.candidate_id}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ============================================================
// MASTER DATA SECTION
// ============================================================
function MasterDataSection({ skills, setSkills, quals, setQuals, langs, setLangs }) {
  const [tab, setTab] = useState("skills");
  const [val, setVal] = useState("");
  const [busy, setBusy] = useState(false);

  const handleAdd = async () => {
    if (!val.trim()) return;
    setBusy(true);
    try {
      if (tab === "skills") {
        const res = await apiRequest("/api/skills/", { method: "POST", body: { skill_name: val } });
        setSkills([...skills, res.data]);
      } else if (tab === "quals") {
        const res = await apiRequest("/api/qualifications/", { method: "POST", body: { qualification_name: val } });
        setQuals([...quals, res.data]);
      } else {
        const res = await apiRequest("/api/languages/", { method: "POST", body: { language_name: val } });
        setLangs([...langs, res.data]);
      }
      setVal("");
    } catch (e) { alert(e.message); } finally { setBusy(false); }
  };

  const handleDelete = async (id) => {
    if (!confirm("Delete this item?")) return;
    try {
      if (tab === "skills") { await apiRequest(`/api/skills/${id}/`, { method: "DELETE" }); setSkills(skills.filter(x => x.skill_id !== id)); }
      else if (tab === "quals") { await apiRequest(`/api/qualifications/${id}/`, { method: "DELETE" }); setQuals(quals.filter(x => x.qualification_id !== id)); }
      else { await apiRequest(`/api/languages/${id}/`, { method: "DELETE" }); setLangs(langs.filter(x => x.lang_id !== id)); }
    } catch (e) { alert(e.message); }
  };

  return (
    <div className="rounded-3xl bg-white p-6 ring-1 ring-neutral-200">
      <div className="mb-6 flex gap-2 border-b border-neutral-200 pb-4">
        <button onClick={() => setTab("skills")} className={`rounded-full px-4 py-2 text-xs font-semibold ${tab === "skills" ? "bg-black text-white" : "bg-neutral-100"}`}>Skills</button>
        <button onClick={() => setTab("quals")} className={`rounded-full px-4 py-2 text-xs font-semibold ${tab === "quals" ? "bg-black text-white" : "bg-neutral-100"}`}>Qualifications</button>
        <button onClick={() => setTab("langs")} className={`rounded-full px-4 py-2 text-xs font-semibold ${tab === "langs" ? "bg-black text-white" : "bg-neutral-100"}`}>Languages</button>
      </div>

      <div className="mb-4 flex gap-2">
        <input type="text" value={val} onChange={e => setVal(e.target.value)} placeholder={`Add new ${tab}...`} className="flex-1 rounded-full border border-neutral-200 bg-[#faf9f6] px-4 py-2 text-sm outline-none focus:border-black" />
        <button onClick={handleAdd} disabled={busy || !val} className="rounded-full bg-black px-5 py-2 text-xs font-semibold text-white hover:bg-neutral-800 disabled:opacity-50">Add</button>
      </div>

      <ul className="flex flex-wrap gap-2">
        {tab === "skills" && skills.map(s => (
          <li key={s.skill_id} className="flex items-center gap-2 rounded-full bg-[#faf9f6] px-3 py-1.5 text-xs ring-1 ring-neutral-200">
            {s.skill_name} <button onClick={() => handleDelete(s.skill_id)} className="text-neutral-400 hover:text-red-500">×</button>
          </li>
        ))}
        {tab === "quals" && quals.map(q => (
          <li key={q.qualification_id} className="flex items-center gap-2 rounded-full bg-[#faf9f6] px-3 py-1.5 text-xs ring-1 ring-neutral-200">
            {q.qualification_name} <button onClick={() => handleDelete(q.qualification_id)} className="text-neutral-400 hover:text-red-500">×</button>
          </li>
        ))}
        {tab === "langs" && langs.map(l => (
          <li key={l.lang_id} className="flex items-center gap-2 rounded-full bg-[#faf9f6] px-3 py-1.5 text-xs ring-1 ring-neutral-200">
            {l.language_name} <button onClick={() => handleDelete(l.lang_id)} className="text-neutral-400 hover:text-red-500">×</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ============================================================
// JOBS SECTION
// ============================================================
function JobsSection({ jobs, hrProfiles }) {
  const hrMap = Object.fromEntries(hrProfiles.map(h => [h.hr_id, h]));
  return (
    <div className="rounded-3xl bg-white p-6 ring-1 ring-neutral-200">
      <h2 className="mb-4 text-lg font-bold text-black">All Jobs</h2>
      <ul className="divide-y divide-neutral-100">
        {jobs.map(j => {
          const hr = hrMap[j.hr_id];
          return (
            <li key={j.job_id} className="py-3">
              <p className="font-semibold text-black">{j.job_title}</p>
              <p className="text-[11px] text-neutral-500">Posted by HR ID: {j.hr_id} · Due: {formatDate(j.due_date)}</p>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

// ============================================================
// APPLICATIONS SECTION
// ============================================================
function ApplicationsSection({ applications, candProfiles, jobs }) {
  const candMap = Object.fromEntries(candProfiles.map(c => [c.candidate_id, c]));
  const jobMap = Object.fromEntries(jobs.map(j => [j.job_id, j]));
  return (
    <div className="rounded-3xl bg-white p-6 ring-1 ring-neutral-200">
      <h2 className="mb-4 text-lg font-bold text-black">All Applications</h2>
      <ul className="divide-y divide-neutral-100">
        {applications.map(a => (
          <li key={a.application_id} className="flex justify-between py-3">
            <div>
              <p className="font-semibold text-black">Candidate: {candMap[a.candidate_id]?.full_name || `ID ${a.candidate_id}`}</p>
              <p className="text-[11px] text-neutral-500">Job: {jobMap[a.job_id]?.job_title || `ID ${a.job_id}`}</p>
            </div>
            <span className="text-[10px] font-semibold uppercase text-neutral-600 bg-neutral-100 px-2 py-1 rounded h-fit">{a.application_status}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}