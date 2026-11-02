"use client";

import { useState, useEffect } from "react";
import Navbar from "@/components/Landing/Navbar";
import JobDetailModal from "@/components/Jobs/JobDetailModal";

// ============================================================
// CONFIG
// ============================================================
const API_BASE_URL = "http://localhost:8000";

// ============================================================
// UTILS
// ============================================================
function formatDate(d) {
  if (!d) return "—";
  try {
    return new Date(d).toLocaleDateString("en-GB", {
      day: "2-digit", month: "short", year: "numeric",
    });
  } catch { return d; }
}

function isOverdue(dateStr) {
  if (!dateStr) return false;
  return new Date(dateStr) < new Date();
}

// ============================================================
// MAIN COMPONENT
// ============================================================
export default function JobsPage() {
  const [jobs, setJobs] = useState([]);
  const [jobSkills, setJobSkills] = useState([]); // All job-skill links
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedJob, setSelectedJob] = useState(null);

  // Fetch jobs + job-skills in parallel
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [jobsRes, jsRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/jobs/`, { credentials: "include" }),
          fetch(`${API_BASE_URL}/api/job-skills/`, { credentials: "include" }),
        ]);
        const jobsPayload = await jobsRes.json();
        const jsPayload = await jsRes.json();

        if (!jobsRes.ok || jobsPayload?.success === false) {
          throw new Error(jobsPayload?.message || "Failed to load jobs");
        }

        if (!cancelled) {
          const sorted = (jobsPayload.data || []).sort(
            (a, b) => new Date(b.created_at) - new Date(a.created_at)
          );
          setJobs(sorted);
          setJobSkills(jsPayload.data || []);
        }
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // Build map: { job_id: [{ skill_id, skill_name }] }
  const skillsByJob = jobSkills.reduce((acc, js) => {
    if (!acc[js.job_id]) acc[js.job_id] = [];
    acc[js.job_id].push({ skill_id: js.skill_id, skill_name: js.skill_name });
    return acc;
  }, {});

  const filteredJobs = jobs.filter((j) => {
    const query = searchQuery.toLowerCase();
    return (
      j.job_title.toLowerCase().includes(query) ||
      j.job_description.toLowerCase().includes(query)
    );
  });

  return (
    <>
      <Navbar />

      <div className="min-h-screen bg-[#f7f6f3] pt-32 pb-20 text-neutral-900">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          
          {/* HERO HEADER */}
          <div className="mb-10 flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.25em] text-neutral-500">Careers at TalentNest</p>
              <h1 className="mt-3 text-5xl font-bold tracking-tight text-black sm:text-6xl">Find Your Next Role.</h1>
              <p className="mt-4 max-w-md text-sm text-neutral-500">Explore open positions, review requirements, and apply to join the team.</p>
            </div>
            <div className="w-full max-w-sm">
              <input
                type="text" placeholder="Search jobs by title or keyword..." value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-full border border-neutral-200 bg-white px-5 py-3.5 text-sm text-black outline-none focus:border-black"
              />
            </div>
          </div>

          {/* CONTENT */}
          {isLoading ? (
            <div className="py-20 text-center text-sm text-neutral-500">Loading open positions...</div>
          ) : error ? (
            <div className="rounded-3xl bg-white p-10 text-center ring-1 ring-neutral-200">
              <p className="text-sm font-semibold text-red-500">Error</p>
              <p className="mt-1 text-sm text-neutral-700">{error}</p>
            </div>
          ) : filteredJobs.length === 0 ? (
            <div className="rounded-3xl bg-white p-12 text-center ring-1 ring-neutral-200">
              <p className="text-lg font-semibold text-black">No jobs found</p>
              <p className="mt-2 text-sm text-neutral-500">
                {searchQuery ? "Try adjusting your search terms." : "There are no open positions right now."}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
              {filteredJobs.map((job) => (
                <JobCard
                  key={job.job_id}
                  job={job}
                  skills={skillsByJob[job.job_id] || []}
                  onViewDetails={() => setSelectedJob(job)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* MODAL */}
      {selectedJob && (
        <JobDetailModal
          job={selectedJob}
          skills={skillsByJob[selectedJob.job_id] || []}
          onClose={() => setSelectedJob(null)}
        />
      )}
    </>
  );
}

// ============================================================
// JOB CARD — with top skills
// ============================================================
function JobCard({ job, skills, onViewDetails }) {
  const overdue = isOverdue(job.due_date);
  const topSkills = skills.slice(0, 3);
  const extraCount = skills.length - topSkills.length;

  return (
    <div className="group flex flex-col justify-between rounded-3xl bg-white p-6 ring-1 ring-neutral-200 transition-all hover:-translate-y-0.5 hover:shadow-lg">
      <div>
        <div className="flex items-center justify-between">
          <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold ${overdue ? "bg-red-50 text-red-700 ring-1 ring-red-200" : "bg-green-50 text-green-700 ring-1 ring-green-200"}`}>
            {overdue ? "Closed" : "Active"}
          </span>
          <span className="text-[11px] font-medium text-neutral-400">Due {formatDate(job.due_date)}</span>
        </div>

        <h3 className="mt-4 text-xl font-bold tracking-tight text-black">{job.job_title}</h3>
        <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-neutral-600">{job.job_description}</p>

        {/* Required skills — top 3 + more */}
        {topSkills.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {topSkills.map((s) => (
              <span
                key={s.skill_id}
                className="rounded-full bg-[#faf9f6] px-2.5 py-1 text-[10px] font-medium text-neutral-700 ring-1 ring-neutral-200"
              >
                {s.skill_name}
              </span>
            ))}
            {extraCount > 0 && (
              <span className="rounded-full bg-black px-2.5 py-1 text-[10px] font-semibold text-white">
                +{extraCount}
              </span>
            )}
          </div>
        )}
        
        <div className="my-5 h-px w-full bg-neutral-100" />
        
        <div className="flex items-center gap-1.5 text-xs text-neutral-500">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="7" width="20" height="14" rx="2" />
            <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
          </svg>
          {Number(job.required_exp)} yrs experience required
        </div>
      </div>

      <div className="mt-6">
        <button
          onClick={onViewDetails}
          className="w-full rounded-full border border-neutral-300 bg-white py-2.5 text-sm font-semibold text-black transition-colors hover:bg-neutral-100"
        >
          View Details
        </button>
      </div>
    </div>
  );
}