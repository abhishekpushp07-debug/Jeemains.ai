import { createAudioPlayer, setAudioModeAsync, type AudioPlayer } from "expo-audio";

// Short arena sound effects (synthesised offline, see backend/rapidfire/make_sfx.py; stored as 96 kbps AAC .m4a, a third of the WAV size).
const FILES: Record<string, number> = {
  entry_spark: require("../assets/sfx/entry_crown.m4a"),
  entry_rocket: require("../assets/sfx/entry_rocket.m4a"),
  entry_lightning: require("../assets/sfx/entry_lightning.m4a"),
  entry_supercar: require("../assets/sfx/entry_supercar.m4a"),
  entry_crown: require("../assets/sfx/entry_crown.m4a"),
  entry_dragon: require("../assets/sfx/entry_dragon.m4a"),
  entry_blackhole: require("../assets/sfx/entry_blackhole.m4a"),
  entry_meteor: require("../assets/sfx/entry_meteor.m4a"),
  entry_galaxy: require("../assets/sfx/entry_galaxy.m4a"),
  entry_phoenix: require("../assets/sfx/entry_phoenix.m4a"),
  entry_tornado: require("../assets/sfx/entry_tornado.m4a"),
  vs: require("../assets/sfx/vs.m4a"),
  go: require("../assets/sfx/go.m4a"),
  correct: require("../assets/sfx/correct.m4a"),
  wrong: require("../assets/sfx/wrong.m4a"),
  combo: require("../assets/sfx/combo.m4a"),
  tick: require("../assets/sfx/tick.m4a"),
  win: require("../assets/sfx/win.m4a"),
  lose: require("../assets/sfx/lose.m4a"),
  levelup: require("../assets/sfx/levelup.m4a"),
  coin: require("../assets/sfx/coin.m4a"),
  // All India card scenes (Mixkit free sound effects, mixed by backend/rapidfire/make_scene_sfx.py)
  scene_space: require("../assets/sfx/scene_space.m4a"),
  scene_cup: require("../assets/sfx/scene_cup.m4a"),
  scene_lion: require("../assets/sfx/scene_lion.m4a"),
  scene_race: require("../assets/sfx/scene_race.m4a"),
  scene_arrow: require("../assets/sfx/scene_arrow.m4a"),
};

const players: Record<string, AudioPlayer> = {};
let ready = false;

/** Respect the phone's silent switch; never interrupt the student's music. */
function audioMode() {
  if (ready) return;
  ready = true;
  setAudioModeAsync({ playsInSilentMode: false, interruptionMode: "mixWithOthers" }).catch(() => {});
}

/** A longer piece of music from our server, downloaded before it plays so a dance can follow its beat. Same sound rules as the effects. */
export function loadTrack(uri: string): AudioPlayer | null {
  try { audioMode(); return createAudioPlayer({ uri }, { downloadFirst: true }); } catch { return null; }
}

export function playSfx(name?: string | null, volume = 1) {
  if (!name || !FILES[name]) return;
  try {
    audioMode();
    const p = players[name] || (players[name] = createAudioPlayer(FILES[name]));
    p.volume = volume;
    p.seekTo(0).catch(() => {});
    p.play();
  } catch {
    // Sound is a bonus; never break the duel over it.
  }
}
