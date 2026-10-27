# Iteration51 — corrupt filename removal and Android size analysis

## Scope and changes
- User approved build fix, then size analysis; retains under20MB and very fast native loading targets.
- Removed only a zero-byte regular file whose basename bytes were `01b0d7404030b1444038` in `frontend/`. Ordinary UTF-8 Node path decoding turned these into replacement characters and `lstat` then addressed a nonexistent path.
- Root `.easignore` now applies to the actual Git-root archive. It includes the standalone frontend package, excludes backend/private notes/archives/credentials/caches. Frontend `.easignore` is retained for standalone input layouts. No secret env files were committed or changed.
- ~69MiB local Metro cache is excluded from source upload. This is NOT an APK size saving.
- No application code, API routing, authentication, database, native engine, dependencies, protected Metro configuration or original artwork changed.

## Index-vs-working-tree finding and report correction
The first iteration51 report treated any invalid name in `git ls-files` as an active archive blocker, even when the working file was deleted. Read-only RCA repeated that EAS always checks out HEAD. **That conclusion was incorrect for the current default configuration.**

Official EAS source inspected:
- https://github.com/expo/eas-cli/blob/main/packages/eas-cli/src/vcs/clients/git.ts — `makeShallowCopyAsync` uses `git clone --no-checkout` when `requireCommit` is false, removes `.git` when ignored, then copies the working tree.
- https://github.com/expo/eas-cli/blob/main/packages/eas-cli/src/vcs/local.ts — `makeShallowCopyAsync` uses `fs.cp` with ignore filtering against actual working files.
- https://docs.expo.dev/build-reference/easignore/ — `.easignore` must be at the Git root in a monorepo.

`eas.json` does not enable `requireCommit`. The corrected regression therefore still FAILS on any existing invalid filename, and performs real Node copy + tar/gzip + extract, but reports deleted residual index entries separately. It asserts `.git` is excluded from staged input. It does not claim coverage for `requireCommit=true`, an older EAS implementation or a fresh checkout of an OLD commit.

The workspace's previous Git index still listed the deleted file during testing. The deletion and new ignore files must be captured by the normal platform snapshot/source export before building from a fresh checkout. No Git index/commit/reset operation was performed by this agent.

## Measured size, not a native artifact
Installed Expo58/ReactNative0.88 were retained. The host is aarch64 with no Java/Gradle/AndroidSDK/device. EAS CLI execution is disabled here; no bypass or cloud build was attempted after that restriction was identified.

`expo export --platform android --no-bytecode` completed. This flag was for raw graph analysis only; production Hermes and release settings are unchanged.

| Raw registered Android export | Bytes |
|---|---:|
| JavaScript | 4,321,833 |
| 74 assets | 3,900,067 |
| Total | 8,221,900 (8.222MB / 7.841MiB) |
| Fonts: 7 | 2,391,096 |
| Sound effects: 20 | 964,458 |
| Avatars: 16 WebP | 305,046 |
| Original four Home JPGs | 173,595 |

The 962KB Material Symbols font and ~1.3MB Material Design Icons font dominate asset weight. Some fonts arrive through dependencies even without app-level imports. Removing/subsetting them without tracing all routes/native registration could break icons; no unverified font or feature removal was made. WAV transcoding also needs native playback testing, not an assumed free improvement.

Raw JS/assets exclude native libraries, compiled resources (including launcher/splash), signing, DEX and Hermes bytecode effects. Total output-directory size also includes an unrelated public handoff ZIP that is NOT registered as a native asset. None of these numbers is APK, AAB, Play download or installed size. The strict target remains **an actual APK <20,000,000 bytes**; AAB device delivery needs its own measurement.

## Build settings verified
- Default `release`: AAB, minification/resource shrink/bundle compression enabled; native-library legacy packaging false; device architectures not narrowed.
- Optional existing `apk-arm64`: APK, same shrinking, `arm64-v8a` only, compressed legacy native-library packaging. This is not compatible with 32-bit-only devices or x86 emulators.
- Expo Doctor:20/20PASS. Default and ARM64 native introspection completed.

## Remaining release gates
- Full EAS archive/cloud build and signed artifact measurement remain unverified here.
- Physical Android cold/warm image, solution and WebView timing must be measured with existing Account > Loading performance. No new speed/FPS/world-best claim is supported by this build-input fix.
- Upstream canonical503/520 issue remains separate; direct account deletion remains deferred/unavailable as owner requested. No learner or archived NEET data was touched.