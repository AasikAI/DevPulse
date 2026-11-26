import { useState } from "react";
import { useAuth } from "../hooks/useAuth";

type Props = { className: string };

export default function LogoutButton({ className }: Props) {
  const { signOut } = useAuth();
  const [failed, setFailed] = useState(false);

  async function handleClick() {
    setFailed(false);
    try {
      await signOut();
    } catch {
      setFailed(true);
    }
  }

  return (
    <>
      <button type="button" className={className} onClick={handleClick}>
        Log out
      </button>
      {failed && <p role="alert">Could not log out. Please try again.</p>}
    </>
  );
}
