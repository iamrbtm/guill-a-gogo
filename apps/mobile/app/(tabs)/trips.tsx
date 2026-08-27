import { useEffect, useState } from "react";
import { ActivityIndicator, FlatList, Text, View } from "react-native";
import { Link, useRouter } from "expo-router";
import { api, Trip } from "../lib/api";
import { Card, PrimaryButton, ScreenHeader } from "../components/ui";

export default function TripsScreen() {
  const [trips, setTrips] = useState<Trip[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    api.get<Trip[]>("/trips").then(setTrips).catch((e) => setError(e.message));
  }, []);

  if (error) return <View style={{ padding: 16 }}><Text accessibilityRole="alert">Failed to load trips: {error}</Text></View>;
  if (trips === null) return <ActivityIndicator accessibilityLabel="Loading trips" style={{ marginTop: 40 }} />;

  return (
    <View>
      <ScreenHeader title="Trips" />
      <PrimaryButton label="New trip" onPress={() => router.push("/trips/new")} />
      <FlatList
        data={trips}
        keyExtractor={(t) => t.id}
        renderItem={({ item }) => (
          <Link href={`/trips/${item.id}`} asChild>
            <Card title={item.title}>
              <Text>{item.origin ?? "?"} → {item.destination ?? "?"}</Text>
              <Text>Status: {item.status}</Text>
            </Card>
          </Link>
        )}
        ListEmptyComponent={<Text style={{ padding: 16 }}>No trips yet. Create your first trip.</Text>}
      />
    </View>
  );
}
