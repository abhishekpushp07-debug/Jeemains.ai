# Iteration40 — silent earliest loading, encrypted device reuse, Android size work

## Latest user instructions override iteration39
- 75-question paper may have78 original image pieces: remove that distracting image counter completely. Do not change canonical questioncounts/content.
- Start/Re-attempt card tap should directly start/open the attempt; noReadySheet/extra confirmation/fixed30second wait. Keep mandatorysilent storage/canonicalpreflight/idempotency and officialdeadline unchanged.
- Warm all question images ASAP; releasedsolutions immediately after submit. Reuse device downloads on subsequent opens.
- Android build requested below20MB. No APK/AAB file or native buildtoolchain was supplied; do not claim this target achieved.

## Implemented
- Removed player/result/solution imageprogress counters and ReadyToStartUI. Local image placeholder only while currentimage ismissing; actualfailure retry remains. Subjecttabs/grid unchanged; paperquestioncount stillsourceauthoritative.
- PYQ tap starts detail+preflight concurrently; canonical/start immediately stages attemptmetadata/imagequeue BEFOREstoragecleanup/navigation/Player render. Player consumes sameinflightmetadata instead ofduplicateGET. Original serverclock uses metadatareceived monotonic time, so staging cannot extend deadline.
- On submitACK, start resultsrequest immediately; Resultscreen sharesinflightrequest and normal202Retry-Afterpolling. Enqueue solutions onlywhen released200summary permits them. No pre-release/embargo/lockedbonus assetdownloads and nofakeconsultationevents.
- Six total slots,one reserved for visiblequestion, remainingbackground; all paths scheduled,48MiBRAM LRU pinscurrentcrops. No admissionstopatRAMlimit: encrypted disk keeps previouslydownloaded crops while RAMwindow rotates.
- Privatepersistentdevicecache256MiBbudget,16MiBperoriginal-imagecap (largerimages stillRAM-only). Native: appcache directory+AES256-GCM encryptedbytes, accountkey inSecureStoreTHIS_DEVICE_ONLY, atomicfiles/index, hashedfilenames, no photos/gallery/publicstorage. Web: realWebCrypto nonextractableAES-GCM CryptoKey+encryptedIndexedDB, smallmetadata-only LRUcatalog, atomicrecord/indexwrites. Nonces random; AADbindsaccountnamespace+sourcecachekey. NoPIN/cookie/sourceURL in diskmetadata.
- Verifiedaccount/origin hash gates reads. Coldsameaccountopen reusesencryptedfiles; otheraccountpurges namespace/key. Explicitlogout purges RAM+disk; expired/unknownsession locksRAM/grants and leaves onlyciphertext forsameaccount reauthentication. Missingquota/crypto gracefully usesRAM, neverplaintextfallback.
- Authorizationgrants derivedonlyfromauthenticatedattempt/releasedresultmetadata. Candidatekey canmatchstableqid/kind/crop/version acrossreattempts, BUT newattemptpathmust passauthorizedfreshnesscheck before reuse. Never inferpermissionfromfileexists.
- Cachefreshness usesETag/Last-Modified+Range(1byte)/If-Range or304. Ifunchanged, reuseoriginalencryptedbytes withoutfullimage download. Changed200response replacescache; missingvalidators/unsupportedpartialrequests mayrequirefullfetch. Server remains authority. Original/revisedpaths separated, modifiedmanifestinvalidatesoldRAM, lateaccountgeneration nevercommitsprivateimages.
- `/api/jl` transparentproxy now forwardsconditional/range requestheaders andETag/Last-Modified/Content-Range responseheaders; authcookies/canonicalorigin unchanged. Originalsourcebytesnottransformed.
- Stronglimits: OS/browser mayevictcache, uninstall/logout clearsit, sourcecorrectionsrequirefreshbytes, deviceoutofspacefallsbackRAM. **Neverpromise “neverdownloadagain”.** Firstquestionbytescannotprecedecanonical/startpermission because noprepare/activateAPIexists.

## Android size
- AddedSDK-matchedexpo-file-system58.0.10+expo-build-properties58.0.11 viaexpo installer (resolvedcompatiblepatches; noSDKdowngrade).
- Releaseconfig enablesR8minify,resourceshrink,JSbundlecompression. Default `release` buildsAAB withfullarchitecture support; optional `apk-arm64` buildprofile targetsARM64only withcompressednativelibraries (not32-bit/emulatorcompatible). Doesnotdropfeaturesfromdefaultprofile.
- Removed unusedRobotoMono fontloading (licencedsourcefiles retained); original4Homeartworks/Figtree/RF assets preserved.
- ExcludedhandoffZIPs/testsfromEASuploadinputs; oldexportZIPnotdeleted. Rawexporthad2,584,559byteweb-staticarchive notlistedinnativeassetmanifest, so NOclaimthatitwasAPKweight.
- Measured `/tmp/jeelive-size-export/metadata.json`: native registered **rawJS+assets8,160,615bytes (~7.78MiB)**; rawJS4,271,485bytes,75registeredassets. Entirefolder10,750,064bytesincludesweb-staticarchive. **Neither measurement is APK/AAB size.**
- DefaultHermesexportblocked: hostARM64 vsbundledx86-64hermescompiler. Troubleshooterconfirmed; `expo export --platform android --no-bytecode` usedONLYforbuild-graph/assetmeasurement. ProductionengineNOTswitched, noSDK/Metroprotectedconfigchanged.
- NoJava/Gradle/AndroidSDK/aapt oractualAPK/AABartifact here. Actualinstallablesizeand<20MBtargetremainUNVERIFIED; useproperreleaseartifactmeasurement beforeanyclaim.

## Testing scope
- Needisolatedcachecrypto/persistence/tamper/expiry/race/validator/early-stage tests plusAndroidconfig/graphchecks, thennativephysicalQA.
- LivePINcredentialsstillpreviously401anduserskippedupdates; doNOTretry,guess,resetorcreateaccounts. Noactualnetworklatency/privatepaperintegration proof withoutworkingauthorizedsession. Syntheticfixturetests mustbelabelledisolated,neverpresentedasliveproof.