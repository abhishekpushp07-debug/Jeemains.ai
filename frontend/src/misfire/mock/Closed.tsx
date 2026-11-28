// Offline Misfire behind the offline door, when this phone may not open the account's things now (signed out, or 7 days
// without a confirmed session: src/offline/identity.ts). The same words as the offline home's.
import React from "react";
import { useRouter } from "expo-router";
import { Empty, Skeleton } from "@/src/components/ui";
import { DCard, Pill } from "@/src/components/design";
import { View } from "react-native";
import { space } from "@/src/theme";

export function MockClosed() {
  const router = useRouter();
  return <DCard testID="mock-closed"><Empty icon="cloud-off-outline" title="Pehle ek baar internet ke saath app kholo"
    body="Bina internet Offline Misfire ke liye is phone par pichhle 7 din mein ek baar sign in hona zaroori hai."
    action={<Pill testID="mock-closed-entry" kind="outline" label="Sign in screen" onPress={() => router.replace("/entry")} />} /></DCard>;
}

export function MockChecking({ testID = "mock-checking" }: { testID?: string }) {
  return <View testID={testID} style={{ gap: space.md }}><Skeleton h={160} /><Skeleton h={90} /></View>;
}
