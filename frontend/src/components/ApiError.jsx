import { Alert } from "@mantine/core";

export default function ApiError({ error }) {
  if (!error) {
    return null;
  }
  const status = error.status ? ` (${error.status})` : "";
  return (
    <Alert color="red" title={`Something went wrong${status}`} mb="md">
      {error.detail || error.message}
    </Alert>
  );
}
