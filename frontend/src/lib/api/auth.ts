/** Auth API */
import { api } from "./client";
import type { UserMe } from "./types";

export const fetchMe = async (): Promise<UserMe> => {
  const { data } = await api.get<UserMe>("/api/auth/me");
  return data;
};

export const login = async (username: string, password: string): Promise<{ access_token: string }> => {
  const { data } = await api.post<{ access_token: string; token_type: string }>("/api/auth/login", {
    username,
    password,
  });
  return data;
};

