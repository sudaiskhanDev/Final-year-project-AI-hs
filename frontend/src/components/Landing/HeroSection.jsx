import React from "react";
import Link from "next/link";

const HeroSection = () => {
  return (
    <section className="w-full bg-white">
      <div className="mx-auto flex max-w-5xl flex-col items-center px-6 pt-32 pb-24 text-center md:pt-40 md:pb-32">
        
        {/* Top: Avatars + Trust text */}
        <div className="mb-8 flex items-center gap-4">
          <div className="flex -space-x-3">
            {/* Avatar placeholders (gradient circles) */}
            <div className="h-10 w-10 rounded-full border-2 border-white bg-gradient-to-br from-purple-400 to-indigo-500" />
            <div className="h-10 w-10 rounded-full border-2 border-white bg-gradient-to-br from-pink-400 to-red-500" />
            <div className="h-10 w-10 rounded-full border-2 border-white bg-gradient-to-br from-yellow-400 to-orange-500" />
            <div className="h-10 w-10 rounded-full border-2 border-white bg-gradient-to-br from-green-400 to-teal-500" />
          </div>
          <div className="text-left text-[13px] leading-tight text-neutral-500">
            <p className="font-medium text-neutral-700">Trusted by 1600+</p>
            <p>TalentNest Creators & Teams</p>
          </div>
        </div>

        {/* Main Headline */}
        <h1 className="mb-6 max-w-4xl text-4xl font-black leading-[1.1] tracking-[-0.02em] text-black md:text-6xl lg:text-[72px]">
          Hire Faster & Smarter with{" "}
          <span className="whitespace-nowrap">
            AI-Powered{" "}
            <span className="relative inline-block">
              Recruitment
              {/* Hand-drawn underline effect */}
              <svg
                className="absolute -bottom-2 left-0 w-full text-black"
                viewBox="0 0 200 10"
                fill="none"
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                <path
                  d="M2 8C60 3 130 2 198 5"
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
              </svg>
            </span>
          </span>
        </h1>

        {/* Subheadline */}
        <p className="mb-10 max-w-2xl text-base leading-relaxed text-neutral-500">
          TalentNest parses resumes, matches candidates to jobs, and runs
          AI-driven interviews — all in one seamless platform. Free tier
          available.
        </p>

        {/* Trusted By Logos Row */}
        <div className="mb-12 flex flex-col items-center gap-4 md:flex-row md:gap-6">
          <span className="text-sm font-medium text-neutral-500">
            Trusted by
          </span>
          <div className="flex flex-wrap items-center justify-center gap-6 text-lg font-bold tracking-tight text-neutral-400 opacity-70">
            <span>AcmeCorp</span>
            <span>Chrono</span>
            <span>OneTech</span>
            <span>Verilife</span>
          </div>
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-col items-center gap-3 sm:flex-row">
          {/* Primary Button */}
          <Link
            href="/register"
            className="inline-flex h-12 items-center justify-center gap-2 rounded-lg bg-black px-6 text-sm font-semibold text-white shadow-lg transition-shadow duration-200 hover:shadow-[0_0_0_2px_#fff,0_0_0_4px_rgba(0,0,0,0.22)]"
          >
            Get Started Free
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M5 12h14" />
              <path d="m12 5 7 7-7 7" />
            </svg>
          </Link>

          {/* Secondary Button */}
          <Link
            href="/jobs"
            className="inline-flex h-12 items-center justify-center gap-2 rounded-lg bg-neutral-100 px-6 text-sm font-medium text-black transition-colors duration-200 hover:bg-neutral-200"
          >
            Explore Jobs
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M5 12h14" />
              <path d="m12 5 7 7-7 7" />
            </svg>
          </Link>
        </div>
        
      </div>
    </section>
  );
};

export default HeroSection;