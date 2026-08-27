import { Stack } from "expo-router";
import { TamaguiProvider } from "./ui/provider";

export default function RootLayout() {
  return (
    <TamaguiProvider>
      <Stack screenOptions={{ headerShown: true }}>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      </Stack>
    </TamaguiProvider>
  );
}
