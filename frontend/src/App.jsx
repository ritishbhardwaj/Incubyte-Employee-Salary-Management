import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { api } from "./lib/api";
import AppLayout from "./components/AppLayout";
import EmployeeDetailPage from "./pages/EmployeeDetailPage";
import EmployeesPage from "./pages/EmployeesPage";
import InsightsPage from "./pages/InsightsPage";
import LoginPage from "./pages/LoginPage";

export default function App() {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    api
      .me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setReady(true));
  }, []);

  if (!ready) {
    return null;
  }

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <LoginPage onLogin={setUser} />} />
      <Route element={user ? <AppLayout user={user} onLogout={() => setUser(null)} /> : <Navigate to="/login" replace />}>
        <Route path="/" element={<InsightsPage />} />
        <Route path="/employees" element={<EmployeesPage />} />
        <Route path="/employees/:id" element={<EmployeeDetailPage />} />
      </Route>
    </Routes>
  );
}
