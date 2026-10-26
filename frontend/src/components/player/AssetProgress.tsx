import React from "react";
import { StyleSheet, View } from "react-native";
import { AssetProgress as Progress } from "@/src/assets/PrivateAssetQueue";
import { colors, space } from "@/src/theme";
import { Icon, Press, T } from "../ui";

export function AssetProgress({ progress, prefix, solutions = false }: { progress: Progress & { retry: () => void }; prefix: string; solutions?: boolean }) {
  if (!progress.total) return null;
  const done = progress.ready === progress.total;
  return <View testID={`${prefix}-image-progress`} style={styles.container}>
    <View style={styles.line}><Icon name={done ? "check-circle-outline" : progress.failed ? "cloud-alert" : "cloud-download-outline"} size={15} color={done ? colors.success : colors.muted} />
      <T testID={`${prefix}-image-count`} size={11} color={done ? colors.success : colors.muted} style={styles.copy}>{done ? `All ${progress.total} images ready` : `${progress.ready}/${progress.total} ${solutions ? "question & solution" : "question"} images ready${progress.limited ? " · memory-safe loading" : " · downloading in background"}`}</T>
      {progress.failed > 0 ? <Press testID={`${prefix}-retry-images`} onPress={progress.retry} style={styles.retry}><T size={11} w="bold" color={colors.brandText}>Retry {progress.failed}</T></Press> : null}
    </View>
    {!done ? <View style={styles.track}><View style={[styles.fill, { width: `${progress.total ? progress.ready / progress.total * 100 : 0}%` }]} /></View> : null}
  </View>;
}
const styles = StyleSheet.create({ container: { gap: 3 }, line: { flexDirection: "row", alignItems: "center", gap: 6 }, copy: { flex: 1 }, retry: { minHeight: 44, minWidth: 44, justifyContent: "center", paddingHorizontal: space.xs }, track: { height: 2, backgroundColor: colors.border, overflow: "hidden" }, fill: { height: 2, backgroundColor: colors.brandPrimary } });