type Props = { label?: string };

export default function LoadingState({ label = "Loading…" }: Props) {
  return (
    <div className="state" role="status">
      {label}
    </div>
  );
}
