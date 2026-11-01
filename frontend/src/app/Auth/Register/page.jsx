"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Poppins, Roboto } from "next/font/google";

const poppins = Poppins({ subsets: ["latin"], weight: ["600", "700", "800"] });
const roboto = Roboto({ subsets: ["latin"], weight: ["400", "500", "700"] });

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

/* Shared neumorphic input classes */
const inputBase =
  "w-full rounded-2xl bg-[#e8e8e8] px-4 py-3.5 text-sm text-black placeholder:text-neutral-400 " +
  "outline-none transition-shadow duration-300 " +
  "shadow-[6px_6px_16px_#c5c5c5,-6px_-6px_16px_#ffffff] " +
  "focus:shadow-[inset_6px_6px_16px_#c5c5c5,inset_-6px_-6px_16px_#ffffff]";

export default function RegisterPage() {
  const router = useRouter();

  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone_no: "",
    password: "",
    confirm_password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");

    if (form.password !== form.confirm_password) {
      setError("Passwords do not match");
      return;
    }

    if (form.password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/auth/register/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          full_name: form.full_name,
          email: form.email,
          phone_no: form.phone_no,
          password: form.password,
          confirm_password: form.confirm_password,
          role: "candidate",
        }),
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        setError(data.message || "Registration failed. Please try again.");
        return;
      }

      router.push("/Auth/Login");
    } catch (err) {
      setError("Network error. Please check your connection.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className={`${roboto.className} min-h-screen bg-[#e8e8e8] px-5 py-16 md:py-20`}>
      <div className="mx-auto w-full max-w-md">
        {/* Brand mark */}
        <div className="mb-10 flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-black">
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="white"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M12 2 2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <span className={`${poppins.className} text-sm font-bold tracking-tight text-black`}>
            TalentNest
          </span>
        </div>

        {/* Heading — Poppins */}
        <div className="mb-8">
          <h1 className={`${poppins.className} text-3xl font-extrabold tracking-tight text-black md:text-4xl`}>
            Create your account
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-neutral-600">
            Start hiring smarter with AI. It only takes a minute.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleRegister} className="space-y-5">
          <div className="space-y-2">
            <label className="block px-1 text-[12px] font-medium tracking-wide text-neutral-700">
              Full name
            </label>
            <input
              type="text"
              name="full_name"
              required
              value={form.full_name}
              onChange={handleChange}
              placeholder="Your full name"
              className={inputBase}
            />
          </div>

          <div className="space-y-2">
            <label className="block px-1 text-[12px] font-medium tracking-wide text-neutral-700">
              Email
            </label>
            <input
              type="email"
              name="email"
              required
              value={form.email}
              onChange={handleChange}
              placeholder="you@example.com"
              className={inputBase}
            />
          </div>

          <div className="space-y-2">
            <label className="block px-1 text-[12px] font-medium tracking-wide text-neutral-700">
              Phone <span className="font-normal text-neutral-500">(optional)</span>
            </label>
            <input
              type="tel"
              name="phone_no"
              value={form.phone_no}
              onChange={handleChange}
              placeholder="+92 300 1234567"
              className={inputBase}
            />
          </div>

          <div className="space-y-2">
            <label className="block px-1 text-[12px] font-medium tracking-wide text-neutral-700">
              Password
            </label>
            <input
              type="password"
              name="password"
              required
              value={form.password}
              onChange={handleChange}
              placeholder="At least 8 characters"
              className={inputBase}
            />
          </div>

          <div className="space-y-2">
            <label className="block px-1 text-[12px] font-medium tracking-wide text-neutral-700">
              Confirm password
            </label>
            <input
              type="password"
              name="confirm_password"
              required
              value={form.confirm_password}
              onChange={handleChange}
              placeholder="Re-enter your password"
              className={inputBase}
            />
          </div>

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13px] text-red-700">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className={`${poppins.className} mt-2 flex h-12 w-full items-center justify-center rounded-2xl bg-black text-sm font-semibold text-white shadow-[6px_6px_16px_#c5c5c5,-6px_-6px_16px_#ffffff] transition-all duration-200 hover:bg-neutral-800 active:shadow-[inset_4px_4px_10px_rgba(0,0,0,0.3)] disabled:cursor-not-allowed disabled:opacity-50`}
          >
            {loading ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="mt-8 text-center text-sm text-neutral-600">
          Already have an account?{" "}
          <Link
            href="/Auth/Login"
            className="font-semibold text-black underline underline-offset-4 transition-opacity hover:opacity-70"
          >
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}