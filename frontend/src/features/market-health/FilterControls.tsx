export interface Filters {
  role: "all" | "UX Design" | "Product Management" | "Software Engineering";
  seniority: "all" | "Mid" | "Senior";
  location: "all" | "London" | "New York" | "Remote";
  period: "3m" | "6m" | "12m";
}

interface FilterControlsProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
}

interface SelectFieldProps<T extends string> {
  id: string;
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
}

function SelectField<T extends string>({
  id,
  label,
  value,
  options,
  onChange,
}: SelectFieldProps<T>) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-xs font-medium text-gray-500 uppercase tracking-wide">
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value as T)}
        className="rounded-md border border-gray-200 bg-white px-3 py-1.5 text-sm text-gray-800 focus:border-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-400 transition-colors"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

const ROLE_OPTIONS: { value: Filters["role"]; label: string }[] = [
  { value: "all", label: "All roles" },
  { value: "UX Design", label: "UX Design" },
  { value: "Product Management", label: "Product Management" },
  { value: "Software Engineering", label: "Software Engineering" },
];

const SENIORITY_OPTIONS: { value: Filters["seniority"]; label: string }[] = [
  { value: "all", label: "All seniority" },
  { value: "Mid", label: "Mid" },
  { value: "Senior", label: "Senior" },
];

const LOCATION_OPTIONS: { value: Filters["location"]; label: string }[] = [
  { value: "all", label: "All locations" },
  { value: "London", label: "London" },
  { value: "New York", label: "New York" },
  { value: "Remote", label: "Remote" },
];

const PERIOD_OPTIONS: { value: Filters["period"]; label: string }[] = [
  { value: "3m", label: "Last 3 months" },
  { value: "6m", label: "Last 6 months" },
  { value: "12m", label: "Last 12 months" },
];

export function FilterControls({ filters, onChange }: FilterControlsProps) {
  function update<K extends keyof Filters>(key: K, value: Filters[K]) {
    onChange({ ...filters, [key]: value });
  }

  return (
    <div className="rounded-lg border border-gray-100 bg-gray-50 px-4 py-3">
      <div className="flex flex-wrap gap-4 items-end">
        <SelectField
          id="filter-role"
          label="Role"
          value={filters.role}
          options={ROLE_OPTIONS}
          onChange={(v) => update("role", v)}
        />
        <SelectField
          id="filter-seniority"
          label="Seniority"
          value={filters.seniority}
          options={SENIORITY_OPTIONS}
          onChange={(v) => update("seniority", v)}
        />
        <SelectField
          id="filter-location"
          label="Location"
          value={filters.location}
          options={LOCATION_OPTIONS}
          onChange={(v) => update("location", v)}
        />
        <SelectField
          id="filter-period"
          label="Time range"
          value={filters.period}
          options={PERIOD_OPTIONS}
          onChange={(v) => update("period", v)}
        />
      </div>
    </div>
  );
}
