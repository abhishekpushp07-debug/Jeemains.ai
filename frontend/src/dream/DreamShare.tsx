// Dream Share Card: the photo friends see on WhatsApp when a dream college's target is crossed. Quiet black metal like
// the Rank Card: the college big in serif, the branch, the mock score against the target, a diamond and the student's name.
// Drawn off screen and sent as a photo with a short caption and the student's own link (see src/shareCard.ts).
// Shared from the end of the Dream Unlocked celebration and from any reached row of the Dream College Meter.
import React, { useRef, useState } from "react";
import { StyleSheet, View } from "react-native";
import { T } from "@/src/components/ui";
import { useAuth } from "@/src/auth";
import { gemColors, rankColors as colors } from "@/src/theme";
import { CardRef, CardShare, shareCard } from "@/src/shareCard";
import { useShareLink } from "@/src/mission/stats";
import { SERIF } from "@/src/rank/tones";
import { Diamond } from "@/src/rank/Diamond";
import { Eyebrow, Hairline, MetalCard, SilverCaps, Small } from "@/src/rank/MetalCard";
import { Dream, EXAM_NAME, FULL, Mock } from "./store";

const SILVER = colors.custom_rankSilver, MUTED = colors.custom_rankSilverMuted;
const ESTIMATE = "2026 cutoff par estimate, guarantee nahi.";

/** Caption = what was crossed + the invite; fallback (no photo possible) adds the estimate note. */
export function dreamShare(d: Dream, mock: Mock, link: string): CardShare {
  const over = Math.round(mock.score - d.need);
  const head = [
    `🎯 Dream unlocked! Mock mein ${d.college} · ${d.branch} ka target cross kar liya.`,
    `Score ${mock.score}/${FULL[d.exam]} · Target ${d.need}${over > 0 ? ` · +${over} marks upar` : ""}`,
  ];
  const invite = `Tum bhi apna dream set karo 👉 ${link}`;
  return { filename: "JEELIVE-Dream-Unlocked.png", caption: [...head, "", invite].join("\n"), fallback: [...head, "", ESTIMATE, "", invite].join("\n") };
}

function DreamCard({ d, mock, name, cardRef }: { d: Dream; mock: Mock; name: string; cardRef: CardRef }) {
  const over = Math.round(mock.score - d.need);
  return <MetalCard testID="dream-share-card" cardRef={cardRef} badge="DREAM UNLOCKED ✓" foot={<>
    <View style={styles.flex}>
      <Eyebrow>STUDENT</Eyebrow>
      <T testID="dream-share-card-name" color={SILVER} numberOfLines={1} style={styles.name}>{name}</T>
    </View>
    <View style={styles.flex}>
      <Eyebrow>MOCK</Eyebrow>
      <T size={12} color={MUTED} numberOfLines={2}>{mock.title}</T>
    </View>
  </>}>
    <View style={styles.head}>
      <View style={[styles.flex, styles.gap]}>
        <Eyebrow>{`${EXAM_NAME[d.exam].toUpperCase()} · DREAM COLLEGE`}</Eyebrow>
        <T testID="dream-share-card-college" color={SILVER} numberOfLines={3} style={styles.college}>{d.college}</T>
        <SilverCaps>{d.branch}</SilverCaps>
      </View>
      <Diamond width={62} tint={gemColors.kohinoor} sparkle />
    </View>
    <Hairline label={over > 0 ? `TARGET CROSS · +${over} MARKS UPAR` : "TARGET CROSS · BILKUL TARGET PAR"} />
    <View style={styles.stats}>
      <Small label="Mock score" value={`${mock.score} / ${FULL[d.exam]}`} testID="dream-share-card-score" />
      <Small label="Target" value={`${d.need}`} testID="dream-share-card-need" />
    </View>
    <T size={11} color={MUTED}>{ESTIMATE}</T>
  </MetalCard>;
}

/** `card` (render it anywhere: it stays off screen) and `share()`, which draws the card, sends its photo with the
 *  caption, then takes it away again, so nothing hidden keeps animating. `note` = something to show under the button. */
export function useDreamShare(d: Dream | undefined, mock: Mock | undefined) {
  const { user } = useAuth();
  const link = useShareLink();
  const ref = useRef<React.ComponentRef<typeof View>>(null);
  const [busy, setBusy] = useState(false);
  const [drawing, setDrawing] = useState(false);
  const [note, setNote] = useState("");
  const share = async () => {
    if (busy || !d || !mock) return;
    setBusy(true); setNote(""); setDrawing(true);
    await new Promise(r => setTimeout(r, 150)); // the card is laid out before its photo is taken
    try { setNote((await shareCard(ref, dreamShare(d, mock, link))).note); }
    catch { setNote("Share nahi ho paya. Ek baar phir try karo."); }
    finally { setBusy(false); setDrawing(false); }
  };
  const card = drawing && d && mock ? <View style={styles.offscreen} pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
    <DreamCard d={d} mock={mock} name={user?.display_name || user?.name || "JEE aspirant"} cardRef={ref} />
  </View> : null;
  return { card, share, busy, note };
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, gap: { gap: 4 },
  head: { flexDirection: "row", alignItems: "flex-start", gap: 12 },
  college: { fontFamily: SERIF, fontSize: 30, lineHeight: 36 },
  name: { fontFamily: SERIF, fontSize: 18, lineHeight: 23 },
  stats: { flexDirection: "row", gap: 16 },
  // Drawn off screen only so the photo can be made; never seen.
  offscreen: { position: "absolute", left: -10000, top: 0, width: 360 },
});
