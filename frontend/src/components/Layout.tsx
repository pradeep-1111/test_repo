import { Link, NavLink, Outlet } from "react-router-dom";
import { ShieldCheck } from "lucide-react";

export function Layout() {
  const navClass = ({ isActive }: { isActive: boolean }) =>
    isActive
      ? "rounded-lg bg-slate-900 px-3 py-2 text-white"
      : "rounded-lg px-3 py-2 text-slate-700 hover:bg-slate-200";

  return (
    <div className="min-h-screen">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-2 font-bold">
            <ShieldCheck className="h-6 w-6" />
            AI Merge Guard
          </Link>

          <nav className="flex gap-2 text-sm">
            <NavLink to="/" className={navClass}>
              Dashboard
            </NavLink>
            <NavLink to="/manual-review" className={navClass}>
              Manual Review
            </NavLink>
            <NavLink to="/jobs" className={navClass}>
              Jobs
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}