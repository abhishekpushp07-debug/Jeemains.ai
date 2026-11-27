// On the result screen, while the result is not answering (a weak line) or could not be read (no line): when this
// phone keeps a copy of that result (./papers.ts), it is offered at once. `wait`: how long to wait before offering.
import React, { useEffect, useState } from "react";
import { StyleSheet } from "react-native";
import { useRouter } from "expo-router";
import { DCard as Card } from "@/src/components/design";
import { Button, T } from "@/src/components/ui";
import { colors, space } from "@/src/theme";
import { useKeptResults } from "./papers";

export function KeptOffer({ id, wait = 0 }: { id: string; wait?: number }) {
  const router = useRouter();
  const rows = useKeptResults();
  const [due, setDue] = useState(wait <= 0);
  useEffect(() => {
    if (wait <= 0) { setDue(true); return; }
    const timer = setTimeout(() => setDue(true), wait);
    return () => clearTimeout(timer);
  }, [wait]);
  if (!due || !rows.some((row) => row.id === id)) return null;
  return <Card testID="kept-offer" style={styles.card}>
    <T w="heavy" size={15}>Internet slow hai?</T>
    <T size={13} color={colors.muted}>Is result ki copy phone par rakhi hai: score, answers aur solutions abhi khul jayenge.</T>
    <Button testID="kept-offer-open" kind="secondary" icon="cellphone-check" label="Phone par rakha result kholo"
      onPress={() => router.replace({ pathname: "/offline/result", params: { id } } as any)} />
  </Card>;
}

const styles = StyleSheet.create({ card: { gap: space.sm } });
