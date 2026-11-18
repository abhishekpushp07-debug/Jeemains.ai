/** Keep default device support; the optional small-APK profile targets ARM64 only. */
module.exports = ({ config }) => {
  const arm64 = process.env.JEELIVE_ANDROID_ARM64_ONLY === "1";
  // Browser arena export only (scripts/build_arena_web.sh): the web build lives under /api/arena on our server.
  const arenaWeb = process.env.JEELIVE_ARENA_EXPORT === "1";
  return {
    ...config,
    ...(arenaWeb ? { experiments: { ...config.experiments, baseUrl: "/api/arena" } } : {}),
    extra: {
      ...config.extra,
      backendUrl: process.env.EXPO_PUBLIC_BACKEND_URL,
      jeeliveApi: process.env.EXPO_PUBLIC_JEELIVE_API,
    },
    plugins: (config.plugins || []).map(plugin => {
      const name = Array.isArray(plugin) ? plugin[0] : plugin;
      if (name !== "expo-build-properties") return plugin;
      return [name, { android: {
        // R8 minify + resource shrinking off: the release build must always produce an APK/AAB.
        enableMinifyInReleaseBuilds: false,
        enableShrinkResourcesInReleaseBuilds: false,
        enableBundleCompression: true,
        useLegacyPackaging: arm64,
        ...(arm64 ? { buildArchs: ["arm64-v8a"] } : {}),
      } }];
    }),
  };
};