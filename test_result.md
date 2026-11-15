#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

## Iteration56 — user click opens app preview instead of download
iteration56_delivery:
  user_request: "Direct toh aur doenload nahi ho rha zip.me shi format do ya kuch aise do jo ho doenload . Actually click krte hi preview khul ja rha app ka"
  priority: high
  stuck_count: 3
  implemented: true
  working: true
  needs_retesting: false
  scope: "NEWphonecompatibleZIPexactly2verified720pbaselineMP4s,preservingoriginalmasterZIP;fixedassetlaunch-mobile-pack.zip+short/api/marketing/videos.zipalias;standalone/backendHTML/api/marketing/downloads withactualformdownloadbutton,noExpo/router/login. No app/auth/academicdatachanges."
  diagnosis: "Publicexistingfile200attachmentbytescorrect,noredirect;appNOuniversal/associateddomains. Useractualchat/browsernotknown. TroubleshooteragainassertedWhatsApp/Telegraminterceptionwithoutdeviceevidence;DO NOT adoptasconfirmedcause. Supportlookupstopped/unverified,no documentedchatattachmentoralternatehostmechanism."
  test_plan: "ValidateNEWZIP publicdownload200PKsignatureSHA/sizeexact2ASCIIrootmembersplainZIP_STOREDnoencryptionCRC/extractedMP4SHA+fullffmpegdecode. Alias+canonicalrouteidenticalbytes/headers/ranges;actualbrowseronstandalonepagebuttonexpect_downloadnotjustcurl, filenamecompletebytesCRC, neitherrootExpo norredirect. BothstandaloneMP4buttonsdownload. Mobile320/390layoutnooverflow,plainHTMLnoauth/Metro. Existing9assetsunchangedexacthashes;allowlistnow10. Userchatclick/physicalphoneconfirmationNOTclaimed."
  files: "backend/marketing_media.py,backend/launch_download.html,marketing/launch45/download_pack.py,marketing_manifest.json"
  main_checks: "MainREALbrowserpageZIPbuttonsave13403359bytes/PKmagic/CRC/extractedMP4SHA PASS;390/320nooverflow. Independent100/100pytest,3/3actualbrowserZIP+MP4clickdownloadscompleteexactfilenames/bytes/SHA/pageunchanged;publicextractedvideofulldecodesPASS. Reporttest_reports/iteration_56.json."
  user_device_verified: false
  final_guidance: "GivecopyableFULL/api/marketing/downloadsURLforChromeaddressbarinstead ofonlyclickablechatlink;DownloadZIPthenFilesDownloadsExtractMP4. Rootcauseofuserchatpreviewopeningunproven;awaitphoneconfirmation."

## Iteration55 — session stability and fast list verification
iteration55_current:
  user_choices: "Pehle logout aur list loading. World best banao na. Then verify MP4 compatibility."
  priority: high
  needs_retesting: false
  implemented: true
  working: true
  changes: "Inherited auth refresh/confirmation and 10s account-scoped list cache need independent edge-case tests. Added catalogue/My Tests focus+foreground revalidation; catalogue pull-refresh and memoized bounded rows; useCached explicit manual-refresh state and immediate matching-key warm data. Original artwork/theme/canonical records unchanged."
  test_plan: "Actual client and provider tests: concurrent data401 + foreground /auth/session rotation race; network/5xx/HTML malformed recovery must not logout; confirmed anonymous must clear; old epoch must not resurrect; cached profile not auth; credentials not replayed. List cold/warm/10s revalidation/manual force/failure/account isolation. Read-only live phone UI login once then PYQ/BITSAT mocks/MyTests navigation, foreground+offline return. No academic writes, no new accounts, no PIN changes or RF writes."
  context: "Integration playbook invoked but generic response incorrectly mentioned POST/auth/session; actual local supplied transport contract specifies GET/auth/session (may rotate) and POST/auth/refresh. Do not adopt invented endpoint. Native current package versions remain source of truth. Handoff claimed universal MP4 fix but compatible files exist only locally, not manifest; check later, no false physical-device claims."
  main_checks: "FINAL23new+7existingfrontendregressionsPASS,tsc/lintsPASS;96backend/mediaPASS. RealBITSAT50/page2/search/clear/revisit andMyTests3tabsPASS. Injected503keeps10visiblecompletedrowsandsession;realRetry200recovers;320pxnooverflow. Originalreport55 failures superseded by main followup, not deleted."
  fixes_verified: "Client sessionGET/refreshPOST rotationordering+tokenrevision; malformedrefresh401transient; PINchange noautoplay; cancellationindependentsharedrenewal. Webproxy perSIDcurrentworkerlocks+mergeincomingcookies. Ordinaryreads stayparallel; multiworkercoordination remainsseparategate."
  compatible_delivery: "NEWvertical-mobile.mp4/landscape-mobile.mp4publicmanagedobjects;7,032,763/6,370,296bytes.45s720pbaselineH264+AAC,fulldecode/SHA/downloadPASS. Originals/ZIPunchanged; physicalphoneplayback nottested."
  final_report: "test_reports/iteration_55_main_followup.json"
  limitations: "No physical Android or signed artifact; world-fastest/<20MB remain unverified. Account deletion remains owner-deferred."

iteration55_testing_review:
  agent: testing
  working: false
  needs_retesting: true
  report: "test_reports/iteration_55.json"
  findings: "Four unresolved auth gaps: sessionGET/refreshPOST rotation overlap (client AND proxy), malformed/null refresh401 clears verified user, automatic auth/pin replay, caller abort waits during refresh. New actual-module tests17/23PASS; backend14/15PASS. Production unchanged."
  passing: "Existingiter49 7/7; iter46cachePASS;10sacademicTTL/force/privatecounts/hookkeyisolation/focusPASS. RealONE approvedlogin200/reusedsession. RealPYQ30,BITSATpagination/search,MyTests3tabsGET5/5PASS. BothcompatibleMP4fulldecode+publishedoriginaldownloadhashesPASS."
  browser: "390/320Home4originalartworks/PYQ30/nooverflowPASS. ActualbrowserPYQfirst247ms,warm137ms,0newrequestsafterHomeprefetch;NOTAndroid. BITSAT/MyTestsUI/failureinjectionnotreachedafterharnessnavigationselectorfailures;dontclaimfullUIpass."

## Iteration54 — launch-file download complaint
launch_download_fallback:
  implemented: true
  working: true
  needs_retesting: false
  report: "test_reports/iteration_54.json"
  change: "Explicitvideo downloads nowoctet-streamattachment;defaultpreviewtypesunchanged. Always-attachmentlaunch-pack.zipcontains2bit-identicalMP4masters. NoappUI/authchanges."
  verified: "58/58deliveryregressionsPASS; independentbrowserusergestureZIP+bothMP4downloads3/3PASSfilename/bytes/SHA;mainalsoZIPdownload/extract/CRC/masterSHAsPASS."
  zip: "15097795bytes;sha256aceeaa6329a41e32109521acb6f9da1118c81b0816b1c27ab33577dbec339822"
  remaining: "Useractualdevice/browserfailurecouldnotbereproduced;don'tassertparticularWebViewcause. NewZIPfallback+binarydownloadverifiedonstandardtestbrowser,awaituserconfirmation."

## Iteration53 — Research-led dual-format45s launch film
iteration53_final:
  working: true
  needs_retesting: false
  report: "test_reports/iteration_53.json"
  checks: "67/67PASSpublicdeliveryandmediaregressions;all6assetsSHA/HEAD/GET/MIME/attachment/allowlist;Ranges/conditionalrequests;4fullvideodecodes1350frames/durations/resolutions/codecs/audio/faststart;posters;realWebMbrowserplayback+seek390andwide."
  delivery: "Currentbase+/api/marketing/launch/vertical.mp4?download=1 andlandscape.mp4?download=1;previewvertical.webm/landscape.webm."
  limitations: "ThisbrowserlacksH264/AAC;validMP4download/decodeverifiedseparatelyfromactualWebMplayback. PhysicalphoneMP4notclaimed. NoappUI/nativebundle/datachanges."
launch45_delivery:
  implemented: true
  working: true
  needs_retesting: false
  user_choices: "BothVerticalReel/ShortsANDLandscapeYouTube;45-secondcinematic;Music+Hinglishtext;researchfirst,beautifulnotmechanical;dominant20secondno-penRapidFireandAllIndiaTestSeries."
  creative: "marketing/launch45/BRIEF.md isauthoritative—notunsupported claims in generateddesign_guidelines.json.27sRapidFire,12sAllIndia,6sbrandfinale;motion-designedconceptpreview,notlearnerfootage;nofakecoins/ranks/percentile/4thexamclaims. Originallogo/avatars/palettepreserved."
  implemented_files: "marketing/launch45/{graphics,shots,render,music,publish}.py;backend/marketing_media.py +server.pyrouterinclude;generatedbackend/marketing_manifest.json. No mobileappUI/auth/data/dependencychanges."
  real_outputs:
    - "vertical.mp4:1080x1920,45.000s,30fps1350frames,H264yuv420p/AAC48kstereo,7724316bytes"
    - "landscape.mp4:1920x1080,45.000s,30fps1350frames,H264yuv420p/AAC48kstereo,7373179bytes"
    - "Same-contentVP9/OpusWebMbrowserpreviews(vertical4486542bytes,landscape4517644bytes),2JPEGposters;managedobjectstorageUUIDuploads+allSHAreadbacksPASS. Sourcestagesalsoobjectstored. No commercialmusiccopied;originalinstrumentalcomposed."
  public_routes: "/api/marketing/launch/{vertical.mp4,landscape.mp4,vertical.webm,landscape.webm,poster-vertical.jpg,poster-landscape.jpg};GET/HEADonly;?download=1attachment;singlebyterangesexplicitbecauseStarlette0.37.2. Fixedallowlist,sanitized503errors,noarbitraryproxy/upload/privatecontent."
  verified_main: "Pythonlint/compilePASS;ffprobemasters45.000s/resolution/codecsPASS;manageduploadsSHAreadbacksPASS;independentvideo/audioanalysisreviewedactualverticalandfinallandscape:legible,nooverlap/blankframes/harshaudio;transitionpolished. RealpublicWebMbrowser390playsbothformats,seek11.9sNewtonanswerand31.5sAllIndiaPASS."
  browser_diagnostic: "MP4testbrowsercannotdecodeH264/AAC:canPlayTypeempty,DEMUXER_ERROR_NO_SUPPORTED_STREAMS,HTTP206valid. The initialRCAclaim'no-storeuniversallypreventsbuffering'wasincorrect;WebMplaysunderSAMEheaders,CDN/env/cacheconfigUNCHANGED. MP4mastersvalid andfornormalclients/upload;WebMactualtestedbrowserpreview."
  testing_required:
    - "Verifyall6publicassetsHEAD/GET fullSHAagainstmanifest/contenttypes/content-length/downloadattachment,unknown/traversalprivatepaths404,bounded/open/suffixranges206withcorrectbytes,invalid/reversed/huge/multirange416,IfRangefallback200/IfNoneMatch304. Noauthrequired/noaccountrequests."
    - "FFmpegFULldecode4videos;ffprobeMP4exact45.000s/WebMwithin.1s,expected1080dimensions30fps,all1350frames,audio48kstereo,MP4faststartmoovbeforemdat. Measureaudiononsilence/peak/blackframeboundaries,don'tmistakedarkdesignforblank."
    - "BrowserVP9/Opusloadplayseekbothvariants,muteunmuteifgesturepossible,endhold,390/landscapewide;don'tcallMP4brokenwhenbrowserdoesn'tsupportitscodec. MainalreadypublicactualWebMplays/seekPASS."
    - "Read-onlyappentryandknownhealthsmoke;frontendlogo/theme/Home/RF/SeriesBanner unchangedhashagainstlatestpre-videoGitcommit. NoAPIacademic/RF/walletwrites/privateuserlogin orfixturesoncanonical. Allassetsoutsidefrontend/nativebundle. NoEAS/build/deploymentchecks."
  limitations: "Quiz/duel are clearlymotion-designedfeatureillustrations;notactuallearnerrecording. BrowserQAusesWebMbecausetestbrowserlacksH264/AAC;physicalphoneMP4notclaimedtested. ExistingAPK<20MB/upstream/deletionbacklogunchanged."

