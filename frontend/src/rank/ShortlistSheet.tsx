// "Meri shortlist": every saved JEE seat and BITS program in one sheet, with remove and WhatsApp share.
import React from "react";
import { StyleSheet, View } from "react-native";
import { Press, T } from "@/src/components/ui";
import { DSheet, Pill } from "@/src/components/design";
import { rankColors as colors, space } from "@/src/theme";
import type { Seat } from "./api";
import { EXAM, TAG } from "./tones";
import { StarButton, Tag } from "./controls";
import { shareShortlist } from "./share";
import { PdfButton } from "./PdfButton";
import { savedPdfBody, toggleSaved, useShortlist } from "./shortlist";

export function ShortlistSheet({ visible, onClose, onOpen }: { visible: boolean; onClose: () => void; onOpen?: (s: Seat) => void }) {
  const list = useShortlist();
  return <DSheet visible={visible} onClose={onClose} title="Meri shortlist" testID="rank-shortlist">
    {list.length === 0 ? <T testID="rank-shortlist-empty" size={13.5} color={colors.muted}>
      Abhi kuch save nahi kiya. Kisi bhi college-branch ke star par tap karo, wo yahan aa jayega.
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
        <StarButton saved onPress={() => toggleSaved(s)} testID={`rank-shortlist-remove-${i}`} />
      </View>;
    })}
    {list.length ? <Pill testID="rank-shortlist-share" icon="whatsapp" label="Shortlist WhatsApp par bhejo" bg={colors.custom_whatsapp} ink={colors.onSurfaceInverse}
      onPress={() => shareShortlist(list)} style={{ marginTop: space.sm }} /> : null}
    {list.length ? <PdfButton testID="rank-shortlist-pdf" path="/saved" body={savedPdfBody(list)} label="Shortlist ki PDF" /> : null}
  </DSheet>;
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
});
