import { useSelector } from "react-redux";
import { useLocation, Navigate } from "react-router-dom";
//import { getToken } from "../slices/authSlice";

export default function RequireAuth({ children }: { children: JSX.Element }) {
  const token = "aa"; //useSelector(getToken);
  let location = useLocation();

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
