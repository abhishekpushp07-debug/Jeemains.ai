import React, { useCallback, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { T, tap } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { GEM_LABEL, GameIcon, GameIconName, Gem, GemColor } from "./Art";
import { SectionTitle } from "./arena";
import { Face, Note } from "./parts";
import { ErrorBox } from "./ui";
import { FeedItem, ago, go, useFeed } from "./social";

const ICONS: Record<string, GameIconName> = { win: "swords", run: "flame", level: "bolt", badge: "trophy" };
const PREVIEW = 3;

/** What happened, written to follow the friend's name. */
function story(e: FeedItem) {
  const d = e.data;
  if (e.kind === "win") return d.team ? `won a Gang Battle for ${d.team}, ${d.mine}–${d.theirs} against ${d.vs}` : d.vs ? `beat ${d.vs} ${d.mine}–${d.theirs}` : `won a ${d.players}-player match with ${d.mine} correct`;
  if (e.kind === "run") return `won ${d.n} matches in a row`;
  if (e.kind === "gem") { const gem = GEM_LABEL[d.colour as GemColor] || "rare"; return `won ${/^[AEIOU]/.test(gem) ? "an" : "a"} ${gem} diamond`; }
  if (e.kind === "level") return `reached Level ${d.level}`;
  return `earned the ${d.title} trophy`;
}

/** Friend activity: the wins, win runs, rare diamonds, level-ups and trophies of the players you added, from the last 7 days. */
export function FriendFeed({ uid, hasFriends }: { uid: string; hasFriends: boolean }) {
  const router = useRouter();
  const feed = useFeed(uid);
  const [all, setAll] = useState(false);
  const reload = feed.reload;
  useFocusEffect(useCallback(() => { reload(); }, [reload]));
  const items = feed.data?.items || [];
  if (!hasFriends && !items.length) return null;
  return <View testID="rf-feed" style={styles.list}>
    <SectionTitle title="Friend activity" testID="rf-feed-toggle" action={items.length > PREVIEW ? (all ? "Show less" : `See all (${items.length})`) : undefined} onAction={() => setAll(!all)} />
    <ErrorBox testID="rf-feed-error" error={feed.error} retry={feed.reload} />
    {!feed.data && feed.loading ? <ActivityIndicator testID="rf-feed-loading" color={arena.aqua} /> : null}
    {(all ? items : items.slice(0, PREVIEW)).map((e, i) => <View key={`${e.from.pid}:${e.id}`}>
      <Pressable testID={`rf-feed-row-${i}`} onPress={() => { tap(); router.push(go.player(e.from.pid)); }} accessibilityRole="button" accessibilityLabel={`${e.from.name} ${story(e)}. Open profile`} style={styles.row}>
        <Face p={e.from} size={42} />
        <View style={styles.flex}>
          <T testID={`rf-feed-text-${i}`} size={13} color={arena.text} numberOfLines={2}><T w="heavy" size={13} color={arena.gold}>{e.from.name}</T> {story(e)}</T>
          <T w="bold" size={11} color={arena.muted}>{ago(e.ts)}</T>
        </View>
        {e.kind === "gem" ? <Gem color={e.data.colour} size={34} /> : <GameIcon name={ICONS[e.kind] || "trophy"} size={36} />}
      </Pressable>
    </View>)}
    {feed.data && !items.length ? <Note testID="rf-feed-empty">Quiet for now. Your friends’ wins, streaks and diamonds show up here.</Note> : null}
  </View>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0, gap: 2 }, list: { gap: 8 },
  row: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 60, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 18, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
});