## Iteration52 — All India native gradient washout
iteration52_final:
  working: true
  needs_retesting: false
  physical_device_verified: false
  regression: "5/5PASS. ActualReactWebsiteGradient render + all ownerexportlayers/shine/CTA/ribbon → actualinstallednativeSVGextractor; everyoriginalARGB/offset/angle/order retained. Reproducesbeforeopaque255 andcorrects0/51/26alphas. Normalizerboundary usesRNWebprocessColor, notnativehardware. TSC/lintsPASS."
  palette_preservation: "Token/theme/SeriesBanner/ExamCardFinish/ExamTile and original4JPG hashes match7cd149d. OnlyRGBAconversionandStopopacitycodechanged."
  main_ui: "RealPINPOST200/Home/banner390and320/readability/explicitopacity/pause/explaineropenclose/Openhub→livePASS. Noacademic/gamewrites."
  tester_ui_note: "Independenttesterentryattemptinconclusive; noPINPOST at09:59inbackendlogs, onlyauth/session200. PriorMAIN09:54realPINPOSTandseriesGET200withsuccessfulbannerflowfulfillsUIcheck; not claimingallauthreliabilityfixed."
  report: "test_reports/iteration_52_main_followup.json"
series_native_opacity:
  user_request: "Yebkyu colour badal diye all india test series ka ? Gadhe — screenshot shows opaque white/black/red banner and white/black CTA hiding title/schedule."
  implemented: true
  working: true
  needs_retesting: false
  priority: high
  files: "frontend/src/gradientStop.ts, frontend/src/components/WebsiteGradient.tsx"
  cause: "Installed react-native-svg/src/lib/extract/extractGradient.ts:91-92 discards stopColor alpha (color &0x00ffffff) and replaces it with stopOpacity default1. Our stops only passed rgba color, so intended0..0.25opacity becameopaque on native, unlike browser. Same forCTAtransparentblack."
  fix: "Use RN processColor to split opaque RGB and explicit unsignedARGBalpha/255, memoized pergradientvalue; pass BOTH stopColor and stopOpacity to SvgStop. Palette/designtokens/layers/order/angles/animation/layout/content unchanged. Home textremoval edit did NOT touch anyseries/themefile (gitcomparison verified)."
  main_checks: "TSC+lintsPASS. RealreadonlyHome390/320: explicit0andsoftalphaSVGstops, darkruby/onyxreadablebanner/redCTA, pause shine, explanationopen/close andOpenhub→/livePASS. Noattempt/accountwrites."
  test_plan:
    - "Add nativegradientregression using actual installed Svg extractGradient conversion with real RN processColor-compatible normalization: reproduce BEFOREopaque255 forRGBA0/.2, AFTERalpha0/51, preserveRGB/offsets. Native extraction code not just hand-reimplemented assertion; nohardwareclaim."
    - "All current ownerexport livebanner layers/shine/CTA/ribbon: alpha0,.04,.1,.13,.15,.2,.25,1; opaque rgb/hex/named andRGBAalpha boundaries. SignedAndroidpackedcolors andtransparent0 handled; fallbackinvalidcolor doesn'tcrash."
    - "Actual WebsiteGradient renderer passes BOTHprops; useMemo transformation preserves layerorder,offsets/angles/size/CSSgradientLine. Compare supplieddesign-tokenfile/theme/SeriesBanner/ExamTile/artwork hashes to7cd149d, no palettechange."
    - "Phone390/320 readonly banner/shinepause/resume/explanation/hub and nohero textregression. Useapprovedcredentials memory/test_credentials.md onlyifneeded; mainalreadyloggedinlive once, no repeatedauthforunitcases; stop401/429. Nolearnerwrites/API mocks/productseeds."
  limitations: "No physicalAndroid here. Browser alone cannot prove native fix; actual native SVG JS gradient extraction regression required, devicevisual confirmation remainsusercheck."

## Home screenshot correction — boxed text removal
home_copy_removal:
  implemented: true
  working: true
  needs_retesting: false
  file: "frontend/app/(tabs)/index.tsx"
  scope: "Remove five marked marketing text elements and unused headline styles; preserve original four exam artworks/labels/routes and all functional sections."
  verification: "Self-tests PASS: real approved PIN sign-in, five removed testIDs absent, four original images fully loaded, 390px/320px grid without horizontal overflow, JEE Main route works, tsc and changed-file lint pass. No academic/learner writes."
  screenshots: "jeelive-home-clean-loaded-390.jpeg, jeelive-home-clean-loaded-320.jpeg"
  limitations: "Phone-size browser preview only; unrelated native build/performance/backlog unchanged."

## Iteration51 — EAS invalid filename fix and native size analysis
iteration51_main_followup:
  local_archive_working: true
  needs_retesting: false
  full_eas_or_signed_artifact_verified: false
  report: "test_reports/iteration_51_main_followup.json"
  verified: "Root+frontend actual Node copy/tar/gzip/extraction PASS202/201files; no existing or staged invalidUTF8 names. Required build inputs retained, secrets/caches/backend/gitmetadata excluded. Existing24frontendtests/TSC/Doctor20/20/public390smoke PASS."
  corrections: "Initial tester/RCA index-only critical conclusion incorrect for current default EAS --no-checkout + working-tree-copy. Officialsourcechecked. Test strengthened to actualfs.cp; this caught root !/frontend/ directoryfilter mismatch, fixed to !/frontend and retestPASS. Deleted path in previousindex remains snapshotwarning, notcurrentworkingarchivefailure."
  limitation: "Normal snapshot must capture deletion and ignorefiles before fresh checkout. No Gitwrites/EASguardbypass/cloudbuild. <20000000byteAPK/physicalspeed stillunverified."
iteration51_build_inputs:
  user_confirmation: "Build fix, phir size jaanch. World best lightening fast and under 20mb app."
  implemented: true
  working: NA
  needs_retesting: true
  priority: high
  changes:
    - "Deleted ONLY the confirmed zero-byte invalid-UTF8 file frontend/<bytes 01 b0 d7 40 40 30 b1 44 40 38>. Byte-path unlink required; no Git writes/reset. Snapshot should record deletion."
    - "Added root .easignore: official EAS docs require Git-root rules; frontend-only .easignore was insufficient for this monorepo. Native frontend code/assets/config/scripts remain included; backend/private notes/content archives/env/key/test/cache/build outputs excluded. Retained frontend ignore for standalone packaging."
    - "Excluded ~69MiB local .metro-cache from source upload. This is NOT an APK-size reduction claim. No native engine/SDK/app code/API/data/auth changes."
  main_checks:
    - "Whole frontend GNU tar to /dev/null PASS; corrupt path absent, no existing tracked invalid UTF8 names."
    - "Expo Doctor20/20 PASS. Android raw export --no-bytecode PASS: JS4321833 + assets3900067 =8221900 bytes (8.222MB/7.841MiB). Not signedAPK, not Hermes bytecode; production Hermes unchanged."
    - "Default and ARM64 native introspection PASS; shrinking/minify/bundle-compression remain enabled."
  test_plan:
    - "Independent byte-safe filesystem/index scan; confirm deleted file no longer in latest tracked snapshot."
    - "Use installed ignore library to stage both repo-root and frontend-only source archives; validate UTF8 roundtrip + Node lstat and gzip/tar extraction. CLI EAS is blocked here: do NOT bypass or call cloud builds. Label archive emulation honestly."
    - "Assert required frontend package/yarn/config/metro/main/preinstall guard sources, app routes, legal JSON, referenced assets remain; reject backend, memory, .emergent, .git, credentials/env, caches, tests, public handoff ZIP. Do not read/report secret values."
    - "Repeat raw-export measurements independently and verify release/ARM64 gradle properties; default architectures unchanged. Run existing iter40/48/49 isolated frontend suites24tests, no learner mutations."
    - "Mobile public entry/privacy smoke390px, no realPIN/login needed. Do not alter account/history/RF/wallet or canonical API."
  limitations: "No AndroidSDK/Java/Gradle/physicaldevice; EASCLI execution disabled. Full cloud archive/build and signedAPK/AAB<20000000bytes not verified. Prior canonical503/520 risks and deferred direct-account-deletion remain."


