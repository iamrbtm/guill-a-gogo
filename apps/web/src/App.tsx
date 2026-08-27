import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { clearTokens, getToken } from "./lib/api";
import Login from "./pages/Login";
import AcceptInvite from "./pages/AcceptInvite";
import Trips from "./pages/Trips";
import TripDetail from "./pages/TripDetail";
import Profiles from "./pages/Profiles";

function Nav() {
  const logout = () => {
    clearTokens();
    window.location.href = "/login";
  };
  return (
    <nav className="nav" aria-label="Primary">
      <span className="brand">Guill-a-Gogo</span>
      <NavLink to="/trips">Trips</NavLink>
      <NavLink to="/profiles">Profiles</NavLink>
      <button className="link" onClick={logout}>
        Log out
      </button>
    </nav>
  );
}

function RequireAuth({ children }: { children: JSX.Element }) {
  return getToken() ? (
    <>
      <Nav />
      {children}
    </>
  ) : (
    <Navigate to="/login" replace />
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/accept" element={<AcceptInvite />} />
      <Route
        path="/trips"
        element={
          <RequireAuth>
            <Trips />
          </RequireAuth>
        }
      />
      <Route
        path="/trips/:id"
        element={
          <RequireAuth>
            <TripDetail />
          </RequireAuth>
        }
      />
      <Route
        path="/profiles"
        element={
          <RequireAuth>
            <Profiles />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/trips" replace />} />
    </Routes>
  );
}
