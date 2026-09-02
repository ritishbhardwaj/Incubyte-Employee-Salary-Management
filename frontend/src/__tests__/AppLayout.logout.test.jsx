import { MantineProvider } from "@mantine/core";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi, beforeEach } from "vitest";
import AppLayout from "../components/AppLayout";
import { api } from "../lib/api";

vi.mock("../lib/api", () => ({
  api: {
    logout: vi.fn(),
  },
}));

beforeEach(() => {
  api.logout.mockReset();
});

function renderLayout(onLogout = vi.fn()) {
  return render(
    <MantineProvider>
      <MemoryRouter>
        <AppLayout user={{ email: "hr.manager@esmincubyte.example" }} onLogout={onLogout} />
      </MemoryRouter>
    </MantineProvider>,
  );
}

test("log out calls the API then clears local session", async () => {
  api.logout.mockResolvedValueOnce({ status: "logged_out" });
  const onLogout = vi.fn();
  renderLayout(onLogout);
  fireEvent.click(screen.getByRole("button", { name: /log out/i }));
  await waitFor(() => expect(api.logout).toHaveBeenCalledTimes(1));
  expect(onLogout).toHaveBeenCalledTimes(1);
});

test("failed logout keeps the local session", async () => {
  api.logout.mockRejectedValueOnce(Object.assign(new Error("Invalid or missing Origin"), { status: 403, detail: "Invalid or missing Origin" }));
  const onLogout = vi.fn();
  renderLayout(onLogout);
  fireEvent.click(screen.getByRole("button", { name: /log out/i }));
  await waitFor(() => expect(api.logout).toHaveBeenCalledTimes(1));
  expect(onLogout).not.toHaveBeenCalled();
  expect(screen.getByText(/invalid or missing origin/i)).toBeInTheDocument();
});