## Iteration 30 — exam isolation, diagrams, weak revision, NEET portable bank
user_problem_statement: "Separate JEE/NEET leaderboards using arena exam selection; quick Biology diagram cards; one-tap most-missed chapter revision; save all existing NEET content independently for future NEETLIVE.AI."
backend:
  - task: "Exam-scoped content, rewards, ranking, history and matchmaking"
    implemented: true
    working: true
    file: "backend/server.py, backend/gamify.py, backend/duels.py, backend/exam_groups.py, backend/exam_migration.py"
    needs_retesting: false
    priority: high
    status_history:
      - agent: main
        working: NA
        comment: "Exam pinned at play creation; separate indexed profile XP counters; backward-compatible defaults Biology=NEET, other old play=JEE. Legacy awarded XP reconstructed. Existing WS/capped event transport unchanged."
  - task: "Idempotent missed-card events and revision"
    implemented: true
    working: true
    file: "backend/revision.py"
    needs_retesting: false
    priority: high
    status_history:
      - agent: main
        working: NA
        comment: "Completed solo/duel incorrect+timeouts count, skips/unseen excluded. Most-missed unresolved active cards grouped by chapter; correct replay clears. Repeat completion does not duplicate misses. Legacy activity backfilled."
  - task: "Independent NEET source and export bundle"
    implemented: true
    working: true
    file: "neetlive/content, neetlive/tools/export_bundle.py, neetlive/README.md"
    needs_retesting: false
    priority: high
    status_history:
      - agent: main
        working: NA
        comment: "7585 cards = Physics 2610, Chemistry 2095, Biology 2880; 18 original diagrams replace text within 90-card caps. Independent IDs for NEET PC, stable old Biology IDs. ZIP manifest/checksums; no personal data/secrets in default content bundle. Optional explicit owner private export only outside repository."
frontend:
  - task: "Exam leaderboard, Biology diagrams, one-tap revision"
    implemented: true
    working: true
    file: "frontend/app/(tabs)/rapid.tsx, frontend/app/rapid/session.tsx, frontend/app/rapid/duel.tsx, frontend/src/components/ArenaLearning.tsx, frontend/src/components/ExamLeaderboard.tsx, frontend/src/components/BiologyDiagram.tsx"
    needs_retesting: false
    priority: high
    status_history:
      - agent: main
        working: true
        comment: "Self-smoke at 390x844: pilot login, NEET toggle, diagram sprint 18 cards, SVG prompt, option feedback, return and NEET leaderboard PASS. Need complete play/revision, exam-switch cache isolation, 320px overflow, all 3 drawings and duel regression. tsc --noEmit passes."
test_plan:
  current_focus: ["Exam scoring/match isolation", "Revision idempotency and clearing", "Diagram correctness/rendering", "Portable NEET export", "Existing sprints/duels/WS regression"]
  stuck_tasks: []
  test_all: false
agent_communication:
  - agent: main
    message: "Read test_credentials.md. Main browser smoke passed; external URL from frontend env. Legacy unscoped catalog/cards returns canonical JEE + Biology, scoped exam=NEET includes independent PC copies; old raw DB total assertions must now filter exam. Please write iteration_30 tests/report. Do not invoke generation/audit scripts or reset DB."
  - agent: main
    message: "Iteration30 passed 10 new +13 regression cases. Follow-up16/16 includes rerun10 new +6 WS checks; 29 unique backend cases total. Mobile320/390 diagram+revision passed; main verified NEET invite/quick-match/complete/rematch/solo/start-another. See iteration_30_followup.md. User verification pending; no known blockers. Private data migration and physical-device/capacity tests not performed."

## Owner ZIP download follow-up
- User requested an actually downloadable NEET ZIP and explanation of independent backend/app/website copying.
- Added an owner-issued 256-bit expiring bearer capability, issued only by trusted-workspace CLI (`backend/tools/owner_download.py`). Only token SHA256 stored; 24h max, explicit expiry/revocation/type/content-hash validation, no HTTP mint endpoint, no learner-header authorization.
- `GET /api/owner-downloads/{token}` returns the fixed existing ZIP as attachment/no-store/nosniff/no-referrer. Exact bytes are checked and returned without path input or replacement race. Uvicorn access log token is redacted; upstream infrastructure logging is not controlled by this app.
- Needs backend tests: valid ZIP/header/hash, invalid/malformed/expired/revoked/type-mismatched/changed-hash grants denied, public mint unavailable, learner header cannot grant access, stored token digest only, CLI revocation and TTL index, no regressions to NEET catalog.
- Final verification:10/10 pass (`test_reports/pytest/iter31_owner_final.xml`). The first run's sole failure was exact Cache-Control equality; the edge keeps no-store and adds no-cache/must-revalidate. Corrected test to require no-store and disallow public/max-age rather than a specific ordering/string. Owner link to be issued only after this verification; no raw token stored in reports.

## Iteration32 — live website theme + direct JEE Main PYQ flow
- User: match changed jeelive.ai theme; replace JEE mocks with new PYQ/solutions. Chosen flow: Mains card -> PYQ -> direct full list, Start / Continue / Result+Re-attempt, minimal clicks; year+shift grouping.
- Implemented Figtree and verified live charcoal/red website tokens, new native brand/exam cards and hub, primary/semantic contrast fixes. BITSAT/COMEDK mocks and chapter practice retained. JEE old catalogue?kind=mocks redirects to /pyq.
- New /pyq list uses real existing student GET /pyq/jee-main through unchanged cookie-session proxy/native direct API. No demo or fabricated app data.
- One-tap start performs fresh server status check + existing preflight + persistent idempotent start key; retries preserve key, per-user/set single-flight. Continue reads exact saved attempt and NEVER starts a new one; sealed attempts route to result. List focus/pull refresh, visible per-row errors, dynamic year/shift filters.
- Supplied solutions retain source-image/question-ID mapping, zoom and answer-key-only honesty; supplied typed question/solution maths now renders with bundled native KaTeX, readable web fallback. No AI-generated replacement for uploaded solutions.
- IMPORTANT LIVE BLOCKER: live authenticated GET https://jeelive.ai/api/pyq/jee-main returnsHTTP200 total0/items[] (also through preview). Correct upstream/config confirmed by independent troubleshooting. Uploaded/staged admin state cannot be inspected; owner needs to check publication/student visibility. Do not mark real PYQ start/submit/solution mapping fully verified with this empty dataset.
- Main checks: tsc and JS lint passed. Preview390/320 confirms new home, Mains->PYQ direct two-tap route, actual0 empty state + refresh, no horizontal overflow. Initial screenshot selector typo was fixed to source testID home-tile-jee-main; app itself rendered correctly.
- Testing needed: test-only fixture scenarios for all button states, one-tap sequence, duplicate prevention, failed start same-key retry, new reattempt newkey, stale active->result no POST; navigation/filter/error/empty/narrow; existing result supplied image/typedmath/answerkey and RF/NEET regression. Keep fixtures isolated to tests, never seed or publish fake live PYQ data.
- Iteration32 report read;4/4 live backend checks passed and real UI navigation/layout/redirects/RF passed. Isolated fixture contract tests passed; main fixed grading hint/result-release logic and verified genuine new-key reattempt. Narrow Re-attempt label now single-line. Existing generic Header back-ID collision found during cleanup was removed for new hub/PYQ screens with explicit unique IDs. No fixture data shipped.
- Remaining P0 is EXTERNAL: real upstream PYQ list still0, so real-paper solve/submit/solution-mapping E2E remains pending publication/visibility by backend owner. Do not mark this as a fully verified real PYQ feature until live rows exist.

## Iteration33 — authoritative PYQ contract + source-environment investigation
- User provided latest public GitHub repo and authorized Go; wants actual website/app shared backend, not a duplicate question bank.
- Found and corrected REAL local frontend bug: blanket `live_enabled:false` checks incorrectly rejected ordinary PYQ practice. Source catalogue permission contract only uses this flag for import/chapter event content. Removed checks in `frontend/src/api/pyq.ts`; count/state/permission checks otherwise retained.
- Verified actual source-project API returns30 genuine papers/2250 questions and separate pilotUIDaac7961a-b3df-4c14-a422-c5c46ab022f4. Current jeelive.ai API returns0 and its known packagepaper IDs404, currentpilotUIDdb0c62b8-eeaf-41be-b8b1-05f5f34ac1d8. Separate identities/data; app URLs remain unchanged. Credentials notes updated for separated test contexts.
- Need regression test falseflag ordinaryPYQ remainsnew/startable and auth/preflight failures stillblock. Prefer real source-project API for academic end-to-end, without changing persistent appconfig or importing data. If temporary browser transport forwards to real sourceproject, explicitly report that it is isolated testing, not mainappswitch or fakeAPI.
- Three earlier manual website-browser trace attempts failed due harness assumptions (loginignoresnext, freshcontexts, authhome notlandinganchors), not duewebsiteauthfailure. Testing agent shouldinspectDOMcontrols afterlogin insideonescript andcaptureactualrequest; no guessedselectors orcacheadvice.
- Iteration33 real API suite3/3passed, includingfalseflagpractice,sourcequestions75,sourcequestionimage200,pre-submit solutionlock,save/resume,submit/results,re-attemptidempotency.
- Main follow-up isolated browser forwarded actualHTTP tosourceproject (notfabricatedresponses): rendered30realpapers inapp,Startwithfalseflag,answerSave/Continue sameID,submit,75questionresult,providedsolutionimages200/render/zoomat320,Re-attempt newID andoriginalresultpreserved. Test signedout/forwardingremoved; persistentappconfigsunchanged. Initialtestassert expectedrows,actualcontractquestions75; correctedtestonly, appalreadyhandledit.
- Codefix verified. Remainingcriticaldecision: retainjeelive.ai'sexistingidentity/history andsyncmissingpaperswithwebsite-owneraccess, or explicitlypointappatworking30-paperproject'sdifferentidentity/history. Never switchorimportsilently. Awaiting ownerconfirmation.
- Owner confirmed keeping currentjeelive.ai history and requested100%sharedbackend. NO preview switch. Live protected-import probe: anonymous401/learner403; currentPYQ0; websiteRFcatalog404. No writes performed. Secure owner credential collection needed for canonical PYQ sync; fullRFsharing requires website-side integration/migration and is not already complete.
- LATEST USER SCOPE OVERRIDE: shared backend is required EXCEPT Rapid Fire. Keep RF separate and do not treat RF404 on canonical website as a blocker. User asks for website-project handoff covering academiccontent/solutions, authidentity/history/results and exact design/card-theme parity. Handoffdocument updated accordingly.

