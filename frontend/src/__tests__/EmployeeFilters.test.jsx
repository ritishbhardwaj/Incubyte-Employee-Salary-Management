import { MantineProvider } from "@mantine/core";
import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import EmployeeFilters from "../components/EmployeeFilters";

test("search changes filters and apply is invoked", () => {
  const onChange = vi.fn();
  const onApply = vi.fn();
  const filters = { q: "", country: "", department: "", job_level: "", status: "" };

  render(
    <MantineProvider>
      <EmployeeFilters
        filters={filters}
        options={{ countries: [], departments: [], job_levels: [], statuses: [] }}
        onChange={onChange}
        onApply={onApply}
        onExport={() => {}}
      />
    </MantineProvider>,
  );

  fireEvent.change(screen.getByLabelText(/search/i), { target: { value: "Ada" } });
  expect(onChange).toHaveBeenCalled();
  expect(onChange.mock.calls[0][0].q).toBe("Ada");
  fireEvent.click(screen.getByRole("button", { name: /apply/i }));
  expect(onApply).toHaveBeenCalled();
});
