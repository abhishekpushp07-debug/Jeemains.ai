import { colors } from "@/src/theme";

// 3D hero portraits bundled with the app (generated once, see backend/rapidfire/generate_avatars.py).
export const AVATAR_IMAGES: Record<string, number> = {
  av_topper: require("../assets/avatars/av_topper.webp"),
  av_scholar: require("../assets/avatars/av_scholar.webp"),
  av_robo: require("../assets/avatars/av_robo.webp"),
  av_panda: require("../assets/avatars/av_panda.webp"),
  av_photon: require("../assets/avatars/av_photon.webp"),
  av_atom: require("../assets/avatars/av_atom.webp"),
  av_ninja: require("../assets/avatars/av_ninja.webp"),
  av_rocket: require("../assets/avatars/av_rocket.webp"),
  av_thunder: require("../assets/avatars/av_thunder.webp"),
  av_crystal: require("../assets/avatars/av_crystal.webp"),
  av_samurai: require("../assets/avatars/av_samurai.webp"),
  av_ice: require("../assets/avatars/av_ice.webp"),
  av_phoenix: require("../assets/avatars/av_phoenix.webp"),
  av_dragon: require("../assets/avatars/av_dragon.webp"),
  av_galaxy: require("../assets/avatars/av_galaxy.webp"),
  av_einstein: require("../assets/avatars/av_einstein.webp"),
};

export const RARITY: Record<string, { label: string; color: string }> = {
  common: { label: "COMMON", color: colors.custom_rarityCommon },
  rare: { label: "RARE", color: colors.custom_rarityRare },
  epic: { label: "EPIC", color: colors.custom_rarityEpic },
  legendary: { label: "LEGENDARY", color: colors.custom_rarityLegendary },
};
