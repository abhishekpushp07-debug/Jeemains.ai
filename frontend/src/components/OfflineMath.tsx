import React, { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { StyleSheet, View } from "react-native";
import { WebView, WebViewMessageEvent } from "react-native-webview";
import { KATEX_CSS } from "@/src/katexCss";
import { colors } from "@/src/theme";
import { clock, loadingMetrics } from "@/src/assets/loadingMetrics";
import { Press, T } from "./ui";

// Public bundled fonts load once per mounted typesetter, not once per question.
// Question/solution content is injected only in RAM; no files or network requests.
const page = (fonts: string) => ({ html: `<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; font-src data:; script-src 'unsafe-inline'">${fonts}<style id="theme"></style></head><body><div id="content"></div><script>
let revision=0, frame=0, last='';
const report=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{const h=document.getElementById('content').scrollHeight+8;const key=revision+':'+h;if(key!==last){last=key;window.ReactNativeWebView.postMessage(JSON.stringify({revision,height:h}));}});};
window.updateMath=(payload)=>{revision=payload.revision;document.getElementById('theme').textContent=payload.css;document.getElementById('content').innerHTML=payload.body;report();if(document.fonts)document.fonts.ready.then(report);};
new ResizeObserver(report).observe(document.getElementById('content'));
window.ReactNativeWebView.postMessage(JSON.stringify({ready:true}));
</script></body></html>` });
const SOURCE = page(`<style>${KATEX_CSS}</style>`);
// Text with plain superscripts and subscripts only: the same page without the maths fonts, so it opens much lighter.
const LIGHT = page("");
type Props = { body: string; css: string; testID: string; backgroundColor?: string; initialHeight?: number; katex?: boolean };
export const OfflineMath = memo(function OfflineMath({ body, css, testID, backgroundColor = colors.custom_reading, initialHeight = 60, katex = true }: Props) {
  const web = useRef<WebView<object>>(null);
  const document = useMemo(() => ({ body, css }), [body, css]);
  const current = useRef(document), ready = useRef(false), sequence = useRef(0), sent = useRef(0);
  const [painted, setPainted] = useState<typeof document | null>(null);
  const [height, setHeight] = useState(initialHeight);
  const [error, setError] = useState(false);
  const update = useCallback(() => {
    if (!ready.current) return;
    sent.current = clock();
    web.current?.injectJavaScript(`window.updateMath(${JSON.stringify({ ...current.current, revision: ++sequence.current })});true;`);
  }, []);
  useEffect(() => { current.current = document; update(); }, [document, update]);
  const receive = (event: WebViewMessageEvent) => {
    try {
      const message = JSON.parse(event.nativeEvent.data);
      if (message.ready) { ready.current = true; update(); return; }
      if (message.revision !== sequence.current || !Number.isFinite(message.height) || message.height <= 0 || message.height > 30000) return;
      if (sent.current) { loadingMetrics.record("math_update", clock() - sent.current); sent.current = 0; }
      setHeight(message.height); setPainted(current.current);
    } catch { /* Ignore non-protocol WebView messages. */ }
  };
  return <View testID={testID} style={styles.container}>
    <WebView<object> ref={web} testID={`${testID}-typeset`} source={katex ? SOURCE : LIGHT} originWhitelist={["about:blank"]} scrollEnabled={false} cacheEnabled={false} incognito
      style={[styles.web, { height, backgroundColor, opacity: painted === document && !error ? 1 : 0 }]} setSupportMultipleWindows={false}
      onShouldStartLoadWithRequest={request => request.url === "about:blank" || request.url.startsWith("data:text/html")}
      onMessage={receive} onError={() => setError(true)} onContentProcessDidTerminate={() => { ready.current = false; setPainted(null); web.current?.reload(); }} />
    {error ? <Press testID={`${testID}-retry`} style={styles.retry} onPress={() => { ready.current = false; setError(false); setPainted(null); web.current?.reload(); }}><T testID={`${testID}-error`} size={13} color={colors.error}>Maths could not display. Tap to retry.</T></Press> : null}
  </View>;
});
const styles = StyleSheet.create({ container: { width: "100%" }, web: { backgroundColor: colors.custom_reading }, retry: { minHeight: 44, justifyContent: "center" } });