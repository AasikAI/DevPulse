import { Navigate } from "react-router-dom";

// Where sign-in lands. A user without a connection goes to the connect page.
// When the dashboard exists, a connected user will be sent there instead.
export default function StartPage() {
  return <Navigate to="/connect" replace />;
}
