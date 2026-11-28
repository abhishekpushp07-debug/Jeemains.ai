// Settings > Privacy: "Share usage analytics" (on by default). Off stops every new analytics event on this phone
// (src/jlTracker.ts optOut); on starts them again (optIn). The choice is kept on the phone across restarts.
import React, { useEffect, useState } from "react";
import { Pressable, StyleSheet, Switch, View } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { T } from "@/src/components/ui";
import { IconCircle } from "@/src/components/design";
import { colors, space } from "@/src/theme";
import { optIn, optOut } from "@/src/jlTracker";

export const ANALYTICS_NOTICE = "We use first-party analytics (no ads, no third-party trackers) to understand how JLive is used and to improve it. You can turn this off any time in Settings > Privacy.";

export function AnalyticsSwitch() {
  const [on, setOn] = useState<boolean | null>(null);
  useEffect(() => {
    AsyncStorage.getItem("jl_optout").then((v) => setOn(v !== "1")).catch(() => setOn(true));
  }, []);
  const change = (next: boolean) => {
    setOn(next);
    if (next) optIn(); else optOut();
  };
  return <Pressable testID="account-analytics" onPress={() => on !== null && change(!on)} disabled={on === null} accessibilityRole="switch"
    accessibilityLabel="Share usage analytics" accessibilityState={{ checked: on ?? true }} style={styles.row}>
    <IconCircle icon="chart-line-variant" color={colors.onSurface} size={40} />
    <View style={{ flex: 1, gap: 1 }}>
      <T testID="account-analytics-label" w="semibold" size={15.5}>Share usage analytics</T>
      <T testID="account-analytics-notice" size={12.5} color={colors.muted}>{ANALYTICS_NOTICE}</T>
    </View>
    {/* The whole row is the button (44 px and more); the switch only shows the state. */}
    <View pointerEvents="none">
      <Switch testID="account-analytics-switch" value={on ?? true} disabled={on === null}
        trackColor={{ false: colors.custom_dim, true: colors.success }} />
    </View>
  </Pressable>;
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 68, paddingHorizontal: space.lg, paddingVertical: space.sm },
});
