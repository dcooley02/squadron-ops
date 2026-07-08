import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { canAccessRoles, rolesForPath } from "../lib/permissions";
import type { Role } from "../lib/api";

/**
 * Nested under ProtectedRoute. When the current path has declared roles,
 * redirects home if the signed-in user is not allowed.
 */
export default function RoleRoute({ roles }: { roles?: Role[] }) {
  const { user } = useAuth();
  const location = useLocation();
  const required = roles ?? rolesForPath(location.pathname);

  if (!user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  if (!canAccessRoles(user.role, required)) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
