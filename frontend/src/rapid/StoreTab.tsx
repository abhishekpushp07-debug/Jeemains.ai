import React, { useState } from "react";
import { Modal, ScrollView, StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { rf } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { useCached } from "@/src/useCached";
import { Icon, T } from "@/src/components/ui";
import { Avatar, EntryShow } from "@/src/components/Entry";
import { useGameProfile } from "@/src/components/game";
import { RARITY } from "@/src/avatars";
import { playSfx } from "@/src/sfx";
import { arena } from "@/src/theme";
import { Alive, GameIcon } from "./Art";
import { GoldTitle, Panel, RaisedButton } from "./arena";
import { Jelly } from "./juice";
import { DiamondWallet, PriceButton, canAfford, costText, haveText, isFree } from "./StoreParts";
import { ErrorBox, Sheet, Skeleton } from "./ui";
import { takeArenaPart } from "./social";

type Tab = "avatar" | "entry" | "frame" | "theme" | "powerup";
const TABS: [Tab, string][] = [["avatar", "Avatars"], ["entry", "Entry Effects"], ["frame", "Frames"], ["theme", "Arenas"], ["powerup", "Power-ups"]];
const EARN = ["2 coins for every correct card", "+50 coins for winning a match with 5 or more correct", "+30 coins for a flawless run of 10 or more cards", "Daily quests pay 30 to 50 coins each", "Coins are only earned by playing. No real money."];

/** Store tab: avatars, entry effects, frames, arenas and power-ups, bought with coins earned in play. */
export function StoreTab() {
  const uid = useAuth().user?.id || "";
  const shop = useCached<any>(uid ? `u.${uid}.rfshop` : null, () => rf("/shop", uid), false);
  const reloadProfile = useGameProfile(uid).reload; // the coins and diamonds at the top of the arena follow every purchase
  const [tab, setTab] = useState<Tab>(() => (takeArenaPart() as Tab) || "avatar");
  const [busy, setBusy] = useState(""), [error, setError] = useState("");
  const [purchase, setPurchase] = useState<any>(null), [info, setInfo] = useState(false), [show, setShow] = useState("");
  const d = shop.data;

  async function act(path: string, body: any, key: string) {
    setBusy(key); setError("");
    try { await rf(path, uid, { method: "POST", body }); reloadProfile(); shop.reload(); return true; }
    catch (e: any) { setError(e.message); return false; }
    finally { setBusy(""); }
  }
  const items = (d?.items || []).filter((i: any) => i.slot === tab);

  return <View style={styles.flex} testID="shop-screen">
    <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
      <Panel gold style={styles.wallet}>
        <Alive kind="hop"><GameIcon name="coin" size={68} testID="shop-coins-art" /></Alive>
        <View style={styles.flex}>
          <GoldTitle size={34} testID="shop-balance">{d?.coins ?? "—"}</GoldTitle>
          <T w="bold" size={12} color={arena.aqua}>Your coins · {d?.freezes ?? 0} streak freeze{d?.freezes === 1 ? "" : "s"}</T>
        </View>
        <RaisedButton testID="shop-what-are-coins" label="Earn" tone="wine" height={42} onPress={() => setInfo(true)} style={styles.earn} />
      </Panel>
      <DiamondWallet diamonds={d?.diamonds} />
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabs} contentContainerStyle={styles.tabRow}>
        {TABS.map(([v, l]) => <Jelly key={v} testID={"shop-tab-" + v} accessibilityRole="tab" accessibilityState={{ selected: tab === v }} onPress={() => setTab(v)} style={[styles.tab, tab === v && styles.tabOn]}>
          <T w="heavy" size={13} color={tab === v ? arena.text : arena.muted}>{l}</T>
        </Jelly>)}
      </ScrollView>
      <ErrorBox error={(!purchase && error) || shop.error} testID="shop-error" retry={shop.reload} />
      {!d && !shop.error ? <Skeleton h={200} /> : null}
      <View style={styles.grid}>
        {d && tab === "avatar" ? d.avatars.map((a: any) => {
          const owned = isFree(a) || d.owned.includes(a.id), selected = d.avatar === a.id, rar = RARITY[a.rarity] || RARITY.common;
          return <View key={a.id} testID={"shop-avatar-" + a.id} style={[styles.item, selected && styles.itemOn]}>
            <View style={[styles.rarity, { backgroundColor: rar.color }]}><T w="heavy" size={9} color={arena.badgeInk}>{rar.label}</T></View>
            <Avatar icon={a.id} frame={selected ? d.equipped?.frame : null} size={88} />
            <T w="heavy" size={14} color={arena.text} numberOfLines={1}>{a.title}</T>
            {owned ? <RaisedButton testID={"shop-avatar-use-" + a.id} tone={selected ? "wine" : "teal"} height={42} label={selected ? "Selected ✓" : isFree(a) ? "Use · Free" : "Use"} busy={busy === a.id} disabled={selected} onPress={() => act("/profile/avatar", { avatar: a.id }, a.id)} style={styles.stretch} />
              : <PriceButton testID={"shop-avatar-buy-" + a.id} it={a} wallet={d} busy={busy === a.id} onPress={() => { setError(""); setPurchase(a); }} />}
          </View>;
        }) : null}
        {d && tab !== "avatar" ? items.map((it: any) => {
          const owned = d.owned.includes(it.id), equipped = d.equipped?.[it.slot] === it.id;
          return <View key={it.id} testID={"shop-item-" + it.id} style={[styles.item, equipped && styles.itemOn]}>
            <Jelly testID={"shop-preview-" + it.id} disabled={it.slot !== "entry"} accessibilityLabel={it.slot === "entry" ? `Watch ${it.title} entry` : it.title} onPress={() => setShow(it.id)} style={styles.preview}>
              <LinearGradient colors={(it.colors as [string, string]) || [arena.panelHi, arena.panelEdge]} style={StyleSheet.absoluteFill} />
              {it.slot === "frame" ? <Avatar icon={d.avatar} frame={it.id} size={62} /> : <Icon name={it.icon} size={48} color={arena.gold} />}
              {it.slot === "entry" ? <View style={styles.playBadge}><Icon name="play" size={16} color={arena.text} /></View> : null}
            </Jelly>
            <T w="heavy" size={14} color={arena.text} numberOfLines={1}>{it.title}</T>
            <T size={11} color={arena.muted} numberOfLines={2} style={styles.blurb}>{it.body}</T>
            {owned && it.slot !== "powerup" ? <RaisedButton testID={"shop-equip-" + it.id} tone={equipped ? "wine" : "teal"} height={42} label={equipped ? "Equipped ✓" : "Equip"} busy={busy === it.id} onPress={() => act("/shop/equip", { slot: it.slot, item_id: equipped ? null : it.id }, it.id)} style={styles.stretch} />
              : <PriceButton testID={"shop-buy-" + it.id} it={it} wallet={d} busy={busy === it.id} onPress={() => { setError(""); setPurchase(it); }} />}
          </View>;
        }) : null}
      </View>
    </ScrollView>
    <Sheet visible={!!purchase} onClose={() => !busy && setPurchase(null)} testID="shop-purchase-sheet">
      <GoldTitle size={24} testID="shop-purchase-title">Make it yours?</GoldTitle>
      <T testID="shop-purchase-item" w="heavy" size={18} color={arena.text}>{purchase?.title}</T>
      <T testID="shop-purchase-cost" w="bold" color={arena.aqua}>{costText(purchase)} · You have {haveText(purchase, d)}</T>
      <T testID="shop-purchase-note" size={12} color={arena.muted}>{purchase?.gems ? "Uses diamonds won with Phoenix streaks. No real money is charged." : "Uses coins earned in the game. No real money is charged."}</T>
      <ErrorBox testID="shop-purchase-error" error={error} />
      <RaisedButton testID="shop-purchase-confirm" label={purchase?.gems ? "Buy with diamonds" : `Buy · ${purchase?.price || 0} coins`} sub={purchase?.gems ? costText(purchase) : undefined} icon={purchase?.gems ? undefined : "coin"} height={56} busy={!!busy} disabled={!purchase || !canAfford(purchase, d)}
        onPress={async () => { if (purchase && await act("/shop/buy", { item_id: purchase.id }, purchase.id)) { playSfx("coin"); setPurchase(null); } }} />
      <RaisedButton testID="shop-purchase-cancel" tone="wine" label="Keep browsing" disabled={!!busy} onPress={() => setPurchase(null)} />
    </Sheet>
    <Sheet visible={info} onClose={() => setInfo(false)} testID="shop-info-sheet">
      <GoldTitle size={22}>How do I earn coins?</GoldTitle>
      {EARN.map((x) => <View key={x} style={styles.earnRow}><GameIcon name="coin" size={22} /><T size={13} color={arena.text} style={styles.flex}>{x}</T></View>)}
      <RaisedButton testID="shop-info-close" label="Got it" onPress={() => setInfo(false)} />
    </Sheet>
    <Modal visible={!!show} transparent animationType="fade" onRequestClose={() => setShow("")} statusBarTranslucent>
      {show ? <EntryShow solo testID="shop-entry-show" players={[{ you: true, avatar: d?.avatar, frame: d?.equipped?.frame, entry: show, level: 1, wins: 0 }]} onDone={() => setShow("")} /> : null}
    </Modal>
  </View>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, stretch: { alignSelf: "stretch" }, content: { paddingHorizontal: 16, paddingTop: 4, paddingBottom: 28, gap: 12 },
  wallet: { flexDirection: "row", alignItems: "center", gap: 12, padding: 14 }, earn: { width: 76 },
  tabs: { flexGrow: 0, marginHorizontal: -16 }, tabRow: { gap: 8, paddingHorizontal: 16 },
  tab: { height: 44, paddingHorizontal: 16, borderRadius: 14, justifyContent: "center", backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  tabOn: { backgroundColor: arena.teal, borderColor: arena.tealOutline, borderBottomWidth: 4, borderBottomColor: arena.tealDeep },
  grid: { flexDirection: "row", flexWrap: "wrap", justifyContent: "space-between", rowGap: 12 },
  item: { width: "48%", borderRadius: 20, padding: 10, gap: 6, alignItems: "center", backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim, borderBottomWidth: 5, borderBottomColor: arena.panelEdge },
  itemOn: { borderColor: arena.gold, borderBottomColor: arena.goldDeep },
  rarity: { alignSelf: "flex-start", paddingHorizontal: 8, height: 18, borderRadius: 9, justifyContent: "center" },
  preview: { width: "100%", height: 92, borderRadius: 14, alignItems: "center", justifyContent: "center", overflow: "hidden" },
  playBadge: { position: "absolute", right: 6, bottom: 6, width: 26, height: 26, borderRadius: 13, alignItems: "center", justifyContent: "center", backgroundColor: arena.teal, borderWidth: 1.5, borderColor: arena.tealOutline },
  blurb: { textAlign: "center", minHeight: 30 }, earnRow: { flexDirection: "row", alignItems: "center", gap: 10 },
});
