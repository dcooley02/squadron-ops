import axios from "axios";

export const api = axios.create({
  baseURL: "http://localhost:8001",
  headers: { "Content-Type": "application/json" },
});

// ---------- Type definitions matching the backend schemas ----------

export type Role =
  | "pilot" | "aircrew" | "sdo"
  | "training_officer" | "maint_control" | "co_xo" | "admin";

export type AircraftStatus = "FMC" | "PMC" | "NMC" | "NMCM" | "NMCS";

export type CrewPosition =
  | "HAC" | "H2P" | "H2P_U" | "CREW_CHIEF" | "AIRCREW" | "AWS";

export type DiscrepancySeverity = "MINOR" | "MAJOR" | "DOWNING";
export type DiscrepancyWorkStatus = "OPEN" | "IN_WORK" | "AWP" | "AWM" | "COMPLETED" | "CLOSED";

export interface PersonSummary {
  id: number;
  last_name: string;
  first_name: string;
  callsign: string | null;
  rank: string | null;
  role: Role;
  is_active: boolean;
}

export interface QualificationOut {
  id: number;
  qual_code: string;
  qualified_date: string | null;
  expires_date: string | null;
}

export interface CurrencyTypeOut {
  id: number;
  code: string;
  name: string;
  periodicity_days: number;
}

export interface CurrencyOut {
  id: number;
  currency_code: string;
  last_event_date: string | null;
  expires_date: string | null;
  currency_type?: CurrencyTypeOut | null;
}

export interface PersonDetail extends PersonSummary {
  qualifications: QualificationOut[];
  currencies: CurrencyOut[];
}

export interface AircraftSummary {
  id: number;
  bureau_number: string;
  side_number: string | null;
  type_model_series: string;
  total_airframe_hours: number;
  hours_since_phase: number;
  phase_interval: number;
  status: AircraftStatus;
}

export interface Discrepancy {
  id: number;
  aircraft_id: number;
  sortie_id?: number | null;
  description: string;
  severity: DiscrepancySeverity;
  work_status: DiscrepancyWorkStatus;
  maf_number?: string | null;
  system_affected?: string | null;
  corrective_action?: string | null;
  notes?: string | null;
  is_open: boolean;
  opened_date: string;
  closed_date?: string | null;
}

// backward compat alias
export type DiscrepancyOut = Discrepancy;

export interface InspectionType {
  id: number;
  code: string;
  name: string;
  periodicity_days?: number | null;
  periodicity_hours?: number | null;
  description?: string | null;
  is_downing_when_overdue: boolean;
}

export interface AircraftInspection {
  id: number;
  aircraft_id: number;
  inspection_type_id: number;
  inspection_type: InspectionType;
  last_completed_date?: string | null;
  last_completed_hours?: number | null;
  next_due_date?: string | null;
  next_due_hours?: number | null;
  last_completion_notes?: string | null;
  is_overdue: boolean;
}

export interface AircraftDetail extends AircraftSummary {
  open_discrepancies: Discrepancy[];
  manual_status_override?: AircraftStatus | null;
  computed_status: AircraftStatus;
  hours_to_phase: number;
}

export interface InstrumentApproachOut {
  id: number;
  approach_type: string;
  actual_or_simulated: "ACTUAL" | "SIMULATED";
  airport_icao: string | null;
  runway: string | null;
  remarks: string | null;
  logged_at: string;
}

export interface FlightLogOut {
  id: number;
  person_id: number;
  person_name: string;
  crew_position: CrewPosition;
  hours_logged: number;
  syllabus_event_completed: string | null;
  // Optional richer fields returned by /api/sorties/{id}; not always present on other endpoints
  instructor_remarks?: string | null;
  crew_qual_code?: string | null;
  data_provenance?: "BACKFILLED" | "ENTERED" | null;
  total_hours?: number | null;
  first_pilot_hours?: number | null;
  copilot_hours?: number | null;
  ac_commander_hours?: number | null;
  mission_commander_hours?: number | null;
  instructor_hours?: number | null;
  special_crew_time_hours?: number | null;
  night_hours?: number | null;
  nvg_hours?: number | null;
  actual_instrument_hours?: number | null;
  sim_instrument_hours?: number | null;
  nvg_unaided_hl_hours?: number | null;
  nvg_unaided_ll_hours?: number | null;
  nvg_tactical_hl_hours?: number | null;
  nvg_tactical_ll_hours?: number | null;
  instrument_approaches?: InstrumentApproachOut[];
}

