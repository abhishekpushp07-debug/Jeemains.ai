import React, { useEffect, useState, useSyncExternalStore } from "react";
import { ActivityIndicator, Modal, Pressable, ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { Image } from "expo-image";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { assetDataUri, privateAssets } from "@/src/api/client";
import { Icon, Press, T } from "@/src/components/ui";
import { colors, radius, space } from "@/src/theme";

// Source stays unmodified, authenticated, private and memory-only. No disk cache.
type Props = { path: string; label: string; testID?: string; onLoaded?: (path: string) => void; onFailed?: (path: string) => void };
export function AssetImage(props: Props) { return <OriginalImage key={props.path} {...props} />; }
function OriginalImage({ path, label, testID = "source-image", onLoaded, onFailed }: Props) {
  const [uri, setUri] = useState<string | null>(() => privateAssets.peek(path) || null);
  useSyncExternalStore(privateAssets.subscribe, privateAssets.snapshot, privateAssets.snapshot);
  const displayed = privateAssets.peek(path) || uri;
  const [err, setErr] = useState("");
  const [ratio, setRatio] = useState(2.2);
  const [zoom, setZoom] = useState(false);
  const [retry, setRetry] = useState(0);
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  useEffect(() => {
    let alive = true;
    assetDataUri(path).then(u => { if (alive) setUri(u); }).catch(e => { if (alive && e?.name !== "AbortError") setErr(e.message); });
    return () => { alive = false; };
  }, [path, retry]);
  useEffect(() => { if (err) onFailed?.(path); }, [err, onFailed, path]);
  if (err) return <View testID={`${testID}-error`} style={styles.error}>
    <T testID={`${testID}-error-text`} size={13} w="medium" color={colors.error}>{err}</T>
    <Press testID={`${testID}-retry`} onPress={() => { setErr(""); setUri(privateAssets.peek(path) || null); setRetry(n => n + 1); }} style={styles.retry}>
      <T size={13} w="bold" color={colors.brandText}>Retry original image</T>
    </Press>
  </View>;
  if (!displayed) return <View testID={`${testID}-loading`} accessibilityLabel="Preparing question image" style={styles.loading}><ActivityIndicator color={colors.brandText} /></View>;
  return <>
    <Pressable testID={testID} onPress={() => setZoom(true)} accessibilityRole="imagebutton" accessibilityLabel={`${label}. Tap to zoom`}>
      <Image source={{ uri: displayed }} testID={`${testID}-bitmap`} recyclingKey={path} cachePolicy="memory" transition={0} style={[styles.image, { aspectRatio: ratio }]} contentFit="contain"
        onError={() => setErr("The image could not be displayed. Retry the original image.")}
        onLoad={e => { if (e.source.width && e.source.height) setRatio(e.source.width / e.source.height); onLoaded?.(path); }} />
      <View style={styles.zoomLabel}><Icon name="magnify-plus-outline" size={14} color={colors.onSurfaceInverse} /><T size={10} w="bold" color={colors.onSurfaceInverse}>Zoom</T></View>
    </Pressable>
    <Modal visible={zoom} animationType="fade" onRequestClose={() => setZoom(false)}>
      <View testID={`${testID}-zoom`} style={[styles.modal, { paddingTop: insets.top }]}>
        <Press testID="asset-zoom-close" onPress={() => setZoom(false)} accessibilityLabel="Close zoom" style={styles.close}><Icon name="close" size={24} color={colors.onSurface} /></Press>
        <ScrollView maximumZoomScale={4} minimumZoomScale={1} contentContainerStyle={styles.zoomScroll}>
          <ScrollView horizontal maximumZoomScale={4} contentContainerStyle={{ minWidth: width }}>
            <Image source={{ uri: displayed }} recyclingKey={path} cachePolicy="memory" transition={0} style={{ width, aspectRatio: ratio }} contentFit="contain" />
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