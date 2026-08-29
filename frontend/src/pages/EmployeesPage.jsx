import { Button, Modal, Pagination, Stack, Table, Text, TextInput, Title } from "@mantine/core";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import ApiError from "../components/ApiError";
import EmployeeFilters from "../components/EmployeeFilters";

const emptyFilters = { q: "", country: "", department: "", job_level: "", status: "" };

export default function EmployeesPage() {
  const [filters, setFilters] = useState(emptyFilters);
  const [applied, setApplied] = useState(emptyFilters);
  const [options, setOptions] = useState({ countries: [], departments: [], job_levels: [], statuses: [] });
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [error, setError] = useState(null);
  const [createOpen, setCreateOpen] = useState(false);

  useEffect(() => {
    api.filters().then(setOptions).catch(setError);
  }, []);

  useEffect(() => {
    api
      .employees({ ...applied, page, page_size: 25 })
      .then((data) => {
        setItems(data.items);
        setTotal(data.total);
      })
      .catch(setError);
  }, [applied, page]);

  function applyFilters() {
    setPage(1);
    setApplied(filters);
  }

  function exportCsv() {
    window.location.href = api.exportUrl(applied);
  }

  return (
    <Stack>
      <GroupHeader
        onCreate={() => setCreateOpen(true)}
        onImport={async (file) => {
          try {
            const result = await api.importEmployees(file);
            setError(null);
            setApplied({ ...applied });
            window.alert(`Imported ${result.created} rows. Failed: ${result.failed.length}.`);
          } catch (err) {
            setError(err);
          }
        }}
      />
      <ApiError error={error} />
      <EmployeeFilters
        filters={filters}
        options={options}
        onChange={setFilters}
        onApply={applyFilters}
        onExport={exportCsv}
      />
      <Text size="sm" c="dimmed">
        {total} people match the current filter.
      </Text>
      <Table highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Code</Table.Th>
            <Table.Th>Name</Table.Th>
            <Table.Th>Department</Table.Th>
            <Table.Th>Country</Table.Th>
            <Table.Th>Level</Table.Th>
            <Table.Th>USD</Table.Th>
            <Table.Th>Status</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {items.map((row) => (
            <Table.Tr key={row.id}>
              <Table.Td>
                <Link to={`/employees/${row.id}`}>{row.employee_code}</Link>
              </Table.Td>
              <Table.Td>
                {row.first_name} {row.last_name}
              </Table.Td>
              <Table.Td>{row.department}</Table.Td>
              <Table.Td>{row.country}</Table.Td>
              <Table.Td>{row.job_level}</Table.Td>
              <Table.Td>{row.current_compensation?.annual_salary_usd || "—"}</Table.Td>
              <Table.Td>{row.employment_status}</Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
      <Pagination total={Math.max(1, Math.ceil(total / 25))} value={page} onChange={setPage} />
      <CreateEmployeeModal
        opened={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          setApplied({ ...applied });
        }}
      />
    </Stack>
  );
}

function GroupHeader({ onCreate, onImport }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
      <div>
        <Title order={2}>Employees</Title>
        <Text c="dimmed">Search and page the directory. Pay lives on compensation records.</Text>
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <Button component="label" variant="light">
          Import CSV
          <input
            type="file"
            accept=".csv,text/csv"
            hidden
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) onImport(file);
              event.target.value = "";
            }}
          />
        </Button>
        <Button onClick={onCreate}>Add employee</Button>
      </div>
    </div>
  );
}

function CreateEmployeeModal({ opened, onClose, onCreated }) {
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    country: "United States",
    city: "Austin",
    department: "Engineering",
    job_title: "Software Engineer II",
    job_level: "IC2",
    employment_status: "ACTIVE",
    hire_date: new Date().toISOString().slice(0, 10),
    annual_salary: "",
    currency: "USD",
    reason: "Initial compensation",
  });
  const [error, setError] = useState(null);

  function setField(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setError(null);
    try {
      await api.createEmployee({
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        country: form.country,
        city: form.city,
        department: form.department,
        job_title: form.job_title,
        job_level: form.job_level,
        employment_status: form.employment_status,
        hire_date: form.hire_date,
        compensation: {
          annual_salary: form.annual_salary,
          currency: form.currency,
          effective_from: form.hire_date,
          reason: form.reason,
        },
      });
      onCreated();
    } catch (err) {
      setError(err);
    }
  }

  return (
    <Modal opened={opened} onClose={onClose} title="Add employee" size="lg">
      <form onSubmit={submit}>
        <Stack>
          <TextInput label="First name" required value={form.first_name} onChange={(e) => setField("first_name", e.target.value)} />
          <TextInput label="Last name" required value={form.last_name} onChange={(e) => setField("last_name", e.target.value)} />
          <TextInput label="Email" required value={form.email} onChange={(e) => setField("email", e.target.value)} />
          <TextInput label="Country" required value={form.country} onChange={(e) => setField("country", e.target.value)} />
          <TextInput label="City" required value={form.city} onChange={(e) => setField("city", e.target.value)} />
          <TextInput label="Department" required value={form.department} onChange={(e) => setField("department", e.target.value)} />
          <TextInput label="Job title" required value={form.job_title} onChange={(e) => setField("job_title", e.target.value)} />
          <TextInput label="Job level" required value={form.job_level} onChange={(e) => setField("job_level", e.target.value)} />
          <TextInput label="Hire date" type="date" required value={form.hire_date} onChange={(e) => setField("hire_date", e.target.value)} />
          <TextInput label="Annual salary" required value={form.annual_salary} onChange={(e) => setField("annual_salary", e.target.value)} />
          <TextInput label="Currency" required value={form.currency} onChange={(e) => setField("currency", e.target.value)} />
          <ApiError error={error} />
          <Button type="submit">Create</Button>
        </Stack>
      </form>
    </Modal>
  );
}
