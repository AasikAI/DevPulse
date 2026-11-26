import { Navigate, Route, Routes } from "react-router-dom";
import AppShell from "./app/AppShell";
import RequireAuth from "./features/auth/components/RequireAuth";
import SignInPage from "./features/auth/pages/SignInPage";
import StartPage from "./features/auth/pages/StartPage";
import Landing from "./Landing";
import "./styles/landing.css";
import "./styles/app.css";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/sign-in" element={<SignInPage />} />
      <Route element={<RequireAuth />}>
        <Route element={<AppShell />}>
          <Route path="/start" element={<StartPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
