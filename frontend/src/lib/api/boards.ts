/** Training boards API */
import { api } from "./client";
import type { BoardSchedule, BoardType, InstructorCandidate } from "./types";

export const createBoardSchedule = async (
  payload: {
    board_type: BoardType;
    scheduled_at: string;
    examinee_person_id: number;
    instructor_person_id?: number;
    syllabus_event_id?: number;
    location?: string;
    remarks?: string;
  }
): Promise<BoardSchedule> => {
  const { data } = await api.post<BoardSchedule>("/api/boards", payload);
  return data;
};

export const fetchBoardSchedules = async (): Promise<BoardSchedule[]> => {
  const { data } = await api.get<BoardSchedule[]>("/api/boards");
  return data;
};

export const fetchInstructorCandidates = async (params: {
  board_type: BoardType;
  examinee_person_id: number;
  scheduled_at: string;
  syllabus_event_id?: number;
}): Promise<InstructorCandidate[]> => {
  const { data } = await api.get<InstructorCandidate[]>("/api/boards/instructor-candidates", {
    params,
  });
  return data;
};

