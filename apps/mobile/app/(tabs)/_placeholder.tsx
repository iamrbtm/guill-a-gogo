import { Text, View } from "react-native";

export default function Placeholder({ label }: { label: string }) {
  return (
    <View style={{ flex: 1, alignItems: "center", justifyContent: "center", padding: 24 }}>
      <Text style={{ fontSize: 20, fontWeight: "600" }}>{label}</Text>
      <Text style={{ marginTop: 8, opacity: 0.6 }}>Scaffold — implemented in later phases.</Text>
    </View>
  );
}
