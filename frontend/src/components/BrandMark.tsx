import React from "react";
import { StyleSheet, View } from "react-native";
import { SvgXml } from "react-native-svg";
import { BRAND_LOGO_XML } from "@/src/assets/brandLogo";

export function BrandMark({ testID = "brand-mark" }: { testID?: string }) {
  return <View testID={testID} style={styles.logo} accessibilityLabel="JeeCircle.ai — Score 200+ with AI" accessibilityRole="image">
    <View testID={`${testID}-original-loaded`} style={StyleSheet.absoluteFill}><SvgXml xml={BRAND_LOGO_XML} width="100%" height="100%" /></View>
  </View>;
}
const styles = StyleSheet.create({ logo: { width: 180, height: 72, flexShrink: 1 } });
