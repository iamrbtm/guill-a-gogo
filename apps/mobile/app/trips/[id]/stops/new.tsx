import { useState } from "react";
import { ScrollView, Text } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { api } from "../../lib/api";
import { AccessibleInput, PrimaryButton, ScreenHeader } from "../../components/ui";

export default function NewStopScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [form, setForm] = useState({ name: "", stop_type: "required_place", order_index: "1", notes: "" });
  const [error, setError] = useState<string | null>(null);

  const submit = () => {
    setError(null);
    api.post(`/trips/${id}/stops`, {
      ...form,
      order_index: Number(form.order_index) || 0,
      required: form.stop_type === "required_place",
    }).then(() => router.back()).catch((e) => setError(e.message));
  };

  return (
    <ScrollView>
      <ScreenHeader title="Add stop" />
      <AccessibleInput label="Name" value={form.name} onChangeText={(t) => setForm((p) => ({ ...p, name: t }))} />
      <AccessibleInput label="Stop type (required_place, optional_place, break, fuel, meal, sightseeing)" value={form.stop_type} onChangeText={(t) => setForm((p) => ({ ...p, stop_type: t }))} />
      <AccessibleInput label="Order index" value={form.order_index} onChangeText={(t) => setForm((p) => ({ ...p, order_index: t }))} />
      <AccessibleInput label="Notes" value={form.notes} onChangeText={(t) => setForm((p) => ({ ...p, notes: t }))} multiline />
      {error && <Text accessibilityRole="alert" style={{ color: "red", padding: 12 }}>{error}</Text>}
      <PrimaryButton label="Save stop" onPress={submit} />
    </ScrollView>
  );
}
