// A Misfire Mock before it starts: what is in it and how long it takes, its pictures coming onto the phone, and
// "Shuru karo", which starts its clock. Nothing runs until then.
import React, { useMemo, useState, useSyncExternalStore } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { privateAssets } from "@/src/api/client";
import { Icon, Notice, T } from "@/src/components/ui";
import { DCard, Pill, ScreenHeader } from "@/src/components/design";
import { colors, radius, space, subjectColor } from "@/src/theme";
import { SHORT, SUBJECTS, splitMinutes, timeLabel } from "@/src/choice/api";
import { ChoiceHero, ON_HERO, heroStyles } from "@/src/choice/looks";
import { PER_QUESTION } from "./build";
import { picturesOf, useMockPictures } from "./pictures";
import { MARKS, Mock, removeMock, saveState } from "./store";

const RULES = [
  ["timer-outline", "Timer “Shuru karo” dabate hi chalega, aur app band karne par bhi chalta rahega."],
  ["fire", "Saare sawaal aapke Misfire se hain: jo pehle galat hue ya chhoot gaye."],
  ["check-decagram-outline", "Jo sahi karoge, woh apne aap “Samajh gaya” mein chale jayenge (bina internet diya ho to internet aate hi)."],
  ["book-open-variant", "Submit karte hi result aur har sawaal ka solution. My Tests aur Misfire dono mein milega."],
] as const;
const PHONE_RULE = ["cloud-off-outline", "Phone par rakhe papers se bana: internet ke bina bhi poora chalega."] as const;

export function MockReady({ mock, short, onBack }: { mock: Mock; short: boolean; onBack: () => void }) {
  const insets = useSafeAreaInsets();
  const [sure, setSure] = useState(false);
  useMockPictures(mock.questions, mock.questions[0]?.id, false);
  const paths = useMemo(() => mock.questions.flatMap((q) => picturesOf(q)), [mock.questions]);
  // The loader itself fetches them (useMockPictures); this only shows how far it has got.
  const seen = useSyncExternalStore(privateAssets.subscribe, () => { const p = privateAssets.progress(paths); return `${p.ready}|${p.failed}`; });
  const [ready, failed] = seen.split("|").map(Number);
  const got = { ready, failed };
  const share = splitMinutes(mock.counts, PER_QUESTION);
  const count = mock.questions.length, all = paths.length;
  const loaded = all ? Math.round((100 * got.ready) / all) : 100;
  const start = () => { const now = Date.now(); saveState(mock, { status: "active", started_at: now, deadline: now + mock.minutes * 60000 }); };
  const drop = async () => { if (!sure) { setSure(true); return; } await removeMock(mock.id); onBack(); };
  // Subjects that gave fewer questions than were asked for, in the student's words.
  const fewer = SUBJECTS.filter((s) => mock.asked && mock.asked[s] > mock.counts[s]).map((s) => `${SHORT[s]}: ${mock.asked![s]} maange, ${mock.counts[s]} mile`);

  return <View testID="mock-ready-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
    <ScreenHeader testID="mock-ready-header" title={mock.title} eyebrow="Offline Misfire · taiyaar" backTestID="mock-ready-back" onBack={onBack} />
    <ScrollView contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: space.xl, gap: space.md }}>
      <ChoiceHero testID="mock-ready-hero">
        <T w="heavy" size={11} color={ON_HERO.soft} style={heroStyles.kicker}>{`OFFLINE MISFIRE #${mock.n}`}</T>
        <T testID="mock-ready-size" w="heavy" size={26} color={ON_HERO.ink}>{count} sawaal · {timeLabel(mock.minutes)}</T>
        <T size={13} color={ON_HERO.soft}>Poore {count * MARKS.correct} marks · Sahi +{MARKS.correct} · Galat −{Math.abs(MARKS.wrong)} · Chhoda 0</T>
        <View style={heroStyles.counts}>
          {SUBJECTS.filter((s) => mock.counts[s]).map((s, i) => <View key={s} testID={`mock-ready-${s.toLowerCase()}`} style={[heroStyles.count, i > 0 && heroStyles.countLine]}>
            <T w="heavy" size={18} color={ON_HERO.ink}>{mock.counts[s]}</T>
            <T size={11} color={ON_HERO.soft}>{SHORT[s]} · {timeLabel(share[s])}</T>
          </View>)}
        </View>
      </ChoiceHero>
      {fewer.length || short ? <Notice tone="warning" testID="mock-ready-short">{fewer.length ? `Utne sawaal nahi mile jitne maange the (${fewer.join(" · ")}); jitne mile, utne liye hain.` : "Kuch subjects mein utne sawaal nahi mile jitne maange the; jitne mile, utne liye hain."}</Notice> : null}
      <DCard testID="mock-ready-rules" style={{ gap: space.md }}>
        {(mock.source === "phone" ? [PHONE_RULE, ...RULES] : RULES).map(([icon, line]) => <View key={icon} style={styles.rule}>
          <Icon name={icon} size={18} color={colors.custom_chipBlood} />
          <T size={13.5} color={colors.custom_softText} style={{ flex: 1 }}>{line}</T>
        </View>)}
      </DCard>
      <DCard testID="mock-ready-pictures" style={{ gap: space.sm }}>
        <View style={styles.rule}>
          <Icon name={loaded >= 100 ? "check-circle" : "image-multiple-outline"} size={18} color={loaded >= 100 ? colors.success : colors.custom_softText} />
          <T testID="mock-ready-pictures-label" w="bold" size={13.5} style={{ flex: 1 }}>{loaded >= 100 ? "Saare sawaal phone par taiyaar" : `Sawaal phone par aa rahe hain · ${loaded}%`}</T>
        </View>
        <View style={styles.track}><View style={[styles.fill, { width: `${loaded}%` }]} /></View>
        {got.failed && got.ready + got.failed >= all ? <T size={12} color={colors.muted}>Kuch pictures abhi nahi aayi; mock ke beech mein dobara koshish hogi.</T> : null}
      </DCard>
      <View style={styles.dots}>
        {SUBJECTS.filter((s) => mock.counts[s]).map((s) => <View key={s} style={styles.dotRow}><View style={[styles.dot, { backgroundColor: subjectColor(s) }]} /><T size={12} color={colors.muted}>{SHORT[s]} {mock.counts[s]}</T></View>)}
      </View>
    </ScrollView>
    <View style={[styles.bar, { paddingBottom: insets.bottom + 10 }]}>
      <Pill testID="mock-start" kind="brand" size="lg" icon="play" label="Mock shuru karo" onPress={start} />
      <Pill testID="mock-remove" kind="outline" size="sm" icon="delete-outline" label={sure ? "Pakka? Dobara dabao, mock hat jayega" : "Is mock ko hatao"} onPress={drop} />
    </View>
  </View>;
}

const styles = StyleSheet.create({
  rule: { flexDirection: "row", alignItems: "flex-start", gap: space.sm },
  track: { height: 6, borderRadius: radius.pill, backgroundColor: colors.custom_cardLine, overflow: "hidden" },
  fill: { height: 6, borderRadius: radius.pill, backgroundColor: colors.custom_chipBlood },
  dots: { flexDirection: "row", gap: space.md, justifyContent: "center" },
  dotRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  dot: { width: 8, height: 8, borderRadius: 4 },
  bar: { gap: space.sm, paddingHorizontal: space.lg, paddingTop: 10, borderTopWidth: 1, borderTopColor: colors.custom_barLine, backgroundColor: colors.custom_bar },
});
