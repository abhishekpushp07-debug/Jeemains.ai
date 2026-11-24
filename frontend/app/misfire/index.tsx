// Misfire: every wrong or skipped question, to be solved again. "Sab" is the website's own Misfire; the other tabs show
// it paper by paper for each test family (AITS, JEE Chapter-wise, JEE PYQ, BITSAT Mocks, BITSAT Chapter-wise, COMEDK Mocks).
import React, { useEffect, useRef, useState } from "react";
import { StyleSheet, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { useCached } from "@/src/useCached";
import { useListFocus } from "@/src/useListFocus";
import { useExams } from "@/src/api/examCatalog";
import { T } from "@/src/components/ui";
import { ScreenHeader } from "@/src/components/design";
import { colors, space } from "@/src/theme";
import { FAMILIES, MisfireSummary, getSummary, misfireKey } from "@/src/misfire/api";
import { AllTab } from "@/src/misfire/AllTab";
import { PapersTab } from "@/src/misfire/PapersTab";
import { PillRow } from "@/src/misfire/parts";
import { misfireAccount } from "@/src/misfire/store";

// Coming back to Misfire opens the tab it was left on.
const memo = { tab: "all" };

export default function Misfire() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const params = useLocalSearchParams<{ tab?: string; subject?: string; chapter?: string; at?: string }>();
  if (user) misfireAccount(user.id);
  const catalog = useExams();
  // A family of an exam the owner has hidden on the website is not offered.
  const families = FAMILIES.filter(f => !catalog.exams || catalog.exams.some(e => e.slug === f.exam));
  const [tab, setTab] = useState(params.chapter ? "all" : params.tab || memo.tab);
  useEffect(() => { if (params.chapter) setTab("all"); else if (params.tab) setTab(params.tab); }, [params.tab, params.chapter, params.at]);
  const family = families.find(f => f.key === tab);
  memo.tab = family ? family.key : "all";
  const summary = useCached<MisfireSummary>(user ? `${misfireKey(user.id)}.summary` : null, getSummary);
  useListFocus(summary.revalidate);
  const d = summary.data, tries = useRef(0), revalidate = summary.revalidate;
  useEffect(() => {
    if (!d?.waiting || tries.current >= 8) return;
    const t = setTimeout(() => { tries.current++; revalidate(); }, 3000);
    return () => clearTimeout(t);
  }, [d, revalidate]);

  return <View testID="misfire-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
    <ScreenHeader testID="misfire-header" title="Misfire" eyebrow="Galat + chhode sawaal · dobara solve karo" backTestID="misfire-back"
      onBack={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)"))}
      right={d ? <View style={styles.badge}><T testID="misfire-open-count" w="bold" size={11} color={colors.brandText} style={{ letterSpacing: 1.2 }}>{d.open} OPEN</T></View> : null} />
    <View style={{ paddingHorizontal: space.lg, paddingBottom: space.md }}>
      <PillRow prefix="misfire-tab" value={family ? family.key : "all"} onChange={setTab} items={[{ key: "all", label: "Sab" }, ...families.map(f => ({ key: f.key, label: f.label }))]} />
    </View>
    {!user ? null : family ? <PapersTab key={family.key} uid={user.id} family={family} />
      : <AllTab key={`${params.subject || ""}|${params.chapter || ""}|${params.at || ""}`} uid={user.id} summary={d} startSubject={params.subject} startChapter={params.chapter} />}
  </View>;
}

const styles = StyleSheet.create({
  badge: { borderRadius: 999, paddingHorizontal: 12, paddingVertical: 6, backgroundColor: colors.brandTertiary },
});
