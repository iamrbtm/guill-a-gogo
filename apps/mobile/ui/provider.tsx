import { ReactNode } from "react";

// Placeholder UI provider. Replace with Tamagui/ThemeProvider later.
// Kept dependency-free so the shell installs and runs without native builds.
export function TamaguiProvider({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