## Iteration35 — complete native theme mapping + newly available canonical PYQs
user_confirmation: "Theme aur UI checks; Pehle PYQ availability check. Abhi confirm nahi. 100% same content except rapid fire."
frontend_theme:
  implemented: true
  working: NA
  needs_retesting: true
  files: ["frontend/src/theme.ts", "frontend/src/components/ExamTile.tsx", "frontend/src/components/ExamCardFinish.tsx", "frontend/src/components/ExamHub.tsx", "frontend/src/components/LearningTheme.tsx", "frontend/src/components/PyqPaperCard.tsx", "frontend/src/components/ui.tsx", "frontend/app/(tabs)/index.tsx", "frontend/app/(tabs)/tests.tsx", "frontend/app/result/[id].tsx"]
  status: "Owner CSS exam colours, native sheen/pause/reduced motion, responsive title wrapping, PYQ spacing, learning badges/top borders, maroon score, 5-colour result tabs. Fixed two pre-existing unfinished compile errors (Press accessibility props, unavailable navigation import). Academic/auth/RF data code unchanged. tsc + modified JS lint pass."
main_smoke:
  result: "PASS: real canonical pilot login, home exam colours, pause switch, JEE hub -> PYQ, 30 real papers, year filter, 390/320 preview."
  artifacts: ["theme-home-390.jpeg", "theme-jee-hub-390.jpeg", "theme-pyq-390.jpeg", "theme-pyq-320.jpeg"]
live_data:
  result: "Canonical GET /pyq/jee-main now returns30 real papers/[2026,2025]. Old external empty-list blocker no longer reproduced. NO source-project switch, import, fake responses or seed. Need real canonical E2E now."
test_plan_iter35:
  current_focus:
    - "Theme switch/animation, all3 exam hubs, responsive320/390; no clipped labels/overflow; My Tests library and all5 Results tabs"
    - "Canonical direct vs app proxy existing identity, all PYQ metadata, chapters/mocks/live catalogue parity, history/result/question/solution consistency"
    - "One actual new canonical PYQ on approved pilot: Start -> answer saved -> leave -> Continue same ID -> submit -> Result -> supplied solution images -> Re-attempt newID, old result preserved"
    - "Read-only Rapid Fire JEE/NEET catalogue/leaderboard and arena smoke; do NOT change RF data or migrate it"
  special_instructions: "Run first4 iteration34 parity tests; fifth has obsolete RF migration assertions, DO NOT treat missing canonicalRF as blocker. Existing pilot9000000001 in memory/test_credentials.md; keep canonical UID. New academic test attempts allowed ONLY on this approved pilot for E2E, log their IDs, never modify old attempts. No mocks/interception/source-environment redirects. No auth changes/OTP. Do not run opt-in RF mutation seed or external-source iteration33 tests."

iteration35_final:
  working: true
  needs_retesting: false
  backend: "9/9 parity tests passed, no skipped cases. See pytest/iter35_parity_final.xml. Includes new75-question result signatures and original question+solution image hashes."
  frontend: "Main real UI E2E passed: Start->source image->saved response->leave->Continue sameID->submit->result->supplied solution/zoom->Re-attempt newID->old result preserved->My Tests. Theme/3hubs/320+390/pause/accessible states and read-onlyRF NEET/JEE board/chapter checks passed."
  followup_fixes: "Test-only repeated logins fixed to session reuse;429 cooldown recovered with no auth policy changes. Corrected actual accessibility selected/checked forwarding and nested My Tests compare buttons. Follow-up verified no nested buttons or accidental compare navigation; final console only expected canceled request on navigation."
  final_report: "test_reports/iteration_35.json"
  artifacts: "test_reports/artifacts_iter35/followup/"
  live_state: "PYQ30 available; BITSAT50 mocks; COMEDK0 mocks in canonical website and app alike. No local replacements. RF separate by explicit scope."
  limitations: "Physical-device QA pending. Source equality verified for listed endpoint samples and75 question signatures, not a claim of every asset/device/signup path tested."

## Iteration36 — owner ZIP authoritative adoption
user_request: "ZIP integration source, canonical https://jeelive.ai/api only; preview URL download-only; RF untouched; preserve existing IDs/history; no PIN cutover. Existing pilot records compare karo, uske baad pilot test bi."
status: "Implemented; main smoke PASS; extended testing pending."
source: "reference/integration-2026-10-26/APP_INTEGRATION.md + design-tokens.json; adoption details NATIVE_ADOPTION.md."
changes: "Source-driven layered home blue/platinum,amber,teal,ruby/onyx; original managed-storage logo; exact font files/licences/icon paths; academic dark status states; black/crimson hubs; real-only series schedule placeholders. Root RF tokens, auth, API routing unchanged."
verification_so_far: "Before pilot writes,9/9 current canonical parity checks passed(-n0). Original logo GET200, bytes/hash match supplied SVG. tsc/lints passed. Real existing learner home/PYQ30, mobile390/320, all4gradients, pause switch, other-page dark hub passed. No new pilot writes yet."
test_next:
  - "First read-only compare existing identity/history/result/resume to canonical;30 packaged paperIDs & sum2250. Do not open old attempt in player (visit writes); readAPI only."
  - "Then user-approved fresh pilot UI scenario on untouched paper; at most2 new attempts including full reattempt. Old7completed + existing active attempt must stay unchanged. Two independent canonical sessions compare saved state/results/source assets; test stale revision rejection only on NEW test."
  - "Compare token layers/source fonts/logo; selected/disabled/reducedmotion;320/390; private source white/unfiltered; original-source assets order; RF read-only smoke."
  - "Use phone9000000001 approved existing pilot from memory/test_credentials.md, never source-project account. Login once per session, run-n0, stop on429/Retry-After. Never seed RF, create new accounts, call PIN endpoints, swap envs or log cookie/identity/answer dumps."

iteration36_user_correction:
  priority: "P0: restore original card artwork. User explicitly rejected replacing target/diamond/rocket/crown with website SVG symbols. Keep JEELIVE theme elsewhere."
  implemented: true
  main_verified: "Exact4 original JPG files hosted via public managed storage and byte-compared. Restored image-top2×2 layout/dark text panels; no colour filters. Removed ExamGlyph. tsc/JS+Python lints PASS. Screenshots390/320 show correct4 artworks; JEE->PYQ30 navigation passes."
  testing_agent_scope: "Verify correction first, all4 destinations and320/390, then existing-record read-only comparison and previously authorized ONE fresh pilot. Do NOT change original icons again even if ZIP tokens differ. Live banner keeps source ruby/onyx."

iteration36_final:
  working: true
  needs_retesting: false
  result: "PASS: original4artworks, byte/hash identity, managed logo, all4destinations,30paper/2250questions, reducedmotion/banner-only switch. Tests11read-only passed; partial optin script intentionally not used. Main fulfilled user's earlier fresh-pilot approval via ONE actual UI flow (notanotheraccount), full result/solution and existing record preservation checks passed."
  assets_configuration: "Backendbranding endpoint now uses explicit BRANDING_STORAGE_URL only; no module fallbackhost. Backend restarted; final5/5 publicassets hash tests pass. No academic auth/RF changes."
  fresh_pilot: "Completed. Minimal ID stored memory/test_credentials.md, no newpublicidentity/answer dumps. Source sample75questions/results equal; sampled originalquestion+solution imagehashes equal direct/proxy."
  transient_harness_issue: "Chromium SIGSEGV before first launch script did not create anattempt; troubleshoot confirmed transient, one retry succeeded."
  context_correction: "Owner evidence filename is evidence/canonical-pyq.json, not pyq-live-index.json. It exists and30IDs/sum2250 match."
  remaining_scope: "PhysicaldeviceQA and previewPIN rollout/authhardening are separate backlog, no cutover. User must never again have original4cardartworks replaced during globaltheme work."

## Iteration37 — remove NEET from this Rapid Fire app, preserve archive
user_request: "Neet ug hata do bhai rapid se wo toh tumne alag zip rkha na bna kr"; choice: "Archive mein safe rakho".
implemented:
  - "JEE-only lobby (Physics,Chemistry,Maths), no NEET toggle/Biology shortcut; leaderboard/recent/revision scopedJEE. Shared coins/XP/streak not reset. Home original4artworks and globaltheme unchanged."
  - "Backend central active-exam boundary: default lists areJEE-only; explicitNEET gets410. Guards block NEET creation, repeat-request reuse, review/completion, invitation joining, duelmutations/settlement andWebSocket access before writes. Oldrecords retain original schemas/data."
  - "NEET bank excluded from live periodic sync; files/ZIP/records not deleted, retired or moved. Logicalarchive: inaccessible in current learner APIs, preserved forowner."
preservation_baseline: "test_reports/iter37_archive_baseline.json includes NEET rf_cards8083(allinclretired),sessions32,duels11,awards10,learning_events8,oneprofileNEETsegment and ZIPhash9b51ca14..."
main_checks: "tsc and changedJS/Pythonlints pass. RFcatalog default JEE/7045cards/3subjects; NEET410. ZIP exists1055634bytes and ziptestpasses beforeedits. Need AFTERhash equality and JEEregression tests."
external_auth_blocker:
  - "Canonical POST/auth/phone was200at18:08; nowphone-only422at18:39. Public /api/openapi.json nowrequiresphone+pin, verified byintegrationexpert+troubleshooter. This is externalPINcutover, notourRFchanges."
  - "No usable approvedexisting session among8newest nonemptyjl_jars checked withGETauth/me. Never guessPIN, reset/createaccount or fakeauth. No auth/canonicalURL changes made."
  - "Main screenshot loads entry but cannotfreshlogin. Authenticated frontendlive verification currentlyBLOCKED. BackendRF X-RF-User testcontract remains operational; isolatedtests notequivalenttoliveUI."
