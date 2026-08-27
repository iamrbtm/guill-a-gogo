import { useState } from "react";
import { ScrollView, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { api } from "../../lib/api";
import { AccessibleInput, PrimaryButton, ScreenHeader } from "../../components/ui";

// Generic create form for a profile kind. The vehicle form intentionally asks
// for the fields the planner needs and never pre-fills guesses.
const FIELDS: Record<string, string[]> = {
  traveler: ["name", "max_walking_distance_meters", "mobility_devices", "food_allergies", "medication_notes"],
  pet: ["name", "species", "breed", "size", "weight_kg", "break_frequency_minutes"],
  vehicle: ["year", "make", "model", "trim", "engine", "fuel_type", "towing_mpg", "rated_towing_capacity_kg", "loaded_trailer_weight_kg"],
  trailer: ["name", "empty_weight_kg", "loaded_weight_kg", "length_m"],
};

export default function ProfileNewScreen() {
  const { kind } = useLocalSearchParams<{ kind: string }>();
  const router = useRouter();
  const fields = FIELDS[kind] ?? ["name"];
  const [form, setForm] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  const submit = () => {
    setError(null);
    const payload: Record<string, unknown> = {};
    for (const f of fields) {
      const v = form[f]?.trim();
      if (!v) continue;
      // numeric fields where the name suggests a number
      if (/_(kg|meters|minutes|mpg|year|capacity|weight|length|m|id)$/.test(f) || f === "year") {
        const n = Number(v);
        payload[f] = Number.isFinite(n) ? n : v;
      } else if (f === "mobility_devices" || f === "food_allergies") {
        payload[f] = v.split(",").map((s) => s.trim());
      } else {
        payload[f] = v;
      }
    }
    api.post(`/profiles/${kind}`, payload).then(() => router.back()).catch((e) => setError(e.message));
  };

  return (
    <ScrollView>
      <ScreenHeader title={`New ${kind}`} />
      {fields.map((f) => (
        <AccessibleInput
          key={f}
          label={f.replace(/_/g, " ")}
          value={form[f] ?? ""}
          onChangeText={(t) => setForm((p) => ({ ...p, [f]: t }))}
        />
      ))}
      {error && <Text accessibilityRole="alert" style={{ color: "red", padding: 12 }}>{error}</Text>}
      <PrimaryButton label="Save" onPress={submit} />
    </ScrollView>
  );
}
