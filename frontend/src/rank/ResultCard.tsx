// The JEE Main Rank Card: expected rank (CRL) in silver serif, percentile on the blue rule, honest notes and share under it.
import React from "react";
import { View } from "react-native";
import Animated, { FadeIn, useReducedMotion } from "react-native-reanimated";
import { space } from "@/src/theme";
import { fmt, fmtRange, RankResult } from "./api";
import { BlueRule, CardActions, Eyebrow, MetalCard, Serial, SerifBig, SilverCaps, Small } from "./MetalCard";

export function ResultCard({ result, candidates, onShare, saved, onShortlist }: {
  result: RankResult; candidates?: number; onShare: () => void; saved: number; onShortlist: () => void;
}) {
  const reduced = useReducedMotion();
  const pct = result.percentile[0] === result.percentile[1] ? result.percentile[0].toFixed(2) : `${result.percentile[0].toFixed(2)} – ${result.percentile[1].toFixed(2)}`;
  const mid = Math.round((result.crl[0] + result.crl[1]) / 2);
  return <Animated.View entering={reduced ? undefined : FadeIn.duration(180)} style={{ gap: space.md }}>
    <MetalCard testID="rank-result" badge="JEE MAIN 2026" foot={<>
      <View style={{ flex: 1, gap: 3 }}>
        <Eyebrow>YOUR SCORE</Eyebrow>
        <SilverCaps testID="rank-result-summary">{result.summary}</SilverCaps>
      </View>
      <Serial testID="rank-result-serial" value={fmt(mid)} of={candidates ? fmt(candidates) : undefined} />
    </>}>
      <View style={{ gap: 2 }}>
        <Eyebrow>EXPECTED RANK · CRL</Eyebrow>
        <SerifBig testID="rank-result-crl">{fmtRange(result.crl)}</SerifBig>
      </View>
      <BlueRule testID="rank-result-percentile" label={`PERCENTILE  ${pct}`} />
      {result.cat_rank || result.pwd_rank ? <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.md }}>
        {result.cat_rank ? <Small testID="rank-result-cat" label={result.cat_rank.label} value={fmtRange(result.cat_rank.range)} /> : null}
        {result.pwd_rank ? <Small testID="rank-result-pwd" label={result.pwd_rank.label} value={fmtRange(result.pwd_rank.range)} /> : null}
      </View> : null}
    </MetalCard>
    <CardActions prefix="rank" onShare={onShare} saved={saved} onShortlist={onShortlist} notes={[
      result.spread, result.paper, result.check,
      result.from_marks && "Sirf marks se ye range estimate ka beech ka hissa hai, guarantee nahi.",
      (result.cat_rank || result.pwd_rank) && "Category aur PwD rank estimate hain; NTA inki table nahi deta.",
      result.delhi_note,
    ]} />
  </Animated.View>;
}
