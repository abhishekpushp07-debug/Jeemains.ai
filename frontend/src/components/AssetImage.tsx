import React, { useEffect, useState } from "react";
import { ActivityIndicator, Modal, Pressable, ScrollView, View } from "react-native";
import { Image } from "expo-image";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { assetDataUri } from "@/src/api/client";
import { Icon, Press, T } from "@/src/components/ui";
import { colors, radius, space } from "@/src/theme";

// Original source image (question or solution) fetched with the session; tap to zoom.
export function AssetImage({ path, label, testID }: { path: string; label: string; testID?: string }) {
  const [uri, setUri] = useState<string | null>(null);
  const [err, setErr] = useState("");
  const [ratio, setRatio] = useState(2.2);
  const [zoom, setZoom] = useState(false);
  const [n, setN] = useState(0);
  const insets = useSafeAreaInsets();
  useEffect(() => {
    let alive = true;
    setErr("");
    assetDataUri(path).then((u) => alive && setUri(u)).catch((e) => alive && setErr(e.message));
    return () => { alive = false; };
  }, [path, n]);
  if (err)
    return (
      <View testID={testID + "-error"} style={{ padding: space.md, borderRadius: radius.md, backgroundColor: colors.custom_errorSoft, gap: 4 }}>
        <T size={13} w="medium" color={colors.error}>Original image didn’t load. Answering this question needs it.</T>
        <Press testID={testID + "-retry"} onPress={() => setN((x) => x + 1)}><T w="bold" size={13} color={colors.brandPrimary}>Retry image</T></Press>
      </View>
    );
  if (!uri) return <View style={{ height: 120, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_reading }}><ActivityIndicator color={colors.brandPrimary} /></View>;
  return (
    <>
      <Pressable testID={testID} onPress={() => setZoom(true)} accessibilityRole="imagebutton" accessibilityLabel={label + ". Tap to zoom"}>
        <Image source={{ uri }} style={{ width: "100%", aspectRatio: ratio, backgroundColor: colors.custom_reading }} contentFit="contain" onLoad={(e) => e.source.width && setRatio(e.source.width / e.source.height)} />
        <View style={{ position: "absolute", right: 6, bottom: 6, flexDirection: "row", gap: 4, alignItems: "center", backgroundColor: colors.custom_overlay, borderRadius: radius.pill, paddingHorizontal: 8, paddingVertical: 3 }}>
          <Icon name="magnify-plus-outline" size={14} color={colors.onSurfaceInverse} />
          <T size={10} w="bold" color={colors.onSurfaceInverse}>Zoom</T>
        </View>
      </Pressable>
      <Modal visible={zoom} animationType="fade" onRequestClose={() => setZoom(false)}>
        <View style={{ flex: 1, backgroundColor: colors.custom_reading, paddingTop: insets.top }}>
          <Press testID="asset-zoom-close" onPress={() => setZoom(false)} accessibilityLabel="Close zoom" style={{ alignSelf: "flex-end", margin: space.md, width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: colors.surface }}>
            <Icon name="close" size={24} color={colors.onSurface} />
          </Press>
          <ScrollView maximumZoomScale={4} minimumZoomScale={1} contentContainerStyle={{ flexGrow: 1, justifyContent: "center" }} horizontal={false}>
            <ScrollView horizontal maximumZoomScale={4} contentContainerStyle={{ width: "100%" }}>
              <Image source={{ uri }} style={{ width: "100%", aspectRatio: ratio, minWidth: 360 }} contentFit="contain" />
            </ScrollView>
          </ScrollView>
          <T size={12} color={colors.muted} style={{ textAlign: "center", padding: space.md, paddingBottom: insets.bottom + space.md }}>Pinch or scroll to read the original.</T>
        </View>
      </Modal>
    </>
  );
}