test_scope:
  - "Verify exactarchive baselinecounts/hashes using actualbackend.env MONGO_URL+DB_NAME; doNOTinfer0NEETdocs from APIavailability. They MUST remain8083."
  - "TestJEEcatalog/cards/history/revision/leaderboard, transientQA-onlysolo/duel flows. No canonicalacademic writes, no realpilotwallet changes."
  - "AttemptNEETquery/create/legacyBiology/archivedrepeat/get/complete/dueljoin/get/actions/websocket; assertreject andnoarchivechanges. Never deleteorreset existingNEETrecords."
  - "Frontend noNEETtoggle/Biology shortcut; archiveddeeplinkstops beforePOST; checkTypeScript and isolatedcomponent/staticproof ifcannotauthenticate. ReportliveUIblocked honestly."

iteration37_final:
  implemented: true
  backend_working: true
  backend_tests: "Final17/17PASS/no skips, pytest/iter37_neet_archive_final.xml. Initialagent14/14; main tightenedJEEduelanswer to200 and added explicitNEETcreation/default-history/finalpost-testhash checks."
  archive_preserved: "Exactall5NEETcollection counts/hashes, NEETprofilestats segment andZIP bytes/hash unchanged aftereveryrequest. No archiveretire/delete/move; original schema retained andliveNEETsyncdisabled."
  frontend_status: "JEE-only source/typechecking passes; noNEETselector/Biologyshortcut, archiveddeep-link guard. LiveauthenticatedUI retestpending: canonicalPINnowrequired, appphone-only422, no validapprovedsession. No claim ofliveUIpass."
  needs_retesting: true
  next_scope: "Owner-coordinatednativePINclient/recovery; onceauthenticationworks, verifyliveRapidUI. Do notmodifyauthorresetaccounts justtofinishNEETremoval."

## Iteration38 — live PIN auth client implementation (testing)
user_scope: "Live PIN pushed; update app login/signupConfirmPIN/PINchange/ForgotPIN. CanonicalAPIonly,existingaccounts/resultspreserved,RFuntouched. User suppliedsecuretestPHONE/PIN then 'Keys added, please continue.'"
implementation:
  - "PINlogin and explicitsignup tabs,4ASCII-digit stringvalidation, leadingzeroes preserved, confirm mismatchbeforePOST; maskedPIN/visibilitytoggle; noPINstorage/logging. Real canonical endpoints, nophonefallback."
  - "New signed-in change-pin route confirms ownmobile,newPIN/confirm; respects other-sessionrevocation, verifies sameauth/meID aftersuccessfulchange; no accountreset. Account buttons, new PINhelp route."
  - "ForgotPIN is honest guidance: liveOpenAPIonly/auth/pin, noforgot/reset/OTP. Existing signed-insession→ChangePIN; otherwise existingofficialadmincontact. Noinventedrecoveryendpoint/contact ormessage-send."
  - "Authbootstrap only trusts canonical/session, no cached-profileauth. Expired401 clearprivateuser/cache, preserveaccountdrafts; logout guardpreventsofflinecookieauto-login; refreshsingleflight+oneretry, explicit429countdown, noautomaticPINretries."
  - "Same nativecanonicalcookie transport and webper-SIDproxy, Constantsconfigfallback; no serverauth/RFcode, brand/cardicons or DBedits. Physicalnativecookiepersistence stillunverified."
main_checks: "tsc+JSbatchlints pass.390login/signup mismatch andForgot guidance screenshotspass; foundrepeatedentry stack onhelpreturn, fixedtodismissTo; no livePINsubmitted yet bymain."
testing_scope:
  - "Use securebackendJEELIVE_TEST_PHONE/PIN withoutprinting. Loginoncepersession, readonlycompare directcanonical vs appproxyID/history/PYQ30/sourceimages ifexistingresult. No guessedPIN, noreset/signup/changePIN on approvedaccount. Stopifcredentialsrejected."
  - "Validate webUIlogin→home→reloadpersist→AccountChangePINform+localmismatch/noPOST→help→logout→privatedeep-linkblocked→relogin. TestpreviousiterationJEEonlyRFUIreadonly (NEETabsent). DoNOTstartRFsession/changeavatarwallet."
  - "Isolatedunit/contracttests fornew-signup+PINchangerequestshapes/malformed4digits/leading0; don'tlabelisolatedpositiveasliveproduction. Signupsuccess/PINchangeidentity-revocation NOTauthorizedonrealaccount."
  - "Rate/offline/refreshprivate-cache behaviour canbeisolatedtransportharness; nofakeprodAPIorappdemo. Reportactual vsisolated scopeandany untestedpositivewrites honestly."

iteration38_current_status:
  implementation: "PINscreens and canonicalrequest wiring ready; authenticatedverificationBLOCKED."
  verification: "Public390/320Login/SignupPINmask/leading0/localconfirmation/Forgotguidance/oneentrybackroute/privateauthgate PASS. Changedauthfiles strictprojecteslint andtsc PASS aftermainfixed6lintissues."
  blocker: "Suppliedsecurephone/PIN got401directcanonical andproxy, oneattemptperchannel. No retryguessing/reset/registration.7dependentbackendcases correctlySKIPPED, NOTpassed. Runtimeenvmatches savedsecrets. RequestsecureworkingLIVEcredentials."
  report: "test_reports/iteration_38.json"
  risks: "No publicForgotPINresetAPI; guidanceonly. Positive signup/PINchangewrites notauthorizedoncurrentaccount. Nativephysicalcookiepersistencenottested."

## Iteration39 — subjectnavigation + aggressive private image preload (implemented, verificationpending)
user_choices: "Subject tabs + question grid; Ready hote hi start. Questions download ho jane chiye background me as soon as possible taki navigation butter smooth ho."
changes: "Priority4-slotdedupqueue/48MiBmemorybudget; all permitted crops backgroundload,current/subject priority; no disk/publiccache; blobURLsforweb/nativeRAMdataURI; activeaccountscope,cancel+purge/logout,retry429respect. Player subjecttabs/subjectgrid/lastquestionmemory/Nextsubject, visibleimagegatesanswers. Results allreleasedquestion+solutionpreloadduringAnalysis, versionedsourcepaths,responsivegrid. ReusedpreflightReadySheet(no30s), no/startuntilStartnow, ContinueexistingID."
source_truth: "reference/PLAYER_LOADING_CONTRACT.md. NO pre-startimage endpoint exists;preflightnotdownload. Can'tpromiseallpaperbeforeclockwithoutcanonicalprepare/activate. Start_keyremainsUUIDnotPIN. Noauthfallback/staffassetuse/RFchanges."
checks_so_far: "Latest tsc+fullESLint overchangedfiles PASS; generallintPASS. Needunit/isolatedtests. LivePINstoredpairpreviously401,userpausedkeyupdate; DONOTretrybadcredentials. SecurecorrectPINneededforlivepaint/networktimings andJEEUI."

iteration39_verification:
  implementation: "ReadyforliveQA; noAPI/content/timer/RFbackendchange."
  tested: "Final17/17isolatedunit/contracttests PASS; actualqueueclassandnavhook testedwithsyntheticloader/statefixtures. Includes75/150normalimages simulated,dedup,reservedslot,48MiBbound,pinnedLRU,abort/latecomplete/pause/groupcancel,429retry,croporder,subjectmemory/fiveunevengroups/gridfit,bonus/release/versiongates,readinesspreflight/startUUID."
  live_smoke: "Hosted390main/375agent appentryrenders,noerrors. No authenticatedfixtureoroldcredentialretry."
  static: "Strictprojecteslint allchangedfiles + tsc PASS afterfinalfollow-up."
  pending: "UpdatedsecureworkingLIVEphone/PIN needed. Liveplayernavigation/sourcequestionmetadata/actuallatency/solutionwarmup E2E unverified. Localhostcross-originCORS isexistingnonrequiredtestorigin issue,hostedworks."
  user_action: "User skipped securecredentialupdate afteriteration39 implementation. No more credential attempts; safehandoffwithliveverificationpending."

## Iteration40 — silent direct start + encrypted persistent images + Androidsize
user_scope: "Remove75/78imagecounter/distraction. DownloadASAPonStart/Reattempttap; solutionsafterSubmit; reuseonsamedevice. ChoiceSeedhatestkholo. UseralsorequestsAndroidbuildunder20MB."
implementation: "RemovedReadySheet/progresscounters; earlyattempt/resultstagingbeforePlayer/Resultsrender,dedupmetadatafetch,originaldeadlinepreserved;6slotsvisiblepriority,fullpaperscheduling+48MiBRAM/256MiBencrypteddisk. AESGCMnativeSecureStore+Files/webnonextractableCryptoKeyIDB;authorizedmanifestgate,ETag/rangevalidatorforreuse,nootheraccount/lockedsolutionleak,logoutpurge,expirylockedciphertext. Transparentproxyconditional/rangeheadersonly."
size_work: "R8/shrink/compression,defaultAAB+optionalARM64APKprofile,unusedMonoloadingremoved,ZIPuploadexclusion. AndroidrawJS/assetsgraphcompiled with--no-bytecode:8,160,615registeredbytes; NOTAPK. ActualHermescompileblockedARM64host/x86binary; noSDK/Gradle/Java orAPKartifact. <20MBNOTverified."
latest_checks: "TypeScript/projectESLint/PythonlintPASS. Neednewiteration40tests; olderiter39ReadySheet/staticexpectations nowobsolete. Noauthcredentialretry/nativephysicaltest."
reference: "reference/ITER40_SILENT_CACHE_AND_ANDROID_SIZE.md"

