// Rank share: a picture of the student's Rank and Score for one All India day (or the whole series), with a message the
// student can write in their own words. The message is on the picture and also goes out as the text with it.
//   Android app: "WhatsApp par bhejo" opens WhatsApp with the picture and the message; "Instagram ya aur apps" opens the
//   phone's share sheet with the picture (the message is copied, to paste as the caption).
//   iPhone: one button, the share sheet (WhatsApp and Instagram are both in it).
//   Browser preview: only the message goes out; the picture is made by the phone app.
// Opened from the pink Rank card of the AITS Leaderboard with ?id=<attempt id | series:all-india-jee>&day=<day number>.
import React, { useRef, useState } from "react";
import { Platform, StyleSheet, TextInput, View, useWindowDimensions } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { KeyboardAwareScrollView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { Skeleton, T } from "@/src/components/ui";
import { Pill, ScreenHeader } from "@/src/components/design";
import { Board, NoticeCard, grouped } from "@/src/components/series/Board";
import { MESSAGE_MAX, RankCard, RankFacts, rankCaption } from "@/src/components/series/RankShare";
import { SERIES_BOARD, useBoard } from "@/src/analysis/Leaderboard";
import { pc } from "@/src/analysis/format";
import { useShareLink } from "@/src/mission/stats";
import { istDate } from "@/src/navigation";
import { dayAttempt, useSeriesData } from "@/src/series";
import { shareCard } from "@/src/shareCard";
import { colors, fonts, noOutline, space } from "@/src/theme";

const STARTER = "Mera All India Rank dekho! Tum bhi aao, saath mein race karte hain.";

export default function SeriesShare() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const { id, day: dayParam } = useLocalSearchParams<{ id: string; day?: string }>();
  const width = useWindowDimensions().width;
  const { series, days } = useSeriesData(user?.id);
  const d: Board | null = useBoard(id);
  const link = useShareLink();
  const card = useRef<React.ComponentRef<typeof View>>(null); // the card, photographed as it stands
  const [message, setMessage] = useState(STARTER);
  const [busy, setBusy] = useState<"" | "whatsapp" | "more">("");
  const [note, setNote] = useState("");
  const back = () => (router.canGoBack() ? router.back() : router.replace("/series-leaderboard" as any));

  const whole = id === SERIES_BOARD;
  const day = days.find(x => String(x.day) === dayParam);
  const attempt = day ? dayAttempt(day) : undefined;
  const you = d?.state === "ready" ? d.you : null;
  const waiting = !d || (!whole && !day && !series.data && !series.error);
  let facts: RankFacts | null = null;
  if (d && you && whole) {
    facts = { when: `Poori series (${d.days_counted} din)`, kicker: `POORI SERIES · ${d.days_counted} DIN`, label: "All India Series Rank", rank: you.rank, n: d.n,
      stats: [["Score", d.maximum ? `${grouped(you.score)}/${grouped(d.maximum)}` : grouped(you.score)], ["Accuracy", pc(you.accuracy)], ["Din diye", `${you.days}/${d.days_counted}`]] };
  } else if (d && you && day && attempt) {
    const live = attempt.mode === "series_live", maximum = attempt.summary?.maximum;
    facts = { when: `Day ${day.day} (${istDate(day.date)})`, kicker: `DAY ${day.day} · ${istDate(day.date).toUpperCase()}${live ? "" : " · PRACTICE"}`, label: live ? "All India Rank" : "Paper Rank", rank: you.rank, n: d.n,
      stats: [["Score", maximum ? `${you.score}/${maximum}` : String(you.score)], ["Accuracy", pc(you.accuracy)], ["Attempted", String(you.attempted)]] };
  }
  if (facts && you?.named) facts.name = you.name;

  const send = async (toWhatsApp: boolean) => {
    if (!facts || busy) return;
    setBusy(toWhatsApp ? "whatsapp" : "more"); setNote("");
    try {
      const out = await shareCard(card, { caption: rankCaption(facts, message, link), filename: "JEELIVE-AITS-Rank.png", toWhatsApp, size: { width: 1080, height: 1350 } });
      // The share sheet takes the picture only; the message was copied for the caption.
      setNote(!toWhatsApp && out.note && Platform.OS !== "web" ? "Message copy ho gaya. Photo ke caption mein paste kar do." : out.note);
    } catch { setNote("Share nahi khul paaya. Ek baar phir try karo."); }
    finally { setBusy(""); }
  };

  return (
    <View testID="aits-share-screen" style={[styles.screen, { paddingTop: insets.top + space.sm }]}>
      <ScreenHeader testID="aits-share-header" title="Rank share karo" eyebrow="All India Series" backTestID="aits-share-back" onBack={back} />
      <KeyboardAwareScrollView bottomOffset={24} keyboardShouldPersistTaps="handled" contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + space.xxl }]}>
        {waiting ? <><Skeleton h={400} style={styles.soft} /><Skeleton h={96} style={styles.soft} /></>
          : !facts ? <NoticeCard testID="aits-share-none" icon="trophy" title="Is Rank ka card abhi nahi ban sakta." note="Card tab banta hai jab leaderboard par aapka Rank aa jaata hai. Thodi der baad dobara dekho.">
            <Pill testID="aits-share-none-back" size="sm" label="Leaderboard par wapas" bg={colors.custom_pastelInk} ink={colors.onSurfaceInverse} onPress={back} />
          </NoticeCard>
          : <>
            <View style={styles.center}>
              <View ref={card} collapsable={false} testID="aits-share-card"><RankCard f={facts} message={message} width={Math.min(340, width - 48)} /></View>
            </View>
            <View style={styles.field}>
              <T w="bold" size={12} color={colors.custom_eyebrow}>Aapka message</T>
              <TextInput testID="aits-share-message" value={message} onChangeText={t => setMessage(t.replace(/\n/g, " "))} maxLength={MESSAGE_MAX} multiline placeholder="Apne doston ke liye kuch likho" placeholderTextColor={colors.custom_dim}
                accessibilityLabel="Card par aapka message" style={[styles.input, noOutline]} />
              <T testID="aits-share-count" size={11.5} color={colors.custom_eyebrow}>Card par likha jaata hai aur photo ke saath message mein bhi jaata hai · {message.length}/{MESSAGE_MAX}</T>
            </View>
            {Platform.OS === "ios"
              ? <Pill testID="aits-share-send" size="lg" icon="share-variant" label="Share karo" busy={busy === "whatsapp"} disabled={!!busy} onPress={() => send(true)} />
              : <>
                <Pill testID="aits-share-whatsapp" size="lg" icon="whatsapp" label="WhatsApp par bhejo" bg={colors.custom_whatsapp} ink={colors.onSurfaceInverse} busy={busy === "whatsapp"} disabled={!!busy} onPress={() => send(true)} />
                <Pill testID="aits-share-more" kind="outline" icon="instagram" label="Instagram ya aur apps" busy={busy === "more"} disabled={!!busy} onPress={() => send(false)} />
              </>}
            {note ? <T testID="aits-share-note" w="bold" size={12.5} color={colors.custom_royalMid} style={styles.centerText}>{note}</T> : null}
            <T testID="aits-share-about" size={11.5} color={colors.custom_eyebrow} style={styles.centerText}>
              {Platform.OS === "web" ? "Browser mein sirf message jaata hai. Rank card ki photo phone ke app se jaati hai."
                : Platform.OS === "ios" ? "Share sheet mein WhatsApp aur Instagram dono hain; photo aur message saath jaate hain."
                : "WhatsApp mein photo aur message saath jaate hain. Instagram mein photo jaati hai; message copy ho jaata hai, caption mein paste kar do."}
            </T>
          </>}
      </KeyboardAwareScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.surface },
  content: { padding: space.lg, paddingTop: space.xs, gap: space.md },
  soft: { borderRadius: 24 },
  center: { alignItems: "center" }, centerText: { textAlign: "center" },
  field: { gap: 6 },
  input: { minHeight: 76, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised, paddingHorizontal: space.lg, paddingVertical: space.md,
    fontFamily: fonts.medium, fontSize: 15, lineHeight: 21, color: colors.onSurface, textAlignVertical: "top" },
});
