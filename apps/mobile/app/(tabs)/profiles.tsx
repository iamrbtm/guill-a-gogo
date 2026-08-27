import { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { api, Profile } from "../lib/api";
import { Card, PrimaryButton, ScreenHeader } from "../components/ui";

const KINDS: { key: string; label: string }[] = [
  { key: "traveler", label: "Travelers" },
  { key: "pet", label: "Pets" },
  { key: "vehicle", label: "Vehicles" },
  { key: "trailer", label: "Trailers" },
];

export default function ProfilesScreen() {
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    Promise.all(KINDS.map((k) => api.get<Profile[]>(`/profiles/${k.key}`).then((r) => [k.key, r.length] as const)))
      .then((pairs) => setCounts(Object.fromEntries(pairs)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <ActivityIndicator accessibilityLabel="Loading profiles" style={{ marginTop: 40 }} />;

  return (
    <ScrollView>
      <ScreenHeader title="Profiles" />
      {KINDS.map((k) => (
        <Card key={k.key} title={k.label}>
          <Text>{counts[k.key] ?? 0} saved</Text>
          <PrimaryButton label={`Add ${k.label.toLowerCase()}`} onPress={() => router.push(`/profiles/${k.key}/new`)} />
        </Card>
      ))}
    </ScrollView>
  );
}
