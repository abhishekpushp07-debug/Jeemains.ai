import React from "react";
import { StyleSheet, View } from "react-native";
import { T } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { GEM_LABEL, GEM_ORDER, Gem, GemColor } from "./Art";
import { Panel, RaisedButton } from "./arena";
import { GemStrip } from "./parts";

// Store prices: most things cost coins. Diamond specials cost streak diamonds from the Vault instead.
export type Priced = { id: string; price: number; gems?: Partial<Record<GemColor, number>> };
type Wallet = { coins?: number; diamonds?: Record<string, number> } | null | undefined;

export const gemsOf = (it?: Priced | null) => GEM_ORDER.filter((c) => it?.gems?.[c]).map((c) => [c, it!.gems![c]!] as [GemColor, number]);
export const isFree = (it: Priced) => !it.price && !it.gems;
export const canAfford = (it: Priced, w: Wallet) => (it.gems ? gemsOf(it).every(([c, n]) => (w?.diamonds?.[c] || 0) >= n) : (w?.coins ?? 0) >= it.price);
export const costText = (it?: Priced | null) => (it?.gems ? `${gemsOf(it).map(([c, n]) => `${n} ${GEM_LABEL[c]}`).join(" + ")} diamonds` : `${it?.price ?? 0} coins`);
export const haveText = (it: Priced | null | undefined, w: Wallet) => (it?.gems ? gemsOf(it).map(([c]) => `${w?.diamonds?.[c] || 0} ${GEM_LABEL[c]}`).join(", ") : `${w?.coins ?? "—"}`);

/** Buy button that shows the price: a coin amount, or the diamonds it costs. Off until the player can pay. */
export function PriceButton({ it, wallet, busy, onPress, testID }: { it: Priced; wallet: Wallet; busy?: boolean; onPress: () => void; testID: string }) {
  const off = !canAfford(it, wallet);
  if (!it.gems) return <RaisedButton testID={testID} height={42} icon="coin" label={`${it.price}`} disabled={off} busy={busy} onPress={onPress} style={styles.stretch} />;
  return <RaisedButton testID={testID} height={42} disabled={off} busy={busy} onPress={onPress} accessibilityLabel={`Buy for ${costText(it)}`} style={styles.stretch}>
    <View style={styles.line}>{gemsOf(it).map(([c, n]) => <View key={c} style={styles.cost}><Gem color={c} size={22} /><T w="heavy" size={15} color={arena.text}>{n}</T></View>)}</View>
  </RaisedButton>;
}

/** The diamonds in hand, shown under the coin balance. */
export function DiamondWallet({ diamonds }: { diamonds?: Record<string, number> }) {
  return <Panel flat testID="shop-diamonds" style={styles.wallet}>
    <T w="heavy" size={12} color={arena.gold} style={styles.title}>YOUR DIAMONDS</T>
    <GemStrip diamonds={diamonds} size={32} />
    <T size={11} color={arena.muted} style={styles.center}>Diamond specials wait in Avatars, Entry Effects and Frames.</T>
  </Panel>;
}

const styles = StyleSheet.create({
  stretch: { alignSelf: "stretch" }, center: { textAlign: "center" },
  line: { flexDirection: "row", alignItems: "center", gap: 10 }, cost: { flexDirection: "row", alignItems: "center", gap: 2 },
  wallet: { padding: 12, gap: 6 }, title: { letterSpacing: 2, textAlign: "center" },
});
