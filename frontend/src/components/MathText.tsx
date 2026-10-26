import React, { useMemo, useState } from "react";
import { Platform, StyleSheet, View } from "react-native";
import { WebView } from "react-native-webview";
import { KATEX_CSS } from "@/src/katexCss";
import { colors } from "@/src/theme";
import { plainMath, tex } from "./AiSolution";
import { T } from "./ui";

// Supplied question/solution text, never generated or fetched from a new AI service.
export function MathText({ text, testID, size = 15 }: { text: string; testID: string; size?: number }) {
  const [height, setHeight] = useState(60);
  const hasMath = /\$[^$]+\$|\\\(|\\\[/.test(text);
  const source = useMemo(() => ({ html: `<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>${KATEX_CSS}
    body{margin:0;background:transparent;color:${colors.custom_onReading};font: ${size}px -apple-system,Roboto,sans-serif;line-height:1.55;overflow-wrap:anywhere}
    #content{white-space:pre-wrap}.katex-display{overflow-x:auto;overflow-y:hidden}.katex{font-size:1.05em}
    </style></head><body><div id="content">${tex(text)}</div><script>
    function size(){window.ReactNativeWebView.postMessage(String(document.getElementById('content').scrollHeight+6))}
    window.addEventListener('load',size);if(document.fonts)document.fonts.ready.then(size);new ResizeObserver(size).observe(document.getElementById('content'));
    </script></body></html>` }), [text, size]);
  if (!hasMath || Platform.OS === "web") return <T testID={testID} size={size} color={colors.custom_onReading}>{hasMath ? plainMath(text) : text}</T>;
  return <View testID={testID} style={styles.container}>
    <WebView testID={`${testID}-typeset`} source={source} originWhitelist={["about:blank"]} scrollEnabled={false}
      style={[styles.web, { height }]} setSupportMultipleWindows={false}
      onShouldStartLoadWithRequest={(request) => request.url === "about:blank" || request.url.startsWith("data:text/html")}
      onMessage={(event) => { const value = Number(event.nativeEvent.data); if (Number.isFinite(value) && value > 0 && value < 30000) setHeight(value); }} />
  </View>;
}

const styles = StyleSheet.create({ container: { width: "100%" }, web: { backgroundColor: colors.custom_reading } });