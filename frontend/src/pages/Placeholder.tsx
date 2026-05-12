import { useLocation } from "react-router-dom";

export default function Placeholder() {
  const { pathname } = useLocation();
  const name = pathname.replace("/", "") || "this page";
  return (
    <div>
      <h1 className="capitalize">{name}</h1>
      <p className="text-slate-400 mt-2">This page hasn't been built yet.</p>
    </div>
  );
}