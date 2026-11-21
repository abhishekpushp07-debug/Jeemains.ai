import React, { memo } from "react";
import { PixelRatio, Platform, StyleSheet, View } from "react-native";
import { Image } from "expo-image";
import { useImageValue } from "../AssetImage";

const WarmImage = memo(function WarmImage({ path, width, height }: { path: string; width: number; height?: number }) {
  const value = useImageValue(path);
  if (!value) return null;
  const ratio = height ? width / height : value.width && value.height ? value.width / value.height : 2.2;
  const pixels = Math.min(value.width || width * PixelRatio.get(), width * PixelRatio.get());
  if (pixels * pixels / ratio * 4 > 4 * 1024 * 1024) return null;
  // Same target size/cache key as the reading surface. No disk cache or full
  // paper of native bitmaps; only the bounded neighbouring-question window.
  return <Image source={{ uri: value.uri, cacheKey: value.cacheKey }} cachePolicy="memory" contentFit="contain" priority="low" transition={0} style={height ? { width, height } : { width, aspectRatio: ratio }} />;
});
/** `sizes`: pictures drawn at their own size (cut pieces); every other picture is drawn `width` wide. */
export const ImageWarmup = memo(function ImageWarmup({ paths, width, sizes }: { paths: string[]; width: number; sizes?: Record<string, { width: number; height: number }> }) {
  if (Platform.OS === "web") return null;
  return <View pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.hidden}>
    {paths.map(path => <WarmImage key={path} path={path} width={sizes?.[path]?.width ?? width} height={sizes?.[path]?.height} />)}
  </View>;
});
const styles = StyleSheet.create({ hidden: { position: "absolute", opacity: 0, height: 1, width: 1, overflow: "hidden" } });