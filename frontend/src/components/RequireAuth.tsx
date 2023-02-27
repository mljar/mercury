import { useSelector } from "react-redux";
import { useLocation, Navigate } from "react-router-dom";
import { getToken } from "./authSlice";
import { isPublic } from "./Sites/sitesSlice";

export default function RequireAuth({ children }: { children: JSX.Element }) {
  const token = useSelector(getToken);
  const isPublicSite = useSelector(isPublic);
  let location = useLocation();

  if (!isPublicSite && !token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
