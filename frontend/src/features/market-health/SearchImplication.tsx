export interface SearchImplicationData {
  text: string;
}

interface SearchImplicationProps {
  implication: SearchImplicationData | null;
}

export function SearchImplication({ implication }: SearchImplicationProps) {
  if (implication === null) {
    return null;
  }

  return (
    <div className="px-1">
      <p className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-1">
        What this means for your search
      </p>
      <p className="text-base text-gray-700 leading-relaxed max-w-prose">
        {implication.text}
      </p>
    </div>
  );
}
