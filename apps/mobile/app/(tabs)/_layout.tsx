import { Tabs } from "expo-router";

export default function TabsLayout() {
  return (
    <Tabs screenOptions={{ headerShown: true }}>
      <Tabs.Screen name="trips" options={{ title: "Trips" }} />
      <Tabs.Screen name="today" options={{ title: "Today" }} />
      <Tabs.Screen name="plan" options={{ title: "Plan" }} />
      <Tabs.Screen name="profiles" options={{ title: "Profiles" }} />
      <Tabs.Screen name="more" options={{ title: "More" }} />
    </Tabs>
  );
}
