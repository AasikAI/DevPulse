import { Navigate, Route, Routes } from "react-router-dom";
import AppShell from "./app/AppShell";
import RequireAuth from "./features/auth/components/RequireAuth";
import SignInPage from "./features/auth/pages/SignInPage";
import StartPage from "./features/auth/pages/StartPage";
import ConnectGitHubPage from "./features/connection/pages/ConnectGitHubPage";
import DashboardPage from "./features/dashboard/pages/DashboardPage";
import SelectRepositoriesPage from "./features/repositories/pages/SelectRepositoriesPage";
import Landing from "./Landing";
import "./styles/landing.css";
import "./styles/app.css";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/sign-in" element={<SignInPage />} />
      <Route element={<RequireAuth />}>
        <Route path="/start" element={<StartPage />} />
        <Route path="/connect" element={<ConnectGitHubPage />} />
        <Route path="/repositories" element={<SelectRepositoriesPage />} />
        <Route element={<AppShell />}>
          <Route path="/dashboard" element={<DashboardPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
