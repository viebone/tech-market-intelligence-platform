interface DataFreshnessLabelProps {
  asOf: string;
  source: string;
}

export function DataFreshnessLabel({ asOf, source }: DataFreshnessLabelProps) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-gray-400">
      <span className="inline-block w-1.5 h-1.5 rounded-full bg-gray-400 shrink-0" aria-hidden="true" />
      <span>
        As of <time dateTime={asOf}>{asOf}</time>
        {" · "}
        {source}
      </span>
    </span>
  );
}
