// Offline Misfire behind the offline door: the mocks made on this phone, and "Naya mock banao" from the finished papers
// kept here. The same list as Misfire's "Offline Misfire" tab (src/misfire/mock/MocksTab.tsx). Open to the signed-in
// student, and without a line to the account confirmed on this phone in the last 7 days.
import React from "react";
import { View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { ScreenHeader } from "@/src/components/design";
import { colors, space } from "@/src/theme";
import { MocksTab } from "@/src/misfire/mock/MocksTab";
import { MockChecking, MockClosed } from "@/src/misfire/mock/Closed";
import { useMockAccess } from "@/src/misfire/mock/offline";

export default function OfflineMisfire() {
  const router = useRouter(), insets = useSafeAreaInsets();
  const access = useMockAccess();
  const back = () => (router.canGoBack() ? router.back() : router.replace("/offline" as any));
  return <View testID="offline-misfire-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
    <ScreenHeader testID="offline-misfire-header" title="Offline Misfire" eyebrow="Apni galtiyon se mock · bina internet bhi" backTestID="offline-misfire-back" onBack={back} />
    {access.state === "open" ? <MocksTab online={access.online} />
      : <View style={{ paddingHorizontal: space.lg }}>{access.state === "closed" ? <MockClosed /> : <MockChecking />}</View>}
  </View>;
}
