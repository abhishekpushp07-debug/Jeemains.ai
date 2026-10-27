import React, { memo } from "react";
import { PixelRatio, Platform, StyleSheet, View } from "react-native";
import { Image } from "expo-image";
import { useImageValue } from "../AssetImage";

const WarmImage = memo(function WarmImage({ path, width }: { path: string; width: number }) {
  const value = useImageValue(path);
  if (!value) return null;
  const ratio = value.width && value.height ? value.width / value.height : 2.2;
  const pixels = Math.min(value.width || width * PixelRatio.get(), width * PixelRatio.get());
  if (pixels * pixels / ratio * 4 > 4 * 1024 * 1024) return null;
  // Same target size/cache key as the reading surface. No disk cache or full
  // paper of native bitmaps; only the bounded neighbouring-question window.
  return <Image source={{ uri: value.uri, cacheKey: value.cacheKey }} cachePolicy="memory" contentFit="contain" priority="low" transition={0} style={{ width, aspectRatio: ratio }} />;
});
export const ImageWarmup = memo(function ImageWarmup({ paths, width }: { paths: string[]; width: number }) {
  if (Platform.OS === "web") return null;
  return <View pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.hidden}>
    {paths.map(path => <WarmImage key={path} path={path} width={width} />)}
  </View>;
});
const styles = StyleSheet.create({ hidden: { position: "absolute", opacity: 0, height: 1, width: 1, overflow: "hidden" } });