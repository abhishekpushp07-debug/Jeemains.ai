import React, { memo, useMemo } from "react";
import { Platform } from "react-native";
import { colors } from "@/src/theme";
import { plainMath, tex } from "./AiSolution";
import { OfflineMath } from "./OfflineMath";
import { T } from "./ui";

type Props = { text: string; testID: string; size?: number; color?: string; backgroundColor?: string };
export const MathText = memo(function MathText({ text, testID, size = 15, color = colors.custom_onReading, backgroundColor = colors.custom_reading }: Props) {
  const hasMath = /\$[^$]+\$|\\\(|\\\[/.test(text);
  const body = useMemo(() => hasMath && Platform.OS !== "web" ? tex(text) : "", [text, hasMath]);
  if (!hasMath || Platform.OS === "web") return <T testID={testID} size={size} color={color}>{hasMath ? plainMath(text) : text}</T>;
  return <OfflineMath body={body} testID={testID} backgroundColor={backgroundColor} css={`body{margin:0;background:transparent;color:${color};font:${size}px -apple-system,Roboto,sans-serif;line-height:1.55;overflow-wrap:anywhere}#content{white-space:pre-wrap}.katex-display{overflow-x:auto;overflow-y:hidden}.katex{font-size:1.05em}`} />;
});