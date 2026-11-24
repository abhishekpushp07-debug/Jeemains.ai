// Solve again: the questions of the list that was open, one at a time, with Pichhla / Agla under the thumb.
import React, { useCallback, useLayoutEffect, useRef, useState } from "react";
import { ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { Redirect, useFocusEffect, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { privateAssets } from "@/src/api/client";
import { Icon, Press, T } from "@/src/components/ui";
import { ScreenHeader } from "@/src/components/design";
import { colors, space } from "@/src/theme";
import { grantPictures } from "@/src/misfire/api";
import { SolveCard } from "@/src/misfire/SolveCard";
import { applied, solveQueue, usePatches } from "@/src/misfire/store";

export default function MisfireSolve() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { width } = useWindowDimensions();
  const { user } = useAuth();
  usePatches();
  const queue = solveQueue();
  const [index, setIndex] = useState(queue.index);
  const page = useRef<React.ElementRef<typeof ScrollView>>(null);
  const raw = queue.items[index], next = queue.items[index + 1];
  // Before the pictures are asked for: this question and the next one may load theirs.
  useLayoutEffect(() => { if (raw) grantPictures(next ? [raw, next] : [raw]); }, [raw, next]);
  useFocusEffect(useCallback(() => { privateAssets.selectGroup("misfire"); }, []));
  const go = useCallback((by: number) => {
    const to = index + by;
    if (!queue.items[to]) return;
    queue.index = to; setIndex(to);
    page.current?.scrollTo({ y: 0, animated: false });
  }, [index, queue]);
  // Opened afresh (a reload in the browser): there is no list to walk through.
  if (!raw) return <Redirect href={"/misfire" as any} />;
  const item = applied(raw);
  const back = () => (router.canGoBack() ? router.back() : router.replace("/misfire" as any));

  return <View testID="misfire-solve-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
    <ScreenHeader testID="misfire-solve-header" title={`Q${item.number} · ${item.subject}`} eyebrow={item.title} backTestID="misfire-solve-back" onBack={back}
      right={<T testID="misfire-solve-position" w="mono" size={13} color={colors.muted}>{index + 1}/{queue.items.length}</T>} />
    <ScrollView ref={page} contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: space.xl }} keyboardShouldPersistTaps="handled">
      <SolveCard key={item.id} item={item} uid={user?.id} width={Math.max(1, width - 4 * space.lg - 2)} onDone={next ? () => go(1) : undefined} />
    </ScrollView>
    <View testID="misfire-solve-bar" style={[styles.bar, { paddingBottom: insets.bottom + 8 }]}>
      <Press testID="misfire-prev" disabled={index === 0} onPress={() => go(-1)} accessibilityLabel="Pichhla sawaal" style={styles.step}>
        <Icon name="chevron-left" size={20} color={colors.onSurface} /><T w="heavy" size={14}>Pichhla</T>
      </Press>
      <Press testID="misfire-next" disabled={!next} onPress={() => go(1)} accessibilityLabel="Agla sawaal" style={[styles.step, styles.next]}>
        <T w="heavy" size={14} color={colors.onSurfaceInverse}>Agla</T><Icon name="chevron-right" size={20} color={colors.onSurfaceInverse} />
      </Press>
    </View>
  </View>;
}

const styles = StyleSheet.create({
  bar: { flexDirection: "row", gap: space.md, paddingHorizontal: space.lg, paddingTop: 8, borderTopWidth: 1, borderTopColor: colors.custom_barLine, backgroundColor: colors.custom_bar },
  step: { flex: 1, height: 48, borderRadius: 24, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 4 },
  next: { backgroundColor: colors.onSurface, borderColor: colors.onSurface },
});
