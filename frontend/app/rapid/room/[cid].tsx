import React, { useCallback, useEffect, useRef, useState } from "react";
import { ActivityIndicator, BackHandler, ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import * as Clipboard from "expo-clipboard";
import { rf, uuid } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { Icon, T } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { Emblem, GameIcon } from "@/src/rapid/Art";
import { ArenaBg, CloseButton, GoldTitle, Panel, RaisedButton, SectionTitle } from "@/src/rapid/arena";
import { Pop } from "@/src/rapid/juice";
import { Face, PersonRow } from "@/src/rapid/parts";
import { ErrorBox, withRapid } from "@/src/rapid/ui";
import { clock, go, refreshInbox, roomLink, shareRoom, shortSubject } from "@/src/rapid/social";
import { encodePicks } from "@/src/rapid/scope";

const STATUS: Record<string, [string, string]> = {
  sent: ["Sent", arena.faint], seen: ["Seen", arena.aqua], joined: ["Joined ✓", arena.online], declined: ["Declined", arena.danger], left: ["Left", arena.danger],
};
const CLOSED: Record<string, [string, string]> = {
  declined: ["Challenge declined", "Nobody took a seat this time."],
  expired: ["Time’s up", "Nobody joined within 3 minutes."],
  cancelled: ["Challenge closed", "This Match Room is no longer open."],
  started: ["Match already started", "This match began before you took a seat. Ask for a new link, or play a Quick Match."],
};

/** Match Room: 5 seats filling up live, a 3-minute countdown, START for the host, and every phone leaves for the entry show together.
 *  A link room (WhatsApp match link) also seats anyone who opens the link; they become the host's friend. */
function Room() {
  const { cid } = useLocalSearchParams<{ cid: string }>();
  const router = useRouter(), insets = useSafeAreaInsets(), uid = useAuth().user?.id || "";
  const [room, setRoom] = useState<any>(null);
  const [error, setError] = useState(""), [busy, setBusy] = useState(""), [copied, setCopied] = useState(false);
  const [, tick] = useState(0);
  const fetchedAt = useRef(0);
  const stamp = useCallback((r: any) => { fetchedAt.current = Date.now(); setRoom(r); }, []);
  const load = useCallback(async () => {
    try { stamp(await rf(`/challenges/${cid}`, uid)); setError(""); }
    catch (e: any) { setError(e.message); }
  }, [cid, uid, stamp]);

  const status: string = room?.status || "";
  const joined = room?.my_status === "joined", inMatch = !!room && (room.is_host || joined);
  const live = !room || status === "open" || (status === "starting" && inMatch);
  useEffect(() => {
    if (!uid || !live) return;
    load();
    const poll = setInterval(load, 1500), second = setInterval(() => tick((n) => n + 1), 1000);
    return () => { clearInterval(poll); clearInterval(second); };
  }, [uid, live, load]);
  // The match started: every phone in the room moves into the same entry show.
  useEffect(() => {
    if (status === "started" && room.duel_id && inMatch) router.replace(go.duel({ did: room.duel_id }));
  }, [status, room?.duel_id, inMatch]); // eslint-disable-line react-hooks/exhaustive-deps

  const act = async (what: "accept" | "decline" | "leave" | "start" | "cancel") => {
    setBusy(what); setError("");
    try { stamp(await rf(`/challenges/${cid}/${what}`, uid, { method: "POST", body: {} })); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(""); refreshInbox(uid); }
  };
  const back = () => (router.canGoBack() ? router.back() : router.replace("/(tabs)/rapid"));
  const close = async () => {
    if (status === "open" && room.is_host) await act("cancel");
    else if (status === "open" && room.my_status === "joined") await act("leave");
    back();
  };
  useFocusEffect(useCallback(() => {
    const sub = BackHandler.addEventListener("hardwareBackPress", () => { close(); return true; });
    return () => sub.remove();
  }, [status, room?.my_status])); // eslint-disable-line react-hooks/exhaustive-deps

  const left = room ? Math.max(0, Math.round(room.expires_in - (Date.now() - fetchedAt.current) / 1000)) : 0;
  const seats = room?.single ? 2 : room?.seats || 0; // a 1 v 1 challenge has one seat for the friend, not five
  const seated = room ? [{ ...room.host, you: room.is_host, host: true }, ...room.players.filter((p: any) => p.status === "joined")].slice(0, seats) : [];
  const invited = room?.players || [];
  const guest = room && !room.is_host, link = !!room?.link, visitor = room?.my_status === "link";
  const title = room?.gang ? room.gang.name : room?.revenge ? "Badla lo! 🔥" : room?.single ? "1 v 1 Challenge" : link ? "Link Match" : "Match Room";
  const label = room?.label || (room ? `${shortSubject(room.subject)} · ${room.chapter || "Mixed chapters"}` : "");
  const remind = () => shareRoom(room, label);
  const copy = async () => { await Clipboard.setStringAsync(roomLink(cid)); setCopied(true); };
  const closed = status !== "open" && !((status === "starting" || status === "started") && inMatch);
  const why = CLOSED[status === "starting" ? "started" : status] || CLOSED.cancelled;

  return <ArenaBg testID="room-screen">
    <View style={[styles.frame, { paddingTop: insets.top + 6, paddingBottom: insets.bottom + 10 }]}>
      <View style={styles.top}>
        <CloseButton testID="room-close" label={room?.is_host ? "Cancel challenge" : "Leave room"} onPress={close} />
        <View style={styles.flex}>
          <GoldTitle testID="room-title">{title}</GoldTitle>
          {room ? <T testID="room-meta" w="bold" size={12} color={arena.aqua} numberOfLines={1}>{label}</T> : null}
        </View>
        {room?.gang ? <Emblem id={room.gang.emblem} size={46} /> : <GameIcon name="swords" size={42} />}
      </View>

      {!room ? <View style={styles.middle}>{error ? <><ErrorBox testID="room-error" error={error} retry={load} /><RaisedButton testID="room-back" tone="wine" label="Back to the Arena" onPress={back} style={styles.stretch} /></> : <ActivityIndicator testID="room-loading" color={arena.aqua} size="large" />}</View>
        : !closed && status !== "open" ? <View style={styles.middle} testID="room-starting"><ActivityIndicator color={arena.gold} size="large" /><GoldTitle size={26} center>Starting the match…</GoldTitle></View>
        : closed ? <View style={styles.middle} testID="room-closed">
          <GameIcon name="rival" size={92} />
          <GoldTitle size={26} center testID="room-closed-title">{why[0]}</GoldTitle>
          <T size={13} color={arena.muted} style={styles.center}>{why[1]}</T>
          <RaisedButton testID="room-quick-match" icon="swords" height={60} label="Quick Match" sub="A rival is always ready" onPress={() => router.replace(go.duel({ mode: "random", picks: encodePicks(room.picks || [{ subject: room.subject, chapter: room.chapter || null }]), r: uuid() }))} style={styles.stretch} />
          {room.is_host ? <RaisedButton testID="room-send-again" tone="wine" label="Send again" onPress={() => router.replace(go.challenge(room.gang ? { gang: room.gang.id } : {}))} style={styles.stretch} /> : null}
          <RaisedButton testID="room-back" tone="wine" label="Back to the Arena" onPress={back} style={styles.stretch} />
        </View>
        : <>
          <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
            {room.revenge ? <Panel testID="room-revenge" style={styles.revenge}>
              <GameIcon name="flame" size={44} />
              <View style={styles.flex}>
                <T w="heavy" size={15} color={arena.gold}>{room.is_host ? "BADLA LO!" : `${room.host.name} wants revenge!`}</T>
                <T w="bold" size={12} color={arena.text}>{room.is_host ? "You lost the last one. Win this and take it back." : "They lost the last match to you. Defend your win!"}</T>
              </View>
            </Panel> : null}
            {visitor ? <Panel gold testID="room-link-invite" style={styles.invite}>
              <Face p={room.host} size={52} />
              <View style={styles.flex}>
                <T w="heavy" size={15} color={arena.gold} numberOfLines={1}>{room.host.name} invited you</T>
                <T w="bold" size={12} color={arena.text}>Take a seat and you two become friends.</T>
              </View>
            </Panel> : null}
            <Panel gold style={styles.clock}>
              <T w="heavy" size={12} color={arena.aqua} style={styles.spaced}>{room.single ? "WAITING FOR YOUR FRIEND" : `${room.joined} / ${seats} JOINED`}</T>
              <T testID="room-countdown" w="heavy" size={46} color={left <= 30 ? arena.danger : arena.gold}>{clock(left)}</T>
              <T size={12} color={arena.muted} style={styles.center}>{room.single ? "The match starts the moment they accept." : "Starts on START, when all 5 seats fill, or when the timer ends."}</T>
            </Panel>
            {link && room.is_host ? <Panel testID="room-link" style={styles.link}>
              <View style={styles.linkTop}>
                <View style={styles.wa}><Icon name="whatsapp" size={24} color={arena.text} /></View>
                <View style={styles.flex}>
                  <T w="heavy" size={14} color={arena.text}>Anyone with the link can join</T>
                  <T w="bold" size={12} color={arena.muted}>They take an open seat and become your friend.</T>
                </View>
              </View>
              <View style={styles.row}>
                <RaisedButton testID="room-copy-link" tone="wine" height={48} glyph={copied ? "check" : "content-copy"} label={copied ? "Copied" : "Copy link"} onPress={copy} style={styles.flex} />
                <RaisedButton testID="room-share-link" glyph="whatsapp" height={48} label="Share on WhatsApp" onPress={remind} style={styles.wide} />
              </View>
            </Panel> : null}
            <View style={[styles.seats, room.single && styles.seatsDuo]} testID="room-seats">
              {seated.map((p: any) => <Pop key={p.pid} style={styles.seat}>
                <Face p={p} size={54} />
                <T w="heavy" size={11} color={p.you ? arena.gold : arena.text} numberOfLines={1}>{p.you ? "You" : p.name}</T>
                <T w="bold" size={9} color={arena.aqua}>{p.host ? "HOST" : "READY"}</T>
              </Pop>)}
              {Array.from({ length: Math.max(0, seats - seated.length) }, (_, i) => <View key={i} style={styles.seat}>
                <View style={styles.empty}><T w="heavy" size={22} color={arena.faint}>?</T></View>
                <T w="bold" size={11} color={arena.faint}>Open</T>
              </View>)}
            </View>
            <SectionTitle title={link ? `Players (${invited.filter((p: any) => p.status === "joined").length + 1})` : `Invited (${invited.length})`} />
            {link && !invited.length ? <T testID="room-link-empty" size={12} color={arena.muted} style={styles.center}>{room.is_host ? "Seats fill up as friends tap your link." : "Be the first to take a seat!"}</T> : null}
            {invited.map((p: any) => <PersonRow key={p.pid} testID={`room-player-${p.pid}`} p={p} sub={p.you ? "You" : `Level ${p.level}`}
              right={<T testID={`room-status-${p.pid}`} w="heavy" size={12} color={(STATUS[p.status] || STATUS.sent)[1]}>{(STATUS[p.status] || STATUS.sent)[0]}</T>} />)}
            <ErrorBox testID="room-error" error={error} />
          </ScrollView>
          <View style={styles.dock}>
            {guest && !joined ? <View style={styles.row}>
              {visitor ? <RaisedButton testID="room-not-now" tone="wine" label="Not now" height={58} disabled={!!busy} onPress={back} style={styles.flex} />
                : <RaisedButton testID="room-decline" tone="wine" label="Decline" height={58} busy={busy === "decline"} disabled={!!busy} onPress={() => act("decline")} style={styles.flex} />}
              <RaisedButton testID="room-accept" icon="swords" label={visitor ? "JOIN MATCH" : "ACCEPT"} height={58} busy={busy === "accept"} disabled={!!busy} onPress={() => act("accept")} style={styles.wide} />
            </View> : <>
              {room.is_host && !room.single ? <RaisedButton testID="room-start" icon="swords" height={62} streak label="START" sub={room.can_start ? `${room.joined} players ready` : "Waiting for 1 friend to join"} busy={busy === "start"} disabled={!room.can_start || !!busy} onPress={() => act("start")} /> : null}
              {joined ? <T testID="room-waiting-host" w="bold" size={13} color={arena.aqua} style={styles.center}>You’re in! Waiting for {room.host.name} to start…</T> : null}
              {joined && room.friend ? <T testID="room-friend-note" w="heavy" size={12} color={arena.gold} style={styles.center}>You and {room.host.name} are now friends ✓</T> : null}
              <View style={styles.row}>
                <RaisedButton testID={room.is_host ? "room-cancel" : "room-leave"} tone="wine" label={room.is_host ? "Cancel" : "Leave"} busy={busy === "cancel" || busy === "leave"} disabled={!!busy} onPress={close} style={styles.flex} />
                {link && room.is_host ? null : <RaisedButton testID="room-remind" glyph="whatsapp" label={link ? "Invite" : "Remind"} onPress={remind} style={styles.wide} />}
              </View>
            </>}
          </View>
        </>}
    </View>
  </ArenaBg>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, wide: { flex: 1.6 }, stretch: { alignSelf: "stretch" }, center: { textAlign: "center" }, spaced: { letterSpacing: 2 },
  frame: { flex: 1, width: "100%", maxWidth: 560, alignSelf: "center" },
  revenge: { flexDirection: "row", alignItems: "center", gap: 12, padding: 12, borderColor: arena.danger },
  invite: { flexDirection: "row", alignItems: "center", gap: 12, padding: 12 },
  link: { padding: 12, gap: 10 }, linkTop: { flexDirection: "row", alignItems: "center", gap: 12 },
  wa: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", backgroundColor: arena.teal, borderWidth: 1.5, borderColor: arena.tealOutline },
  top: { flexDirection: "row", alignItems: "center", gap: 12, paddingHorizontal: 16, minHeight: 56 },
  middle: { flex: 1, alignItems: "center", justifyContent: "center", gap: 12, paddingHorizontal: 20 },
  content: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 16, gap: 12 },
  clock: { alignItems: "center", padding: 16, gap: 2 },
  seats: { flexDirection: "row", justifyContent: "space-between" }, seatsDuo: { justifyContent: "center", gap: 40 }, seat: { width: "19%", alignItems: "center", gap: 2 },
  empty: { width: 54, height: 54, borderRadius: 27, alignItems: "center", justifyContent: "center", borderWidth: 2, borderStyle: "dashed", borderColor: arena.rimHi, backgroundColor: arena.panelEdge },
  dock: { paddingHorizontal: 16, paddingTop: 8, gap: 10 }, row: { flexDirection: "row", gap: 10 },
});

export default withRapid(Room, { banner: false });
