// A Solo Sprint from the phone's own cards. Reached two ways: from the arena, when a fresh sprint cannot get its cards
// from the server (no line, or a line too slow), and from the screen that opens without a line (/offline).
import React, { useEffect, useMemo, useState } from "react";
import { View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { nameOf, useAuth } from "@/src/auth";
import { uuid } from "@/src/api/client";
import { BankCard, dealRound, handRound, takeRound } from "@/src/offline/bank";
import { Who, offlineIdentity } from "@/src/offline/identity";
import { PlainRound } from "@/src/offline/PlainRound";
import { OfflineShell } from "@/src/offline/Shell";
import { Button, Card, Empty, Skeleton } from "@/src/rapid/ui";
import { CARD_COUNTS, decodePicks } from "@/src/rapid/scope";
import { space } from "@/src/theme";

export default function OfflineRapid() {
  const p = useLocalSearchParams<{ r?: string }>();
  return <OfflineShell testID="rf-plain-screen"><Round key={String(p.r || "")} /></OfflineShell>;
}

function Round() {
  const p = useLocalSearchParams<{ picks?: string; n?: string; again?: string }>();
  const router = useRouter(), { user } = useAuth();
  const picks = useMemo(() => decodePicks(p.picks), [p.picks]);
  const size = (CARD_COUNTS as readonly number[]).includes(Number(p.n)) ? Number(p.n) : 30;
  // undefined = not known yet; null = this phone may not play without a line / these cards are not on the phone.
  const [who, setWho] = useState<Who | null | undefined>(undefined);
  const [cards, setCards] = useState<BankCard[] | null | undefined>(undefined);
  useEffect(() => {
    let alive = true;
    (async () => {
      const mine = user ? { uid: user.id, name: nameOf(user) } : await offlineIdentity();
      const dealt = !mine ? null : takeRound(p.again) || (picks ? await dealRound(picks, size) : null);
      if (alive) { setWho(mine); setCards(dealt); }
    })();
    return () => { alive = false; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const back = () => (router.canGoBack() ? router.back() : router.replace("/offline" as any));

  if (who === undefined) return <View style={{ padding: space.lg }}><Skeleton h={380} /></View>;
  if (!who || !cards) return <View style={{ padding: space.lg }}><Card testID="rf-plain-closed"><Empty icon="cards-outline"
    title={who ? "Yeh cards phone par nahi hain" : "Pehle ek baar internet ke saath app kholo"}
    body={who ? "Is selection ke cards abhi phone par nahi aaye, ya 30 se kam hain. Koi aur chapter chuno, ya internet ke saath app kholo." : "Bina internet khelne ke liye is phone par pichhle 7 din mein ek baar sign in hona zaroori hai."}
    action={<Button testID="rf-plain-back" kind="secondary" label="Wapas" onPress={back} />} /></Card></View>;

  return <PlainRound uid={who.uid} cards={cards} picks={p.again ? null : picks} repeat={!!p.again} signedIn={!!user} onExit={back}
    onAgain={picks ? () => router.replace({ pathname: "/offline/rapid", params: { picks: p.picks || "", n: String(size), r: uuid() } } as any) : undefined}
    onRepeat={(missed) => { const token = uuid(); handRound(token, missed); router.replace({ pathname: "/offline/rapid", params: { picks: p.picks || "", n: String(size), again: token, r: token } } as any); }} />;
}
