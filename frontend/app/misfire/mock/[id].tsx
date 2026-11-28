// One Offline Misfire: not started yet (its questions, its time, "Shuru karo"), being taken (the paper screen), or over
// (its result and solutions). A mock whose clock ran out while the app was closed is marked the moment it is opened.
// The same screen behind the offline door (/offline/misfire/[id]): then open to the account confirmed on this phone lately.
import React, { useEffect } from "react";
import { View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { Empty, Skeleton } from "@/src/components/ui";
import { DCard, Pill, ScreenHeader } from "@/src/components/design";
import { colors, space } from "@/src/theme";
import { misfireAccount } from "@/src/misfire/store";
import { useMock } from "@/src/misfire/mock/store";
import { sendRight, settle } from "@/src/misfire/mock/marking";
import { MockReady } from "@/src/misfire/mock/Ready";
import { MockPlayer } from "@/src/misfire/mock/Player";
import { MockResult } from "@/src/misfire/mock/Result";
import { MockClosed } from "@/src/misfire/mock/Closed";
import { useMockAccess, useMockPaths } from "@/src/misfire/mock/offline";

export default function MisfireMockScreen() {
  const { id, short } = useLocalSearchParams<{ id: string; short?: string }>();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  if (user) misfireAccount(user.id);
  const access = useMockAccess(), paths = useMockPaths();
  // The mock is read once this phone may open the account's store (signed in, or the offline door's 7 days).
  const { mock, missing } = useMock(access.state === "open" ? id : undefined);
  useEffect(() => {
    if (!mock) return;
    const now = settle(mock, !!user);
    if (user && now.status === "done" && now.sync?.todo.length) void sendRight(now.id);
  }, [mock?.id, mock?.status]); // eslint-disable-line react-hooks/exhaustive-deps
  const back = () => (router.canGoBack() ? router.back() : router.replace(paths.list));

  if (!mock) return <View testID="mock-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
    <ScreenHeader testID="mock-header" title="Offline Misfire" backTestID="mock-back" onBack={back} />
    <View style={{ paddingHorizontal: space.lg, gap: space.md }}>
      {access.state === "closed" ? <MockClosed /> : missing ? <DCard testID="mock-missing"><Empty icon="file-question-outline" title="Yeh mock is phone par nahi hai." body="Mock usi phone par rehta hai jis par bana tha (sign out karne par hat jata hai). Naya mock banao."
        action={<Pill testID="mock-missing-new" kind="brand" label="Naya mock banao" onPress={() => router.replace(paths.make)} />} /></DCard>
        : <View testID="mock-loading" style={{ gap: space.md }}><Skeleton h={180} /><Skeleton h={90} /></View>}
    </View>
  </View>;
  if (mock.status === "ready") return <MockReady mock={mock} short={short === "1"} onBack={back} />;
  if (mock.status === "active") return <MockPlayer key={mock.id} mock={mock} />;
  return <MockResult mock={mock} onBack={back} />;
}
