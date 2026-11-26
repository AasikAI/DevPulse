type Props = {
  title: string;
  message: string;
  onRetry?: () => void;
};

// Only show a retry button when retrying can actually help.
export default function ErrorState({ title, message, onRetry }: Props) {
  return (
    <div className="state state-error" role="alert">
      <strong>{title}</strong>
      <p>{message}</p>
      {onRetry && (
        <button type="button" className="btn btn-secondary" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}
