import { MantineProvider } from "@mantine/core";
import { fireEvent, render, screen } from "@testing-library/react";
import LoginPage from "../pages/LoginPage";

test("requires email and password", () => {
  render(
    <MantineProvider>
      <LoginPage onLogin={() => {}} />
    </MantineProvider>,
  );
  fireEvent.change(screen.getByLabelText(/email/i), { target: { value: "" } });
  fireEvent.change(screen.getByLabelText(/password/i), { target: { value: "" } });
  fireEvent.click(screen.getByRole("button", { name: /sign in/i }));
  expect(screen.getByText(/email and password are required/i)).toBeInTheDocument();
});
