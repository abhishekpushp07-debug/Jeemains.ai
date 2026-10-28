import { processColor } from "react-native";

/** Native SVG replaces a color's alpha with stopOpacity; pass them separately. */
export function gradientStop(color: string) {
  const packed = processColor(color);
  if (typeof packed !== "number") return { stopColor: color, stopOpacity: 1 };
  return {
    stopColor: `#${(packed & 0x00ffffff).toString(16).padStart(6, "0")}`,
    stopOpacity: (packed >>> 24) / 255,
  };
}