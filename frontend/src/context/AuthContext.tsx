import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, fetchMe, login as apiLogin, type Role, type UserMe } from "../lib/api";

const TOKEN_KEY = "squadron_ops_token";

interface AuthContextValue {
  user: UserMe | null;
  token: string | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (...roles: Role[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserMe | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [isLoading, setIsLoading] = useState(!!localStorage.getItem(TOKEN_KEY));

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
    delete api.defaults.headers.common.Authorization;
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const { access_token } = await apiLogin(username, password);
    localStorage.setItem(TOKEN_KEY, access_token);
    setToken(access_token);
    api.defaults.headers.common.Authorization = `Bearer ${access_token}`;
    const me = await fetchMe();
    setUser(me);
  }, []);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
    fetchMe()
      .then(setUser)
      .catch(() => logout())
      .finally(() => setIsLoading(false));
  }, [token, logout]);

  const hasRole = useCallback(
    (...roles: Role[]) => {
      if (!user) return false;
      if (user.role === "admin") return true;
      return roles.includes(user.role);
    },
    [user]
  );

  const value = useMemo(
    () => ({ user, token, isLoading, login, logout, hasRole }),
    [user, token, isLoading, login, logout, hasRole]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}