## Iterations42–44 — approved Rapid Fire premium portrait refresh
iteration44_rapid_current:
  implemented: true
  backend_working: true
  frontend_working: true
  reports: "test_reports/iteration_42.json, iteration_43.json, iteration_44_self_verify.json"
  scope: "FULL approved /app/plan/plan.md Phase1; portraitenergyart/lobby/darkcards/actualcoins/privatefriendhistory/shop/results + fullbankreview/permanentRFcleanup. Academic/PINaccounts/PYQs and archivedNEET unchanged. Phase2/3 notbuilt."
  content: "7045 fullhash-bound AI-assisted cardreviews,6155kept,890newrejected deleted plus4041olderretiredJEErecords.14 originalscientificvector diagrams. No bulkrewriting. Freshdecks30unique,20sec; no padding. Timing editorialestimate not measuredguarantee."
  cleanup: "209solo,388duels,255learningevents deleted; JEEperformance/leaderboardreset.344profiles/10257Coins/399awardrecords andallprotectedwallet/ownership/NEETfingerprints unchanged aftercleanupandQA. Maintenanceoff, freshJEEhistoryempty."
  backend_checks: "Finalserial regression19passed1sparsePhysicsdata-dependent skip; canonicalpositiveintegrationpreviouslypassed, not repeatedly retried. HTTPownerbinding/WSfirstframetoken,30cardduelfinish/rewards,solo/idempotence,shop/equip/insufficient,historyprivacyanduniquecontent passed."
  ui_checks: "Main390/360phonechecks completedsolo correct/skip/real20stimeout/result+2Coins/currentbalance/newplayagain; invite/join/liveanswer/full30duelfinish/historyread-onlyrow; shoppurchaseconfirmation/deduction/equip/balancerefresh/cancel; nativevectordiagramreadability,4optionsaccessible,nohorizontaloverflow."
  harness_findings: "Iteration43fakecanonicalfixturetriggeredlegitimate401signoutfromacademicprefetch; solvedONLYintestharnessbyisolatingirrelevantJLcalls, notweakeningproductionauth. Combinedparallelpytestfixturebroadcleanupdeletedotherworkergrant; fixedexactownedIDs inclshopfixturesandranserial."
  app_mocked_apis: "None. UItests usedexplicitisolatedauthfixtures; allRFgameplay/wallet/historyresponsesreal. AllQAdataremoved."
  remaining: "Canonicalupstream502/503/timeoutsstillpossible; boundederrorhandling/safeGETretry present,noautomaticPOSTcredentialretry. PhysicalAndroidcookiebridge/typesetting/performance/accessibilityandactualAPKsize measurement pending; <20MBnotguaranteed."

## Iterations45–47 — API speed and private Redis priority
api_speed_redis_current:
  implemented: true
  working: true
  baseline: "test_reports/api_speed_before.json"
  measured_after: "test_reports/api_speed_after.json"
  reports: "test_reports/iteration_46.json, iteration_47_api_speed_self_verify.json"
  scope: "Private server-side UNIXsocketRedis32MB; publicRFmetadataonly; no privateacademic/auth/coin/resultcaching. Sourceauthority intact. No newnative/frontenddependency."
  measured: "Warm30cardselectionp5017.586to1.718ms~10.2x. ExternalRFcatalog82.562to68.878ms; cards73.652to62.174ms~16%median. Identicalresponsehashes. Cataloguep95worsened280.234to324.782(networkcoldvariance). LocalHTTPX~42ms retained, notcherry-pickedaway."
  frontend: "Singleflightreads, boundedRAM, onebackgroundprefetchlane, correctsharedcataloguekey, Home5to2speculativecalls. Publicfreshcataloguefocusreuse/privatewalletrefetch. Main390pxverified1catalogue+1profileinitialGET; samecatalogue1throughshop/history; liveprofile2GETs. ActualQA250to252Coinresult/shoprefreshverified."
  validation: "Final25backendpassed1skip1canonicaldeselected; frontendcacheunits/TSC/lintpassed. Redisstopfailopen/privatepermissions/noauthdata/protectedartworkschecked. CORSnowexactconfiguredorigins, trusted200/foreign400."
  preservation: "ExactQAfixturesremoved.344profiles/10257Coins/399awardrecords; fullprotectedfingerprintsunchanged.2non-QA-taggedJEEduels(cancelled/ready)foundinfinalinspectionanddeliberatelyretained; donotresetnewplayhistory."
  caveats: "PhysicalAndroidandAPKsizemeasurementpending; canonicalupstream502/503notfixedbyRedis; no worldfastest/under20MBguarantee. Fixtureauthonlyinharness, no productionmockedAPIs."

## Iteration48 — native image/render pipeline deep optimization (verification pending)
user_confirmation: "Haan, investigate → fix → test. Mera xareer k baat hai deep me jao world best banao."
frontend_loading_current:
  implemented: true
  working: NA
  needs_retesting: true
  stuck_count: 2
  priority: high
  status: "User still finds physicalAndroid questions/solutions/cards sluggish after Redis. Native canonical transport does NOT use proxyRedis. Address actual image, encrypted disk and React rendering pipeline; do not claim phone performance from web."
  changes:
    - "Path-specific queue subscriptions + memo AssetImage; no global download-progress subscription on Player/Result. Queue reprioritizes subject jumps, current crops reserved, neighbour soft-LRU retention, independent Result/Solutions focus scheduling."
    - "Encrypted native/web reads overtake queued background writes via barrier-aware scheduler; SHA IDs coalesced; scope generations preserved. Native FileReader/Blob roundtrip replaced with bounded48KiB yielding base64; PNG/JPEG/WebP/GIF dimensions parsed before paint, bytes unmodified."
    - "Native-only decoded-memory warmup for next2/previous images (max6 crops,4MiB estimated decodeeach); memory-only expoImage with opaque per-value cachekeys. NO Image.loadAsync/writeToCacheAsync because plaintextdisk controls unsuitable."
    - "Stable offlineMath WebView shell + revision-checked RAM DOM updates; bundledCSS/fonts no longer resent/reparsed perquestion. memoRapidText, remove card-key WebView remount, RF100ms expiry checks retained but second-only UI updates; SVG native animation."
    - "Account->Loadingperformance: boundeddeviceRAM stagep50/p95 counts, reset/shareaggregateonly. No private text,IDs,URLs,PINs or automaticupload."
  main_checks: "TypeScript + strictESLint all touchedfiles PASS. Main390 entry screenshot PASS. No backendcode/auth/APIcontract/db/content/attemptwrites; no new dependencies."
test_plan_iter48:
  current_focus:
    - "Queue path notifications/75-image renderfanout vs baseline63241ad, reservedslot/dedup/reprioritization/softpins/budgets/abort/logouts"
    - "priorityOperations read-aheadwrite and open/clear barriers inclerror; nativeStore stubs/read+write encryption paths and realwebIndexedDB accountisolation"
    - "Exact nativebase64binary roundtrip/chunkboundaries/abort/yield; headerdimensions variants/corrupt; no staleURIafterinvalidate; original unchanged/grant/version/429guard"
    - "OfflineMath actualHTMLshell in browser harness (nativebridge simulatedonly), ready/update/fastswitch/staleACK/ResizeObserver/fonts/no source reload/HTMLescape+CSP/externalURLblock. RapidText no nonmathTeXwork; timer still20s/no answer/scoring changes"
    - "Read-only real canonical PINlogin/catalog/available sourceimage hash parity; NO academicstart/visit/answer/submit/solution-open/PINchange. IsolatedUIfixtures for player/releasedsolutions if necessary; labelseparately. ActualRF tests can use exact-cleaned localTESTfixtures periter43, no userwallet mutations."
    - "Preview390/320 homeoriginalartworks/playernavigation/solutiongrid+zoom/imageanswerblock/retry/failure/RF30cards+timeout+advancing/diagnosticsreset & boundedredactedshare. Capture measures, neverpresent browser asAndroidperformance."
  limitations: "PhysicalAndroid unavailable; APK/AAB not built here (<20MB unverified). Upstream503/520 remains externalP1; existing readonlyretry timings are22sasset/28sJSON vs25sasset/32sJSONclient, NOT RF15s (separateAPI). Do not increase alltimeouts based on incorrectRCA."
agent_communication_iter48:
  - agent: main
    message: "Please create iteration48 tests/report; existingtests import stub dependencies may need added newlyintroduced imports/stubmethods (testharness only, do not weakenassertions). Verify realproduction no mockedAPIs; syntheticfixtures tests only. Read memorytestcredentials latest first (approvedlivePIN works sinceiter42); reuse1login,stop401/429. Preserve academicrecords and NEET/walletdata. Native lack of hardware honest; validate platform-code using spies+realbrowser document. Compare beforecode from gitshow63241ad, no reset."

iteration48_followup_for_iter49:
  superseded_by: "iteration49_main_final below; earlier remaining_tests are historical requests, not a claim of completed coverage."
  findings: "Report48 isolated5/5 + iter40 12/12 PASS; backend4PASS1SKIP; home390/320/performance UIpass. Directcanonicalauth timedout, parity3SKIP. Claimed infinitespinner not established: troubleshoot verified GETauth/session may rotatecookies per reference/handoff/01_BACKEND_AND_AUTH.md, correctnoretry; frontendalreadyfinallyreadytrue anderror UI. Rootintermittent24sreadtimeout isupstream, notRedis. Keepbackendpolicyunchanged."
  critical_fix: "NEW requestDeadline.ts wraps full JSON fetch+body with32sbudget evenwhen callerAbortSignal supplied. Races explicitabort tosettle evenifbodyreaderignores signal. Preserved401refresh/credentialnoautoretry/sessionexception andallURLs. Fixes unbounded stalledJSONbody onauth/attempt/result. No credentials modified. Integrationplaybookconsultedbeforepatch. TSC/strictESLintPASS; mainentry390checkPASS."
  remaining_tests: "Need actualbrowserexerciseof OfflineMathHTML andRF/player/solution fixtures beyondpreviousstatics; prioritytestmustactuallyplace a highpriorityreadAFTERabarrier; nativeStore/APIspies+realwebIndexedDBtest, imagebase64deepEqual allbytes(not17samples). Criticalrequestdeadlinehelper+apiRaw same bodydeadline withcallerSignal/slowbody/32stimeout/error/cleanup/no PINPOSTretry tests. Forced503bootstrap showsentryerrornotendlessspinner. ActualPINsuccessseen inreport48; additionalparitymustdiscover OWN completedIDs viamy/tests, removehistorical9000000001 andsourceprojectIDs from test48 (differentaccount). No academicwrites. Synthetic testfixturesexplicitonly; no mockedproductionAPI."

## Iteration49 main final verification — local optimization verified; native/upstream gates remain
> **USER DEFERRED WEBSITE DELETION:** latest response “In future” / “No”. Do NOT ask for matchingPINsource again or modifycanonicalauth/data untiluserresumes. Verifiedmobile/native/privacyfixesretained;directdeletionunavailable andfullPlayStorereadinessnotclaimed. No productionbackend/account/Gitsettingschangesmade.