export interface SortieTmrCodeOut {
  code: string;
  description: string | null;
  slot: number;
  hours: number | null;
}

export interface SortieSummary {
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
}

export interface SortieTaskCredit {
  id: number;
  task_code: string;
  grade: string | null;
  remarks: string | null;
  person_id: number;
  person_name: string;
}

export interface SortieDetail extends SortieSummary {
  day_hours: number | null;
  night_hours: number | null;
  nvg_hours: number | null;
  instrument_hours: number | null;
  debrief_notes: string | null;
  notes: string | null;
  flight_mode: string;
  // Activity quantities
  rounds_fired_20mm: number | null;
  ugr_fired: number | null;
  csw_rounds: number | null;
  csw_rounds_night: number | null;
  landings_day: number | null;
  landings_night: number | null;
  landings_dve_day: number | null;
  landings_dve_night: number | null;
  hoist_streams: number | null;
  hoist_recoveries: number | null;
  amns_iterations: number | null;
  almds_hours: number | null;
  amns_ntrs: number | null;
  strafe_dry_profiles_day: number | null;
  strafe_dry_profiles_night: number | null;
  flight_logs: FlightLogOut[];
  task_credits: SortieTaskCredit[];
  tmr_codes?: SortieTmrCodeOut[] | null;
}

export interface DashboardSummary {
  total_personnel: number;
  total_pilots: number;
  total_aircrew: number;
  aircraft_total: number;
  aircraft_fmc_count: number;
  aircraft_pmc_count: number;
  aircraft_nmc_count: number;
  fmc_rate: number;
  open_discrepancies_count: number;
  currencies_expiring_14d_count: number;
  currencies_expired_count: number;
  sorties_last_30_days: number;
  total_hours_last_30_days: number;
}

// ---------- API functions ----------

export const fetchDashboardSummary = async (): Promise<DashboardSummary> => {
  const { data } = await api.get<DashboardSummary>("/api/dashboard/summary");
  return data;
};

export const fetchPersons = async (role?: string): Promise<PersonSummary[]> => {
  const { data } = await api.get<PersonSummary[]>("/api/persons", {
    params: role ? { role } : undefined,
  });
  return data;
};

export const fetchPerson = async (id: number): Promise<PersonDetail> => {
  const { data } = await api.get<PersonDetail>(`/api/persons/${id}`);
  return data;
};

export const fetchAircraft = async (status?: string): Promise<AircraftSummary[]> => {
  const { data } = await api.get<AircraftSummary[]>("/api/aircraft", {
    params: status ? { status } : undefined,
  });
  return data;
};

export const fetchAircraftDetail = async (id: number): Promise<AircraftDetail> => {
  const { data } = await api.get<AircraftDetail>(`/api/aircraft/${id}`);
  return data;
};

export const fetchSorties = async (
  params?: { date_from?: string; date_to?: string; limit?: number }
): Promise<SortieSummary[]> => {
  const { data } = await api.get<SortieSummary[]>("/api/sorties", { params });
  return data;
};

export const fetchSortie = async (id: number): Promise<SortieDetail> => {
  const { data } = await api.get<SortieDetail>(`/api/sorties/${id}`);
  return data;
};

export interface CbrTaskOption {
  id: number;
  code: string;
  capability_area: string;
  description: string;
  crew_scope: string;
  sim_eligible: boolean;
  is_active: boolean;
}

