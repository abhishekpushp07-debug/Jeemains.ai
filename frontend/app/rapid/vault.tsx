import React from "react";
import { StyleSheet, View } from "react-native";
import { useAuth } from "@/src/auth";
import { T } from "@/src/components/ui";
import { useGameProfile } from "@/src/components/game";
import { arena, gemColors } from "@/src/theme";
import { GEM_AT, GEM_LABEL, GEM_ORDER, Gem, PhoenixDiamond, topGem } from "@/src/rapid/Art";
import { Panel } from "@/src/rapid/arena";
import { Count, Pop, Twinkles } from "@/src/rapid/juice";
import { InnerScreen, Note } from "@/src/rapid/parts";
import { ErrorBox, withRapid } from "@/src/rapid/ui";

/** Diamond Vault: every diamond won with a Phoenix streak, and the longest streak so far. */
function Vault() {
  const prof = useGameProfile(useAuth().user?.id), p = prof.data;
  const total = GEM_ORDER.reduce((n, c) => n + (p?.diamonds?.[c] || 0), 0);
  return <InnerScreen testID="vault-screen" title="Diamond Vault" sub="Won with Phoenix streaks">
    <Panel gold style={styles.hero}>
      <View>
        <PhoenixDiamond width={170} color={topGem(p?.diamonds_total)} breathe testID="vault-phoenix" />
        <Twinkles spots={[[12, 20, 14], [88, 26, 12], [50, 6, 10]]} />
      </View>
      <Count key={total} to={total} size={46} color={arena.gold} testID="vault-total" />
      <T w="heavy" size={12} color={arena.aqua} style={styles.spaced}>DIAMONDS</T>
      <T testID="vault-best-streak" w="bold" size={13} color={arena.text}>Longest Phoenix streak: {p?.best_phoenix ?? 0}</T>
    </Panel>
    <ErrorBox testID="vault-error" error={prof.error} retry={prof.reload} />
    {GEM_ORDER.map((c, i) => {
      const n = p?.diamonds?.[c] || 0;
      return <Pop key={c} delay={i * 80}>
        <View testID={`vault-row-${c}`} style={[styles.row, n ? { borderColor: gemColors[c] } : null]}>
          <Gem color={c} size={54} locked={!n} />
          <View style={styles.flex}>
            <T w="heavy" size={16} color={n ? arena.text : arena.muted}>{GEM_LABEL[c]} Diamond</T>
            <T w="bold" size={12} color={arena.aqua}>{GEM_AT[c]} correct in a row</T>
          </View>
          <T testID={`vault-count-${c}`} w="heavy" size={26} color={n ? arena.gold : arena.faint}>{n}</T>
        </View>
      </Pop>;
    })}
    <Note testID="vault-note">Answer in a row inside one match to light the Phoenix. A wrong card, a skip or a time-out restarts the streak, and the same diamond can be won again. Leaving a match loses its diamonds.</Note>
  </InnerScreen>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, spaced: { letterSpacing: 3 },
  hero: { alignItems: "center", padding: 18, gap: 2 },
  row: { flexDirection: "row", alignItems: "center", gap: 14, minHeight: 76, paddingHorizontal: 14, paddingVertical: 10, borderRadius: 20, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim, borderBottomWidth: 5, borderBottomColor: arena.panelEdge },
});

export default withRapid(Vault);
