/** Status / QA-release preview helpers for aircraft maintenance UI. */
import type {
  AircraftInspection,
  AircraftStatus,
  Discrepancy,
  DiscrepancySeverity,
  DiscrepancyWorkStatus,
} from "../../lib/api";

export const STATUS_VARIANT: Record<AircraftStatus, "success" | "warning" | "danger" | "neutral"> = {
  FMC: "success",
  PMC: "warning",
  NMC: "danger",
  NMCM: "danger",
  NMCS: "danger",
};

export const SEV_VARIANT: Record<DiscrepancySeverity, "neutral" | "warning" | "danger"> = {
  MINOR: "neutral",
  MAJOR: "warning",
  DOWNING: "danger",
};

export const WS_VARIANT: Record<
  DiscrepancyWorkStatus,
  "neutral" | "warning" | "danger" | "success" | "info"
> = {
  OPEN: "danger",
  IN_WORK: "info",
  AWP: "warning",
  AWM: "warning",
  COMPLETED: "success",
  CLOSED: "neutral",
};

export const WS_LABEL: Record<DiscrepancyWorkStatus, string> = {
  OPEN: "Open",
  IN_WORK: "In Work",
  AWP: "AWP",
  AWM: "AWM",
  COMPLETED: "Completed",
  CLOSED: "Closed",
};

export const NON_RELEASE: AircraftStatus[] = ["NMC", "NMCM", "NMCS"];

/** Mirror backend compute_status rules for QA release preview. */
export function previewComputedStatus(
  openDiscs: Discrepancy[],
  overdueDowningInspections: AircraftInspection[]
): AircraftStatus {
  if (openDiscs.some((d) => d.severity === "DOWNING" && d.work_status === "AWP")) return "NMCS";
  if (openDiscs.some((d) => d.severity === "DOWNING")) return "NMCM";
  if (overdueDowningInspections.length > 0) return "NMCM";
  if (openDiscs.some((d) => d.severity === "MAJOR")) return "PMC";
  return "FMC";
}

export function collectReleaseBlockers(
  openDiscs: Discrepancy[],
  overdueDowningInspections: AircraftInspection[]
): string[] {
  const blockers: string[] = [];
  for (const d of openDiscs.filter((x) => x.severity === "DOWNING")) {
    blockers.push(`Open DOWNING discrepancy ${d.maf_number ?? `#${d.id}`}`);
  }
  for (const insp of overdueDowningInspections) {
    blockers.push(`Overdue downing inspection: ${insp.inspection_type.name}`);
  }
  const computed = previewComputedStatus(openDiscs, overdueDowningInspections);
  if (NON_RELEASE.includes(computed)) {
    blockers.push(
      `Computed status is ${computed} — not safe for flight until maintenance is complete`
    );
  }
  return blockers;
}
