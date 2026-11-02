"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

// ============================================================
// CONFIG
// ============================================================
const API_BASE_URL = "http://localhost:8000";
// ============================================================
// HELPERS
// ============================================================
function getInitials(name) {
  if (!name) return "U";
  return name
    .trim()
    .split(/\s+/)
    .map((word) => word[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

function getStoredUser() {
  try {
    const raw = localStorage.getItem("auth_user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

async function logoutUser() {
  try {
    await fetch(`${API_BASE_URL}/api/auth/logout/`, {
      method: "POST",
      credentials: "include",
    });
  } catch {
    /* network fail ho jaye to bhi local state clear karenge */
  }
}

// ============================================================
// COMPONENT
// ============================================================
const Navbar = () => {
  const router = useRouter();
  const pathname = usePathname();

  const [user, setUser] = useState(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const dropdownRef = useRef(null);

  // Route change pe localStorage se auth re-check
  useEffect(() => {
    setUser(getStoredUser());
  }, [pathname]);

  // Bahar click pe dropdown band
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    await logoutUser();
    localStorage.removeItem("auth_user");
    setUser(null);
    setDropdownOpen(false);
    setIsLoggingOut(false);
    router.push("/");
    router.refresh();
  };

  const handleProfileClick = () => {
    setDropdownOpen(false);
    router.push("/UserDashboard");
  };

  return (
    <header className="fixed inset-x-0 top-6 z-50 flex justify-center pointer-events-none">
      <nav className="pointer-events-auto flex items-center gap-8 rounded-full bg-[#1e1e1e] px-2 py-2 shadow-xl">
        {/* Logo circle (left) */}
        <Link
          href="/"
          className="flex h-9 w-9 items-center justify-center rounded-full bg-white"
          aria-label="TalentNest home"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-black"
            aria-hidden="true"
          >
            <path d="M12 2 2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        </Link>

        {/* Nav links (center) */}
        <ul className="flex items-center gap-7 text-[13px] font-medium text-neutral-300">
          <li>
            <Link href="/" className="transition-colors hover:text-white">
              Home
            </Link>
          </li>
          <li>
            <Link href="/Jobs" className="transition-colors hover:text-white">
              Jobs
            </Link>
          </li>
          <li>
            <Link href="/about" className="transition-colors hover:text-white">
              About
            </Link>
          </li>
          <li>
            <Link href="/contact" className="transition-colors hover:text-white">
              Contact
            </Link>
          </li>
        </ul>

        {/* Right actions */}
        <div className="flex items-center gap-2">
          {!user ? (
            <>
              <Link
                href="/Auth/Login"
                className="rounded-full px-4 py-2 text-[13px] font-semibold text-neutral-300 transition-colors hover:text-white"
              >
                Login
              </Link>
              <Link
                href="/Auth/Register"
                className="rounded-full bg-white px-4 py-2 text-[13px] font-semibold text-black transition-colors hover:bg-neutral-200"
              >
                Register
              </Link>
            </>
          ) : (
            <div className="relative" ref={dropdownRef}>
              {/* Profile icon (initials avatar) */}
              <button
                type="button"
                onClick={() => setDropdownOpen((prev) => !prev)}
                aria-haspopup="menu"
                aria-expanded={dropdownOpen}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-[12px] font-bold text-black transition-colors hover:bg-neutral-200"
              >
                {getInitials(user.full_name)}
              </button>

              {/* Dropdown */}
              {dropdownOpen && (
                <div
                  role="menu"
                  className="absolute right-0 top-full mt-3 w-56 overflow-hidden rounded-2xl bg-[#1e1e1e] shadow-xl ring-1 ring-white/10"
                >
                  {/* User info */}
                  <div className="border-b border-white/10 px-4 py-3">
                    <p className="truncate text-[13px] font-semibold text-white">
                      {user.full_name || "User"}
                    </p>
                    <p className="truncate text-[11px] text-neutral-400">
                      {user.email}
                    </p>
                  </div>

                  {/* Profile / Dashboard */}
                  <button
                    type="button"
                    onClick={handleProfileClick}
                    role="menuitem"
                    className="flex w-full items-center gap-3 px-4 py-2.5 text-left text-[13px] font-medium text-neutral-300 transition-colors hover:bg-white/5 hover:text-white"
                  >
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
                      <circle cx="12" cy="8" r="4" />
                      <path d="M4 20c0-4 4-6 8-6s8 2 8 6" />
                    </svg>
                    Profile
                  </button>

                  {/* Logout */}
                  <button
                    type="button"
                    onClick={handleLogout}
                    disabled={isLoggingOut}
                    role="menuitem"
                    className="flex w-full items-center gap-3 px-4 py-2.5 text-left text-[13px] font-medium text-red-400 transition-colors hover:bg-white/5 hover:text-red-300 disabled:cursor-not-allowed disabled:opacity-60"
                  >
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
                      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                      <path d="M16 17l5-5-5-5" />
                      <path d="M21 12H9" />
                    </svg>
                    {isLoggingOut ? "Logging out..." : "Logout"}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </nav>
    </header>
  );
};

export default Navbar;