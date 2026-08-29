import { Card, Grid, SimpleGrid, Stack, Table, Text, Title } from "@mantine/core";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";
import ApiError from "../components/ApiError";

function money(value) {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(
    Number(value),
  );
}

export default function InsightsPage() {
  const [summary, setSummary] = useState(null);
  const [breakdowns, setBreakdowns] = useState(null);
  const [distribution, setDistribution] = useState([]);
  const [recent, setRecent] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([api.summary(), api.breakdowns(), api.distribution(), api.recentChanges()])
      .then(([s, b, d, r]) => {
        setSummary(s);
        setBreakdowns(b);
        setDistribution(d);
        setRecent(r);
      })
      .catch(setError);
  }, []);

  return (
    <Stack>
      <div>
        <Title order={2}>How ACME pays</Title>
        <Text c="dimmed">Active employees, current compensation, USD reporting amounts.</Text>
      </div>
      <ApiError error={error} />
      {summary ? (
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }}>
          <Kpi label="Active headcount" value={summary.active_headcount} />
          <Kpi label="Annual payroll (USD)" value={money(summary.total_annual_payroll_usd)} />
          <Kpi label="Average (USD)" value={money(summary.average_salary_usd)} />
          <Kpi label="Median (USD)" value={money(summary.median_salary_usd)} />
        </SimpleGrid>
      ) : null}
      {summary?.percentiles?.source === "postgresql_percentile_cont_only" ? (
        <Text size="sm" c="dimmed">
          Percentiles (p25/p50/p75/p90) are computed with PostgreSQL percentile_cont in production. This
          environment ({summary.percentiles.dialect}) does not expose that path.
        </Text>
      ) : null}
      {summary?.percentiles?.p25 ? (
        <Text size="sm" c="dimmed">
          Percentiles USD — p25 {money(summary.percentiles.p25)} · p75 {money(summary.percentiles.p75)} · p90{" "}
          {money(summary.percentiles.p90)}
        </Text>
      ) : null}
      <Grid>
        <Grid.Col span={{ base: 12, md: 7 }}>
          <Card withBorder>
            <Title order={4} mb="md">
              Pay distribution (USD)
            </Title>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={distribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="headcount" fill="#0ca678" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 5 }}>
          <BreakdownTable title="By country" rows={breakdowns?.country || []} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <BreakdownTable title="By department" rows={breakdowns?.department || []} />
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <BreakdownTable title="By level" rows={breakdowns?.job_level || []} />
        </Grid.Col>
      </Grid>
      <Card withBorder>
        <Title order={4} mb="md">
          Recent compensation changes
        </Title>
        <Table>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Employee</Table.Th>
              <Table.Th>Reason</Table.Th>
              <Table.Th>USD</Table.Th>
              <Table.Th>Effective</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {recent.map((row) => (
              <Table.Tr key={row.id}>
                <Table.Td>
                  {row.employee_name} ({row.employee_code})
                </Table.Td>
                <Table.Td>{row.reason}</Table.Td>
                <Table.Td>{money(row.annual_salary_usd)}</Table.Td>
                <Table.Td>{row.effective_from}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
        {recent.length === 0 ? <Text c="dimmed">No non-seed changes yet.</Text> : null}
      </Card>
    </Stack>
  );
}

function Kpi({ label, value }) {
  return (
    <Card withBorder>
      <Text size="sm" c="dimmed">
        {label}
      </Text>
      <Text fw={700} size="xl">
        {value}
      </Text>
    </Card>
  );
}

function BreakdownTable({ title, rows }) {
  return (
    <Card withBorder h="100%">
      <Title order={4} mb="md">
        {title}
      </Title>
      <Table>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Slice</Table.Th>
            <Table.Th>People</Table.Th>
            <Table.Th>Avg USD</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {rows.map((row) => (
            <Table.Tr key={row.key}>
              <Table.Td>{row.key}</Table.Td>
              <Table.Td>{row.headcount}</Table.Td>
              <Table.Td>
                {new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(
                  Number(row.average_usd || 0),
                )}
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Card>
  );
}
