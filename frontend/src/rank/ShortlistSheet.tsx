// "Meri shortlist": every college-branch added to Compare (JEE, COMEDK, BITS) in one sheet, with remove, PDF and WhatsApp share.
// WhatsApp sends a Shortlist card photo (drawn off screen, in the Rank card's black metal) with a short caption.
import React, { useRef, useState } from "react";
import { StyleSheet, View } from "react-native";
import { Press, T } from "@/src/components/ui";
import { DSheet, Pill } from "@/src/components/design";
import { rankColors as colors, space } from "@/src/theme";
import { shareCard } from "@/src/shareCard";
import { useShareLink } from "@/src/mission/stats";
import type { Seat } from "./api";
import { EXAM, SERIF, TAG } from "./tones";
import { RemoveButton, Tag } from "./controls";
import { shareShortlist } from "./share";
import { PdfButton } from "./PdfButton";
import { Eyebrow, MetalCard } from "./MetalCard";
import { Saved, savedPdfBody, toggleSaved, useShortlist } from "./shortlist";

const ON_CARD = 8;

export function ShortlistSheet({ visible, onClose, onOpen }: { visible: boolean; onClose: () => void; onOpen?: (s: Seat) => void }) {
  const list = useShortlist();
  const card = useRef<React.ComponentRef<typeof View>>(null);
  const link = useShareLink();
  const [busy, setBusy] = useState(false);
  const share = async () => {
    if (busy) return;
    setBusy(true);
    try { await shareCard(card, shareShortlist(list, link)); } catch { /* share sheet closed */ } finally { setBusy(false); }
  };
  return <DSheet visible={visible} onClose={onClose} title="Meri shortlist" testID="rank-shortlist">
    {list.length === 0 ? <T testID="rank-shortlist-empty" size={13.5} color={colors.muted}>
      Abhi kuch save nahi kiya. Kisi bhi college card par “Add to Compare” dabao, wo yahan aa jayega.
    </T> : null}
    {list.map((s, i) => {
      const exam = EXAM[s.exam];
      const open = s.seat && onOpen ? () => { onClose(); onOpen(s.seat!); } : undefined;
      return <View key={s.id} style={styles.row}>
        <Row open={open} testID={`rank-shortlist-item-${i}`} label={`${s.title}, ${s.sub}`}>
          <View style={{ flex: 1, gap: 3 }}>
            <View style={styles.line}>
              <T w="bold" size={14.5} numberOfLines={1} style={{ flexShrink: 1 }}>{s.title}</T>
              <Tag label={exam.label} ink={exam.ink} soft={exam.soft} />
            </View>
            <T size={13.5} color={colors.custom_softText} numberOfLines={2}>{s.sub}</T>
            <T size={12} color={colors.muted} numberOfLines={2}>{s.line}</T>
          </View>
          {s.tag ? <Tag label={TAG[s.tag].label} ink={TAG[s.tag].ink} soft={TAG[s.tag].soft} /> : null}
        </Row>
        <RemoveButton onPress={() => toggleSaved(s)} testID={`rank-shortlist-remove-${i}`} label={`${s.title} shortlist se hatao`} />
      </View>;
    })}
    {list.length ? <Pill testID="rank-shortlist-share" icon="whatsapp" label="Shortlist card WhatsApp par bhejo" bg={colors.custom_whatsapp} ink={colors.onSurfaceInverse}
      busy={busy} onPress={share} style={{ marginTop: space.sm }} /> : null}
    {list.length ? <PdfButton testID="rank-shortlist-pdf" path="/saved" body={savedPdfBody(list)} label="Shortlist ki PDF" card={card} /> : null}
    {list.length ? <View style={styles.offscreen} pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
      <ShortlistCard list={list} cardRef={card} />
    </View> : null}
  </DSheet>;
}

/** The photo that goes to WhatsApp: the saved colleges (first 8) on the Rank card's black metal. */
function ShortlistCard({ list, cardRef }: { list: Saved[]; cardRef: React.RefObject<React.ComponentRef<typeof View> | null> }) {
  return <MetalCard testID="rank-shortlist-card" cardRef={cardRef} badge="MERI SHORTLIST">
    <View style={{ gap: 2 }}>
      <Eyebrow>{`${list.length} COLLEGES · 2026 CUTOFF`}</Eyebrow>
      <T color={colors.custom_rankSilver} style={styles.title}>Meri dream list</T>
    </View>
    <View style={{ gap: space.sm }}>
      {list.slice(0, ON_CARD).map((s, i) => <View key={s.id} style={styles.cardRow}>
        <T w="heavy" size={13} color={colors.custom_rankBloodInk} style={styles.num}>{i + 1}</T>
        <View style={{ flex: 1, gap: 1 }}>
          <T w="bold" size={13.5} color={colors.custom_rankSilver} numberOfLines={1}>{s.title}</T>
          <T size={11.5} color={colors.custom_rankSilverMuted} numberOfLines={1}>{EXAM[s.exam].label} · {s.sub}</T>
        </View>
        {s.tag ? <Tag label={TAG[s.tag].label} ink={TAG[s.tag].ink} soft={TAG[s.tag].soft} /> : null}
      </View>)}
      {list.length > ON_CARD ? <T size={11.5} color={colors.custom_rankSilverMuted}>+{list.length - ON_CARD} aur</T> : null}
    </View>
  </MetalCard>;
}

/** JEE rows open the college sheet; BITSAT rows are plain text at full contrast. */
function Row({ open, testID, label, children }: { open?: () => void; testID: string; label: string; children: React.ReactNode }) {
  return open ? <Press testID={testID} onPress={open} scaleTo={0.99} accessibilityLabel={label} style={styles.main}>{children}</Press>
    : <View testID={testID} accessibilityLabel={label} style={styles.main}>{children}</View>;
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "flex-start", borderBottomWidth: 1, borderBottomColor: colors.custom_barLine },
  main: { flex: 1, flexDirection: "row", gap: space.sm, paddingVertical: space.md, alignItems: "flex-start" },
  line: { flexDirection: "row", alignItems: "center", gap: space.sm },
  // Drawn off screen only so the photo can be made; never seen in the sheet.
  offscreen: { position: "absolute", left: -10000, top: 0, width: 360 },
  title: { fontFamily: SERIF, fontSize: 28, lineHeight: 34 },
  cardRow: { flexDirection: "row", alignItems: "center", gap: space.sm, paddingVertical: 6, borderTopWidth: 1, borderTopColor: colors.custom_rankLine },
  num: { width: 18, textAlign: "center" },
});
