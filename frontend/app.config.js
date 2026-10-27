/** Keep default device support; the optional small-APK profile targets ARM64 only. */
module.exports = ({ config }) => {
  const arm64 = process.env.JEELIVE_ANDROID_ARM64_ONLY === "1";
  return {
    ...config,
    plugins: (config.plugins || []).map(plugin => {
      const name = Array.isArray(plugin) ? plugin[0] : plugin;
      if (name !== "expo-build-properties") return plugin;
      return [name, { android: {
        enableMinifyInReleaseBuilds: true,
        enableShrinkResourcesInReleaseBuilds: true,
        enableBundleCompression: true,
        useLegacyPackaging: arm64,
        ...(arm64 ? { buildArchs: ["arm64-v8a"] } : {}),
      } }];
    }),
  };
};