type Props = { label?: string };

export default function LoadingState({ label = "Loading…" }: Props) {
  return (
    <div className="state">
      <p className="banner banner-info" role="status">
        <span aria-hidden="true">↻</span> {label}
      </p>
    </div>
  );
}
