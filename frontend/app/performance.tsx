import React, { useState } from "react";
import { Platform, ScrollView, Share, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { loadingMetrics } from "@/src/assets/loadingMetrics";
import { Button, Card, Header, Notice, T } from "@/src/components/ui";
import { colors, space } from "@/src/theme";

const names: Record<string, string> = { disk_read: "Encrypted cache read", image_network: "Image server + download", image_encode: "Native image preparation", image_paint: "Open → displayed image", math_update: "Maths update → layout" };
export default function Performance() {
  const router = useRouter(), insets = useSafeAreaInsets();
  const [report, setReport] = useState(() => loadingMetrics.snapshot());
  const [message, setMessage] = useState("");
  return <View testID="loading-performance-screen" style={[styles.screen, { paddingTop: insets.top }]}>
    <Header title="Loading performance" eyebrow="THIS DEVICE ONLY" backTestID="loading-performance-back" onBack={() => router.back()} />
    <ScrollView contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + space.xl }]}>
      <Notice testID="loading-performance-explanation">Open a paper or released solutions, move between questions, then return here. These are actual timings from this app session, not estimated speed scores.</Notice>
      <T testID="loading-performance-privacy" size={13} color={colors.muted}>Only counts and timings are kept in memory. No phone number, question text, answer, URL or login information is collected. Nothing is uploaded automatically.</T>
      {Object.entries(report.stages).map(([key, value]) => <Card key={key} testID={`loading-stage-${key}`} style={styles.row}>
        <T testID={`loading-stage-label-${key}`} size={15} w="bold">{names[key] || key}</T>
        <T testID={`loading-stage-values-${key}`} size={14}>Median {value.p50} ms · p95 {value.p95} ms</T>
        <T testID={`loading-stage-count-${key}`} size={12} color={colors.muted}>{value.n} recent samples</T>
      </Card>)}
      {!Object.keys(report.stages).length ? <T testID="loading-performance-empty" size={14}>No image measurements yet. Open a question or solution first.</T> : null}
      <T testID="loading-performance-counts" size={13} color={colors.muted}>Memory hits: {report.counters.memory_hit || 0} · Encrypted cache hits: {report.counters.disk_hit || 0} · Image opens: {report.counters.image_open || 0}</T>
      <T testID="loading-performance-context" size={12} color={colors.muted}>Cold and cached loads are included. Prefetched downloads are included in network timings. Paint timing ends at the image display callback; it is not an FPS measurement. Web preview cannot measure Android decoding.</T>
      <Button testID="loading-performance-refresh" label="Refresh timings" onPress={() => setReport(loadingMetrics.snapshot())} />
      <Button testID="loading-performance-share" label="Share timing report" kind="secondary" onPress={async () => { try { await Share.share({ message: JSON.stringify({ app: "JEELIVE loading", platform: Platform.OS, ...report }, null, 2) }); } catch { setMessage("The report could not be shared. Please try again."); } }} />
      <Button testID="loading-performance-reset" label="Reset timings only" kind="ghost" onPress={() => { loadingMetrics.reset(); setReport(loadingMetrics.snapshot()); setMessage("Timings reset. Saved answers and cached images are unchanged."); }} />
      {message ? <T testID="loading-performance-message" size={13}>{message}</T> : null}
    </ScrollView>
  </View>;
}
const styles = StyleSheet.create({ screen: { flex: 1, backgroundColor: colors.surface }, content: { padding: space.lg, gap: space.lg }, row: { gap: space.sm } });