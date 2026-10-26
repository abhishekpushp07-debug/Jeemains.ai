import React, { useId, useMemo, useState } from "react";
import { StyleSheet, View } from "react-native";
import Svg, { Defs, LinearGradient, Rect, Stop } from "react-native-svg";
import { cssGradientLine, parseGradientLayers } from "@/src/websiteDesign";

/** Pure-native SVG layering; CSS is data, never applied as unsupported RN styles. */
export function WebsiteGradient({ value, testID }: { value: string; testID?: string }) {
  const id = useId().replace(/[^a-z0-9]/gi, "");
  const [size, setSize] = useState({ width: 1, height: 1 });
  const layers = useMemo(() => parseGradientLayers(value).reverse(), [value]);
  return <View testID={testID} pointerEvents="none" style={StyleSheet.absoluteFill}
    onLayout={({ nativeEvent: { layout } }) => setSize({ width: Math.max(layout.width, 1), height: Math.max(layout.height, 1) })}>
    <Svg width="100%" height="100%">
      <Defs>{layers.map((layer, index) => <LinearGradient key={index} id={`${id}-${index}`} gradientUnits="userSpaceOnUse" {...cssGradientLine(layer.angle, size.width, size.height)}>
        {layer.stops.map((stop, i) => <Stop key={i} offset={stop.offset} stopColor={stop.color} />)}
      </LinearGradient>)}</Defs>
      {layers.map((_, index) => <Rect key={index} width="100%" height="100%" fill={`url(#${id}-${index})`} />)}
    </Svg>
  </View>;
}