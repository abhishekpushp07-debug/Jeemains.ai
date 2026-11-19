import React, { useEffect, useState } from "react";
import { StyleSheet, TextInput, View } from "react-native";
import { api } from "@/src/api/client";
import { Icon, T } from "@/src/components/ui";
import { colors, fonts, noOutline, radius, space } from "@/src/theme";
import { TONE, mmss, pc } from "./format";
import { Block, ChipButton, EmptyLine } from "./parts";

const seen = new Map<string, { d: any; at: number }>();

/** This paper's leaderboard, kept for a minute so the picker and the board share one request. */
export function useBoard(id: string, q = "") {
  const key = id + "|" + q;
  const [d, setD] = useState<any>(() => seen.get(key)?.d || null);
  useEffect(() => {
    const hit = seen.get(key);
    let live = true;
    if (hit && Date.now() - hit.at < 60000) {
      Promise.resolve().then(() => { if (live) setD(hit.d); });
      return () => { live = false; };
    }
    const t = setTimeout(() => api(`/attempts/${id}/leaderboard${q ? "?q=" + encodeURIComponent(q) : ""}`)
      .then(x => { seen.set(key, { d: x, at: Date.now() }); if (live) setD(x); })
      .catch(() => { if (live) setD({ state: "error", rows: [], around: [], found: [] }); }), q ? 350 : 0);
    return () => { live = false; clearTimeout(t); };
  }, [id, q, key]);
  return d;
}

function Rows({ rows, value, onPick, testID }: { rows: any[]; value: string; onPick: (v: string) => void; testID: string }) {
  return <View testID={testID} style={{ gap: 8 }}>
    {rows.map(r => {
      const on = value === "user:" + r.handle;
      return <View key={r.handle} testID={"a2-board-row-" + r.handle} style={[styles.row, r.is_you && styles.you]}>
        <View style={styles.line}>
          <T w="heavy" size={14} color={r.rank <= 3 ? colors.custom_gold : colors.onSurface} style={styles.rank}>#{r.rank}</T>
          <T w="heavy" size={14} numberOfLines={1} style={{ flex: 1 }}>{r.is_you ? "Aap" : r.name}</T>
          <T w="heavy" size={17}>{r.score}</T>
        </View>
        <View style={styles.line}>
          <T size={11.5} color={colors.muted} style={{ flex: 1 }}>Attempted {r.attempted} · Accuracy {pc(r.accuracy)} · {mmss(r.time)}</T>
          {!r.is_you ? <ChipButton testID={"a2-board-compare-" + r.handle} on={on} onPress={() => onPick("user:" + r.handle)} label={`${r.name} se Compare`}>
            <Icon name={on ? "check" : "compare-horizontal"} size={14} color={colors.custom_softText} />
            <T size={12} w="heavy">Compare</T>
          </ChipButton> : <View style={styles.youTag}><T size={10.5} w="heavy" color={colors.brandText}>AAP</T></View>}
        </View>
      </View>;
    })}
  </View>;
}

/** Names, Scores and totals only: another student's answers never reach the phone. */
export function Leaderboard({ id, value, onPick }: { id: string; value: string; onPick: (v: string) => void }) {
  const [q, setQ] = useState("");
  const d = useBoard(id, q.trim());
  if (!d || d.state !== "ready") return null;
  const top: any[] = d.rows.slice(0, 10);
  const rows: any[] = q.trim() ? d.found : top;
  return <Block id="leaderboard" kicker={`${d.n} STUDENTS`} title="Is paper ka leaderboard" note="Kisi bhi student se Compare karo. Sirf naam, Score aur totals dikhte hain; kisi ke jawab kabhi nahi.">
    <View style={styles.search}>
      <Icon name="magnify" size={18} color={colors.custom_softText} />
      <TextInput testID="a2-board-search" value={q} onChangeText={t => setQ(t.slice(0, 20))} placeholder="Naam ya Rank" placeholderTextColor={colors.custom_dim}
        accessibilityLabel="Leaderboard mein dhoondo" autoCorrect={false} returnKeyType="search" style={[styles.input, noOutline]} />
    </View>
    {rows.length ? <Rows rows={rows} value={value} onPick={onPick} testID="a2-board-top" /> : <EmptyLine testID="a2-board-none">Is naam ya Rank ka koi student nahi mila.</EmptyLine>}
    {!q.trim() && d.around.length > 0 && !top.some(r => r.is_you) ? <>
      <View style={styles.sub}><Icon name="account-multiple-outline" size={16} color={colors.custom_softText} /><T w="heavy" size={13.5}>Aapke aas-paas</T></View>
      <Rows rows={d.around} value={value} onPick={onPick} testID="a2-board-around" />
    </> : null}
  </Block>;
}

const styles = StyleSheet.create({
  search: { flexDirection: "row", alignItems: "center", gap: 8, minHeight: 48, paddingHorizontal: space.md, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_bar },
  input: { flex: 1, minHeight: 46, fontFamily: fonts.medium, fontSize: 14, color: colors.onSurface, paddingVertical: 0 },
  row: { gap: 4, paddingVertical: 10, paddingHorizontal: space.md, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_bar },
  you: { borderColor: TONE.brand.line, backgroundColor: TONE.brand.soft },
  line: { flexDirection: "row", alignItems: "center", gap: 8, minHeight: 24 },
  rank: { minWidth: 38 },
  youTag: { height: 24, paddingHorizontal: 10, borderRadius: 12, borderWidth: 1, borderColor: TONE.brand.line, alignItems: "center", justifyContent: "center" },
  sub: { flexDirection: "row", alignItems: "center", gap: 6, marginTop: 4 },
});
