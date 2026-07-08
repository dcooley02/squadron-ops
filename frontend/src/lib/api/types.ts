/** Hand-maintained API types matching backend Pydantic schemas.
 *  See `scripts/generate-api-types.md` for optional OpenAPI generation.
 */

export type Role =
  | "pilot" | "aircrew" | "sdo"
  | "training_officer" | "maint_control" | "co_xo" | "admin";

export interface UserMe {
  id: number;
  username: string;
  last_name: string;
  first_name: string;
  callsign: string | null;
  rank: string | null;
  role: Role;
}

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
  // CNAF M-4790.2
  type_wo_code?: string | null;
  jcn?: string | null;
  reported_by_name?: string | null;
  work_order_id?: number | null;
  work_center_code?: string | null;
  has_qa_signoff?: boolean;
}

export interface WorkCenter {
  id: number;
  code: string;
  name: string;
  description: string | null;
}

export interface WorkOrder {
  id: number;
  jcn: string;
  type_wo_code: string;
  aircraft_id: number;
  maf_id: number | null;
  discrepancy_id: number | null;
  work_center_id: number | null;
  work_center_code: string | null;
  work_center_name: string | null;
  status: DiscrepancyWorkStatus;
  corrective_action: string | null;
  opened_date: string;
  assigned_at: string | null;
  completed_at: string | null;
  maf_number: string | null;
  has_qa_signoff: boolean;
}

export interface LogbookEntry {
  id: number;
  aircraft_id: number;
  entry_type: string;
  entry_date: string;
  hours_at_entry: number | null;
  title: string;
  description: string | null;
  work_order_id: number | null;
  sortie_id: number | null;
  created_by_name: string | null;
}

export interface PhaseForecastRow {
  aircraft_id: number;
  side_number: string | null;
  hours_since_phase: number;
  hours_to_phase: number;
  weekly_flight_hours_assumed: number;
  projected_phase_date: string | null;
}

export interface ReleaseForecast {
  aircraft_id: number;
  computed_status: string;
  blockers: string[];
  projected_release_date: string | null;
  open_discrepancy_count: number;
  open_work_order_count: number;
}

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
  // Per-crewmember landings (B1)
  landings_day?: number;
  landings_night?: number;
  landings_dve_day?: number;
  landings_dve_night?: number;
  landings_shipboard_day?: number;
  landings_shipboard_night?: number;
  instrument_approaches?: InstrumentApproachOut[];
}

export interface SortieTmrCodeOut {
  code: string;
  description: string | null;
  slot: number;
  hours: number | null;
}

export type SortieOpsStatus =
  | "PLANNED" | "PUBLISHED" | "BRIEFED" | "MANNED"
  | "AIRBORNE" | "RECOVERED" | "DEBRIEFED";

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
  ops_status?: SortieOpsStatus;
  mission_summary?: string | null;
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
  comm_plan?: string | null;
  brief_sheet_notes?: string | null;
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

export interface CbrTaskOption {
  id: number;
  code: string;
  capability_area: string;
  description: string;
  crew_scope: string;
  sim_eligible: boolean;
  is_active: boolean;
}

export interface FlightLogActualsPayload {
  flight_log_id: number;
  hours_logged: number;
  night_hours?: number;
  nvg_hours?: number;
  actual_instrument_hours?: number;
  sim_instrument_hours?: number;
  total_hours?: number;
  first_pilot_hours?: number;
  copilot_hours?: number;
  ac_commander_hours?: number;
  mission_commander_hours?: number;
  instructor_hours?: number;
  special_crew_time_hours?: number;
  syllabus_event_completed?: string | null;
  landings_day?: number | null;
  landings_night?: number | null;
  landings_dve_day?: number | null;
  landings_dve_night?: number | null;
  landings_shipboard_day?: number | null;
  landings_shipboard_night?: number | null;
}

