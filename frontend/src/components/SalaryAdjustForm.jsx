import { Button, Stack, TextInput } from "@mantine/core";
import { useState } from "react";

export default function SalaryAdjustForm({ onSubmit, submitting = false }) {
  const [annualSalary, setAnnualSalary] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [effectiveFrom, setEffectiveFrom] = useState(new Date().toISOString().slice(0, 10));
  const [reason, setReason] = useState("");
  const [fieldError, setFieldError] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    const amount = Number(annualSalary);
    if (!reason.trim()) {
      setFieldError("Reason is required");
      return;
    }
    if (!Number.isFinite(amount) || amount <= 0) {
      setFieldError("Annual salary must be greater than zero");
      return;
    }
    setFieldError("");
    onSubmit({
      annual_salary: String(amount),
      currency,
      effective_from: effectiveFrom,
      reason: reason.trim(),
    });
  }

  return (
    <form onSubmit={handleSubmit}>
      <Stack>
        <TextInput
          label="Annual salary"
          value={annualSalary}
          onChange={(event) => setAnnualSalary(event.target.value)}
        />
        <TextInput label="Currency" value={currency} onChange={(event) => setCurrency(event.target.value)} />
        <TextInput
          label="Effective from"
          type="date"
          value={effectiveFrom}
          onChange={(event) => setEffectiveFrom(event.target.value)}
        />
        <TextInput
          label="Reason"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          placeholder="Promotion, market adjustment, correction"
        />
        {fieldError ? <div role="alert">{fieldError}</div> : null}
        <Button type="submit" loading={submitting}>
          Save adjustment
        </Button>
      </Stack>
    </form>
  );
}
