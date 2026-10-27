import React, { memo, useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { ActivityIndicator, Modal, Pressable, ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { Image } from "expo-image";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { assetDataUri, privateAssets } from "@/src/api/client";
import { Icon, Press, T } from "@/src/components/ui";
import { colors, radius, space } from "@/src/theme";
import { clock, loadingMetrics } from "@/src/assets/loadingMetrics";

// Native decoded memory only; persistent source bytes use our encrypted store.
type Props = { path: string; label: string; testID?: string; onLoaded?: (path: string) => void; onFailed?: (path: string) => void };
export const AssetImage = memo(function AssetImage(props: Props) { return <OriginalImage key={props.path} {...props} />; });
export function useImageValue(path: string) {
  return useSyncExternalStore(useCallback(listener => privateAssets.subscribePath(path, listener), [path]), useCallback(() => privateAssets.value(path), [path]), () => undefined);
}
function OriginalImage({ path, label, testID = "source-image", onLoaded, onFailed }: Props) {
  const value = useImageValue(path);
  const displayed = value?.uri;
  const source = useMemo(() => ({ uri: displayed, cacheKey: value?.cacheKey }), [displayed, value?.cacheKey]);
  const started = useRef(0);
  const measured = useRef(false);
  const [err, setErr] = useState("");
  const [ratio, setRatio] = useState(2.2);
  const [zoom, setZoom] = useState(false);
  const [retry, setRetry] = useState(0);
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  useEffect(() => {
    let alive = true;
    started.current = clock(); measured.current = false;
    loadingMetrics.count("image_open");
    if (privateAssets.peek(path)) loadingMetrics.count("memory_hit");
    assetDataUri(path).catch(e => { if (alive && e?.name !== "AbortError") { loadingMetrics.count("image_error"); setErr(e.message); } });
    return () => { alive = false; };
  }, [path, retry]);
  // An explicit manifest invalidation must refetch, not retain an old URI.
  useEffect(() => { if (!value && !err) void assetDataUri(path).catch(() => {}); }, [path, value, err]);
  useEffect(() => { if (err) onFailed?.(path); }, [err, onFailed, path]);
  if (err) return <View testID={`${testID}-error`} style={styles.error}>
    <T testID={`${testID}-error-text`} size={13} w="medium" color={colors.error}>{err}</T>
    <Press testID={`${testID}-retry`} onPress={() => { privateAssets.invalidate(path); setErr(""); setRetry(n => n + 1); }} style={styles.retry}>
      <T size={13} w="bold" color={colors.brandText}>Retry original image</T>
    </Press>
  </View>;
  if (!displayed) return <View testID={`${testID}-loading`} accessibilityLabel="Preparing question image" style={styles.loading}><ActivityIndicator color={colors.brandText} /></View>;
  return <>
    <Pressable testID={testID} onPress={() => setZoom(true)} accessibilityRole="imagebutton" accessibilityLabel={`${label}. Tap to zoom`}>
      <Image source={source} testID={`${testID}-bitmap`} recyclingKey={value?.cacheKey || path} cachePolicy="memory" priority="high" transition={0} style={[styles.image, { aspectRatio: value?.width && value.height ? value.width / value.height : ratio }]} contentFit="contain"
        onError={() => setErr("The image could not be displayed. Retry the original image.")}
        onLoad={e => { if (e.source.width && e.source.height) setRatio(e.source.width / e.source.height); }}
        onDisplay={() => { if (!measured.current) { measured.current = true; loadingMetrics.record("image_paint", clock() - started.current); } onLoaded?.(path); }} />
      <View style={styles.zoomLabel}><Icon name="magnify-plus-outline" size={14} color={colors.onSurfaceInverse} /><T size={10} w="bold" color={colors.onSurfaceInverse}>Zoom</T></View>
    </Pressable>
    <Modal visible={zoom} animationType="fade" onRequestClose={() => setZoom(false)}>
      <View testID={`${testID}-zoom`} style={[styles.modal, { paddingTop: insets.top }]}>
        <Press testID="asset-zoom-close" onPress={() => setZoom(false)} accessibilityLabel="Close zoom" style={styles.close}><Icon name="close" size={24} color={colors.onSurface} /></Press>
        <ScrollView maximumZoomScale={4} minimumZoomScale={1} contentContainerStyle={styles.zoomScroll}>
          <ScrollView horizontal maximumZoomScale={4} contentContainerStyle={{ minWidth: width }}>
            <Image testID={`${testID}-zoom-bitmap`} source={source} recyclingKey={value?.cacheKey || path} cachePolicy="memory" transition={0} style={{ width, aspectRatio: value?.width && value.height ? value.width / value.height : ratio }} contentFit="contain" />
          </ScrollView>
        </ScrollView>
        <T testID={`${testID}-zoom-help`} size={12} color={colors.custom_onReading} style={[styles.help, { paddingBottom: insets.bottom + space.md }]}>Pinch or scroll to read the original.</T>
      </View>
    </Modal>
  </>;
}
const styles = StyleSheet.create({
  error: { padding: space.md, borderRadius: radius.md, backgroundColor: colors.custom_errorSoft, gap: 4 }, retry: { minHeight: 44, justifyContent: "center" },
  loading: { height: 120, gap: space.sm, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_reading },
  image: { width: "100%", backgroundColor: colors.custom_reading },
  zoomLabel: { position: "absolute", right: 6, bottom: 6, flexDirection: "row", gap: 4, alignItems: "center", backgroundColor: colors.custom_overlay, borderRadius: radius.pill, paddingHorizontal: 8, paddingVertical: 3 },
  modal: { flex: 1, backgroundColor: colors.custom_reading }, close: { alignSelf: "flex-end", margin: space.md, width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: colors.surface },
  zoomScroll: { flexGrow: 1, justifyContent: "center" }, help: { textAlign: "center", padding: space.md },
});