export type StatusTone = "available" | "degraded" | "unavailable" | "checking";

interface ServiceStatusProps {
  label: string;
  detail: string;
  tone: StatusTone;
}

const toneLabels: Record<StatusTone, string> = {
  available: "Available",
  degraded: "Unavailable",
  unavailable: "Unreachable",
  checking: "Checking",
};

export function ServiceStatus({ label, detail, tone }: ServiceStatusProps) {
  return (
    <article className="service-status">
      <div>
        <p className="service-status__label">{label}</p>
        <p className="service-status__detail">{detail}</p>
      </div>
      <span className={`status-badge status-badge--${tone}`}>
        <span className="status-badge__indicator" aria-hidden="true" />
        {toneLabels[tone]}
      </span>
    </article>
  );
}
