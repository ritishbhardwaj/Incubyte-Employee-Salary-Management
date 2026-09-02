import { Button, Card, Grid, Group, Modal, Select, Stack, Table, Text, TextInput, Title } from "@mantine/core";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";
import ApiError from "../components/ApiError";
import SalaryAdjustForm from "../components/SalaryAdjustForm";

export default function EmployeeDetailPage() {
  const { id } = useParams();
  const [employee, setEmployee] = useState(null);
  const [error, setError] = useState(null);
  const [adjustOpen, setAdjustOpen] = useState(false);

  function load() {
    api.employee(id).then(setEmployee).catch(setError);
  }

  useEffect(() => {
    load();
  }, [id]);

  async function saveProfile(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      const updated = await api.patchEmployee(id, {
        city: form.get("city"),
        department: form.get("department"),
        job_title: form.get("job_title"),
        job_level: form.get("job_level"),
        employment_status: form.get("employment_status"),
      });
      setEmployee(updated);
    } catch (err) {
      setError(err);
    }
  }

  async function savePay(payload) {
    try {
      await api.adjustCompensation(id, payload);
      setAdjustOpen(false);
      load();
    } catch (err) {
      setError(err);
    }
  }

  if (!employee) {
    return <ApiError error={error} />;
  }

  const pay = employee.current_compensation;

  return (
    <Stack>
      <Group justify="space-between">
        <div>
          <Title order={2}>
            {employee.first_name} {employee.last_name}
          </Title>
          <Text c="dimmed">
            {employee.employee_code} · {employee.email}
          </Text>
        </div>
        <Button onClick={() => setAdjustOpen(true)}>Adjust salary</Button>
      </Group>
      <ApiError error={error} />
      <Grid>
        <Grid.Col span={{ base: 12, md: 5 }}>
          <Card withBorder>
            <Title order={4} mb="md">
              Profile
            </Title>
            <form onSubmit={saveProfile}>
              <Stack>
                <TextInput label="City" name="city" defaultValue={employee.city} />
                <TextInput label="Department" name="department" defaultValue={employee.department} />
                <TextInput label="Job title" name="job_title" defaultValue={employee.job_title} />
                <TextInput label="Job level" name="job_level" defaultValue={employee.job_level} />
                <Select
                  label="Status"
                  name="employment_status"
                  defaultValue={employee.employment_status}
                  data={["ACTIVE", "ON_LEAVE", "TERMINATED"]}
                />
                <Button type="submit" variant="light">
                  Save profile
                </Button>
              </Stack>
            </form>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 7 }}>
          <Card withBorder>
            <Title order={4} mb="sm">
              Current compensation
            </Title>
            {pay ? (
              <Text>
                {pay.annual_salary} {pay.currency} · {pay.annual_salary_usd} USD (rate {pay.fx_rate_to_usd}) from{" "}
                {pay.effective_from}
              </Text>
            ) : (
              <Text c="dimmed">No current compensation.</Text>
            )}
            <Title order={5} mt="lg" mb="sm">
              History
            </Title>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>From</Table.Th>
                  <Table.Th>To</Table.Th>
                  <Table.Th>Local</Table.Th>
                  <Table.Th>USD</Table.Th>
                  <Table.Th>Reason</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {(employee.compensation_history || []).map((row) => (
                  <Table.Tr key={row.id}>
                    <Table.Td>{row.effective_from}</Table.Td>
                    <Table.Td>{row.effective_to || "current"}</Table.Td>
                    <Table.Td>
                      {row.annual_salary} {row.currency}
                    </Table.Td>
                    <Table.Td>{row.annual_salary_usd}</Table.Td>
                    <Table.Td>{row.reason}</Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Card>
        </Grid.Col>
      </Grid>
      <Modal opened={adjustOpen} onClose={() => setAdjustOpen(false)} title="Adjust salary">
        <SalaryAdjustForm onSubmit={savePay} />
      </Modal>
    </Stack>
  );
}
