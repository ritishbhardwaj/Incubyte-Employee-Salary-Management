import { AppShell, Button, Group, NavLink, Text } from "@mantine/core";
import { Link, Outlet, useLocation } from "react-router-dom";
import { api } from "../lib/api";
import { ORG_NAME } from "../lib/org";

export default function AppLayout({ user, onLogout }) {
  const location = useLocation();

  async function handleLogout() {
    await api.logout();
    onLogout();
  }

  return (
    <AppShell
      header={{ height: 64 }}
      navbar={{ width: 220, breakpoint: "sm" }}
      padding="lg"
    >
      <AppShell.Header>
        <Group h="100%" px="lg" justify="space-between">
          <div>
            <Text fw={700}>IncubyteESM</Text>
            <Text size="xs" c="dimmed">
              {ORG_NAME} salary management
            </Text>
          </div>
          <Group>
            <Text size="sm">{user.email}</Text>
            <Button variant="light" color="gray" onClick={handleLogout}>
              Log out
            </Button>
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="md">
        <NavLink component={Link} to="/" label="Insights" active={location.pathname === "/"} />
        <NavLink
          component={Link}
          to="/employees"
          label="Employees"
          active={location.pathname.startsWith("/employees")}
        />
      </AppShell.Navbar>
      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}
