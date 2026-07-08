import { useState, type FormEvent } from "react";
import { Navigate, useLocation } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { API_BASE_URL } from "../lib/api";

const DEMO_ACCOUNTS = [
  { label: "SDO", username: "anderson.robert", hint: "Schedule publish, Ops console" },
  { label: "Maint Control", username: "morgan.david", hint: "Maintenance rollups" },
  { label: "Line Pilot", username: "mitchell.james", hint: "Crew jacket, logbook" },
  { label: "Admin", username: "admin", hint: "Audit log, full access" },
];

export default function Login() {
  const { user, login, isLoading } = useAuth();
  const location = useLocation();
  const [username, setUsername] = useState("anderson.robert");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const from = (location.state as { from?: string } | null)?.from ?? "/";

  if (!isLoading && user) {
    return <Navigate to={from} replace />;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username.trim(), password);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 401) {
          setError("Invalid username or password.");
        } else if (err.code === "ERR_NETWORK" || !err.response) {
          setError(
            `Cannot reach API at ${API_BASE_URL}. Is the backend running on port 8001?`
          );
        } else {
          setError(`Login failed (HTTP ${err.response.status}).`);
        }
      } else {
        setError("Login failed. Check the console for details.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-6">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-xl font-semibold text-slate-100">HSC Squadron Ops</h1>
          <p className="text-sm text-slate-500 mt-1">Sign in to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-4">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-slate-100"
              autoComplete="username"
              required
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-slate-100"
              autoComplete="current-password"
              required
            />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="w-full py-2 rounded bg-blue-700 hover:bg-blue-600 text-white text-sm font-medium disabled:opacity-50"
          >
            {submitting ? "Signing in…" : "Sign in"}
          </button>
          <p className="text-xs text-slate-500 text-center">Demo password: demo1234</p>
        </form>

        <div className="card">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">
            Demo accounts
          </h2>
          <ul className="space-y-2">
            {DEMO_ACCOUNTS.map((a) => (
              <li key={a.username}>
                <button
                  type="button"
                  onClick={() => setUsername(a.username)}
                  className="w-full text-left text-sm hover:bg-slate-800/50 rounded px-2 py-1.5 -mx-2"
                >
                  <span className="text-slate-200 font-medium">{a.label}</span>
                  <span className="text-slate-500 ml-2 font-mono text-xs">{a.username}</span>
                  <span className="block text-xs text-slate-500">{a.hint}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}