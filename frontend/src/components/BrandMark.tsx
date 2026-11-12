import React from "react";
import { StyleSheet, View } from "react-native";
import { SvgXml } from "react-native-svg";
import { BRAND_LOGO_XML } from "@/src/assets/brandLogo";
import { colors } from "@/src/theme";

// Same emblem and wordmark, inked for the light canvas.
const LIGHT_LOGO = BRAND_LOGO_XML.replace(/#FAF7F5/g, colors.onSurface).replace(/#FF6974/g, colors.brandText);

export function BrandMark({ testID = "brand-mark", height = 56 }: { testID?: string; height?: number }) {
  return <View testID={testID} style={[styles.logo, { height, width: height * 2.5 }]} accessibilityLabel="JeeCircle.ai — Score 200+ with AI" accessibilityRole="image">
    <View testID={`${testID}-original-loaded`} style={StyleSheet.absoluteFill}><SvgXml xml={LIGHT_LOGO} width="100%" height="100%" /></View>
  </View>;
}
const styles = StyleSheet.create({ logo: { flexShrink: 1 } });
