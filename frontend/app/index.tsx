import { Redirect } from "expo-router";
import { View } from "react-native";
import { useAuth } from "@/src/auth";
import { colors } from "@/src/theme";
import { HOME_ROUTE } from "@/src/arenaMode";

export default function Index() {
  const { user, ready } = useAuth();
  if (!ready) return <View style={{ flex: 1, backgroundColor: colors.surface }} />;
  return <Redirect href={user ? HOME_ROUTE : "/entry"} />;
}