export interface SortieCompletePayload {
  actual_takeoff_time: string;
  actual_land_time: string;
  duration_hours: number;
  day_hours: number;
  night_hours: number;
  nvg_hours: number;
  instrument_hours: number;
  debrief_notes?: string | null;
  rounds_fired_20mm?: number | null;
  ugr_fired?: number | null;
  csw_rounds?: number | null;
  csw_rounds_night?: number | null;
  landings_day?: number | null;
  landings_night?: number | null;
  landings_dve_day?: number | null;
  landings_dve_night?: number | null;
  hoist_streams?: number | null;
  hoist_recoveries?: number | null;
  amns_iterations?: number | null;
  almds_hours?: number | null;
  amns_ntrs?: number | null;
  strafe_dry_profiles_day?: number | null;
  strafe_dry_profiles_night?: number | null;
  flight_log_actuals: Array<{ flight_log_id: number; hours_logged: number }>;
  task_credits?: Array<{
    task_code: string;
    person_ids: number[];
    grade?: string | null;
    remarks?: string | null;
  }>;
  new_discrepancies?: Array<{
    description: string;
    severity: string;
    system_affected?: string | null;
    notes?: string | null;
  }>;
  safety_reports?: Array<{
    severity: string;
    category?: string | null;
    description: string;
    actions_taken?: string | null;
  }>;
}

export const fetchCbrTaskOptions = async (): Promise<CbrTaskOption[]> => {
  const { data } = await api.get<CbrTaskOption[]>("/api/logging/tasks/options");
  return data;
};

export const completeSortie = async (
  sortieId: number,
  payload: SortieCompletePayload
): Promise<SortieDetail> => {
  const { data } = await api.post<SortieDetail>(
    `/api/logging/sorties/${sortieId}/complete`,
    payload
  );
  return data;
};

// ---------- Scheduling types ----------

export interface FitnessWarning {
  severity: "red" | "yellow";
  message: string;
  target: string;
}

export interface SortieFitness {
  overall_status: "green" | "yellow" | "red";
  warnings: FitnessWarning[];
}

export interface EligibleCrewmember {
  person_id: number;
  last_name: string;
  first_name: string;
  callsign?: string | null;
  rank?: string | null;
  score: number;
  reasons: string[];
}

export interface SortieCreate {
  event_type?: string;
  event_code?: string;
  aircraft_id?: number;
  brief_time?: string;
  takeoff_time: string;
  land_time?: string;
  duration_hours?: number;
  day_hours?: number;
  night_hours?: number;
  nvg_hours?: number;
  instrument_hours?: number;
  notes?: string;
}

export interface FlightLogCreate {
  person_id: number;
  crew_position: CrewPosition;
  hours_logged?: number;
  syllabus_event_completed?: string;
}

// ---------- Scheduling API functions ----------

export const fetchUpcomingSorties = async (): Promise<SortieSummary[]> => {
  const { data } = await api.get<SortieSummary[]>("/api/scheduling/sorties/upcoming");
  return data;
};

export const fetchSortieFitness = async (id: number): Promise<SortieFitness> => {
  const { data } = await api.get<SortieFitness>(`/api/scheduling/sorties/${id}/fitness`);
  return data;
};

export const fetchEligibleCrew = async (
  sortieId: number,
  crewPosition: CrewPosition
): Promise<EligibleCrewmember[]> => {
  const { data } = await api.get<EligibleCrewmember[]>(
    `/api/scheduling/sorties/${sortieId}/eligible-crew`,
    { params: { crew_position: crewPosition } }
  );
  return data;
};

export const createSortie = async (payload: SortieCreate): Promise<SortieSummary> => {
  const { data } = await api.post<SortieSummary>("/api/scheduling/sorties", payload);
  return data;
};

export const assignCrew = async (
  sortieId: number,
  payload: FlightLogCreate
): Promise<FlightLogOut> => {
  const { data } = await api.post<FlightLogOut>(
    `/api/scheduling/sorties/${sortieId}/crew`,
    payload
  );
  return data;
};

export const removeCrew = async (sortieId: number, flightLogId: number): Promise<void> => {
  await api.delete(`/api/scheduling/sorties/${sortieId}/crew/${flightLogId}`);
};

export const deleteSortie = async (id: number): Promise<void> => {
  await api.delete(`/api/scheduling/sorties/${id}`);
};

// ---------- Syllabus / Training types ----------

