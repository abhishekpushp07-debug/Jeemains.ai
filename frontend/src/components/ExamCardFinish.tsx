import React, { useCallback, useEffect, useRef, useState } from "react";
import { Animated, AppState, Easing, Platform, StyleSheet, View } from "react-native";
import { useFocusEffect } from "expo-router";
import { useReducedMotion } from "react-native-reanimated";
import { ExamCardKind, examCardColors } from "@/src/theme";
import { websiteMotion } from "@/src/websiteDesign";
import { WebsiteGradient } from "./WebsiteGradient";

/** Exported seven-second, staggered mobile shine. Static polish never disappears. */
export function ExamCardFinish({ enabled, kind, testID }: { enabled: boolean; kind: ExamCardKind; testID: string }) {
  const reduced = useReducedMotion(), palette = examCardColors(kind);
  const [focused, setFocused] = useState(false);
  const [foreground, setForeground] = useState(AppState.currentState === "active");
  const [width, setWidth] = useState(1);
  const progress = useRef(new Animated.Value(0)).current;
  useFocusEffect(useCallback(() => { setFocused(true); return () => setFocused(false); }, []));
  useEffect(() => { const sub = AppState.addEventListener("change", s => setForeground(s === "active")); return () => sub.remove(); }, []);
  const running = enabled && !reduced && focused && foreground;
  useEffect(() => {
    progress.setValue(0);
    if (!running) return;
    const duration = kind === "live" ? 1500 : websiteMotion.exam_shine_seconds * 1000;
    const delay = kind === "live" ? 200 : websiteMotion.exam_shine_delays_seconds[kind === "jee" ? 0 : kind === "bitsat" ? 1 : 2] * 1000;
    const sweep = Animated.timing(progress, { toValue: 1, duration, easing: Easing.inOut(Easing.ease), useNativeDriver: Platform.OS !== "web" });
    const animation = Animated.sequence([Animated.delay(delay), kind === "live" ? sweep : Animated.loop(sweep)]);
    animation.start();
    return () => animation.stop();
  }, [progress, running, kind]);
  return <View testID={testID} pointerEvents="none" style={StyleSheet.absoluteFill} onLayout={({ nativeEvent }) => setWidth(nativeEvent.layout.width)}>
    <WebsiteGradient testID={`${testID}-glass`} value={palette.layers} />
    <View style={[styles.inner, { borderColor: palette.innerLine }]} />
    {running ? <Animated.View testID={`${testID}-shine`} style={[StyleSheet.absoluteFill, { opacity: progress.interpolate({ inputRange: [0, .1, .3, .55, 1], outputRange: [0, 0, 1, 0, 0] }), transform: [{ translateX: progress.interpolate({ inputRange: [0, .55, 1], outputRange: [-width, width, width] }) }] }]}>
      <WebsiteGradient value={palette.shine} />
    </Animated.View> : null}
  </View>;
}
const styles = StyleSheet.create({ inner: { position: "absolute", top: 6, bottom: 6, left: 6, right: 6, borderWidth: 1, borderRadius: 16 } });