export interface SortieCompletePayload {
  actual_takeoff_time: string;
  actual_land_time: string;
  duration_hours: number;
  flight_mode?: "LIVE" | "SIM_TOFT";
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
  flight_log_actuals: FlightLogActualsPayload[];
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

export interface CrewSuggestionSlot {
  crew_position: CrewPosition;
  suggestions: EligibleCrewmember[];
  recommended_person_id: number | null;
}

export interface SuggestCrewResponse {
  sortie_id: number;
  slots: CrewSuggestionSlot[];
  conflicts: FitnessWarning[];
}

export interface ProposedCrewAssignment {
  crew_position: CrewPosition;
  person_id: number;
  last_name: string;
  first_name: string;
  reasons: string[];
}

export interface ProposedSortie {
  stub_index: number;
  event_type: string | null;
  event_code: string | null;
  aircraft_id: number | null;
  takeoff_time: string;
  duration_hours: number | null;
  suggested_crew: ProposedCrewAssignment[];
  warnings: FitnessWarning[];
}

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

export interface AuditLogEntry {
  id: number;
  ts: string;
  actor: string | null;
  method: string;
  path: string;
  query_string: string | null;
  response_status: number;
  request_body: unknown;
  client_host: string | null;
  duration_ms: number | null;
}

export interface QaReleasePayload {
  qa_notes: string;
  close_discrepancy_ids?: number[];
  corrective_action?: string;
}

export interface QaReleaseError {
  message: string;
  blockers: string[];
}

export type CapabilityArea = "MOB" | "FSO" | "ASU" | "SOF" | "PR" | "STW" | "LOG" | "MIW";

export type TRating = "T-1" | "T-2" | "T-3";

export interface AnchorTaskStatus {
  task_code: string;
  status: string;
  days_since: number | null;
}

export interface PersonAreaRating {
  capability_area: CapabilityArea;
  label: string;
  rating: TRating;
  contributing_factors: string[];
  anchor_tasks: AnchorTaskStatus[];
  t1_window_days?: number;
  t2_window_days?: number;
}

export interface PersonReadinessSummary {
  person_id: number;
  person_name: string;
  callsign: string | null;
  role: Role;
  overall_rating: TRating;
  areas: PersonAreaRating[];
}

export interface SquadronAreaSummary {
  capability_area: CapabilityArea;
  label: string;
  squadron_rating: TRating;
  t1_count: number;
  t2_count: number;
  t3_count: number;
  pilots_rated: number;
}

export interface SquadronReadiness {
  as_of_date: string;
  pilots_rated: number;
  aircrew_rated: number;
  squadron_overall_rating: TRating;
  aircrew_overall_rating: TRating | null;
  areas: SquadronAreaSummary[];
  persons: PersonReadinessSummary[];
  aircrew: PersonReadinessSummary[];
}

export type BoardType = "HAC_BOARD" | "INSTRUCTOR_BOARD" | "NATOPS_CHECK" | "STAN_EVAL";

export type BoardStatus = "SCHEDULED" | "COMPLETED" | "CANCELLED";

export interface BoardSchedule {
  id: number;
  board_type: BoardType;
  scheduled_at: string;
  examinee_person_id: number;
  examinee_name: string;
  instructor_person_id: number | null;
  instructor_name: string | null;
  syllabus_event_id: number | null;
  event_code: string | null;
  status: BoardStatus;
  location: string | null;
  remarks: string | null;
}

export interface InstructorCandidate {
  person_id: number;
  person_name: string;
  callsign: string | null;
  rank: string | null;
  score: number;
  factors: string[];
}

export interface SyllabusProgressEntry {
  syllabus_event_id: number;
  event_code: string | null;
  name: string;
  track: string | null;
  level: string | null;
  status: "NOT_STARTED" | "IN_PROGRESS" | "COMPLETE";
  gradecard_id: number | null;
  is_stan_eval: boolean;
}

export type WatchbillRole = "SDO" | "ODO" | "DUTY_PILOT" | "DUTY_AIRCREW" | "ALERT";

export interface DayOpsSortie {
  id: number;
  event_code: string | null;
  event_type: string | null;
  aircraft_side_number: string | null;
  brief_time: string | null;
  takeoff_time: string | null;
  land_time: string | null;
  ops_status: SortieOpsStatus;
  is_complete: boolean;
  mission_summary: string | null;
  comm_plan: string | null;
  crew: Array<{ person_id: number; person_name: string; crew_position: string }>;
}

export interface DayOps {
  ops_date: string;
  is_published: boolean;
  publication: {
    id: number;
    schedule_date: string;
    published_at: string;
    published_by_name: string | null;
    remarks: string | null;
  } | null;
  watchbill: Array<{
    id: number;
    duty_date: string;
    role: WatchbillRole;
    person_id: number;
    person_name: string;
    shift_label: string | null;
    notes: string | null;
  }>;
  sorties: DayOpsSortie[];
  sortie_count: number;
  airborne_count: number;
}
