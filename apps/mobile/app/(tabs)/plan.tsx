import { useEffect, useState } from "react";
import { ActivityIndicator, FlatList, Text } from "react-native";
import { Link } from "expo-router";
import { api, Trip } from "../lib/api";
import { Card, ScreenHeader } from "../components/ui";

export default function PlanScreen() {
  const [trips, setTrips] = useState<Trip[] | null>(null);
  useEffect(() => {
    api.get<Trip[]>("/trips").then(setTrips).catch(() => setTrips([]));
  }, []);

  if (trips === null) return <ActivityIndicator accessibilityLabel="Loading plan" style={{ marginTop: 40 }} />;

  return (
    <FlatList
      ListHeaderComponent={<ScreenHeader title="Plan" />}
      data={trips}
      keyExtractor={(t) => t.id}
      renderItem={({ item }) => (
        <Link href={`/trips/${item.id}`} asChild>
          <Card title={item.title}>
            <Text>Open itinerary, stops, lodging, meals, and budget.</Text>
          </Card>
        </Link>
      )}
      ListEmptyComponent={<Text style={{ padding: 16 }}>No trips to plan yet.</Text>}
    />
  );
}
