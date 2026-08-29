import { Button, Group, TextInput } from "@mantine/core";

export default function EmployeeFilters({ filters, options, onChange, onApply, onExport }) {
  return (
    <Group align="flex-end">
      <TextInput
        label="Search"
        placeholder="Name, email, or code"
        value={filters.q}
        onChange={(event) => onChange({ ...filters, q: event.target.value })}
      />
      <NativeFilter
        label="Country"
        value={filters.country}
        items={options.countries || []}
        onChange={(value) => onChange({ ...filters, country: value })}
      />
      <NativeFilter
        label="Department"
        value={filters.department}
        items={options.departments || []}
        onChange={(value) => onChange({ ...filters, department: value })}
      />
      <NativeFilter
        label="Level"
        value={filters.job_level}
        items={options.job_levels || []}
        onChange={(value) => onChange({ ...filters, job_level: value })}
      />
      <NativeFilter
        label="Status"
        value={filters.status}
        items={options.statuses || []}
        onChange={(value) => onChange({ ...filters, status: value })}
      />
      <Button onClick={onApply}>Apply</Button>
      <Button variant="light" onClick={onExport}>
        Export CSV
      </Button>
    </Group>
  );
}

function NativeFilter({ label, value, items, onChange }) {
  return (
    <label>
      <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>{label}</div>
      <select
        aria-label={label}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        style={{ height: 36, minWidth: 140 }}
      >
        <option value="">All</option>
        {items.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
    </label>
  );
}
