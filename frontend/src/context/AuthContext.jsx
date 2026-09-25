import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("c2i_token") || "");
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!token);

  useEffect(() => {
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    api("/api/auth/me", { token })
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("c2i_token");
        setToken("");
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  const value = useMemo(
    () => ({
      token,
      user,
      loading,
      login: async (email, password) => {
        const data = await api("/api/auth/login", { method: "POST", body: { email, password } });
        localStorage.setItem("c2i_token", data.access_token);
        setToken(data.access_token);
        return data;
      },
      logout: () => {
        localStorage.removeItem("c2i_token");
        setToken("");
        setUser(null);
      },
      dashboardPath: () => {
        const role = user?.primary_role;
        if (!role) return "/login";
        if (["admin", "super_admin"].includes(role)) return "/admin/dashboard";
        if (["government_officer", "government_department"].includes(role)) return "/government/dashboard";
        if (["university", "faculty", "student"].includes(role)) return "/university/dashboard";
        if (["industry", "startup", "msme", "csr"].includes(role)) return "/industry/dashboard";
        return "/citizen/dashboard";
      },
    }),
    [token, user, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
