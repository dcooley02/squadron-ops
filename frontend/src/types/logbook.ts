// TypeScript mirrors of backend Pydantic schemas in app/schemas/logging.py
// and app/schemas/sorties.py (for the detail modal).

// ── Logbook entry sub-types ──────────────────────────────────────────────────

export interface ApproachEntry {
  type: string;
  conditions: string;
  airport_icao: string | null;
  runway: string | null;
  approach_remarks: string | null;
}

export interface LogbookTmrOut {
  code: string;
  slot: number;
  hours: number | null;
}

// ── Core logbook entry (LogbookEntry in schemas/logging.py) ─────────────────

export interface LogbookEntry {
  sortie_id: number;
  flight_log_id: number;
  date: string; // ISO date "YYYY-MM-DD"
  tms: string | null;
  bureau_number: string | null;
  side_number: string | null;
  event_code: string | null;
  flight_mode: string;
  crew_position: string;
  departure_location: string | null;
  arrival_location: string | null;
  total_hours: number;
  night_hours: number;
  nvg_hours: number;
  actual_instrument_hours: number;
  sim_instrument_hours: number;
  first_pilot_hours: number;
  copilot_hours: number;
  ac_commander_hours: number;
  mission_commander_hours: number;
  instructor_hours: number;
  special_crew_time_hours: number;
  nvg_unaided_hl_hours: number;
  nvg_unaided_ll_hours: number;
  nvg_tactical_hl_hours: number;
  nvg_tactical_ll_hours: number;
  landings_day: number;
  landings_night: number;
  landings_dve_day: number;
  landings_dve_night: number;
  landings_shipboard_day: number;
  landings_shipboard_night: number;
  approaches: ApproachEntry[];
  tmr_codes: LogbookTmrOut[];
  remarks: string | null;
  data_provenance: string | null;
}

// ── Totals (LogbookTotals in schemas/logging.py) ─────────────────────────────

export interface LogbookTotals {
  total_hours: number;
  night_hours: number;
  nvg_hours: number;
  total_actual_instrument_hours: number;
  total_sim_instrument_hours: number;
  total_first_pilot_hours: number;
  total_copilot_hours: number;
  total_ac_commander_hours: number;
  total_mission_commander_hours: number;
  total_instructor_hours: number;
  total_spec_crew_hours: number;
  landings_day: number;
  landings_night: number;
  landings_dve_day: number;
  landings_dve_night: number;
  landings_shipboard_day: number;
  landings_shipboard_night: number;
  approaches_total: number;
  approaches_by_type: Record<string, number>;
  sortie_count: number;
  flight_log_count: number;
  data_provenance_breakdown: Record<string, number>;
}

export interface LogbookWindowTotals {
  career: LogbookTotals;
  last_365d: LogbookTotals;
  last_90d: LogbookTotals;
  last_30d: LogbookTotals;
}

// ── Response wrapper ─────────────────────────────────────────────────────────

export interface LogbookPersonOut {
  id: number;
  name: string; // "{last_name}, {first_name}"
  callsign: string | null;
  rank: string;
  role: string;
}

export interface LogbookFilters {
  date_from?: string; // YYYY-MM-DD
  date_to?: string;
  aircraft_id?: number;
  event_code?: string;
  crew_position?: string;
  flight_mode?: string;
}

export interface LogbookResponse {
  person: LogbookPersonOut;
  filters_applied: {
    date_from: string | null;
    date_to: string | null;
    aircraft_id: number | null;
    event_code: string | null;
    crew_position: string | null;
    flight_mode: string | null;
  };
  entries: LogbookEntry[];
  totals: LogbookWindowTotals;
}

// ── Full sortie detail types (used by LogbookEntryDetail modal) ───────────────
// Mirrors schemas/sorties.py: SortieDetail, FlightLogOut, InstrumentApproachRead,
// SortieLegRead, SortieTaskCreditOut; and schemas/logging.py: SortieTmrOut.

export interface InstrumentApproachDetail {
  id: number;
  approach_type: string;
  actual_or_simulated: string;
  airport_icao: string;
  runway: string | null;
  remarks: string | null;
  logged_at: string;
}

export interface FlightLogFull {
  id: number;
  person_id: number;
  person_name: string;
  crew_position: string;
  hours_logged: number;
  night_hours: number;
  nvg_hours: number;
  actual_instrument_hours: number;
  sim_instrument_hours: number;
  total_hours: number;
  first_pilot_hours: number;
  copilot_hours: number;
  ac_commander_hours: number;
  mission_commander_hours: number;
  instructor_hours: number;
  special_crew_time_hours: number | null;
  syllabus_event_completed: string | null;
  instructor_remarks: string | null;
  data_provenance: string;
  instrument_approaches: InstrumentApproachDetail[];
}

export interface SortieLegDetail {
  id: number;
  leg_number: number;
  departure_location: string;
  arrival_location: string;
  takeoff_time: string | null;
  land_time: string | null;
  duration_hours: number | null;
}

export interface SortieTmrDetail {
  code: string;
  description: string;
  slot: number;
  hours: number | null;
}

export interface SortieDetailFull {
  id: number;
  event_code: string | null;
  event_type: string | null;
  aircraft_id: number | null;
  aircraft_side_number: string | null;
  brief_time: string | null;
  takeoff_time: string | null;
  land_time: string | null;
  duration_hours: number | null;
  is_complete: boolean;
  debrief_notes: string | null;
  notes: string | null;
  flight_mode: string;
  departure_location: string | null;
  arrival_location: string | null;
  landings_day: number | null;
  landings_night: number | null;
  landings_shipboard_day: number | null;
  landings_shipboard_night: number | null;
  legs: SortieLegDetail[];
  flight_logs: FlightLogFull[];
  tmr_codes: SortieTmrDetail[];
  task_credits: Array<{
    id: number;
    task_code: string;
    grade: string | null;
    remarks: string | null;
    person_id: number;
    person_name: string;
  }>;
}
