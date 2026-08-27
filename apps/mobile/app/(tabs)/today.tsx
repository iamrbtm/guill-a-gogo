import { Text, View } from "react-native";

export default function TodayScreen() {
  return (
    <View style={{ flex: 1, alignItems: "center", justifyContent: "center", padding: 24 }}>
      <Text style={{ fontSize: 20, fontWeight: "600" }}>Today mode</Text>
      <Text style={{ marginTop: 8, opacity: 0.6, textAlign: "center" }}>
        The low-clutter travel-day dashboard (next destination, departure deadline,
        fuel range, large navigation action, delay handling) arrives in Phase 4.
      </Text>
    </View>
  );
}
