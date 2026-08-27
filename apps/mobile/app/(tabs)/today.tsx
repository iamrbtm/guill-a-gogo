import { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { api, Trip } from "../lib/api";
import { Card, PrimaryButton, ScreenHeader } from "../components/ui";

interface Dashboard {
  trip_id: string;
  trip_title: string;
  day_number: number;
  next_stop: { name: string; address?: string } | null;
  remaining_count: number;
  completed_count: number;
  actions: Record<string, boolean>;
  eta_note: string;
}

export default function TodayScreen() {
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    // Pick the first trip and load its live dashboard.
    api.get<Trip[]>("/trips")
      .then((trips) => {
        if (trips.length === 0) return null;
        return api.get<Dashboard>(`/trips/${trips[0].id}/today`);
      })
      .then((d) => d && setDash(d))
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <View style={{ padding: 16 }}><Text accessibilityRole="alert">Error: {error}</Text></View>;
  if (dash === null) return <ActivityIndicator accessibilityLabel="Loading Today" style={{ marginTop: 40 }} />;

  const big = (label: string, enabled: boolean, onPress?: () => void) => (
    <PrimaryButton label={label} disabled={!enabled} onPress={() => onPress?.()} />
  );

  return (
    <ScrollView>
      <ScreenHeader title="Today" />
      <Card title={dash.trip_title}>
        <Text>Day {dash.day_number}</Text>
        <Text>Next: {dash.next_stop ? dash.next_stop.name : "—"}</Text>
        <Text>Remaining stops: {dash.remaining_count} · Completed: {dash.completed_count}</Text>
      </Card>

      <Card title="Navigation">
        <PrimaryButton
          label="Open Navigation"
          onPress={() => dash.next_stop && router.push(`/nav?trip=${dash.trip_id}&to=${encodeURIComponent(dash.next_stop.name)}`)}
        />
      </Card>

      <Card title="Actions">
        {big("Departed", !!dash.actions.can_depart)}
        {big("Arrived", !!dash.actions.can_arrive)}
        {big("Completed stop", !!dash.actions.can_complete_stop)}
        {big("Delayed", !!dash.actions.can_delay)}
        {big("Skipped", !!dash.actions.can_skip)}
        {big("Emergency pause", true)}
      </Card>

      <Text style={{ padding: 12, opacity: 0.6 }}>{dash.eta_note}</Text>
    </ScrollView>
  );
}
