import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Crew from "./pages/Crew";
import CrewDetail from "./pages/CrewDetail";
import Aircraft from "./pages/Aircraft";
import AircraftDetail from "./pages/AircraftDetail";
import Sorties from "./pages/Sorties";
import SortieDetail from "./pages/SortieDetail";
import Schedule from "./pages/Schedule";
import Training from "./pages/Training";
import GradecardDetail from "./pages/GradecardDetail";
import GradecardFill from "./pages/GradecardFill";
import Admin from "./pages/Admin";
import Maintenance from "./pages/Maintenance";
import AircraftMaintenance from "./pages/AircraftMaintenance";
import CompleteSortie from "./pages/CompleteSortie";
import Logbook from "./pages/Logbook";
import BoardIndex from "./pages/BoardIndex";
import OpsBoard from "./board/OpsBoard";
import MaintenanceBoard from "./board/MaintenanceBoard";
import ReadinessBoard from "./board/ReadinessBoard";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
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
            <Route path="/schedule" element={<Schedule />} />
            <Route path="/training" element={<Training />} />
            <Route path="/training/gradecard/:id" element={<GradecardDetail />} />
            <Route path="/training/gradecard/:id/fill" element={<GradecardFill />} />
            <Route path="/maintenance" element={<Maintenance />} />
            <Route path="/maintenance/:aircraftId" element={<AircraftMaintenance />} />
            <Route path="/board" element={<BoardIndex />} />
            <Route path="/admin" element={<Admin />} />
          </Route>

          {/* TV board views — fullscreen, no sidebar */}
          <Route path="/board/ops" element={<OpsBoard />} />
          <Route path="/board/maint" element={<MaintenanceBoard />} />
          <Route path="/board/readiness" element={<ReadinessBoard />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
