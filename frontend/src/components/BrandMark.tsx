import React, { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { SvgXml } from "react-native-svg";
import Constants from "expo-constants";
import { colors } from "@/src/theme";
import { Press, T } from "./ui";

const backend = Constants.expoConfig?.extra?.backendUrl || process.env.EXPO_PUBLIC_BACKEND_URL;
const logoUri = `${backend}/api/brand/logo.svg`;
let publicLogo: string | null = null;

export function BrandMark({ testID = "brand-mark" }: { testID?: string }) {
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [retry, setRetry] = useState(0);
  const [xml, setXml] = useState<string | null>(publicLogo);
  useEffect(() => {
    const controller = new AbortController();
    if (publicLogo) { setXml(publicLogo); setState("ready"); return; }
    fetch(logoUri, { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error("Original logo unavailable");
      // Accessibility belongs to the native wrapper. SvgXml otherwise turns this
      // browser-only aria-labelledby into an invalid React ariaLabelledby prop.
      // No path, gradient, viewBox or source pixel is changed.
      const source = (await response.text()).replace(/\s(?:role|aria-labelledby)="[^"]*"/g, "");
      if (controller.signal.aborted) return;
      publicLogo = source;
      setXml(source);
      setState("ready");
    }).catch(() => { if (!controller.signal.aborted) setState("error"); });
    return () => controller.abort();
  }, [retry]);
  return <View testID={testID} style={styles.logo} accessibilityLabel="Jeelive.ai — Score 200+ with AI" accessibilityRole="image">
    {xml && state === "ready" ? <View testID={`${testID}-original-loaded`} style={StyleSheet.absoluteFill}><SvgXml xml={xml} width="100%" height="100%" onError={() => setState("error")} /></View> : null}
    {state === "loading" ? <ActivityIndicator testID={`${testID}-loading`} style={StyleSheet.absoluteFill} color={colors.brandText} /> : null}
    {state === "error" ? <Press testID={`${testID}-retry`} accessibilityLabel="Retry original logo" style={styles.fallback} onPress={() => { setState("loading"); setRetry(n => n + 1); }}>
      <T size={20} w="heavy">Jeelive.ai</T><T size={10} color={colors.muted}>Tap to reload logo</T>
    </Press> : null}
  </View>;
}
const styles = StyleSheet.create({ logo: { width: 180, height: 72, flexShrink: 1 }, fallback: { position: "absolute", top: 0, bottom: 0, left: 0, right: 0, backgroundColor: colors.surface, justifyContent: "center", minHeight: 44 } });