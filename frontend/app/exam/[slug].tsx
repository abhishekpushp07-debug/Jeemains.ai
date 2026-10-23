import React from "react";
import { useLocalSearchParams } from "expo-router";
import { ExamHub } from "@/src/components/ExamHub";

export default function ExamHubRoute() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  return <ExamHub slug={slug} />;
}
