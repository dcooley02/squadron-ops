/** Syllabus / gradecard API */
import { api } from "./client";
import type {
  CompletionStatus,
  FourTierScore,
  GradecardLineItemResultOut,
  GradecardOut,
  GradecardStatus,
  GradecardSummary,
  PersonSummary,
  SyllabusEventOut,
  SyllabusProgressEntry,
} from "./types";

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

export const fetchEligibleInstructors = async (eventId: number): Promise<PersonSummary[]> => {
  const { data } = await api.get<PersonSummary[]>(`/api/syllabus/events/${eventId}/instructors`);
  return data;
};

export const fetchGradecard = async (id: number): Promise<GradecardOut> => {
  const { data } = await api.get<GradecardOut>(`/api/syllabus/gradecards/${id}`);
  return data;
};

export const fetchPersonGradecards = async (personId: number): Promise<GradecardSummary[]> => {
  const { data } = await api.get<GradecardSummary[]>(`/api/syllabus/persons/${personId}/gradecards`);
  return data;
};

export const fetchSyllabusEvents = async (
  params?: { track?: string; is_stan_eval?: boolean }
): Promise<SyllabusEventOut[]> => {
  const { data } = await api.get<SyllabusEventOut[]>("/api/syllabus/events", { params });
  return data;
};

export const fetchSyllabusProgress = async (
  personId: number
): Promise<SyllabusProgressEntry[]> => {
  const { data } = await api.get<SyllabusProgressEntry[]>(
    `/api/syllabus/persons/${personId}/progress`
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

