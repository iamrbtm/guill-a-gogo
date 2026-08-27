import { ReactNode } from "react";
import { Pressable, Text, TextInput, View, StyleSheet } from "react-native";

// Shared accessible primitives. All touch targets are >=44pt and carry labels.

export function ScreenHeader({ title }: { title: string }) {
  return (
    <View style={styles.header} accessibilityRole="header">
      <Text style={styles.headerText}>{title}</Text>
    </View>
  );
}

export function AccessibleInput({
  label,
  value,
  onChangeText,
  multiline,
  secure,
}: {
  label: string;
  value: string;
  onChangeText: (t: string) => void;
  multiline?: boolean;
  secure?: boolean;
}) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={[styles.input, multiline && styles.inputMultiline]}
        value={value}
        onChangeText={onChangeText}
        multiline={multiline}
        secureTextEntry={secure}
        accessibilityLabel={label}
        autoCapitalize="none"
      />
    </View>
  );
}

export function PrimaryButton({ label, onPress, disabled }: { label: string; onPress: () => void; disabled?: boolean }) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      accessibilityRole="button"
      accessibilityLabel={label}
      style={({ pressed }) => [
        styles.button,
        pressed && styles.buttonPressed,
        disabled && styles.buttonDisabled,
      ]}
    >
      <Text style={styles.buttonText}>{label}</Text>
    </Pressable>
  );
}

export function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>{title}</Text>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  header: { padding: 16, paddingTop: 24, backgroundColor: "#0b3d2e" },
  headerText: { color: "#fff", fontSize: 22, fontWeight: "700" },
  field: { marginBottom: 12 },
  label: { fontSize: 15, marginBottom: 4, color: "#222" },
  input: {
    borderWidth: 1, borderColor: "#bbb", borderRadius: 8, padding: 12,
    fontSize: 16, minHeight: 44, backgroundColor: "#fff",
  },
  inputMultiline: { minHeight: 88, textAlignVertical: "top" },
  button: {
    backgroundColor: "#0b3d2e", borderRadius: 10, paddingVertical: 12,
    paddingHorizontal: 20, minHeight: 48, justifyContent: "center", alignItems: "center",
  },
  buttonPressed: { opacity: 0.8 },
  buttonDisabled: { backgroundColor: "#9bb3a8" },
  buttonText: { color: "#fff", fontSize: 17, fontWeight: "600" },
  card: {
    backgroundColor: "#fff", borderRadius: 12, padding: 16, margin: 12,
    shadowColor: "#000", shadowOpacity: 0.05, shadowRadius: 4,
  },
  cardTitle: { fontSize: 18, fontWeight: "700", marginBottom: 8, color: "#0b3d2e" },
});