> **NEW SOURCE SAFETY GATE:** ownerprovidedpublicJeemains.aiGitrepo; main2e0c883hasOLDphone-onlyauth, App e25ec0fismobileproxy. FreshliveOpenAPIrequiresPINandadditionalPINroutesabsentfromrepo. Read-onlyref/tree/schema checksconfirmedmismatch; NOwebsitebackendcode/datachangesmade. NeedlatestactualwebsitePINsourcebranch/commit/export beforedestructivedeletionimplementation. See`reference/CANONICAL_SOURCE_COMPATIBILITY.md`andlatestPRD. DoNOToverwriteworkingliveauthwitholdmainoraskforGitHubcredentialsunnecessarily.

> **LATEST iteration50 implementation:** see `test_reports/iteration_50_main_followup.json` andlastPRDsection. NativeSDKDoctor20/20PASS/branding+permissions+policy/contact/publicaccessfixed.24frontendregressions+RF9PASS/1SKIP;publiclegal/brand15PASS/1edge-injectionassertionFAIL(originclean,CSPblocks,notcategoricalPlayJSban). MainrealPINPOST200/Home→Account→PrivacyPASS; previousagent'sforce-clickduringpendingbootstrapdidNOTsendPIN. Privategate+keyboardreadyguardpass; all344profiles/10257coins+archivefingerprintsunchanged. **BLOCKED:** userchosePINdirectaccountdeletion;LIVEcanonical121pathschema hasnodeleteaccountAPI. Needwebsitebackendproject/sourceURL;unavailableinfoisNOTimplementeddeletion,andnorealaccount/datawasdeleted. Signedartifact/physical<20MB/Consolegatesstillunverified. AsknecessaryownerURLafterrestartingExpo;doNOTclaimPlayStore-ready.

> Later read-only Play Store review supersedes any inference of store readiness: see `test_reports/play_store_readiness_review.md` / `.json`. Installed ExpoDoctor17/20PASS with3 native-readiness failures (missingexpo-asset directpeer, duplicateexpo-file-system58.0.11/58.0.10,4SDKpatch mismatches). Publicprivacy page existsbutin-applink/contact/deletionmechanism incomplete; signuphasnoaccountdeletionUI. Launcherlabel=`frontend`/buildericons+splash; unnecessarycandidate recording/backgroundmedia/overlay/legacypermissions needreview. No source/config/dependency/account/build/publishchanges made. Prior deployment healthPASS was infrastructure-only, NOTstorepolicy/nativeartifact approval. NativeartifactAPI36/64bit/16KB/size/physicalQA/Console evidence andknownexternal503/520 remainpending. Exactrequestednamedskill wasnotavailabletocall; equivalentmanualreviewperformed,notnamedskill execution.

iteration49_main_final:
  frontend_automated: "24PASS (iter40:12,iter48:5,iter49:7). StrictTSC/ESLint touchedfiles PASS. Bodydeadline actualapiRaw/callerabort/PINnoretry tests executed; priorityreadAFTERbarrier andallbytebase64SHA added. OfflineMath browserdocumentbridge verificationpass, notnativeWebViewhardware."
  backend_gameplay: "Existingiter43 realRF API regression re-run:9PASS,1SKIP(no sparsechapter). XMLtest_reports/pytest/iter49_rf_gameplay_recheck.xml. ExactTEST-run records cleaned byfixture."
  main_ui: "IsolatedRFauthbrowser+REALRFAPI/disposableQA:390feedback,Nextcard,320 untouchedcard20.4sexpiry/ring0,auto-next,answer-next-exit/finishsummaryPASS. Actualsource testIDs used afterscriptselector corrections; noapplicationgameplayfailurefound. Forced503session settles/Retryworks. MyTests newunavailablemessage verified390 forced503; falseemptyhistorycard absent."
  live_readonly: "ApprovedrealPINloginPASS onwebproxy; initialownedcompletedlist14total/12loadedPASS. Latercanonical503AI/assets and520MyTests blocked releasedimage+zoomretest. Paritytests3SKIPdirectcanonicalReadTimeout; noPINguesses/resets/retriesandnoacademicPOSTsent. Inresultbrowseronly solution-open analyticsPOSTintercepted503 toprotectrecords; sourceimage GETsreal. Do notclaimliveimageE2Evalidatedthispass."
  small_bug_fix: "MyTests no longerlabels serverfailure as emptyhistory; savedworkpreservedguidance. Comparisonselectionreset movedintotab/examevents(removesextraeffectrender). Verifiedscreenshot/loading-failure-not-empty-390.jpg."
  preservation: "TemporaryUI3profiles/grants/matchesexact-UIDcleaned;grantfilesdeleted. iter43_baseline_guard_checkPASS:344originalprofiles,10257coins,originalwalletownership+archive fingerprints unchanged. PIN/sourcecontents/artworks/DBschema/env/nativeengineunchanged."
  limitations: "P0physicalAndroidimagecache/decode/WebView/timingQA stillrequired; no signedAPK/AAB (<20MBunverified). NativeStore API-sim/realIndexedDB deepertests notnewlyperformed beyondexistinghelpertests. Externalcanonical503/520 persists; DONOTautoretrycookie-rotatingauth/session/PIN. No worldbest/instant/FPS claim."
  reports: "test_reports/iteration_48.json,iteration_49.json,iteration_49_main_followup.json;reference/ITER49_NATIVE_LOADING.md;memory/PRD.md latestsection."
## Iteration62 — Rapid Fire Phase 3 (frontend wiring + Badla flow)
test_plan_iter62:
  current_focus:
    - "Lobby: subject chips (Physics/Chemistry/Maths/PCM, one row at 390 and 320), battleground ribbon opens ScopeSheet (max 5 picks, Quick Mix, chapter tabs, search, tray, card count, 5-pick warning)"
    - "Knockout Cup hub /rapid/cup: Open vs Friends, 4/8/16 sizes, battleground, prizes strip, watch-with-code, Your cups list; lobby seats/progress/countdown/watch code; bracket with auto-scroll, BYE/TBD, champion"
    - "Live spectating /rapid/watch/[did]: LiveStrip in lobby and cup hub, watch codes (max 100)"
    - "Badla lo: user choice = choose subject/chapter again FIRST, then same opponent gets the challenge. Entry points: MatchResult (lost 1v1 vs friend), player profile player-badla, h2h sheet h2h-badla-top / h2h-badla-<id>. Sheet testID rf-badla-sheet, done rf-scope-done (label SEND BADLA). Backend POST /api/rf/challenges {rematch_of, picks} uses the new picks; without picks keeps the old scope."
    - "Trophy tab Ranks: All India / Friends (weekly league, claim) / Gang War top 100 boards"
    - "Gang form: Gang vs Batch segment; Gang War sheet in gang screen"
agent_communication_iter62:
  - agent: main
    message: "Backend tests/test_rf_phase3.py 7/7 pass (run with -o addopts=). Login 7004186276 / PIN 5524 (web). Fixture: python /app/tests/rf_social_fixture.py seed|cleanup (adds 3 TEST friends + 4 h2h matches vs Aarav incl. 1 lost). Clean up after testing."

## Iteration65 — Badla pending strip, Crown celebration, Colosseum entry, daily Cup Night
agent_communication_iter65:
  - agent: main
    message: "Backend: GET /api/rf/badla; /api/rf/cups/night, POST /night/join, /night/leave; cup view first_title/real_players/night/night_no; background loop seats Cup Night. pytest tests/test_rf_phase4.py (2) + test_rf_phase3.py (7) pass with -o addopts=. Fixture rf_social_fixture.py seed adds 2 recent losses vs Diya (Badla x2)."

## Iteration66 — Crown celebration on EVERY cup win (user choice), focus-gated; Phase 4 polish
agent_communication_iter66:
  - agent: main
    message: "User chose: crown celebration on EVERY cup win (not only first). Backend cups.py: finish() stores title_no (champion's cups_won after this win) on the cup; view returns title_no (0 unless you are champion), first_title (title_no==1), my_crown {won,real}. Night: round-1 lead-in 30 s (NIGHT_LEAD) for night cups; night_guard → 409 on POST /cups and /cups/{cid}/join in the last 15 min before start for a player seated tonight; seat_night stores missed (busy uids); /cups/night count = seated after draw, new field missed. Frontend: [cid].tsx celebration only when screen focused (isFocused state from useFocusEffect), storage rf.crown.<cid> set only when user closes (Continue/See/back). CrownCelebration: props no/crown, kicker FIRST CROWN vs CROWN #N, title 'Champion again!' for N>1, chip GOLD/SILVER CROWN · N CUPS, ScrollView for short screens. CupNight banner: shorter kicker ('DAILY · 8:00 PM'), 2-line countdown line, smaller trophy <360px. Cup hub: night banner moved to top. Night screen: night-missed panel. Entry flash toned down (peak 0.28). client.ts rapidAccess: session generation race now retries instead of 'sign in again'. pytest test_rf_phase4/phase3/iter65 pass."
agent_communication_iter66b:
  - agent: main
    message: "Fixes after iteration66: client.ts rapidAccess — empty userId throws early (no exchange), waiters use grantFlight.catch(), generation check moved above the verify throw; cup [cid].tsx load() returns early when uid empty. RaisedButton big labels: 19px/letterSpacing 1 on <360px + adjustsFontSizeToFit. duel.tsx: countdown number (testID duel-countdown-left) ticks during the wait before the entry show (Cup Night 30 s lead-in). CrownCelebration art/rays gold follows the player's overall crown (my_crown.real>0), matching the chip."

