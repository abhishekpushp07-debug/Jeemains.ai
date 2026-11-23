import React, { memo, useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { ActivityIndicator, Modal, Pressable, ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { Image } from "expo-image";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { ApiError, assetDataUri, privateAssets } from "@/src/api/client";
import { drawAsPlain } from "@/src/assets/assetGrants";
import { Icon, Press, T } from "@/src/components/ui";
import { colors, radius, space } from "@/src/theme";
import { clock, loadingMetrics } from "@/src/assets/loadingMetrics";

// Native decoded memory only; persistent source bytes use our encrypted store.
type Props = { path: string; label: string; testID?: string; onLoaded?: (path: string) => void; onFailed?: (path: string) => void };
export const AssetImage = memo(function AssetImage(props: Props) { return <OriginalImage key={props.path} {...props} />; });
export function useImageValue(path: string) {
  return useSyncExternalStore(useCallback(listener => privateAssets.subscribePath(path, listener), [path]), useCallback(() => privateAssets.value(path), [path]), () => undefined);
}

// A passing failure (no line, busy, the website down for a minute) is asked for again on its own, each time a little
// later (~67 s in all); only then does the student see a Retry button.
const RETRY_DELAYS = [2000, 5000, 10000, 20000, 30000];
const IMAGE_DOWN = "This picture could not load right now. Your answers are safe. Tap retry.";
const passing = (e: any) => !(e instanceof ApiError) || e.status === 0 || e.status === 408 || e.status === 429 || e.status >= 500;
export function useImageRetry(path: string, value: unknown) {
  const [attempt, setAttempt] = useState(0); // a bump asks for the picture again
  const [error, setError] = useState("");
  const [retrying, setRetrying] = useState(false); // only while an automatic try is waiting or running
  const tries = useRef(0), timer = useRef<any>(null);
  useEffect(() => { tries.current = 0; setRetrying(false); return () => clearTimeout(timer.current); }, [path]);
  useEffect(() => { if (value) { tries.current = 0; setRetrying(false); } }, [value]); // loaded: a later failure gets the full set of tries again
  const failed = useCallback((e: any) => {
    if (e?.name === "AbortError") return;
    // The picture arrived but the phone could not draw it: the next try fetches the plain picture afresh.
    if (e?.message === "display") drawAsPlain(path);
    if (passing(e) && tries.current < RETRY_DELAYS.length) {
      const wait = Math.max(RETRY_DELAYS[tries.current++], e?.retryAfterMs || 0);
      clearTimeout(timer.current);
      setRetrying(true);
      timer.current = setTimeout(() => { privateAssets.invalidate(path); setAttempt(n => n + 1); }, wait);
      return;
    }
    setRetrying(false);
    setError(passing(e) ? IMAGE_DOWN : e?.message || IMAGE_DOWN);
  }, [path]);
  const retry = useCallback(() => {
    tries.current = 0; clearTimeout(timer.current);
    privateAssets.invalidate(path); setRetrying(false); setError(""); setAttempt(n => n + 1);
  }, [path]);
  return { attempt, error, retrying, failed, retry };
}
function OriginalImage({ path, label, testID = "source-image", onLoaded, onFailed }: Props) {
  const value = useImageValue(path);
  const displayed = value?.uri;
  const source = useMemo(() => ({ uri: displayed, cacheKey: value?.cacheKey }), [displayed, value?.cacheKey]);
  const started = useRef(0);
  const measured = useRef(false);
  const { attempt, error: err, retrying, failed, retry } = useImageRetry(path, value);
  const [ratio, setRatio] = useState(2.2);
  const [zoom, setZoom] = useState(false);
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  useEffect(() => {
    let alive = true;
    started.current = clock(); measured.current = false;
    loadingMetrics.count("image_open");
    if (privateAssets.peek(path)) loadingMetrics.count("memory_hit");
    assetDataUri(path).catch(e => { if (alive && e?.name !== "AbortError") { loadingMetrics.count("image_error"); failed(e); } });
    return () => { alive = false; };
  }, [path, attempt, failed]);
  // An explicit manifest invalidation must refetch, not retain an old URI.
  useEffect(() => { if (!value && !err) void assetDataUri(path).catch(() => {}); }, [path, value, err]);
  useEffect(() => { if (err) onFailed?.(path); }, [err, onFailed, path]);
  if (err) return <View testID={`${testID}-error`} style={styles.error}>
    <T testID={`${testID}-error-text`} size={13} w="medium" color={colors.error}>{err}</T>
    <Press testID={`${testID}-retry`} onPress={retry} style={styles.retry}>
      <T size={13} w="bold" color={colors.brandText}>Retry original image</T>
    </Press>
  </View>;
  if (!displayed) return <View testID={`${testID}-loading`} accessibilityLabel="Preparing question image" style={styles.loading}>
    <ActivityIndicator color={colors.brandText} />
    {retrying ? <T testID={`${testID}-retrying`} size={12} color={colors.muted}>Picture is taking longer · trying again</T> : null}
  </View>;
  return <>
    <Pressable testID={testID} onPress={() => setZoom(true)} accessibilityRole="imagebutton" accessibilityLabel={`${label}. Tap to zoom`}>
      <Image source={source} testID={`${testID}-bitmap`} recyclingKey={value?.cacheKey || path} cachePolicy="memory" priority="high" transition={0} style={[styles.image, { aspectRatio: value?.width && value.height ? value.width / value.height : ratio }]} contentFit="contain"
        onError={() => failed(new Error("display"))}
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