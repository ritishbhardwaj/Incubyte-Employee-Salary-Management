import { Button, Card, PasswordInput, Stack, Text, TextInput, Title } from "@mantine/core";
import { useState } from "react";
import { api } from "../api";
import ApiError from "../components/ApiError";

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState("hr.manager@acme.example");
  const [password, setPassword] = useState("ChangeMeNow!");
  const [fieldError, setFieldError] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    if (!email.trim() || !password.trim()) {
      setFieldError("Email and password are required");
      return;
    }
    setFieldError("");
    setLoading(true);
    try {
      const user = await api.login(email.trim(), password);
      onLogin(user);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Stack align="center" justify="center" mih="100vh" bg="gray.0">
      <Card withBorder shadow="sm" w={420} p="xl">
        <Title order={2}>IncubyteESM</Title>
        <Text c="dimmed" mb="md">
          Sign in as ACME HR Manager
        </Text>
        <form onSubmit={handleSubmit}>
          <Stack>
            <TextInput label="Email" value={email} onChange={(event) => setEmail(event.target.value)} />
            <PasswordInput label="Password" value={password} onChange={(event) => setPassword(event.target.value)} />
            {fieldError ? <Text c="red">{fieldError}</Text> : null}
            <ApiError error={error} />
            <Button type="submit" loading={loading}>
              Sign in
            </Button>
            <Text size="xs" c="dimmed">
              Demo account is prefilled. Change it after the assessment.
            </Text>
          </Stack>
        </form>
      </Card>
    </Stack>
  );
}
