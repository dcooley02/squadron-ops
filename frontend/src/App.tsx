import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Layout from "./components/Layout";
import Loading from "./components/Loading";
import { ToastProvider } from "./components/Toast";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import RoleRoute from "./components/RoleRoute";
import Login from "./pages/Login";

// Eager: shell + login stay in the main chunk for first paint
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Crew = lazy(() => import("./pages/Crew"));
const CrewDetail = lazy(() => import("./pages/CrewDetail"));
const Aircraft = lazy(() => import("./pages/Aircraft"));
const AircraftDetail = lazy(() => import("./pages/AircraftDetail"));
const Sorties = lazy(() => import("./pages/Sorties"));
const SortieDetail = lazy(() => import("./pages/SortieDetail"));
const Schedule = lazy(() => import("./pages/Schedule"));
const Training = lazy(() => import("./pages/Training"));
const GradecardDetail = lazy(() => import("./pages/GradecardDetail"));
const GradecardFill = lazy(() => import("./pages/GradecardFill"));
const Admin = lazy(() => import("./pages/Admin"));
const Maintenance = lazy(() => import("./pages/Maintenance"));
const Readiness = lazy(() => import("./pages/Readiness"));
const Ops = lazy(() => import("./pages/Ops"));
const AircraftMaintenance = lazy(() => import("./pages/AircraftMaintenance"));
const CompleteSortie = lazy(() => import("./pages/CompleteSortie"));
const Logbook = lazy(() => import("./pages/Logbook"));
const BoardIndex = lazy(() => import("./pages/BoardIndex"));
const OpsBoard = lazy(() => import("./board/OpsBoard"));
const MaintenanceBoard = lazy(() => import("./board/MaintenanceBoard"));
const ReadinessBoard = lazy(() => import("./board/ReadinessBoard"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

function RouteFallback() {
  return (
    <div className="min-h-[40vh] flex items-center justify-center">
      <Loading message="Loading…" />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
      <ToastProvider>
      <BrowserRouter>
        <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute />}>
          {/* App shell — renders with sidebar nav */}
          <Route element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="/crew" element={<Crew />} />
            <Route path="/crew/:id" element={<CrewDetail />} />
            <Route path="/aircraft" element={<Aircraft />} />
            <Route path="/aircraft/:id" element={<AircraftDetail />} />
            <Route path="/sorties" element={<Sorties />} />
            <Route path="/sorties/:id" element={<SortieDetail />} />
            <Route path="/sorties/:id/complete" element={<CompleteSortie />} />
            <Route path="/logbook/:personId" element={<Logbook />} />
            <Route element={<RoleRoute roles={["sdo", "co_xo", "admin", "training_officer"]} />}>
              <Route path="/schedule" element={<Schedule />} />
            </Route>
            <Route element={<RoleRoute roles={["sdo", "co_xo", "admin"]} />}>
              <Route path="/ops" element={<Ops />} />
            </Route>
            <Route path="/training" element={<Training />} />
            <Route path="/training/gradecard/:id" element={<GradecardDetail />} />
            <Route path="/training/gradecard/:id/fill" element={<GradecardFill />} />
            <Route path="/readiness" element={<Readiness />} />
            <Route path="/maintenance" element={<Maintenance />} />
            <Route path="/maintenance/:aircraftId" element={<AircraftMaintenance />} />
            <Route path="/board" element={<BoardIndex />} />
            <Route element={<RoleRoute roles={["admin", "co_xo"]} />}>
              <Route path="/admin" element={<Admin />} />
            </Route>
          </Route>

          {/* TV board views — fullscreen, no sidebar */}
          <Route path="/board/ops" element={<OpsBoard />} />
          <Route path="/board/maint" element={<MaintenanceBoard />} />
          <Route path="/board/readiness" element={<ReadinessBoard />} />
          </Route>
        </Routes>
        </Suspense>
      </BrowserRouter>
      </ToastProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
