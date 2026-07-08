/** Currency catalog API */
import { api } from "./client";
import type { CurrencyTypeOut } from "./types";

export const fetchCurrencyTypes = async (): Promise<CurrencyTypeOut[]> => {
  const { data } = await api.get<CurrencyTypeOut[]>("/api/currency/types");
  return data;
};

export const fetchPersonApplicableCurrencies = async (personId: number): Promise<CurrencyTypeOut[]> => {
  const { data } = await api.get<CurrencyTypeOut[]>(`/api/currency/types/applicable-to/${personId}`);
  return data;
};

