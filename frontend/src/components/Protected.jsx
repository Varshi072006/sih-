import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Loading } from "../components/ui";

export default function Protected({ roles, children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8"><Loading /></div>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.primary_role) && !["admin", "super_admin"].includes(user.primary_role)) {
    return <Navigate to="/" replace />;
  }
  return children;
}
