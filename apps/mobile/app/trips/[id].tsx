import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { api, Trip } from "../../lib/api";
import { Card, PrimaryButton, ScreenHeader } from "../../components/ui";

interface Stop { id: string; name?: string; stop_type: string; required: boolean; order_index: number; }
interface Lodging { id: string; name: string; user_confirmed: boolean; required_accessibility_confirmed?: boolean; }
interface Meal { id: string; meal_type: string; restaurant_name?: string; serves_fish?: boolean | null; }
interface Expense { id: string; category: string; amount_minor: number; currency: string; }
interface Warning { id: string; severity: string; message: string; }

export default function TripDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<{
    trip?: Trip; stops: Stop[]; lodging: Lodging[]; meals: Meal[]; expenses: Expense[]; warnings: Warning[];
  }>({ stops: [], lodging: [], meals: [], expenses: [], warnings: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      api.get<Trip>(`/trips/${id}`),
      api.get<Stop[]>(`/trips/${id}/stops`),
      api.get<Lodging[]>(`/trips/${id}/lodging`),
      api.get<Meal[]>(`/trips/${id}/meals`),
      api.get<Expense[]>(`/trips/${id}/expenses`),
      api.get<Warning[]>(`/trips/${id}/warnings`),
    ])
      .then(([trip, stops, lodging, meals, expenses, warnings]) =>
        setData({ trip, stops, lodging, meals, expenses, warnings })
      )
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(load, [load]);

  if (loading) return <ActivityIndicator accessibilityLabel="Loading trip" style={{ marginTop: 40 }} />;
  if (error) return <View style={{ padding: 16 }}><Text accessibilityRole="alert">Error: {error}</Text></View>;

  const { trip, stops, lodging, meals, expenses, warnings } = data;
  const blocking = warnings.filter((w) => w.severity === "blocking");

  return (
    <ScrollView>
      <ScreenHeader title={trip?.title ?? "Trip"} />
      {blocking.length > 0 && (
        <View style={{ backgroundColor: "#fdecea", padding: 12, margin: 12, borderRadius: 10 }} accessibilityRole="alert">
          <Text style={{ fontWeight: "700" }}>⚠ Blocking warnings</Text>
          {blocking.map((w) => <Text key={w.id}>• {w.message}</Text>)}
          <PrimaryButton label="Refresh warnings" onPress={() => api.post(`/trips/${id}/warnings/refresh`, {}).then(load)} />
        </View>
      )}

      <Card title="Stops">
        {stops.length === 0 ? <Text>No stops yet.</Text> :
          stops.map((s) => <Text key={s.id}>• {s.name ?? s.stop_type}{s.required ? " (required)" : ""}</Text>)}
        <PrimaryButton label="Add stop" onPress={() => router.push(`/trips/${id}/stops/new`)} />
      </Card>

      <Card title="Lodging">
        {lodging.length === 0 ? <Text>No lodging yet.</Text> :
          lodging.map((l) => (
            <Text key={l.id}>• {l.name} {l.user_confirmed ? "✓ confirmed" : ""}{l.required_accessibility_confirmed ? " · accessibility confirmed" : ""}</Text>
          ))}
      </Card>

      <Card title="Meals">
        {meals.length === 0 ? <Text>No meals planned.</Text> :
          meals.map((m) => <Text key={m.id}>• {m.meal_type}: {m.restaurant_name ?? "—"}{m.serves_fish ? " (serves fish)" : ""}</Text>)}
      </Card>

      <Card title="Expenses">
        {expenses.length === 0 ? <Text>No expenses.</Text> :
          expenses.map((e) => <Text key={e.id}>• {e.category}: {(e.amount_minor / 100).toFixed(2)} {e.currency}</Text>)}
      </Card>
    </ScrollView>
  );
}