## Iteration68 — Champions Wall, Cheer Squad, Crown Share, Cup Night reminder, Build cleanup
agent_communication_iter68:
  - agent: main
    message: "User asks: (1) Champions Wall in lobby: tonight's/last night's Cup Night champions (real players only) shown until next night's doors open (7 pm); Cheer button opens the champion's profile with cheer=1 where a Cheer Squad (dancing cheerleaders + swinging CONGRATULATIONS board + stage lights + confetti) plays over the Trophy Cabinet; no inbox message (user said only the animation). Trophy Cabinet (renamed from 'Cup Champion' section) has a 'Cheer squad' button for champions to replay. (2) Crown Share: 'Share on WhatsApp' button on the crown celebration opens a crown card preview (4:5) + SEND ON WHATSAPP (native: captures card with react-native-view-shot and opens share sheet via expo-sharing, Android copies caption to clipboard; iOS Share.share url+message; web sends text via wa.me) + 'Message only' + Back. (3) 7:55 pm reminder: night_tick inserts one rf_notices kind cup_night per seat holder (expires start+120, NIGHT_REMIND=300s), inbox returns night {day,start_ts,time_label,starts_in}, expired notices filtered, leaving Cup Night clears it; frontend NightReminder banner (testID rf-night-reminder) shown where ChallengeBanner shows when no challenge; Later/OPEN dismiss; night screen auto-dismisses. Gang tab list + badge exclude cup_night. (4) Cleanup: removed backend/tools image scripts (kept owner_download.py), unused frontend assets (old fonts, react logos, unused images, roboto-mono). Redis: redis-server was missing in this pod (jeelive-redis FATAL) — installed and running; metadata_cache keeps L1 up to 30 s when Redis is down. Backend endpoint GET /api/rf/cups/champions. Tests: tests/test_iter67_champions_reminder.py pass."

## Iteration70 — Stadium Cheer banner, diamond unlock confirm, Store entry, smaller Android bundle
agent_communication_iter70:
  - agent: main
    message: "User (Hinglish): Cheer squad good but the board 'chamak nahi rha, baccho jaisa lag rha, sexy rugby match jaisa nahi' -> board redesigned as a pro-stadium banner (new src/rapid/CheerBanner.tsx; colours theme.ts `cheer` per squad level 1-4): satin cloth with cut corners + gloss, metallic trim, 2 leaning corner stripes, CONGRATULATIONS! as forward-leaning metallic-foil SVG text (outline + drop shadow), white glint sweep, twinkling glitter (10/13/15/18 by level), swaying gold fringe, pulsing halo on each count, spear-tip gold poles; the carnival bulbs and rainbow bouncing letters are gone. testIDs kept: cheer-banner, cheer-banner-title (a11y label CONGRATULATIONS!), cheer-banner-name. User also chose 'Diamonds se cheerleader kharidna' with rule 'wins open levels automatically + diamonds unlock early' (backend squads.py already had buy/equip): /rapid/squads Buy now opens confirm sheet (squad-buy-sheet, squad-buy-title, squad-buy-cost, squad-buy-confirm, squad-buy-cancel); after buying, coin sfx, arena diamonds reload and the new squad dances at once (CheerSquad preview). Store tab has a CHEER SQUADS card (shop-squads) under the diamond wallet that opens /rapid/squads. APK size: removed unused optional dependency expo-symbols (only expo-router's Android native-tabs converter required it; app uses NativeTabs on iOS 26 only with sf icons) -> Android export drops the 962 KB Material Symbols font. Android export (no bytecode) JS 4.63 MB + assets 3.28 MB = 7.91 MB (before 8.94 MB). Not an APK measurement."

## Iteration71 — Phone login through our server (bug fix)
agent_communication_iter71:
  - agent: main
    message: "User bug (Hinglish): 'Login not working' on installed Android app (preview + live). Phone screenshot: entry screen shows 'Couldn't check your session. Connect to the internet and retry, or sign in below.' and after Sign in 'Connection interrupted. Your last saved work is safe. Please try again.' = native fetch to https://jeelive.ai/api threw (phone browser opens jeelive.ai fine). Deployer RCA: production backend healthy, no failing requests (native login never touched our backend). Fix (user-approved): frontend/src/api/client.ts now sends ALL platforms through our pass-through proxy `${EXPO_PUBLIC_BACKEND_URL}/api/jl` with the X-JL-Sid handle (web unchanged: AsyncStorage key jl_sid; native: SecureStore key jl_sid). Removed native direct-cookie capture (captureNativeAccess/nativeAccessCookie); /api/rf/access now always uses X-JL-Sid with body {}. resetSessionHandle clears the handle on every platform (sign-out = fresh jar)."

## Iteration72 — Forgot PIN (phone + new PIN + confirm, no OTP — owner's explicit choice after warning)
agent_communication_iter72:
  - agent: main
    message: "User insisted: 'Forgot PIN → create new PIN → confirm → done. Anybody can change any phone number pin. I want my app to be like that.' (warned twice about account takeover). Canonical jeelive.ai has no public reset; backend/pin_reset.py POST /api/account/forgot-pin {phone,new_pin,confirm_pin}: signs in as site owner (env JEELIVE_OWNER_EMAIL / JEELIVE_OWNER_PASSWORD via POST {JEELIVE_API}/auth/login, owner cookies in-process only), GET admin/students?q=<last10digits> → exact match by last 10 digits → POST auth/owner/student-pin-reset with expected_pin_version. Throttle 5/hour per number, 30/hour per IP (Mongo pin_resets log, sha256 keys). Errors: 422 mismatch/format, 404 unknown number, 429 throttle, 503 owner not configured/upstream. Frontend app/forgot-pin.tsx: phone (forgot-pin-phone-input), new PIN (forgot-pin-new-input), confirm (forgot-pin-confirm-input), submit (forgot-pin-submit) → reset → signIn → Home; if sign-in after reset fails shows forgot-pin-success. Security audit (iteration72) findings SEC-001 session handle no TTL/rotation and SEC-002 PIN brute force: user chose 'Abhi nahi' (not now)."

## Iteration74 — 100k scale (many servers through MongoDB) + cheerleader diamond shortfall
agent_communication_iter74:
  - agent: main
    message: "User: scale for 100k (servers joined through the database, no Redis) AND diamond cheerleader buy with 'kitne aur chahiye' shortfall. Backend duels.py: rf_duels.ws_nodes (servers holding a match's sockets, $addToSet on first socket per server, $pull on last close); live channel rf_events (capped 128MB) events {node, ts, to:[nodes], by:{node:[dids]}} tailed with filter to=node and projection by.<node>; quick_answer = one find_one_and_update pipeline (server-measured ms from last_ts/start_at) with full-path fallback; rf_watch (TTL) spectator count/limit across servers; inbox returns poll_s (8, or 20 when busy); MONGO_MAX_POOL default 40; server.py Collections wrapper caches collection objects. squads.py 409 lists exact shortfall ('You need 3 more Red, 1 more Blue'). Frontend: StoreParts ShortNote (testIDs squad-<id>-short on locked squad cards when diamonds are short, squad-buy-short in the buy sheet); social.ts InboxPoller every 25s inside rapid/duel|session|watch, follows poll_s. Tests: tests/test_iter74_multiserver.py (RF_NODE_B=http://127.0.0.1:8002 needs a second `uvicorn server:app --port 8002 --workers 3`), iter73, phase3, iter69 pass. Load tool tools/loadtest_rf.py --pairs added."

## Iteration76 — One brand JEELIVE.AI, website-driven exams/sections, browser arena at /api/arena
test_plan_iter76:
  current_focus:
    - "Brand: no visible JEECIRCLE text anywhere (entry, Home 'Explore JEELIVE', footer, Account, Mission, privacy, /api/legal/privacy, /api/rf/c|g link pages, WhatsApp texts). Logo testIDs home-brand / entry-brand draw the original Jeelive.ai wordmark."
    - "Home Practice grid (home-exam-grid) is built from GET /api/jl/catalog/exams: tiles home-tile-<slug> in website order + home-tile-live last. Odd tile count: the last tile is full width."
    - "Exam page (exam-hub-<slug>): rows exam-destination-<section slug> must equal the non-hidden sections in the LIVE answer of GET /api/jl/catalog/exams/<slug> at test time, in that order (compare against the response, not a fixed list); JEE Main keeps exam-destination-pyq first; history row last. COMEDK sends no sections -> default mocks + chapters rows. Unknown slug (/exam/no-such-exam) -> 'This exam is not available right now.' and no crash."
    - "Catalogue: /catalogue?slug=bitsat&kind=mocks and kind=chapters lists unchanged; /catalogue?slug=jee-main&kind=pyq still redirects to /pyq. The old redirect of jee-main&kind=mocks to /pyq is removed: it lists JEE Main mocks only while the website lists that section. The website's JEE Main section list changed during development (mocks listed at 22:13 UTC, gone at 22:28 UTC, 404 'This section is not available.'); when it is not listed the exam page must have no mocks row and the direct URL must show that message with Retry, not a crash or a blank screen."
    - "My Tests exam chips (my-tests-exam-all, my-tests-exam-JEE Main, ...) come from the website list; filtering still works."
    - "Browser arena: <backend>/api/arena -> entry screen (eyebrow 'RAPID FIRE · ONE ACCOUNT') -> sign in -> lobby (arena-screen) at /api/arena/rapid. 480 px column at 1280 px width; full width at 390/320. App tab bar (tab-tests) must be absent. Typing /api/arena/pyq, /api/arena/live, /api/arena/exam/jee-main, /api/arena/attempt/x redirects to the lobby. arena-tab-home leaves to https://jeelive.ai/. Own profile (arena-top-profile) has player-account -> Account -> sign out -> /api/arena/entry. Reload keeps the session."
    - "Arena play: Solo Sprint and Practice Rival run to the result screen inside /api/arena (WebSocket to the same origin); Store, Trophy, Gang, Cup hub, Squads, Vault open without leaving the column."
agent_communication_iter76:
  - agent: main
    message: "Frontend-only data change for exams (src/api/examCatalog.ts, ExamHub.tsx, catalogue.tsx, (tabs)/index.tsx, (tabs)/tests.tsx); backend adds only arena_web.py (static files). Arena build: /app/scripts/build_arena_web.sh -> backend/arena_web. Login 7004186276 / 5524 works in both the app preview and /api/arena. Do NOT start, answer or submit any test paper (academic records are real). Rapid Fire practice matches are fine. Not testable here: a brand-new exam or an owner-created section (needs the website owner panel) — say so, do not fake it."


## Iteration77 — Deployment health check + lint cleanup (no behaviour change)
agent_communication_iter77:
  - agent: main
    message: "Deployment health check: status warn, no blockers. Lint cleanup only: removed eslint-disable comments for rules that do not exist (app/rapid/duel.tsx, app/rapid/session.tsx) and merged a duplicate import from @/src/navigation in app/(tabs)/index.tsx. No logic changed. Verify Home, Solo Sprint (session.tsx) and Practice Rival (duel.tsx) still work in the app preview."
