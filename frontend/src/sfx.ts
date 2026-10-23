import { createAudioPlayer, setAudioModeAsync, type AudioPlayer } from "expo-audio";

// Short arena sound effects (synthesised offline, see backend/rapidfire/make_sfx.py).
const FILES: Record<string, number> = {
  entry_rocket: require("../assets/sfx/entry_rocket.wav"),
  entry_lightning: require("../assets/sfx/entry_lightning.wav"),
  entry_supercar: require("../assets/sfx/entry_supercar.wav"),
  entry_crown: require("../assets/sfx/entry_crown.wav"),
  entry_dragon: require("../assets/sfx/entry_dragon.wav"),
  entry_blackhole: require("../assets/sfx/entry_blackhole.wav"),
  entry_meteor: require("../assets/sfx/entry_meteor.wav"),
  entry_galaxy: require("../assets/sfx/entry_galaxy.wav"),
  entry_phoenix: require("../assets/sfx/entry_phoenix.wav"),
  entry_tornado: require("../assets/sfx/entry_tornado.wav"),
  vs: require("../assets/sfx/vs.wav"),
  go: require("../assets/sfx/go.wav"),
};

const players: Record<string, AudioPlayer> = {};
let ready = false;

export function playSfx(name?: string | null, volume = 1) {
  if (!name || !FILES[name]) return;
  try {
    if (!ready) {
      ready = true;
      // Respect the phone's silent switch; never interrupt the student's music.
      setAudioModeAsync({ playsInSilentMode: false, interruptionMode: "mixWithOthers" }).catch(() => {});
    }
    const p = players[name] || (players[name] = createAudioPlayer(FILES[name]));
    p.volume = volume;
    p.seekTo(0).catch(() => {});
    p.play();
  } catch {
    // Sound is a bonus; never break the duel over it.
  }
}
