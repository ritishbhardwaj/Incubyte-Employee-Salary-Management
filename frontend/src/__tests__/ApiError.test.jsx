import { MantineProvider } from "@mantine/core";
import { render, screen } from "@testing-library/react";
import ApiError from "../components/ApiError";

test("renders API status and detail", () => {
  render(
    <MantineProvider>
      <ApiError error={{ status: 401, detail: "Not authenticated" }} />
    </MantineProvider>,
  );
  expect(screen.getByText(/something went wrong \(401\)/i)).toBeInTheDocument();
  expect(screen.getByText(/not authenticated/i)).toBeInTheDocument();
});

test("renders validation errors", () => {
  render(
    <MantineProvider>
      <ApiError error={{ status: 400, detail: "annual_salary must be greater than zero" }} />
    </MantineProvider>,
  );
  expect(screen.getByText(/400/)).toBeInTheDocument();
  expect(screen.getByText(/annual_salary must be greater than zero/i)).toBeInTheDocument();
});
