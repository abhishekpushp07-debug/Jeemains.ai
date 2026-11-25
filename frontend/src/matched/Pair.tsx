// A matched question in a shift's list: the JEE question and ours on one card, one above the other, without options
// (those are in the shift's real paper), with glossy tabs "Question | Solution". The Solution tab opens both solutions.
import React, { memo, useEffect, useState } from "react";
import { View } from "react-native";
import { GlossTabs } from "@/src/components/GlossTabs";
import { colors } from "@/src/theme";
import type { MatchedItem } from "./api";
import { QuestionBlock } from "./QuestionBlock";
import { BOX, FLAME, Ribbon, SUN, Seal, SideHead, cardStyles, kept } from "./parts";

type Tab = "question" | "solution";

export const Pair = memo(function Pair({ it, k, width, year, where }: { it: MatchedItem; k: number; width: number; year: string; where: string }) {
  const id = `matched-pair-${k}`;
  const [tab, setTab] = useState<Tab>(kept.get(k) ?? "question");
  useEffect(() => { kept.set(k, tab); }, [k, tab]);
  const open = tab === "solution", inner = width - 2 * BOX;
  return <View testID={id} style={cardStyles.card}>
    <Ribbon it={it} id={id} word={it.n ? `Q${it.n}` : undefined} />
    <View style={cardStyles.body}>
      <GlossTabs prefix={`${id}-tab`} value={tab} onChange={setTab} items={[{ key: "question", label: "Question", look: FLAME }, { key: "solution", label: "Solution", look: SUN }]} />
      <View style={[cardStyles.panel, cardStyles.jee]}>
        <SideHead label={`JEE MAIN ${year}`} tint={colors.custom_flame} detail={where} testID={`${id}-jee-where`} />
        <QuestionBlock side={it.jee} width={inner} testID={`${id}-jee`} open={open} paper={colors.custom_flameSoft} />
      </View>
      {it.ours.map((o, j) => <React.Fragment key={j}>
        <Seal tag={o.tag} testID={`${id}-ours-${j}-tag`} />
        <View style={[cardStyles.panel, cardStyles.ours]}>
          <SideHead label="HAMARA QUESTION" tint={colors.custom_goldDeep} detail={o.source} testID={`${id}-ours-${j}-source`} />
          <QuestionBlock side={o} width={inner} testID={`${id}-ours-${j}`} open={open} paper={colors.custom_goldSoft} />
        </View>
      </React.Fragment>)}
    </View>
  </View>;
});
