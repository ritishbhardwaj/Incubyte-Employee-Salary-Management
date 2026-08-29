import { MantineProvider } from "@mantine/core";
import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import SalaryAdjustForm from "../components/SalaryAdjustForm";

function renderForm(onSubmit = vi.fn()) {
  render(
    <MantineProvider>
      <SalaryAdjustForm onSubmit={onSubmit} />
    </MantineProvider>,
  );
  return onSubmit;
}

test("requires a reason", () => {
  const onSubmit = renderForm();
  fireEvent.change(screen.getByLabelText(/annual salary/i), { target: { value: "120000" } });
  fireEvent.click(screen.getByRole("button", { name: /save adjustment/i }));
  expect(screen.getByRole("alert")).toHaveTextContent(/reason is required/i);
  expect(onSubmit).not.toHaveBeenCalled();
});

test("rejects non-positive salary", () => {
  const onSubmit = renderForm();
  fireEvent.change(screen.getByLabelText(/reason/i), { target: { value: "Promotion" } });
  fireEvent.change(screen.getByLabelText(/annual salary/i), { target: { value: "0" } });
  fireEvent.click(screen.getByRole("button", { name: /save adjustment/i }));
  expect(screen.getByRole("alert")).toHaveTextContent(/greater than zero/i);
  expect(onSubmit).not.toHaveBeenCalled();
});