export type SyllabusTrack = "PILOT_CORE" | "PILOT_AMCM" | "AIRCREW_CORE" | "AIRCREW_AMCM";
export type GradingScheme = "FOUR_TIER" | "COMPLETION";
export type GradecardStatus = "PASS" | "CONDITIONAL_PASS" | "UNSAT" | "COMPLETE" | "INCOMPLETE" | "IN_PROGRESS";
export type CompletionStatus = "COMPLETE" | "INCOMPLETE";
export type FourTierScore = "UNSAT_1_0" | "BELOW_STANDARD_2_0" | "STANDARD_3_0" | "EXCEPTIONAL_4_0";

export interface SyllabusEventOut {
  id: number;
  code: string;
  name: string;
  event_code: string | null;
  stage_legacy: string | null;
  track: SyllabusTrack | null;
  is_stan_eval: boolean;
  grading_scheme: GradingScheme | null;
  time_hours: number | null;
  description: string | null;
}

export interface GradecardSummary {
  id: number;
  event_code: string | null;
  person_name: string;
  card_date: string;
  overall_status: GradecardStatus;
  grading_scheme: GradingScheme;
}

export interface GradecardLineItemTemplate {
  id: number;
  section: string;
  item_name: string;
  role: string | null;
  is_critical: boolean;
  is_required: boolean;
  display_order: number;
  mop_below_standard?: string | null;
  mop_standard?: string | null;
}

export interface GradecardLineItemResultOut {
  id: number;
  line_item_id: number;
  waived: boolean;
  completion_status: CompletionStatus | null;
  four_tier_score: FourTierScore | null;
  remarks: string | null;
  line_item: GradecardLineItemTemplate;
}

// Alias used in fill workflow
export type GradecardLineItemResult = GradecardLineItemResultOut;

export interface GradecardOut {
  id: number;
  person_id: number;
  syllabus_event_id: number;
  sortie_id: number | null;
  flight_log_id: number | null;
  instructor_person_id: number | null;
  card_date: string;
  grading_scheme: GradingScheme;
  overall_status: GradecardStatus;
  remarks: string | null;
  line_item_results: GradecardLineItemResultOut[];
  created_at: string;
  updated_at: string;
}

// ---------- Currency types ----------

export interface CurrencyApplicabilityOut {
  applies_to: string;
  required_qualification: string | null;
}

export interface CurrencyTypeOut {
  id: number;
  code: string;
  name: string;
  periodicity_days: number;
  requirement_text: string;
  description: string | null;
  sim_eligible: boolean;
  min_hours: number | null;
  min_count: number | null;
  count_unit: string | null;
  is_active: boolean;
  applicability: CurrencyApplicabilityOut[];
}

// ---------- Syllabus / Training API functions ----------

export const fetchSyllabusEvents = async (
  params?: { track?: string; is_stan_eval?: boolean }
): Promise<SyllabusEventOut[]> => {
  const { data } = await api.get<SyllabusEventOut[]>("/api/syllabus/events", { params });
  return data;
};

export const fetchPersonGradecards = async (personId: number): Promise<GradecardSummary[]> => {
  const { data } = await api.get<GradecardSummary[]>(`/api/syllabus/persons/${personId}/gradecards`);
  return data;
};

export const fetchGradecard = async (id: number): Promise<GradecardOut> => {
  const { data } = await api.get<GradecardOut>(`/api/syllabus/gradecards/${id}`);
  return data;
};

export const createBlankGradecard = async (body: {
  person_id: number;
  syllabus_event_id: number;
  instructor_person_id?: number | null;
  card_date: string;
  remarks?: string | null;
}): Promise<GradecardOut> => {
  const { data } = await api.post<GradecardOut>("/api/syllabus/gradecards/blank", body);
  return data;
};

export const patchGradecardLineItem = async (
  gradecardId: number,
  resultId: number,
  body: {
    four_tier_score?: FourTierScore | null;
    completion_status?: CompletionStatus | null;
    remarks?: string | null;
    waived?: boolean;
  }
): Promise<GradecardLineItemResultOut> => {
  const { data } = await api.patch<GradecardLineItemResultOut>(
    `/api/syllabus/gradecards/${gradecardId}/line-items/${resultId}`,
    body
  );
  return data;
};

