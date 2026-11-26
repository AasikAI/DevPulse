type Props = { tone?: "brand" | "light" };

// Lowercase wordmark as in the design system. "light" is for the dark sidebar.
export default function Logo({ tone = "brand" }: Props) {
  return <span className={`wordmark wordmark-${tone}`}>DevPulse</span>;
}
