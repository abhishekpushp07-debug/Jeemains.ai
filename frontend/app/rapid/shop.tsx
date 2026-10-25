import React, { useState } from "react";
import { ScrollView, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { rf } from "@/src/api/client";
import { invalidate, useCached } from "@/src/useCached";
import { Button, ErrorBox, Icon, Press, Sheet, Skeleton, T } from "@/src/components/ui";
import { Avatar, EntryEffect, EntryShow } from "@/src/components/Entry";
import { RARITY } from "@/src/avatars";
import { colors, radius, space } from "@/src/theme";

type Tab = "entry" | "frame" | "theme" | "powerup" | "avatar";
const TABS: [Tab, string][] = [["avatar", "Avatars"], ["entry", "Entry Effects"], ["frame", "Frames"], ["theme", "Arenas"], ["powerup", "Power-ups"]];

export default function Shop() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const uid = user?.id || "";
  const shop = useCached<any>(uid ? `u.${uid}.rfshop` : null, () => rf("/shop", uid), false);
  const params = useLocalSearchParams<{ tab?: Tab }>();
  const [tab, setTab] = useState<Tab>(params.tab || "avatar");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [preview, setPreview] = useState<any>(null);
  const [play, setPlay] = useState(0);
  const [info, setInfo] = useState(false);
  const [show, setShow] = useState("");
  const d = shop.data;
  const refresh = () => { invalidate(`u.${uid}.rfprofile`); shop.reload(); };

  async function act(path: string, body: any, key: string) {
    setBusy(key);
    setError("");
    try { await rf(path, uid, { method: "POST", body }); refresh(); } catch (e: any) { setError(e.message); }
    setBusy("");
  }
  const items = (d?.items || []).filter((i: any) => i.slot === tab);

  return (
    <View testID="shop-screen" style={{ flex: 1, backgroundColor: colors.custom_gameBg, paddingTop: insets.top + space.sm }}>
      <View style={{ flexDirection: "row", alignItems: "center", gap: space.md, paddingHorizontal: space.lg, minHeight: 52 }}>
        <Press testID="shop-back" onPress={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)/rapid"))} accessibilityLabel="Back" style={{ width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_gameCard }}>
          <Icon name="arrow-left" size={22} color={colors.onSurfaceInverse} />
        </Press>
        <T w="heavy" size={20} color={colors.onSurfaceInverse} style={{ flex: 1 }}>Arena Store</T>
      </View>
      <ScrollView contentContainerStyle={{ padding: space.lg, paddingBottom: insets.bottom + space.xl, gap: space.lg }}>
        <LinearGradient colors={[colors.custom_gameCardHi, colors.custom_examBitsatDeep]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={{ borderRadius: radius.lg, padding: space.xl, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: space.md }}>
          <Icon name="hexagon-multiple" size={54} color={colors.custom_neonAmber} />
          <View>
            <T w="heavy" size={36} color={colors.onSurfaceInverse} testID="shop-balance">{d?.coins ?? "—"}</T>
            <T w="bold" size={13} color={colors.custom_neonAmber}>Your coins · {d?.freezes ?? 0} streak freeze{d?.freezes === 1 ? "" : "s"}</T>
          </View>
        </LinearGradient>
        <Press testID="shop-what-are-coins" onPress={() => setInfo(true)} style={{ flexDirection: "row", alignItems: "center", padding: space.md, borderRadius: radius.md, borderWidth: 1, borderColor: colors.custom_gameLine }}>
          <T w="bold" size={14} color={colors.onSurfaceInverse} style={{ flex: 1 }}>How do I earn coins?</T>
          <Icon name="chevron-right" size={22} color={colors.onSurfaceInverse} />
        </Press>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ flexGrow: 0, marginHorizontal: -space.lg }} contentContainerStyle={{ gap: space.sm, paddingHorizontal: space.lg }}>
          {TABS.map(([v, l]) => (
            <Press key={v} testID={"shop-tab-" + v} onPress={() => setTab(v)} style={{ height: 44, paddingHorizontal: space.lg, borderRadius: radius.pill, justifyContent: "center", flexShrink: 0, backgroundColor: tab === v ? colors.custom_neonAmber : colors.custom_gameCard }}>
              <T w="heavy" size={13} color={tab === v ? colors.custom_gameBg : colors.onSurfaceInverse}>{l}</T>
            </Press>
          ))}
        </ScrollView>
        <ErrorBox error={error} testID="shop-error" />
        {!d ? <Skeleton h={200} /> : null}
        {d && tab === "avatar" ? (
          <View style={{ flexDirection: "row", flexWrap: "wrap", justifyContent: "space-between", rowGap: space.md }}>
            {d.avatars.map((a: any) => {
              const owned = !a.price || d.owned.includes(a.id);
              const selected = d.avatar === a.id;
              const rar = RARITY[a.rarity] || RARITY.common;
              return (
                <View key={a.id} testID={"shop-avatar-" + a.id} style={{ width: "48%", borderRadius: radius.lg, padding: space.md, gap: 6, alignItems: "center", backgroundColor: colors.custom_gameCard, borderWidth: selected ? 2 : 1, borderColor: selected ? colors.custom_neonAmber : rar.color + "66" }}>
                  <LinearGradient colors={[rar.color + "55", colors.custom_gameBg]} style={{ position: "absolute", left: 0, right: 0, top: 0, height: 110, borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg }} />
                  <View style={{ alignSelf: "flex-start", paddingHorizontal: 8, height: 20, borderRadius: 10, justifyContent: "center", backgroundColor: rar.color }}>
                    <T w="heavy" size={10} color={colors.custom_gameBg}>{rar.label}</T>
                  </View>
                  <Avatar icon={a.id} frame={selected ? d.equipped?.frame : null} size={92} />
                  <T w="heavy" size={14} color={colors.onSurfaceInverse} numberOfLines={1}>{a.title}</T>
                  {owned ? (
                    <Button testID={"shop-avatar-use-" + a.id} kind={selected ? "secondary" : "primary"} label={selected ? "Selected ✓" : a.price ? "Use" : "Use · Free"} color={colors.custom_amber} busy={busy === a.id} onPress={() => !selected && act("/profile/avatar", { avatar: a.id }, a.id)}
                      style={{ alignSelf: "stretch", minHeight: 40 }} />
                  ) : (
                    <Button testID={"shop-avatar-buy-" + a.id} label={d.coins >= a.price ? `Buy · ${a.price}` : `${a.price} coins`} icon="hexagon-multiple" disabled={d.coins < a.price} color={colors.custom_examJee} busy={busy === a.id}
                      style={{ alignSelf: "stretch", minHeight: 40 }} onPress={() => act("/shop/buy", { item_id: a.id }, a.id)} />
                  )}
                </View>
              );
            })}
          </View>
        ) : null}
        {d && tab !== "avatar" ? (
          <View style={{ flexDirection: "row", flexWrap: "wrap", justifyContent: "space-between", rowGap: space.md }}>
            {items.map((it: any) => {
              const owned = d.owned.includes(it.id);
              const equipped = d.equipped?.[it.slot] === it.id;
              const afford = d.coins >= it.price;
              return (
                <View key={it.id} testID={"shop-item-" + it.id} style={{ width: "48%", borderRadius: radius.lg, padding: space.md, gap: 6, alignItems: "center", backgroundColor: colors.custom_gameCard, borderWidth: 1, borderColor: equipped ? colors.custom_neonAmber : colors.custom_gameLine }}>
                  <Press testID={"shop-preview-" + it.id} onPress={() => { setPreview(it); setPlay((n) => n + 1); }} style={{ width: "100%", height: 96, borderRadius: radius.md, alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
                    <LinearGradient colors={(it.colors as [string, string]) || [colors.custom_gameCardHi, colors.custom_gameBg]} style={{ position: "absolute", left: 0, right: 0, top: 0, bottom: 0 }} />
                    {it.slot === "frame" ? <Avatar icon={d.avatar} frame={it.id} size={60} /> : <Icon name={it.icon} size={48} color={colors.custom_neonAmber} />}
                    {it.slot === "entry" ? <View style={{ position: "absolute", bottom: 6, right: 6 }}><Icon name="play-circle" size={22} color={colors.onSurfaceInverse} /></View> : null}
                  </Press>
                  <T w="heavy" size={14} color={colors.onSurfaceInverse} numberOfLines={1}>{it.title}</T>
                  <T size={11} color={colors.custom_gameMuted} numberOfLines={2} style={{ textAlign: "center", minHeight: 28 }}>{it.body}</T>
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
                    {it.price ? <Icon name="hexagon-multiple" size={14} color={colors.custom_neonAmber} /> : null}
                    <T w="heavy" size={15} color={it.price ? colors.custom_neonAmber : colors.custom_neonGreen}>{it.price || "FREE"}</T>
                  </View>
                  {owned && it.slot !== "powerup" ? (
                    <Button testID={"shop-equip-" + it.id} kind={equipped ? "secondary" : "primary"} label={equipped ? "Equipped ✓" : "Equip"} color={colors.custom_amber} busy={busy === it.id} style={{ alignSelf: "stretch", minHeight: 40 }}
                      onPress={() => act("/shop/equip", { slot: it.slot, item_id: equipped ? null : it.id }, it.id)} />
                  ) : (
                    <Button testID={"shop-buy-" + it.id} label={afford ? "Buy" : "Need more"} disabled={!afford} color={colors.custom_examJee} busy={busy === it.id} style={{ alignSelf: "stretch", minHeight: 40 }}
                      onPress={() => act("/shop/buy", { item_id: it.id }, it.id)} />
                  )}
                </View>
              );
            })}
          </View>
        ) : null}
      </ScrollView>
      <Sheet visible={!!preview} onClose={() => setPreview(null)} testID="shop-preview-sheet">
        <T w="heavy" size={18}>{preview?.title}</T>
        <View style={{ height: 180, borderRadius: radius.lg, backgroundColor: colors.custom_gameBg, alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
          <EntryEffect effect={preview?.slot === "entry" ? preview.id : null} play={play} sound>
            <Avatar icon={d?.avatar} frame={preview?.slot === "frame" ? preview.id : d?.equipped?.frame} size={72} />
          </EntryEffect>
        </View>
        <Button testID="shop-preview-replay" kind="secondary" icon="replay" label="Replay preview" onPress={() => setPlay((n) => n + 1)} />
        {preview?.slot === "entry" ? <Button testID="shop-preview-full" icon="fullscreen" label="Watch full duel intro" color={colors.custom_amber} onPress={() => { setShow(preview.id); setPreview(null); }} /> : null}
      </Sheet>
      {show ? <EntryShow me={{ avatar: d?.avatar, frame: d?.equipped?.frame, entry: show }} opp={{ name: "Rival", avatar: "av_dragon", frame: "frame_fire", entry: "entry_lightning", bot: true }} onDone={() => setShow("")} testID="shop-entry-show" /> : null}
      <Sheet visible={info} onClose={() => setInfo(false)} testID="shop-info-sheet">
        <T w="heavy" size={18}>How do I earn coins?</T>
        {["2 coins per correct card in sprints and duels", "+50 coins for every duel win", "+30 coins for a flawless session", "Daily quests pay 30–50 coins each", "Coins are earned only — no real money, no purchases"].map((x) => (
          <View key={x} style={{ flexDirection: "row", gap: 8 }}><Icon name="star-four-points" size={16} color={colors.custom_amber} /><T size={13} style={{ flex: 1 }}>{x}</T></View>
        ))}
        <Button testID="shop-info-close" label="Got it" onPress={() => setInfo(false)} />
      </Sheet>
    </View>
  );
}
