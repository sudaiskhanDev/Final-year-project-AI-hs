"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

// ============================================================
// CONFIG
// ============================================================
const API_BASE_URL = "http://localhost:8000";
const ROLE_REDIRECTS = {
  hr: "/HR",
  admin: "/Admin",
  candidate: "/",
};

// ============================================================
// API HELPERS
// ============================================================
async function apiRequest(path, { method = "GET", body } = {}) {
  const url = `${API_BASE_URL}${path}`;

  let response;
  try {
    response = await fetch(url, {
      method,
      credentials: "include", // Django session cookie ke liye
      headers: { "Content-Type": "application/json" },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Server se connect nahi ho saka. Backend chal raha hai?");
  }

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    /* non-JSON response — ignore */
  }

  // Backend shape: { success, message, data | errors }
  if (!response.ok || payload?.success === false) {
    throw new Error(payload?.message || `Request failed (${response.status})`);
  }

  return payload;
}

async function loginUser(email, password) {
  return apiRequest("/api/auth/login/", {
    method: "POST",
    body: { email, password },
  });
}

function getRedirectPathByRole(role) {
  return ROLE_REDIRECTS[role] || "/";
}

// ============================================================
// COMPONENT
// ============================================================
const LoginPage = () => {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const response = await loginUser(email, password);
      const role = response?.data?.role;
      const redirectPath = getRedirectPathByRole(role);

      // Session cookie backend se set ho jati hai (credentials: "include")
      // Navbar ke liye user info localStorage mein save karo
      localStorage.setItem("auth_user", JSON.stringify(response.data));

      router.push(redirectPath);
      router.refresh(); // Navbar ko updated auth state dikhane ke liye
    } catch (err) {
      setError(err.message || "Login failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-100 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-md">
        <h1 className="mb-2 text-2xl font-semibold text-neutral-900">Login</h1>
        <p className="mb-6 text-sm text-neutral-500">
          Welcome back to TalentNest.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email */}
          <div>
            <label
              htmlFor="email"
              className="mb-1 block text-sm font-medium text-neutral-700"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              placeholder="you@example.com"
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-900"
            />
          </div>

          {/* Password */}
          <div>
            <label
              htmlFor="password"
              className="mb-1 block text-sm font-medium text-neutral-700"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              placeholder="••••••••"
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-neutral-900"
            />
          </div>

          {/* Error */}
          {error && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
              {error}
            </p>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-neutral-900 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-neutral-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "Logging in..." : "Login"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-neutral-500">
          Don&apos;t have an account?{" "}
          <Link
            href="/Auth/Register"
            className="font-semibold text-neutral-900 hover:underline"
          >
            Register
          </Link>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;