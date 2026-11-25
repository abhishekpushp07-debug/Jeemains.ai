// Under one of our questions in a Matched paper (the test player, and the solutions after it): the JEE Main question it
// matched, without options. Drawn only for a paper this phone knows to be a Matched paper (./api.ts keeps their ids), so
// an ordinary paper asks the server nothing and shows nothing.
import React, { useEffect, useMemo, useState } from "react";
import { View } from "react-native";
import { useCached } from "@/src/useCached";
import { colors } from "@/src/theme";
import { MatchedShift, getPaper, isMatchedPaper, shortDay, yearOf } from "./api";
import { QuestionBlock } from "./QuestionBlock";
import { BOX, SideHead, cardStyles } from "./parts";

/** `paper` = the paper's id on the website (the attempt's set_id), `qid` = the question on screen, `open` = the JEE
 *  question's own answer and solution are shown too (after the paper is submitted). */
export function MatchedWith({ paper, qid, width, open = false }: { paper?: string | null; qid: string; width: number; open?: boolean }) {
  const [known, setKnown] = useState(false);
  useEffect(() => {
    let live = true;
    setKnown(false);
    if (paper) void isMatchedPaper(paper).then(yes => { if (live) setKnown(yes); });
    return () => { live = false; };
  }, [paper]);
  // Kept in memory while the app is open: one read for the whole paper.
  const d = useCached<MatchedShift>(known && paper ? `matched.paper.${paper}` : null, getPaper(paper || ""), false).data;
  const hit = useMemo(() => d?.items.find(it => it.ours.some(o => o.qid === qid)), [d, qid]);
  if (!d || !hit) return null;
  return <View testID="matched-with" style={[cardStyles.panel, cardStyles.jee]}>
    <SideHead label={`JEE MAIN ${yearOf(d.day)} MEIN AAYA`} tint={colors.custom_flame} detail={`${shortDay(d.day)} · Shift ${d.shift}${hit.n ? ` · Q${hit.n}` : ""}`} testID="matched-with-where" />
    <QuestionBlock key={qid} side={hit.jee} width={Math.max(1, width - 2 * BOX)} testID="matched-with-jee" open={open} paper={colors.custom_flameSoft} />
  </View>;
}
