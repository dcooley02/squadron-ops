/** WTM readiness API */
import { api } from "./client";
import type { PersonReadinessSummary, SquadronReadiness } from "./types";

export const fetchPersonReadiness = async (
  personId: number
): Promise<PersonReadinessSummary> => {
  const { data } = await api.get<PersonReadinessSummary>(
    `/api/readiness/persons/${personId}`
  );
  return data;
};

export const fetchSquadronReadiness = async (): Promise<SquadronReadiness> => {
  const { data } = await api.get<SquadronReadiness>("/api/readiness/squadron");
  return data;
};

