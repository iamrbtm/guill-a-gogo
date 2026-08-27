import { useState } from "react";
import { ScrollView, Text } from "react-native";
import { useRouter } from "expo-router";
import { api } from "../../lib/api";
import { AccessibleInput, PrimaryButton, ScreenHeader } from "../../components/ui";

export default function NewTripScreen() {
  const router = useRouter();
  const [form, setForm] = useState({ title: "", origin: "", destination: "" });
  const [error, setError] = useState<string | null>(null);

  const submit = () => {
    setError(null);
    api.post("/trips", form).then(() => router.back()).catch((e) => setError(e.message));
  };

  return (
    <ScrollView>
      <ScreenHeader title="New trip" />
      <AccessibleInput label="Title" value={form.title} onChangeText={(t) => setForm((p) => ({ ...p, title: t }))} />
      <AccessibleInput label="Origin" value={form.origin} onChangeText={(t) => setForm((p) => ({ ...p, origin: t }))} />
      <AccessibleInput label="Destination" value={form.destination} onChangeText={(t) => setForm((p) => ({ ...p, destination: t }))} />
      {error && <Text accessibilityRole="alert" style={{ color: "red", padding: 12 }}>{error}</Text>}
      <PrimaryButton label="Create trip" onPress={submit} />
    </ScrollView>
  );
}
