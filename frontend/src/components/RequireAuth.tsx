import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useLocation, Navigate } from "react-router-dom";
import { getToken } from "../slices/authSlice";
import { fetchSite, isPublic } from "../slices/sitesSlice";

export default function RequireAuth({ children }: { children: JSX.Element }) {
  const token = useSelector(getToken);
  const isPublicSite = useSelector(isPublic);
  let location = useLocation();
  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(fetchSite());
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!isPublicSite && !token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
