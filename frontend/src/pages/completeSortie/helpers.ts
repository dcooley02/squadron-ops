/** Pure helpers for the Complete Sortie debrief form. */
import type { FlightLogActualsPayload } from "../../lib/api";

export type FlightMode = "LIVE" | "SIM_TOFT";
export type Severity = "MINOR" | "MAJOR" | "DOWNING";
export type Grade = "Q" | "CQ" | "U" | "NO" | "NG";
export type SafetyLevel = "INFO" | "HAZARD" | "INCIDENT" | "MISHAP";

let _seq = 0;
export const uid = () => String(++_seq);

export interface CrewActual {
  flight_log_id: number;
  person_name: string;
  crew_position: string;
  hours_logged: string;
  night_hours: string;
  nvg_hours: string;
  actual_instrument_hours: string;
  /** Per-crew landings (string inputs for controlled number fields). */
  landings_day: string;
  landings_night: string;
  landings_dve_day: string;
  landings_dve_night: string;
  landings_shipboard_day: string;
  landings_shipboard_night: string;
}

export function roleHoursForPosition(position: string, hours: number) {
  switch (position) {
    case "HAC":
      return { ac_commander_hours: hours, first_pilot_hours: hours };
    case "H2P":
    case "H2P_U":
      return { copilot_hours: hours };
    case "CREW_CHIEF":
    case "AIRCREW":
    case "AWS":
      return { special_crew_time_hours: hours };
    default:
      return {};
  }
}

export const CREW_LANDING_FIELDS = [
  "landings_day",
  "landings_night",
  "landings_dve_day",
  "landings_dve_night",
  "landings_shipboard_day",
  "landings_shipboard_night",
] as const;

export type CrewLandingField = (typeof CREW_LANDING_FIELDS)[number];

export function emptyCrewLandings(): Record<CrewLandingField, string> {
  return {
    landings_day: "",
    landings_night: "",
    landings_dve_day: "",
    landings_dve_night: "",
    landings_shipboard_day: "",
    landings_shipboard_night: "",
  };
}

function parseLanding(value: string): number | null {
  const t = value.trim();
  if (t === "") return null;
  const n = parseInt(t, 10);
  return Number.isFinite(n) ? Math.max(0, n) : null;
}

/** True when any crewmember has a non-empty landing field. */
export function hasPerCrewLandings(crewActuals: CrewActual[]): boolean {
  return crewActuals.some((c) =>
    CREW_LANDING_FIELDS.some((field) => c[field].trim() !== "")
  );
}

export function sumCrewLandings(crewActuals: CrewActual[]): {
  landings_day: number;
  landings_night: number;
  landings_dve_day: number;
  landings_dve_night: number;
  landings_shipboard_day: number;
  landings_shipboard_night: number;
} {
  const sum = (key: keyof CrewActual) =>
    crewActuals.reduce((acc, c) => acc + (parseLanding(String(c[key])) ?? 0), 0);
  return {
    landings_day: sum("landings_day"),
    landings_night: sum("landings_night"),
    landings_dve_day: sum("landings_dve_day"),
    landings_dve_night: sum("landings_dve_night"),
    landings_shipboard_day: sum("landings_shipboard_day"),
    landings_shipboard_night: sum("landings_shipboard_night"),
  };
}

export function buildFlightLogActuals(
  crewActuals: CrewActual[],
  mission: { nightH: string; nvgH: string; instrH: string },
  eventCode: string | null | undefined
): FlightLogActualsPayload[] {
  const perCrew = hasPerCrewLandings(crewActuals);
  return crewActuals.map((c) => {
    const hours = parseFloat(c.hours_logged) || 0;
    const night = parseFloat(c.night_hours) || parseFloat(mission.nightH) || 0;
    const nvg = parseFloat(c.nvg_hours) || parseFloat(mission.nvgH) || 0;
    const instr = parseFloat(c.actual_instrument_hours) || parseFloat(mission.instrH) || 0;
    const row: FlightLogActualsPayload = {
      flight_log_id: c.flight_log_id,
      hours_logged: hours,
      total_hours: hours,
      night_hours: night,
      nvg_hours: nvg,
      actual_instrument_hours: instr,
      syllabus_event_completed: eventCode || null,
      ...roleHoursForPosition(c.crew_position, hours),
    };
    if (perCrew) {
      row.landings_day = parseLanding(c.landings_day) ?? 0;
      row.landings_night = parseLanding(c.landings_night) ?? 0;
      row.landings_dve_day = parseLanding(c.landings_dve_day) ?? 0;
      row.landings_dve_night = parseLanding(c.landings_dve_night) ?? 0;
      row.landings_shipboard_day = parseLanding(c.landings_shipboard_day) ?? 0;
      row.landings_shipboard_night = parseLanding(c.landings_shipboard_night) ?? 0;
    }
    return row;
  });
}

export interface TaskCreditRow {
  _key: string;
  person_id: string;
  task_code: string;
  grade: Grade;
  remarks: string;
}

export interface DiscrepancyRow {
  _key: string;
  description: string;
  severity: Severity;
  system_affected: string;
  notes: string;
}

export interface SafetyRow {
  _key: string;
  severity: SafetyLevel;
  category: string;
  description: string;
  actions_taken: string;
}

export function toInputDT(iso: string | null): string {
  return iso ? iso.slice(0, 16) : "";
}

export function addHoursToStr(dtStr: string, hours: number): string {
  if (!dtStr) return "";
  const [datePart, timePart] = dtStr.split("T");
  const [h, m] = timePart.split(":").map(Number);
  const totalMins = h * 60 + m + Math.round(hours * 60);
  const dayBump = Math.floor(totalMins / 1440);
  const rem = totalMins % 1440;
  const newH = Math.floor(rem / 60);
  const newM = rem % 60;
  let newDate = datePart;
  if (dayBump > 0) {
    const [y, mo, d] = datePart.split("-").map(Number);
    const next = new Date(y, mo - 1, d + dayBump);
    newDate = [
      next.getFullYear(),
      String(next.getMonth() + 1).padStart(2, "0"),
      String(next.getDate()).padStart(2, "0"),
    ].join("-");
  }
  return `${newDate}T${String(newH).padStart(2, "0")}:${String(newM).padStart(2, "0")}`;
}

export function durationBetween(t: string, l: string): number {
  if (!t || !l) return 0;
  const parse = (s: string) => {
    const [date, time] = s.split("T");
    const [y, mo, d] = date.split("-").map(Number);
    const [h, m] = time.split(":").map(Number);
    return new Date(y, mo - 1, d, h, m).getTime();
  };
  const diffH = (parse(l) - parse(t)) / 3_600_000;
  return Math.max(0, Math.round(diffH * 10) / 10);
}
