import React, { useCallback, useEffect, useRef, useState } from "react";
import { Animated, AppState, Easing, Platform, StyleSheet, View } from "react-native";
import { useFocusEffect } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { useReducedMotion } from "react-native-reanimated";
import { colors } from "@/src/theme";

/** Native equivalent of the supplied website's 4.8-second exam-card sheen. */
export function ExamCardFinish({ enabled, kind, testID }: { enabled: boolean; kind: "jee" | "bitsat"; testID: string }) {
  const reduced = useReducedMotion();
  const [focused, setFocused] = useState(false);
  const [foreground, setForeground] = useState(AppState.currentState === "active");
  useFocusEffect(useCallback(() => { setFocused(true); return () => setFocused(false); }, []));
  useEffect(() => {
    const listener = AppState.addEventListener("change", (state) => setForeground(state === "active"));
    return () => listener.remove();
  }, []);
  const progress = useRef(new Animated.Value(0)).current;
  const [width, setWidth] = useState(180);
  const running = enabled && !reduced && focused && foreground;
  useEffect(() => {
    progress.setValue(0);
    if (!running) return;
    const loop = Animated.loop(Animated.sequence([
      Animated.delay(384),
      Animated.timing(progress, { toValue: 1, duration: 1632, easing: Easing.inOut(Easing.ease), useNativeDriver: Platform.OS !== "web" }),
      Animated.delay(2784),
    ]));
    loop.start();
    return () => loop.stop();
  }, [progress, running]);
  return <View testID={testID} pointerEvents="none" style={StyleSheet.absoluteFill} onLayout={(event) => setWidth(event.nativeEvent.layout.width)}>
    <LinearGradient testID={`${testID}-glass`} colors={kind === "jee" ? [colors.custom_webJeeFinish, colors.custom_webTransparent] : [colors.custom_webFinishStrong, colors.custom_webFinishSoft, colors.custom_webTransparent]}
      start={{ x: 0.1, y: 0 }} end={{ x: 0.9, y: 1 }} locations={kind === "jee" ? [0, 0.37] : [0, 0.34, 0.35]} style={StyleSheet.absoluteFill} />
    <LinearGradient colors={[colors.custom_webBottomShade, colors.custom_webShadowClear]} locations={[0, 0.6]} start={{ x: 0, y: 1 }} end={{ x: 0, y: 0 }} style={StyleSheet.absoluteFill} />
    {running ? <Animated.View testID={`${testID}-shine`} style={[styles.shine, { transform: [
      { translateX: progress.interpolate({ inputRange: [0, 1], outputRange: [-width * 2, width * 2] }) },
      { rotate: "20deg" },
    ] }]}>
      <LinearGradient colors={[colors.custom_webTransparent, kind === "jee" ? colors.custom_webJeeShine : colors.custom_webBitsatShine, colors.custom_webTransparent]}
        locations={[0.35, 0.5, 0.65]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={StyleSheet.absoluteFill} />
    </Animated.View> : null}
  </View>;
}

const styles = StyleSheet.create({ shine: { position: "absolute", width: 160, top: -80, bottom: -80 } });