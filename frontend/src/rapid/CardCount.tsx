import React from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { T, tap } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { CARD_COUNTS, CardCount, fitCount, roundLength, setCardCount, useCardCount } from "./scope";

/**
 * Rule R2: 30, 50 or 100 cards a round, one shared choice (lobby + battleground sheet).
 * With `available`, a pill the picks cannot fill is dimmed and a note says what will really be dealt.
 */
export function CardCountPicker({ available, value, onChange, testID = "rf-card-count" }: { available?: number; value?: CardCount; onChange?: (n: CardCount) => void; testID?: string }) {
  const stored = useCardCount(), chosen = value ?? stored; // a sheet can hold its own choice until SAVE
  const fit = available === undefined ? chosen : fitCount(chosen, available);
  return <View testID={testID} style={styles.wrap}>
    <View style={styles.row} accessibilityRole="radiogroup" accessibilityLabel="Cards in a round">
      <T w="heavy" size={11} color={arena.gold} style={styles.label}>CARDS</T>
      {CARD_COUNTS.map((n) => {
        // The pill that lights up is the round that will really be dealt (a too-big choice falls back to the largest that fits).
        const on = (fit || chosen) === n, short = available !== undefined && available < n;
        return <Pressable key={n} testID={`${testID}-${n}`} accessibilityRole="radio" accessibilityState={{ checked: on }} aria-checked={on}
          accessibilityLabel={`${n} cards, about ${roundLength(n)}${short ? ", this pick needs more cards" : ""}`}
          onPress={() => { tap(); if (onChange) onChange(n); else setCardCount(n); }} style={[styles.pill, on && styles.pillOn, short && !on && styles.short]}>
          <T w="heavy" size={16} color={on ? arena.badgeInk : arena.text}>{n}</T>
          <T w="bold" size={10} color={on ? arena.badgeInk : arena.muted} numberOfLines={1}>{short ? "need more" : roundLength(n)}</T>
        </Pressable>;
      })}
    </View>
    {available !== undefined && fit < chosen ? <T testID={`${testID}-note`} w="bold" size={11} color={arena.aqua} style={styles.note}>
      {fit ? `${available} cards in this pick · this round will be ${fit}` : `${available} cards in this pick · add a chapter to play`}
    </T> : null}
  </View>;
}

const styles = StyleSheet.create({
  wrap: { alignSelf: "stretch", gap: 4 },
  row: { flexDirection: "row", alignItems: "center", gap: 6 },
  label: { letterSpacing: 1.5, width: 46 },
  pill: { flex: 1, minHeight: 48, borderRadius: 16, alignItems: "center", justifyContent: "center", paddingVertical: 4, borderWidth: 1.5, borderColor: arena.rim, backgroundColor: arena.panelEdge },
  pillOn: { backgroundColor: arena.gold, borderColor: arena.goldDeep },
  short: { opacity: 0.5 },
  note: { textAlign: "center" },
});
