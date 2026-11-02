"use client";

import { useEffect } from "react";

function formatDate(d) {
  if (!d) return "—";
  try {
    return new Date(d).toLocaleDateString("en-GB", {
      day: "2-digit", month: "short", year: "numeric",
    });
  } catch { return d; }
}

export default function JobDetailModal({ job, skills = [], onClose }) {
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = "unset"; };
  }, []);

  if (!job) return null;

  const overdue = job.due_date && new Date(job.due_date) < new Date();

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 px-4 backdrop-blur-sm">
      <div className="absolute inset-0" onClick={onClose} />

      <div className="relative z-10 w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-3xl bg-white shadow-2xl ring-1 ring-neutral-200">
        
        {/* Header */}
        <div className="sticky top-0 flex items-start justify-between border-b border-neutral-100 bg-white/95 p-6 backdrop-blur-md sm:p-8">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold ${overdue ? "bg-red-50 text-red-700 ring-1 ring-red-200" : "bg-green-50 text-green-700 ring-1 ring-green-200"}`}>
                {overdue ? "Closed" : "Active"}
              </span>
              <span className="text-xs font-medium text-neutral-500">Due {formatDate(job.due_date)}</span>
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-black sm:text-3xl">{job.job_title}</h2>
          </div>
          
          <button onClick={onClose} className="rounded-full p-2 text-neutral-400 hover:bg-neutral-100 hover:text-black transition-colors" aria-label="Close modal">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="space-y-6 p-6 sm:p-8">
          
          {/* Experience */}
          <div className="rounded-2xl bg-[#faf9f6] p-4 ring-1 ring-neutral-200">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-neutral-500">Experience Required</p>
            <p className="mt-1 text-sm font-bold text-black">{Number(job.required_exp)} Years</p>
          </div>

          {/* Required Skills */}
          {skills.length > 0 && (
            <div>
              <h3 className="text-sm font-bold text-black mb-3">Required Skills</h3>
              <div className="flex flex-wrap gap-2">
                {skills.map((s) => (
                  <span
                    key={s.skill_id}
                    className="rounded-full bg-[#faf9f6] px-3 py-1.5 text-xs font-medium text-neutral-800 ring-1 ring-neutral-200"
                  >
                    {s.skill_name}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Description */}
          <div>
            <h3 className="text-sm font-bold text-black mb-2">Job Description</h3>
            <div className="prose prose-sm prose-neutral max-w-none text-neutral-600 whitespace-pre-wrap">
              {job.job_description}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 border-t border-neutral-100 bg-white p-6 sm:p-8">
          <button
            disabled={overdue}
            onClick={() => {
              // TODO: Apply logic
              alert("Apply flow coming soon!");
            }}
            className={`w-full rounded-full py-3.5 text-sm font-semibold transition-colors ${
              overdue
                ? "cursor-not-allowed bg-neutral-100 text-neutral-400"
                : "bg-black text-white hover:bg-neutral-800"
            }`}
          >
            {overdue ? "Applications Closed" : "Apply for this Job"}
          </button>
        </div>
      </div>
    </div>
  );
}