export const patchGradecard = async (
  gradecardId: number,
  body: {
    overall_status?: GradecardStatus;
    remarks?: string | null;
    instructor_person_id?: number | null;
    card_date?: string;
  }
): Promise<GradecardOut> => {
  const { data } = await api.patch<GradecardOut>(`/api/syllabus/gradecards/${gradecardId}`, body);
  return data;
};

export const fetchEligibleInstructors = async (eventId: number): Promise<PersonSummary[]> => {
  const { data } = await api.get<PersonSummary[]>(`/api/syllabus/events/${eventId}/instructors`);
  return data;
};

// ---------- Currency API functions ----------

export const fetchCurrencyTypes = async (): Promise<CurrencyTypeOut[]> => {
  const { data } = await api.get<CurrencyTypeOut[]>("/api/currency/types");
  return data;
};

export const fetchPersonApplicableCurrencies = async (personId: number): Promise<CurrencyTypeOut[]> => {
  const { data } = await api.get<CurrencyTypeOut[]>(`/api/currency/types/applicable-to/${personId}`);
  return data;
};

// ---------- Maintenance API functions ----------

export const fetchAircraftInspections = async (aircraftId: number): Promise<AircraftInspection[]> => {
  const { data } = await api.get<AircraftInspection[]>(
    `/api/maintenance/aircraft/${aircraftId}/inspections`
  );
  return data;
};

export const fetchAircraftDiscrepancies = async (
  aircraftId: number,
  openOnly?: boolean
): Promise<Discrepancy[]> => {
  const { data } = await api.get<Discrepancy[]>(
    `/api/maintenance/aircraft/${aircraftId}/discrepancies`,
    { params: openOnly ? { open_only: true } : undefined }
  );
  return data;
};

export const patchDiscrepancy = async (
  id: number,
  body: { work_status?: DiscrepancyWorkStatus; corrective_action?: string; system_affected?: string }
): Promise<Discrepancy> => {
  const { data } = await api.patch<Discrepancy>(`/api/maintenance/discrepancies/${id}`, body);
  return data;
};

export interface TrainingJacketEntry {
  sortie_id: number;
  sortie_date: string;
  event_code: string | null;
  event_type: string | null;
  flight_mode: string | null;
  crew_position: CrewPosition;
  hours_logged: number;
  instructor_remarks: string | null;
  syllabus_event_completed: string | null;
  task_credits: Array<{ task_code: string; grade: string | null; remarks: string | null }>;
}

export const fetchPersonTrainingJacket = async (personId: number): Promise<TrainingJacketEntry[]> => {
  const { data } = await api.get<TrainingJacketEntry[]>(
    `/api/logging/persons/${personId}/training-jacket`
  );
  return data;
};

export type SafetyReportSeverity = "INFO" | "HAZARD" | "INCIDENT" | "MISHAP";
export type SafetyReportStatus = "OPEN" | "UNDER_REVIEW" | "CLOSED";

export interface SafetyReport {
  id: number;
  sortie_id: number | null;
  reported_by_person_id: number | null;
  severity: SafetyReportSeverity;
  category: string | null;
  description: string;
  actions_taken: string | null;
  status: SafetyReportStatus;
  created_at: string;
  closed_at: string | null;
}

export const fetchSafetyReportsForSortie = async (
  sortieId: number
): Promise<SafetyReport[]> => {
  const { data } = await api.get<SafetyReport[]>("/api/logging/safety/reports", {
    params: { sortie_id: sortieId },
  });
  return data;
};

export const fetchAircraftAdb = async (aircraftId: number): Promise<Discrepancy[]> => {
  const { data } = await api.get<Discrepancy[]>(
    `/api/logging/aircraft/${aircraftId}/adb`
  );
  return data;
};

export const patchInspection = async (
  aircraftId: number,
  inspectionId: number,
  body: {
    last_completed_date?: string;
    last_completed_hours?: number;
    last_completion_notes?: string;
  }
): Promise<AircraftInspection> => {
  const { data } = await api.patch<AircraftInspection>(
    `/api/maintenance/aircraft/${aircraftId}/inspections/${inspectionId}`,
    body
  );
  return data;
};