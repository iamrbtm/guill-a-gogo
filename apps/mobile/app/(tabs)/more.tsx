import { useEffect, useState } from "react";
import { ActivityIndicator, Text, View } from "react-native";
import { api } from "../lib/api";
import { Card, ScreenHeader } from "../components/ui";

export default function MoreScreen() {
  const [status, setStatus] = useState<{ providers?: Record<string, unknown> } | null>(null);
  useEffect(() => {
    api.get<{ providers: Record<string, unknown> }>("/provider-status").then(setStatus).catch(() => setStatus({ providers: {} }));
  }, []);

  return (
    <View>
      <ScreenHeader title="More" />
      <Card title="Provider status">
        {status === null ? (
          <ActivityIndicator accessibilityLabel="Loading provider status" />
        ) : (
          <Text>{JSON.stringify(status.providers ?? {}, null, 2)}</Text>
        )}
      </Card>
      <Card title="Account security">
        <Text>Passkeys, recovery codes, and session management live here (Phase 1).</Text>
      </Card>
    </View>
  );
}
