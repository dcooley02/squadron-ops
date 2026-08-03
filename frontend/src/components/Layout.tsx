import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Menu, X } from "lucide-react";
import Sidebar from "./Sidebar";

export default function Layout() {
  const [navOpen, setNavOpen] = useState(false);
  const location = useLocation();
  // Close mobile drawer when the route changes (incl. browser back/forward)
  const [navPath, setNavPath] = useState(location.pathname);
  if (location.pathname !== navPath) {
    setNavPath(location.pathname);
    if (navOpen) setNavOpen(false);
  }

  useEffect(() => {
    if (!navOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [navOpen]);

  return (
    <div className="flex h-screen bg-slate-950 overflow-hidden">
      {/* Desktop permanent sidebar */}
      <div className="hidden md:flex h-full shrink-0">
        <Sidebar />
      </div>

      {/* Mobile drawer */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-56 transform transition-transform duration-200 ease-out md:hidden ${
          navOpen ? "translate-x-0" : "-translate-x-full pointer-events-none"
        }`}
        aria-hidden={!navOpen}
      >
        <Sidebar id="app-sidebar" onNavigate={() => setNavOpen(false)} />
      </div>
      {navOpen && (
        <button
          type="button"
          aria-label="Close menu"
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setNavOpen(false)}
        />
      )}

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="flex shrink-0 items-center gap-3 border-b border-slate-800 bg-slate-900 px-3 py-2 md:hidden">
          <button
            type="button"
            className="inline-flex h-10 w-10 items-center justify-center rounded-md text-slate-200 hover:bg-slate-800"
            aria-expanded={navOpen}
            aria-controls="app-sidebar"
            onClick={() => setNavOpen((o) => !o)}
          >
            {navOpen ? <X size={20} aria-hidden /> : <Menu size={20} aria-hidden />}
            <span className="sr-only">{navOpen ? "Close menu" : "Open menu"}</span>
          </button>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold tracking-tight">
              HSC Squadron Ops
            </div>
            <div className="truncate text-xs text-slate-500">MH-60S Operations</div>
          </div>
        </header>

        <main className="min-w-0 flex-1 overflow-auto">
          <div className="mx-auto max-w-7xl p-4 md:p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
