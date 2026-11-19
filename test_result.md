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

## Iteration78 — WhatsApp match links (anyone with the link joins; joiner becomes host's friend)
agent_communication_iter78:
  - agent: main
    message: "User choices: up to 5 players (host + 4), no-app visitors get BOTH 'Play in your browser' and 'Get the app', room stays 3 minutes, friendship made the moment a player takes a seat. Backend rooms.py: POST /api/rf/challenges {link:true, picks|subject, pids?(optional friends), gang_id?} -> room with link:true, single:false, invites [] allowed. GET /challenges/{cid} is open to anyone (not blocked by/with host) for link rooms: my_status 'link' until seated, plus fields link, friend (guest is host's friend). POST /challenges/{cid}/accept for a link visitor pushes a new invite {status:joined, via:link} (max 4 guests) and calls social.make_friends(guest, host) (both directions + 'friend_added' notice to host). Link rooms never auto-start on 1 join: they start on host START, when 4 guests fill it, or at the 3-minute mark with >=1 guest. Invite-only rooms unchanged (strangers 404). Public page GET /api/rf/c/{cid}: link rooms show '<host> wants you in a Rapid Fire match', 'N of 4 seats open', buttons rf-link-open (frontend://rapid/room/{cid}), rf-link-browser (/api/arena/rapid/room/{cid}), rf-link-download; closed/started -> 'This match has started' / 'This match link has closed'. og:title/og:description added. Frontend: app/rapid/challenge.tsx panel challenge-link + button challenge-share-link (creates link room, opens room, opens WhatsApp share). app/rapid/room/[cid].tsx: title 'Link Match'; host panel room-link with room-copy-link + room-share-link; visitor panel room-link-invite + buttons room-not-now / room-accept ('JOIN MATCH'); joined guest sees room-friend-note; outsiders on a started room see room-closed 'Match already started'. Signed-out user opening /rapid/room/<cid> -> /entry?next=... with entry-match-note, after sign-in returns to the room (app/_layout.tsx AuthGate + app/entry.tsx). Browser arena rebuilt (scripts/build_arena_web.sh). Backend test tests/test_iter77_match_link.py passes; tests/test_rf_social.py still passes."

## Iteration79 — JEELIVE.AI Rank predictor Phase 1 (RANK tab, one text-only screen)
agent_communication_iter79:
  - agent: main
    message: "RANK tab (app/(tabs)/rank.tsx) replaced the coming-soon page with the predictor; components in src/rank/ (api.ts, tones.ts, controls.tsx, InputCard, ResultCard, SeatList, CollegeSheet, PercentileChart). Backend rank_predictor.py mounted at /api/rank (public, no auth): GET /meta (states, 20 branch groups, 50 chart lines 99.9->80 with rank + Normal-paper marks, notes), POST /predict {marks?|percentile?, level tough|normal|easy, category GEN|EWS|OBC-NCL|SC|ST, female, pwd, state, branches[], segment all|NIT|IIIT|GFTI|DELHI, page 1|2, page_size 25|20} -> result (percentile range, CRL range, cat/pwd rank, Tough/Easy spread line, paper/check notes), counts per segment (max 50), items (25 per page, tag safe/likely/borderline), near (5 'bas thoda sa door' with +N marks). POST /college {form + inst, prog?, quota?, gender N|F?, seat open|cat?, all?} -> top 10 (or all) branches x rounds (JoSAA R1-R5 + CSAB 1-2, or JAC R1-R4 + Upgrade/Spot empty) with open/close and 'in' highlight, path options, official links. Data file backend/rank_data/jee_main_2026.json.gz built by backend/tools/rank_data/build_rank_data.py from official JoSAA 2026 R1-5, CSAB Special 2026 R1-2, JAC Delhi 2026 R1-4 PDFs and NTA 2026 counts; marks->percentile from public 2026 shift tables (estimate). Known gaps shown on screen: JAC Upgrade/Spot not published, IIIT-Delhi Round 1 PDF not parsed."

## Iteration80 — Rank predictor: Phase 1 fixes + Phase 2 (BITSAT, shift, 2025 trend, shortlist, WhatsApp, dark-metal Rank Card)
agent_communication_iter80:
  - agent: main
    message: "Phase 1 fixes from iteration79: POST /api/rank/college now returns blocked (reason) + line 'Ye raasta aapke liye nahi: ...' and every cell in=false when the chosen quota/gender path is not open to the student (Home state of another state, Other state of own state, Female-only for non-female, Delhi region for non-Delhi, Outside Delhi for Delhi, GO/JK/LA); CRL range clamped to total candidates (-75 marks -> [1537468, 1538468]); 'all' and segment lists of 50 now mix up to 20 Borderline + 15 Likely + 15 Safe (filled by demand when a tag is short), ordered by demand; Toggle chips and the two Segmented bars are 44px; collapsed summary wraps to 2 lines; college sheet shows the tapped branch detail above the table. Phase 2: GET /meta adds shifts[19 {name, level}], y25_label '2025 R6', candidates; POST /predict accepts shift (e.g. '22 Jan S2', 422 for unknown) and uses that shift's own marks table (result.shift note, summary shows the shift); items carry y25 (JoSAA 2025 final round closing for the same seat path, from rank_data/jee_main_2025_close.json.gz) and y26 (2026 final JoSAA closing); seat rows show '2025: X → 2026: Y ↑ aasaan hua / ↓ tough hua'; college sheet has an extra last column y25_label. New POST /api/rank/bitsat {score -130..390, campus all|Pilani|Goa|Hyderabad, degree all|BE|MSc|BPharm} (rank_bitsat.py, data rank_data/bitsat_cutoffs.json = official BITS 2022-2026 final cutoffs, 50 programs): result {score, max 390, cleared/total (filtered), cleared_all/total_all (all programs), best, target {gap}}, items (tag safe >= cutoff+10, likely >= cutoff, borderline cutoff-5..cutoff-1), near (gap <= 20), rest. Frontend: BITSAT segment -> src/rank/Bitsat.tsx (bitsat-score-input, bitsat-show, bitsat-input-collapsed, bitsat-card*, bitsat-campus-*, bitsat-degree-*, bitsat-item-N(-star|-trend|-history), bitsat-near, bitsat-rest-show). Rank Card (src/rank/MetalCard.tsx + ResultCard.tsx): dark brushed-metal card, silver serif CRL, blue rule with percentile, № serial; under it notes + rank-share (WhatsApp text) + rank-shortlist-open. Shift chips rank-shift-none / rank-shift-22-jan-s2 etc. Shortlist: star on every seat row (rank-seat-N-star, rank-near-N-star, rank-chart-seat-N-star, bitsat-item-N-star), stored on the phone (rank.shortlist.v1), sheet rank-shortlist with rank-shortlist-item-N, rank-shortlist-remove-N, rank-shortlist-share."

## Iteration81 — Rank tab fully dark (user: "whole screen dark, far more beautiful"), shift picker removed
agent_communication_iter81:
  - agent: main
    message: "User rejected the shift picker (next-year students will not have 2026 shift dates) -> removed from UI AND backend (no shift field, no meta.shifts, rank_data/jee_main_2026_shifts.json + tools/rank_data/build_shifts.py deleted); Tough/Normal/Easy stays. Whole Rank tab is now dark: theme.ts rankColors palette (dark overrides of the light palette) provided via PaletteContext in app/(tabs)/rank.tsx and imported as `colors` in every src/rank file; background = two LinearGradients (charcoal -> navy + blue glow top-right); serif title; dark panels (Strip = blue hairline + tracked caps title, no colored side bar); new dark Switch replaces Segmented for rank-exam-* / rank-mode-* (same testIDs, 44px); chips dark with silver selected state; Show buttons electric blue; Rank Card gets an outer blue glow. DSheet (src/components/design.tsx) now reads backdrop/sheet/handle/close colours from useTheme(), so Rank sheets are dark and every other screen is unchanged (default palette = light). Status bar light while Rank tab is focused. Iter80 minor fixes: JEE trend line says 'JoSAA final · 2025: X → 2026: Y' (compares JoSAA finals, same path) with <3% = 'lagbhag same'; arrows now mean the same on JEE and BITSAT (▲ tough hua red, ▼ aasaan hua green; BITSAT |d|<=2 = '2025 jitna hi'); BITSAT shortlist rows render as plain View at full contrast. Backend tests: tests/test_rank_predictor.py + tests/test_rank_phase2.py (shift tests replaced) 45 pass with EXPO_BACKEND_URL set."

## Iteration82 — Rank: COMEDK (GM only, marks or rank), round-wise ladder on every college sheet, sparkle silver + light blood red, JEE data recheck
agent_communication_iter82:
  - agent: main
    message: "Backend: new rank_comedk.py (data rank_data/comedk_2026.json from official COMEDK 2026 Round 1-4 cut-off PDFs + 2025 final + 2026 seat/fee matrix, built by tools/rank_data/build_comedk.py). ONLY GM (General Merit, All India) seats; KKR never returned. POST /api/rank/comedk {marks 0..180 | rank 1..200000 (rank wins if both), branches[] (groups from GET /api/rank/meta -> comedk.groups), area all|blr|other, page 1|2} -> result {rank [lo,hi], mid, from_marks, candidates 129000, in_reach, total, summary, spread (marks: range across 3 public marks-vs-rank analyses), check}, counts {all,blr,other} (max 50), items 25/page {id, code, college, city, blr, course, cc, group, close (= max closing across rounds), round, rounds[R1..R4], y25, seats (GM), fee, tag}, near (5 with gap), rounds, notes. POST /api/rank/comedk/college {marks|rank, code, course?, all?} -> college, your_rank, rounds R1-R4, rows (top 10 or all) with cells [{close, in, mine}] per round, y25, fee, seats, tag, first_in, line; 404 unknown code. JEE /api/rank/college cells now also carry `mine` (rank compared; null when the path is blocked). Frontend: exam switch has 3 tabs (rank-exam-jee / rank-exam-bitsat / rank-exam-comedk). COMEDK panel src/rank/Comedk.tsx: comedk-marks-input, comedk-rank-input, comedk-branch (picker comedk-branch-picker), comedk-input-error, comedk-show, comedk-input-collapsed, comedk-card (comedk-card-rank, comedk-card-reach, comedk-card-summary, comedk-card-serial), comedk-share, comedk-shortlist-open, comedk-list with comedk-area-all|blr|other, comedk-list-branch, rows comedk-seat-N (+ -star, -trend, -tag), comedk-page-1/2, comedk-near / comedk-near-N. Tapping a row opens sheet comedk-college with comedk-college-ladder (rows comedk-college-ladder-0..3 + -prev = 2025 final; -N-close, -N-in, -N-mine) and table comedk-college-table (comedk-college-branch-<cc> taps switch the ladder), comedk-college-all, comedk-college-official. JEE college sheet: rank-college-branch-detail now holds the round ladder rank-college-ladder (R1-R5 + CSAB 1-2, or JAC R1-R4 + Upgrade/Spot, then 2025 R6), table testIDs unchanged (rank-college-table, rank-college-branch-<prog>, rank-college-y25-<prog>). Look: blue accents replaced by sparkle silver + light blood red on the Rank tab (card glow, top shimmer edge, badge, hairline rule, № serial, twinkling silver glints beside the big number, switch selected = silver outline, Show buttons blood red). Shortlist accepts COMEDK items (exam tag COMEDK). Backend tests: tests/test_rank_comedk.py + test_rank_predictor.py + test_rank_phase2.py = 52 pass. JEE data recheck: tools/rank_data/verify_jee_data.py against a fresh JoSAA/CSAB/JAC download: 58,382 in-scope official rows match exactly, rebuild identical (0 differing seats)."
agent_communication_iter82_fix:
  - agent: main
    message: "Fixed iteration_82 report: (HIGH) /api/rank/college always includes the tapped prog even outside the top 10 (NSUT/DTU); JEE cells now carry hi (worst estimate) and unpublished (JAC Upgrade/Spot) -> ladder says 'JAC ne ye rank publish nahi ki'; COMEDK cells carry hi. Ladder: 3 states (andar = close >= worst estimate, 'borderline · aapki range ke andar' = only part of the range, 'aapki rank bahar'), silver band = student's range, scale includes the student's own rank (marker no longer stuck at 100%), state text on its own line (fits 320px), 2025 row empty text '2025 mein is seat ka data nahi'. Table: green = whole range in, amber = part. Sheet line (rank-college-line / comedk-college-line) follows the course currently picked. Card: big number font sized from window width (no ellipsis at 320px), score caps 3 lines, foot stacks under 360px. COMEDK in_reach counts seats the middle estimate reaches (label adds '(MID ESTIMATE)' for marks). Segment/area chips show real reachable totals (predict 'reach' / comedk 'reach'); list header 'Top 50'. Table name column 140px, 4 lines."

## Iteration84 — Rank tab: separate RANK PREDICTOR tile above/before COLLEGE PREDICTOR
agent_communication_iter84:
  - agent: main
    message: "User: 'Add a rank predictor feature above the college predictor. Same select exam, give marks, categories, paper type - predict rank and percentile.' Then: like the Home exam tiles, one tile Rank predictor, the other College predictor; BITSAT left out (no official rank/percentile). Built: Rank tab now opens with two Home-style tiles (rank-tool-rank default selected, rank-tool-college). Rank tool (src/rank/RankPredictor.tsx): exam switch rp-exam-jee / rp-exam-comedk; rp-marks-input (JEE -75..300, COMEDK 0..180); JEE only: paper rp-level-tough|normal|easy, category rp-cat-GEN|EWS|OBC-NCL|SC|ST, rp-pwd; rp-input-error; rp-show ('Predict rank'); collapses to rp-input-collapsed (Edit). JEE result: rp-card (rp-card-percentile big, rp-card-crl hairline, rp-card-cat / rp-card-pwd, rp-card-summary, rp-card-serial), strip rp-levels with rows rp-levels-tough|normal|easy (tap = card switches to that paper type), rp-share (WhatsApp), no shortlist button. COMEDK result: rp-card (rp-card-rank, rp-card-percentile), strip rp-sources (rp-sources-0..2: each analysis' rank). rp-colleges ('Is score se colleges dekho') switches to College tool with the same score already shown (JEE: rank-input-collapsed + rank-result + list; COMEDK: comedk-input-collapsed + comedk-card). College tool = everything that existed before (rank-exam-jee/bitsat/comedk ...), unchanged. Backend: POST /api/rank/estimate {exam jee|comedk, marks, level, category, pwd} -> JEE {result (same as /predict result), levels[3] {level, percentile, crl, cat_rank, pwd_rank}, candidates, notes}; COMEDK {rank [lo,hi], mid, percentile [lo,hi], candidates, summary, sources[3], notes}; 422 for COMEDK marks >180, JEE >300, exam bitsat. tests/test_rank_estimate.py 5 pass."
agent_communication_iter84_fix:
  - agent: main
    message: "Fixed iteration_84: (1) paper-type rows restructured: tag on top, percentile | CRL in two columns, category/PwD rank on its own line, no ellipsis at 320/375/390 (no adjustsFontSizeToFit). (2) Rank predictor keeps one query+result per exam: switching JEE <-> COMEDK shows that exam's own card (or its input if none yet); rp-colleges always sends the selected exam's score. (3) COMEDK handover seed is cleared after use (onSeedUsed) and the handed-over marks are saved (branches kept), so later visits open with the newest saved entry. Minor: Rank predictor stays mounted (hidden) when the College tile is open, so its result survives tile switches; input error clears on typing; 'OBC-NCL' uses a non-breaking hyphen in summaries (SilverCaps, Summary)."
agent_communication_iter85_fix:
  - agent: main
    message: "Fixed iteration_85: estimate effect cleanup resets busy (Predict button never stuck after switching exam mid-request; verified by screenshot script); category and PwD rank each on their own line in paper-type rows with non-breaking hyphen and dash (verified at 320px)."

## Iteration86 — Rank tab: 5 tools grid + Percentile se rank, Target marks, College compare
agent_communication_iter86:
  - agent: main
    message: "User: 'Percentile Se Rank (NTA percentile -> expected rank), Target Marks (selected college/branch ke liye kitne marks chahiye), College Compare (2-3 saved colleges side by side: round-wise cutoff, fee, seats). Sab buttons me do: easy navigation, app MB na badhe, quality na kam ho.' Built (text only, no new packages/images): Rank tab top = ToolGrid (src/rank/ToolGrid.tsx) of 5 Home-style tiles: rank-tool-rank (default), rank-tool-pct, rank-tool-target, rank-tool-college, rank-tool-compare (full-width; value shows 'N saved · side by side'). A tool mounts on first open and stays mounted (hidden) so its result survives switching. PERCENTILE SE RANK (PercentileRank.tsx): pr-percentile-input (0-100, decimals), pr-cat-GEN|EWS|OBC-NCL|SC|ST, pr-pwd, pr-input-error, pr-show -> collapses to pr-input-collapsed (Edit); pr-card (pr-card-crl range, pr-card-percentile, pr-card-cat, pr-card-pwd, pr-card-summary, pr-card-serial), strip pr-marks with pr-marks-tough|normal|easy (marks/300 for that percentile), pr-share, pr-colleges -> College predictor (JEE) with that percentile shown. TARGET MARKS (TargetMarks.tsx): exam switch tm-exam-jee|bitsat|comedk. JEE: tm-cat-*, tm-female, tm-pwd, tm-state (picker tm-state-picker), tm-college -> search sheet tm-college-sheet (tm-college-sheet-search, rows tm-college-sheet-<inst>); list tm-list with rows tm-row-N (big Normal-paper marks tm-row-N-normal, line tm-row-N-line Tough/Easy/percentile), tap -> tm-row-N-rounds table (R1-R5 + CSAB 1-2 or JAC R1-R4 + Upgrade/Spot 'publish nahi'; closing + Tough/Normal/Easy marks). COMEDK: tm-college -> tm-college-sheet-<code e.g. E095>; rows tm-row-N (tm-row-N-mid marks/180, range of 3 analyses, fee + GM seats), tap -> round table. BITSAT: tm-campus-all|Pilani|Goa|Hyderabad; rows tm-row-N (tm-row-N-cutoff, history 2022-2026, safe = cutoff+10). Choices saved on phone (rank.target.v1). COLLEGE COMPARE (Compare.tsx): empty -> cmp-empty + cmp-go-college. With saved items: cmp-list (cmp-item-N checkboxes; first 3 saved pre-ticked; 4th tick -> cmp-hint; <2 -> cmp-need), cmp-table: columns cmp-col-N, rows cmp-row-head|final|r0..rN|prev|seats|fee|tag, cmp-final-N, cmp-easiest-N (only when all same exam). All 2-3 columns fit the screen (no sideways scroll) at 320-390px. Backend rank_tools.py (registered in rank_predictor.make_router, public): POST /api/rank/percentile {percentile 0..100, category, pwd}; POST /api/rank/target/jee {inst, category, female, pwd, state?} (404 unknown inst, 422 unknown state); POST /api/rank/target/comedk {code} (404 unknown); GET /api/rank/target/bitsat; GET /api/rank/colleges {jee[], comedk[]}; POST /api/rank/compare {items 1..3 [{exam jee|bitsat|comedk, id, prog?, quota?, gender?, path?}]} -> items with title/sub/path/rounds/final/prev/seats/fee/fee_note, missing:true when not found. JEE seats from rank_data/jee_main_2026_seat_matrix.json (JoSAA only; JAC = none)."
agent_communication_iter86_fix:
  - agent: main
    message: "Fixed iteration_86: (HIGH) Compare pre-tick: until the student ticks/unticks anything, the latest 3 saved stay ticked (follows every new save, even if Compare was first opened while empty and stayed mounted hidden); after the first manual tick, picks stay as chosen. pr-card-percentile shows the typed value (97.4567). BITSAT target history shows '—' for missing years. NEW badge moved onto the bottom edge of the tile icon (rank-tool-<key>-badge) so it never covers the title. Target JEE rounds table: under 360px headers are small title case with narrower columns; JAC Upgrade/Spot show '—*' + footnote '* JAC ne Upgrade / Spot round ki rank publish nahi ki.'; CSAB footnote only when the college has CSAB rounds. Compare: JEE CSAB cells for category/PwD seats carry crl:true (API rounds[].crl) and show a small 'CRL' after the number; cmp-easiest only when all columns share exam AND rank_label; titles up to 4 lines. College search sheet also matches the full college name (e.g. 'delhi technological' -> DTU)."

## Iteration88 — COMEDK answer kept on exam switch + white A4 PDF export of every Rank list
agent_communication_iter88:
  - agent: main
    message: "User: (1) College predictor: exam switch karne par COMEDK marks aur results bache rahein. (2) Har college list ki PDF (pura list with details) for easy access and transfer. Choices: PDF on College predictor lists (JEE, COMEDK, BITSAT) + Target marks college + Saved colleges/Compare; only Top 50 like the screen; white print-friendly; 'genuine data, app ko kuch nahi hona chahiye'. (1) app/(tabs)/rank.tsx: College predictor exam panels (JEE / BITSAT / COMEDK) mount on first open and then only hide (same as tools), so each exam keeps its own input + result. COMEDK meta ErrorBox testID is now comedk-meta-error (JEE keeps rank-meta-error). (2) Backend rank_pdf.py (reportlab 5.1.0, fonts backend/rank_data/fonts/FreeSans*.ttf for ₹), registered in rank_predictor.make_router, all public POST returning application/pdf with Content-Disposition filename: /api/rank/pdf/jee {Form + segment} (same Top 50 as /predict for that segment + 5 'Bas thoda sa door'; columns R1-R5, CSAB 1-2, 2025 R6, Seats (JoSAA seat matrix), Chance; red bold = round that gave the chance; JAC rows fill R1-R4), /pdf/comedk {marks|rank, branches, area} (Top 50 + near; R1-R4, 2025 final, GM seats, fee, chance), /pdf/bitsat {score, campus, degree} (in reach / near / rest, 2022-2026 cutoffs), /pdf/target/jee {inst, category, female, pwd, state} (per branch block: closing + Tough/Normal/Easy marks per round), /pdf/target/comedk {code}, /pdf/target/bitsat {campus}, /pdf/saved {items[1..50] CompareItem, tags[], pick[<=3 indices]} (side-by-side of picked if >=2, then every saved college with round-wise closing, final + last year, seats/fee, chance; missing seats flagged). 422 bad input, 404 unknown college. Every page: JEELIVE.AI header, title, estimate line, 'Page x / y'. Frontend: src/rank/pdf.ts (POST, web = file download, native = save to cache + share sheet via expo-sharing; no new packages), src/rank/PdfButton.tsx (testID, label, spinner, <testID>-msg shows '<file> taiyaar' or error). Buttons: rank-pdf (JEE list, under segment/branch filters), comedk-pdf, bitsat-pdf (under campus/degree chips), tm-pdf (Target marks list: JEE/COMEDK/BITSAT), cmp-pdf (Compare: 'Compare + saved list ki PDF' when >=2 ticked else 'Saved list ki PDF'), rank-shortlist-pdf (shortlist sheet). Native share sheet cannot be tested in web preview."

## Iteration89 — PDF straight to WhatsApp, series day count from the website, royal-blue Home share card
agent_communication_iter89:
  - agent: main
    message: "User asks: (1) 'PDF WhatsApp Direct' with the PDF FILE itself attached (chosen over a link). (2) Home All India card showed 62 days but the website series is now 50 days: make it dynamic. (3) Replace the last Home block (old 'made for every aspirant' footer) with a beautiful royal-blue share card, share button on its face, proper English text about: 100% free, built by AI deeply analysing 4,000 PYQs, PYQ-DNA questions, Rapid Fire revision, Rank to know colleges, target dream college, mocks + All India Test Series, AI target that 200+ marks of questions match every shift (same concept, only numbers change). DONE: (1) src/rank/pdf.ts sendPdfWhatsApp + PdfButton now shows two buttons per list: <testID>-whatsapp (green 'WhatsApp') and <testID> (outline PDF, unchanged). Android build: react-native-share 12.3.1 (installed via yarn expo install) opens WhatsApp / WhatsApp Business with the PDF attached (app.json expo-build-properties android.manifestQueries com.whatsapp + com.whatsapp.w4b); iPhone & Expo Go: share sheet (iOS allows no direct file to WhatsApp); web: navigator.share with the file on phone browsers, else downloads the PDF and opens WhatsApp Web (api.whatsapp.com) with the caption; <testID>-msg says what happened. Native direct path only testable in a real Android build. (2) series.ts seriesDays/useSeriesDays read Series.total (website: 50, 9 Dec 2026 – 27 Jan 2027): HomeSeriesCard (series-home-day '50 DAYS', ring 'of 50', title '50 daily full mocks'), Home ALL INDIA tile ('opens 9 dec' from first_date), promo (home-promo-title '50 daily mocks, free.'), /live header eyebrow + 'N-day map' + How it works sheet, TodayCard prelaunch text, JourneyCard ring/cups (streak.total_days, 'Starts 9 Dec' from streak.first_date), Mission stat. No '62' left in UI. (3) src/components/home/ShareCard.tsx (testID home-share-card; home-share-title, home-share-dna, home-share-goal, buttons home-share-whatsapp (opens WhatsApp with the invite text) and home-share-more (system share)); invite text in src/shareApp.ts, also used by Explore 'share with friends' and Mission share. Theme keys custom_royal*. Website check: AITS section has 0 published papers and all 50 slots ready=false/set_id=null, so no test is startable yet (not an app bug)."

## Iteration90 — Build cleanup + Rank tab cards as Elite-style black metal cards (5 jewel colours + diamond), page pure black
agent_communication_iter90:
  - agent: main
    message: "User: build cleanup (extra lock file, Expo SDK 58 versions) and Rank tab theme. Feedback: 'Background pura black rkho, bas cards badalne the'; 'problem dar se nahi, dull se hai, elegance nahi hai metal card jaise'; cards 'bilkul Elite card jaise + dono milake (metal chamak + gehra rang)'; 'charo card alag: purple-blue-black, maroon-black, teal-black, pink-black; all cards with diamond hint'. FEATURES MUST NOT CHANGE, no testID changed. Build: package-lock.json gone (yarn only), corrupt zero-byte file deleted, expo-doctor 20/20, tsc clean. Theme: previous navy/gold attempt reverted; page bg solid #000 (custom_rankBg). New src/rank/Metal.tsx: MetalFace = graphite→jewel diagonal gradient + SVG radial glow behind the diamond + SVG Pattern brush streaks + broad diagonal sheen + bevelled top edge + foot shade; on = stronger glow + jewel top edge. JewelContext/useJewel/JewelPill. New src/rank/Diamond.tsx (faceted SVG brilliant with sparkles). Tool tiles: rank=maroon, pct=indigo (purple-blue), target=teal, college=pink, compare=champagne gold; each tile has a diamond in its bottom-right corner (brighter + sparkles when chosen), chosen tile = jewel border/glow/title. LATER (user: niche simple rkho): everything below the tiles reverted to the original black panels with red hairlines; only the Rank Card changed to a quiet black metal card with a hairline diamond watermark (DiamondLine) and a small DiamondMark by JEELIVE.AI. Tile value line has right padding so the corner diamond never sits under it. Tile fonts lighter/smaller (user: font heavy): title semibold 10.5 (9.5 narrow) tracked caps, value regular 10.5 single line, icon 34px, tile minHeight 64. Lists: medal coins 1/2/3 with soft wash; type + chance tags under the college name. PDF buttons wrap to two rows on phones."

## Iteration91 — Mission tab = one shareable "Creator's Letter" card (royal blue + gold, Hinglish)
agent_communication_iter91:
  - agent: main
    message: "User picked design 5 (Creator's Letter) of 5 shown concepts. Mission tab (app/(tabs)/mission.tsx) is watch-only: eyebrow + title, a RED share button on top (testID mission-share-top) and below the card (mission-share-bottom): WhatsApp icon + 'Please share karo' + 'aur free education ko support karo' (the whole red block is the button), the card (testID mission-card, src/mission/MissionCard.tsx: 4:5, royal blue + gold, gold corner ribbon '100% MADE BY AI ASTRA', gold quote, maker's words, signature 'Abhishek Pushp' + gold AP seal, 4 chips PYQ DNA / Target 200+ / Rapid Fire / Rank + College, footer '100% FREE' + 'Please share karo · jeelive.ai'), a 'Doosre app mein share karo' link (mission-share-more), optional note (mission-share-note), 'Poori baat' list (mission-points, 6 segments) and fine print (mission-disclaimer). Share (src/mission/share.ts): web → WhatsApp button opens wa.me with CAPTION (src/mission/copy.ts); 'Doosre app' → Share.share, or copies caption + note on browsers without share. Native: captureRef PNG 1080x1350 → Android build WhatsApp direct via react-native-share (new shared helper src/whatsappFile.ts, also now used by src/rank/pdf.ts sendPdfWhatsApp), iOS share sheet with image + caption, Expo Go Android share sheet + caption copied. Text is fixed-size (allowFontScaling false) inside the card."

## Iteration92 — "Share to view results" gate after every test submission
agent_communication_iter92:
  - agent: main
    message: "User: after every test submission (Mock, AITS, PYQ paper) show the Mission card before the result with 'Share to view results'; user chose a HARD gate (result opens only after a share). Implementation: app/attempt/[id].tsx toResult (used for manual and auto submit) now calls lockResult(id) (src/mission/gate.ts → storage key `share_gate.<attemptId>` = true; on web this is window.localStorage 'share_gate.<id>' = 'true') before router.replace('/result/<id>'). app/result/[id].tsx checks isResultLocked: locked → renders <ShareGate> (src/mission/ShareGate.tsx, testIDs share-gate, share-gate-back, share-gate-title, share-gate-share, share-gate-more, share-gate-note, share-gate-thanks) while the result keeps loading behind it; after a share (WhatsApp red button or 'Doosre app se share karo') a green 'Shukriya! Result khul raha hai…' shows ~0.9s, the flag is removed and the normal result renders. Leaving with back keeps the lock (reopening shows the gate again). Old/unflagged results open normally. Shared red button + share flow now live in src/mission/ShareButton.tsx (ShareButton, useMissionShare; fallback to WhatsApp text if the picture share fails) and are reused by the Mission tab (title 'Please share karo'). IMPORTANT TEST RULE: the QA account is read-only for academics — never start/answer/submit a test; simulate a fresh submission by setting localStorage 'share_gate.<completed attempt id>'='true' and opening /result/<id>."

## Iteration93 — Share gate opens on return from WhatsApp + Share Card Stats (personal link, friends helped)
agent_communication_iter93:
  - agent: main
    message: "User: 'Phone pakka nahi bata pata ki WhatsApp par message sach me gaya ya nahi. Result kab khulna chahiye?: WhatsApp khol kar wapas aane par; Max 3 sec.' Then 'Share Card Stats; Thank you, ki aapne itne log free education mein help kiya.' Choices: friend counts on 'Aapka personal link kholne par'; message also 'Share hone wali photo par bhi'; 'Make it very beautiful.' (1) GATE: src/mission/share.ts watchReturn() (AppState). ShareOutcome now {shared, away, note}. In useMissionShare (src/mission/ShareButton.tsx) with onShared (gate): when the share goes to another app/tab (away=true: web WhatsApp, Android WhatsApp/share sheet) the button spins, note share-gate-note = 'WhatsApp par bhej kar wapas aao, result yahin khul jaayega.', and the result unlocks only when the app/page comes back to foreground (web: document visibilitychange hidden -> visible); if the app never leaves within 3 s (popup blocked / desktop), it unlocks after 3 s. Then green share-gate-thanks ~0.9 s and the result. iOS sheet / web navigator.share: unlock when the sheet returns with a share; dismissed/AbortError keeps it locked. (2) STATS backend backend/mission_links.py: GET /api/rf/mission/me (RF grant, Bearer from /api/rf/access) -> {code (7 chars A-Z2-9 no 0/O/1/I/L), helped, week}; creates the link on first call. Public GET /api/j/{code} -> 302 https://jeelive.ai, sets cookie jlv (path /api/j, 1 yr); counts a friend (+1 helped) only if BOTH the visitor cookie and sha256(ip|ua) are new for that code; robots (WhatsApp/Telegram/facebookexternalhit/curl/python/headless/playwright...), empty UA, unknown/bad code never counted. Collections mission_links, mission_visits. (3) FRONTEND: src/mission/stats.ts useMissionStats (cache key u.<uid>.mission, revalidates on focus); caption(link) in copy.ts now ends 'Abhi kholo 👉 <BACKEND>/api/j/<code>'. Mission tab: ImpactPanel (src/mission/ImpactPanel.tsx) between title and top share button: testID mission-impact; helped>0: gold medal mission-impact-count (count-up), mission-impact-line 'Aapne N logon ki free education mein help ki', mission-impact-week '+K is hafte' (only K>0), milestone 'Agla padaav: X dost' + mission-impact-goal 'N/X' + gold track; helped=0: hand-heart medal + 'Aapka pehla share kisi ki free taiyari shuru karega'; always mission-impact-how line. Pull-to-refresh on the Mission tab. MissionCard (also on ShareGate and in the shared PNG): when helped>0 a gold thank-you band mission-card-thanks under the signature (medal mission-card-thanks-count + 'THANK YOU, <FIRST NAME> 🙏' + 'Aapne N logon ki free education mein help ki'); letter font steps down a touch. QA: account 7004186276 / 5524 has mission code VU6PE38, temporarily helped=12 and 3 counted visits this week (for visuals)."

## Iteration94 — Rank tab: each tool's form in its own bright colour + College predictor colleges as button-cards
agent_communication_iter94:
  - agent: main
    message: "User: students can't tell the form opens below a tile. Rule (user's words): tiles keep their metal colours EXCEPT the College predictor tile becomes blood red; the FORM of each tool gets a bright colour: Rank predictor = bright yellow, Percentile se rank = teal, Target marks = bright lime green, College predictor = bright pink, College compare = sky blue; the chosen tile's border + glow (+ top edge) use that same form colour. College predictor lists: every college a proper card/button with a side button 'Cutoff dekho ›', 'segment everything, inspiring, proper carding'. DONE: src/rank/accent.tsx (ACCENTS per tool, AccentContext set around each tool pane in app/(tabs)/rank.tsx, FormButton, useField). Strip `form` prop (controls.tsx): 1.5px frame in the colour, solid colour header band testID '<strip testID>-head' (tool icon in a dark circle, tool name caps, strip title), soft colour wash; plain Toggles (no own colour) inside a form fill with the colour (dark text); Switch chosen side + Summary (collapsed form: icon + 'Edit') also in the tool colour. Forms: rp-input, pr-input, tm-profile (JEE + COMEDK), new tm-campus (BITSAT target campus chips), rank-input, bitsat-input, comedk-input, cmp-list, cmp-empty. Main buttons rp-show, pr-show, rank-show, bitsat-show, comedk-show, cmp-go-college now in the colour with dark text. Text fields framed in the colour. ToolGrid: college tile jewel 'blood' (new tokens custom_blood*); chosen tile border 1.5 + glow + top edge = form colour. Tile tap scrolls the form into view only if it is far below. College cards (src/rank/CollegeCard.tsx): JEE SeatRow (rank-seat-N, rank-near-N, rank-chart-seat-N), COMEDK (comedk-seat-N, comedk-near-N), BITSAT (bitsat-item-N, bitsat-near-N, bitsat-rest-N): left edge in chance colour, medal, name, tags, course, 3 stat boxes (JEE: CLOSING / ROUND / 2025 SE (testID <id>-trend); COMEDK: CLOSING / 2025 SE / FEE / SAAL; BITSAT: CUTOFF / 2025 SE / AAPKA), footer teaser + pink pill <id>-cta 'Cutoff dekho ›' (BITSAT open: 'Band karo'), star <id>-star top-right, '<id>-viewed' ('Dekha · …') after opening. Whole card opens the detail (JEE CollegeSheet rank-college, COMEDK ComedkSheet, BITSAT inline 5-year history <id>-history as year boxes). Lists now: filter panel Strip (rank-list-head / comedk-list-head / bitsat-list-head) then tap hint (rank-tap-hint / comedk-tap-hint / bitsat-tap-hint: 'Kisi bhi college card par tap karo' → after opening 'N college dekhe, shabaash!'), cards, pager, 'BAS THODA SA DOOR' heading + near cards. Outer wrappers keep testIDs rank-list / comedk-list / bitsat-list. First card's CTA breathes until the student opens any college once (storage rank.cta.seen.v1)."
agent_communication_iter95:
  - agent: main
    message: "User fixes (only these 3): (1)+(2) College predictor must be BLOOD RED, not pink: form accent for the college pane is now blood red (ink #D10F2A fills: header band, chosen chips, Show buttons, CTA 'Cutoff dekho', tap-hint icon; text on it WHITE; words/icons/tile glow on black use lighter red #FF4D5E; frame rgba(255,59,78,0.75)). Chosen tile border+glow use the accent 'text' colour (college = #FF4D5E). Glow fixed: shadow props now live in one inline style with shadowColor (+ elevation) on tiles, form strips and the breathing CTA. (3) Collapsed form (Summary: rank-input-collapsed, rp-input-collapsed, pr-input-collapsed, bitsat-input-collapsed, comedk-input-collapsed) now has a filled glowing pill button '<testID>-edit' (pencil + 'Edit', tool colour, min height 44) plus a hint line '<testID>-hint' 'Doosra number dekhna hai?'; tapping anywhere on the row (incl. the pill) reopens the form. Stat boxes on college cards allow 2 lines (no cut text at 320px)."
agent_communication_iter96:
  - agent: main
    message: "User: 'I want the College Predictor tab to be without that black colour hint, pure blood red, so it's different from other tabs.' The College predictor TILE (rank-tool-college) is now pure blood red: Metal jewel 'blood' has `pure` — gradient #E01B33 → #B80D24 → #860818 (all red, no graphite), no dark brush streaks, no dark foot shade; tile background red; title white, small line #FFE1E5, icon circle white-glass. Chosen: border/top edge #FFC2C9 + red glow. Other 4 tiles unchanged (graphite metal). Unused pink jewel + tokens removed."

## Audit Phase 1 (June 2026) — Dream College Goal + College predictor purple bar + PDF with card photo
agent_communication_audit_p1:
  - agent: main
    message: "Finished wiring the Dream College feature (previous fork left Home + Result unwired and rank.tsx missing the useLocalSearchParams import = Rank tab crash). Home: section 'DREAM COLLEGE' with DreamMeter testID home-dream (limit 3; home-dream-add -> Rank tab College predictor; home-dream-more 'Sab N dream dekho' -> Rank tab with Dream panel open; home-dream-add-more). Rank tab: dream-panel (dream-panel-toggle, dream-panel-line, switch dream-exam-jee|bitsat|comedk with 'N/5', DreamMeter dream-meter with rows dream-meter-row-N, -remove, -need/-gap/-reached, dream-meter-count). College cards: 🎯 DREAM button <card testID>-dream (JEE rank-seat-N-dream / rank-near-N-dream, COMEDK comedk-seat-N-dream, BITSAT bitsat-item-N-dream); message <card>-dream-msg; max 5 per exam (6th shows 'ke 5 dream college ho gaye...'). Stored in phone storage key dream.v1 (web localStorage). Result screen: Analysis tab shows result-dream (DreamMeter for that exam, mockId = attempt id) only for full papers (max >= half of exam full marks); released results are recorded as mocks (score scaled to 300/390/180). College predictor: open form = blood red; after Show the collapsed bar (rank-input-collapsed / bitsat-input-collapsed / comedk-input-collapsed) = shining purple gradient with blood red Edit pill <id>-edit. PDF WhatsApp (<pdf testID>-whatsapp: rank-pdf, comedk-pdf, bitsat-pdf, rank-shortlist-pdf): web passes [card PNG, PDF] to navigator.share when canShare({files}) is true, else downloads PDF + opens WhatsApp web."

## Audit fixes (June 2026) — build, database safety, 1 lakh scale, Dream College per account
agent_communication_audit_fix:
  - agent: main
    message: "Fixes from memory/AUDIT_2026_06.md. BUILD: removed stray frontend/package-lock.json (yarn project), app.config.js minify/shrink off. BACKEND: jl_transport.py now aiohttp (Upstream class, make_client, UpstreamError); proxy forwards X-Forwarded-For; cookie jar saved per cookie field (cookie_changes/save_cookie_changes, names with '.'/'$' encoded), jl_jars.seen_at + 90-day TTL; startup setup (indexes, migrations, card sync) once per code version via rf_meta 'setup:<hash>'; card sync by content hash (rf_meta card_files); sweep loop every ~5 min (one process, rf_meta turn:sweep): stale duels settled, sprints active >24h -> expired, unpaid cups paid. gamify.award: per-field $inc on day_stats/week_stats, guarded day/week reset, pay_once (paid_refs on profile, exactly once), stale award marker (>15 s, no reward) is finished by the next call. cups.finish -> payout 'pending' + pay_cup (pay_once per player) + resume_payouts. rf_gang_reports unique (gang_id, uid). NEW dream.py: GET /api/rf/dream, PUT /api/rf/dream/dreams (max 5 per exam, unique ids), POST /api/rf/dream/mocks (newest 30, same id replaces). Tests: backend/tests/test_audit_2026_06_db_fixes.py (5 pass). FRONTEND: src/dream/store.ts per account (setDreamAccount from auth, phone copy dream.v2.<uid>, old dream.v1 migrated once, server sync, backfill of full mocks from /my/tests completed page 1); full mock = exam's question count (JEE 75, BITSAT 130, COMEDK 180, >=90%) AND >= half marks; toggleDream/removeDream/recordMock wait for load; need.ts JEE target uses the round shown on the card (e.g. CSAB 2); HomeDream switch (home-dream-exam-<exam>) when dreams in >1 exam; auth.tsx session check retries 429/5xx/offline (2/5/10/20 s + Retry-After) before showing an error; useAttempt: at 00:00 random 0-10 s, one flush, POST submit, retry with backoff, non-transient -> one GET; last-minute save retry <=2 s; attempt options no longer locked until image loads; images saved on the phone reused for 3 days without re-download (website sends no ETag)."

## Iteration101 — fixes from iteration_100 (old phone dreams move, account merge, BITSAT bonus, submit drain)
agent_communication_iter101:
  - agent: main
    message: "Fixed iteration_100. (MEDIUM) Old phone dreams (dream.v1) no longer drop account dreams: dream sync is now a 3-way merge. Phone copy dream.v2.<uid> = {dreams, mocks, dirty, base (ids of the account list the phone's changes were made on), unsent}. PUT /api/rf/dream/dreams body is now {dreams, base} (base REQUIRED, 422 without): server merge(current, base, mine) = account dreams the phone removed (in base, not in dreams) go, phone additions (not in base) join only while that exam has < 5, dreams added on other devices stay; returns the merged list; atomic with a rev field (retry on conflict, 503 after 10). Legacy dream.v1 items count as phone additions (base unchanged) -> they only fill free slots. Frontend src/dream/store.ts: one sync at a time (queue): GET /rf/dream first (once per sign-in, again on app focus at most once a minute), then PUT with base, then POST unsent mocks. A pin made before the account list loads is merged, never overwrites. Refused saves (400/409/413/422) are not retried forever: the account list comes back and DreamMeter shows '<testID>-notice' ('Ye badlav account mein save nahi hua...'). Sign-out: pending dream changes are sent first (<=4 s), then dream.v2.<uid> is removed (kept only if it still has unsent changes); session expiry keeps it. BITSAT: a paper worth more than full marks (426 with bonus) keeps the real score (no scaling to 390); shorter papers still scale up; meter line says '426 marks ka paper (bonus sawal ke saath)'. useAttempt: before auto-submit (every round) and manual submit, drain() waits for a save already in flight, then sends what is still pending. Touch targets: dream-meter-row-N-remove 44x44, <card>-dream 44x44. Backend tests: tests/test_iter100_dream_api_public.py (16, incl. merge + parallel) + test_audit_2026_06_db_fixes.py (5) = 21 pass."
agent_communication_iter101_fix:
  - agent: main
    message: "Fixed iteration_101 optional items: PUT /rf/dream/dreams accepts a missing base (= [] : older builds only add, never remove). A dream added here that finds no room (that exam already 5 on the account) shows dream-meter-notice '<college> nahi juda: account mein <exam> ke 5 dream college pehle se hain...'. Refused save resets fetchedAt so the account list is read again first next time. Meter header allows 2 lines (no 'JEE MA...'). BITSAT bonus paper score shows '/ 426' (max of full marks and paper marks). Auto-submit: answers still unsent because of the network hold submit back for up to 3 retries (~40 s), then it goes anyway. Backend tests 25 pass (iter100 public 16 + iter101 merge 4 + audit 5)."

## Iteration102 — "Add to Compare" on college cards, college vs college compare with branch lists, Dream Progress Chart
agent_communication_iter102:
  - agent: main
    message: "User: (1) Compare: star not enough -> 'Add to Compare'; add colleges from inside Compare: 'Sirf college search, saari branches ek saath; when a college is chosen, all branches shown only on See branches inside that card; student can compare colleges and also compare branches'. (2) Dream Progress Chart: line graph of all past mock scores towards dream colleges, 'kitne door' in cards; on Rank Dream panel, Home Dream card and Mock result. 'Make it perfect, elegant, powerful.' DONE. CARDS (src/rank/CollegeCard.tsx): star removed; under each College predictor card an action row: '<card>-compare' pill ('+ Add to Compare' sky outline -> '✓ In Compare' filled sky) and '<card>-dream' pill ('Dream college' -> 'Dream ✓', blood red); after adding, '<card>-compare-msg'. JEE rank-seat-N / rank-near-N, COMEDK comedk-seat-N / comedk-near-N, BITSAT bitsat-item-N / bitsat-near-N / bitsat-rest-N. Shortlist sheet remove = X (rank-shortlist-remove-N). COMPARE (Rank tab tile rank-tool-compare, tile line 'N college · M branch'): switch cmp-mode-college | cmp-mode-branch ('Colleges · N' / 'Branches · M'). Colleges (src/rank/CompareColleges.tsx): Strip cmp-colleges; cmp-add-college opens sheet cmp-college-sheet (exam switch cmp-sheet-exam-jee|comedk|bitsat, search cmp-college-sheet-search, rows cmp-college-sheet-<jee-INST|comedk-CODE|bitsat-CAMPUS>, '<row>-on' = 'Juda'; tapping a picked row removes it); list rows cmp-college-N (tick cmp-college-N-tick, remove cmp-college-N-remove, 'Saari branches dekho' cmp-college-N-branches -> cmp-college-N-branch-list with rows cmp-college-N-branch-M (marks cmp-college-N-branch-M-marks, + button cmp-college-N-branch-M-add adds that branch to the Branches compare), go button cmp-college-N-branch-go); newest 3 auto-ticked until the student ticks; cmp-college-hint (4th tick), cmp-college-need, cmp-profile (JEE category/state from College predictor form). Table cmp-college-table: rows cmp-college-row-head|entry|cs|top|count|seats|fee, cells cmp-college-entry-N / cs-N / top-N, highlight cmp-college-best-N (same exam only). Colleges stored on phone key rank.compare.colleges.v1. Branches mode = old compare (cmp-list, cmp-item-N, NEW cmp-item-N-remove, cmp-table, cmp-pdf; empty cmp-empty with cmp-go-college + cmp-go-colleges). BACKEND rank_tools.py: POST /api/rank/compare/colleges {items 1..3 [{exam, id: JEE inst number | COMEDK code | BITS campus}], category, female, pwd, state} -> items [{title, name, place, kind, branches, seats, seats_label, fee [min,max]|null, fee_note, easiest/toughest/cs {branch, close, label, rank_label, marks}, cs_count} | {missing:true}], notes; GET /api/rank/colleges now also has bitsat [{campus, name, programs}]; /api/rank/target/jee rows have quota + gender. tests/test_iter102_college_compare.py (4 pass). DREAM CHART (src/dream/ProgressChart.tsx, SVG): inside DreamMeter when chart prop set: '<meter>-chart' with stats '<meter>-chart-best|avg|speed', score line + purple area, dashed target line per dream in row colour (solid when reached), right labels '<meter>-chart-target-N' (number + need or ✓), tap zones '<meter>-chart-point-N' -> tooltip '<meter>-chart-tip' (score, title, date; 'IS MOCK' on result), 1 mock -> '<meter>-chart-one'. Rows: number ring in the line colour + '<meter>-row-N-eta' ('Is raftaar (+X/mock) se ~K mock mein pahunchoge' etc.). Where: dream-meter (Rank Dream panel, all mocks up to 30), home-dream (compact, last 8, first 3 dreams), result-dream (mocks up to that result)."
agent_communication_iter102_fix:
  - agent: main
    message: "Fixed iteration_102: (MEDIUM) chart tooltip no longer floats over the chart: the chosen mock is a bar '<meter>-chart-tip' between the stats and the chart (score / total, title, date, 'mock k / n' or 'last mock', 'IS MOCK' on result), so target labels are never covered. 320px: card buttons say 'Compare' / 'Dream' under 360px width ('Add to Compare' / 'Dream college' on wider phones); chart stats labels BEST / AVG (sub 'last 3') / RAFTAAR (sub 'per mock'); dream row target line up to 2 lines, ETA up to 3 lines; 3-college table on <360px uses smaller text (no mid-word breaks), titles up to 4 lines. ETA wording: speed >0.5 'Raftaar dheemi (+X/mock)', < -0.5 'Score gir raha hai', else 'Score ruka hai'."

## Iteration104 — "Dream Unlocked" celebration (Kohinoor Legends 30 s routine + confetti)
agent_communication_iter104:
  - agent: main
    message: "User: first time a student crosses a dream college target -> confetti burst + Rapid Fire's Kohinoor Legends (level 4 Cheer Squad) doing a proper 30 s routine. Choices: once per dream college; opens where the new score is first seen (Mock Result, or Home for a mock seen first there); banner 'DREAM UNLOCKED!' + college name; full routine then Continue, Skip always visible while it plays. BUILT: src/dream/DreamCheer.tsx (DreamCheerHost on Home HomeDream + Result Analysis, only when that screen is focused), src/dream/routine.ts (64 counts @128 BPM = 30 s, 8 sections, chants), store.ts claimCheer(exam, mockId?) = newest full mock of the exam, <=7 days old, crosses dreams (score >= need, dream added before the mock) not yet celebrated; marks them celebrated at once (state.cheered, phone copy + POST /api/rf/dream/cheered {ids}); GET /api/rf/dream now returns cheered. Track: backend/rf_art/sound/dream_cheer.m4a served public at /api/rf/art/dream_cheer.m4a (made offline by backend/rapidfire/make_dream_cheer.py). TestIDs: dream-cheer, dream-cheer-pill, dream-cheer-skip (during loading/dance), dream-cheer-chant / -chant-text, dream-cheer-stage, dream-cheer-lead, dream-cheer-holder-1/2, dream-cheer-card, -college, -need, -score, -over, -more, dream-cheer-progress, dream-cheer-cannons, rf-confetti, after 30 s: dream-cheer-continue + dream-cheer-again (replay). Fixture: python /app/backend/tests/dream_cheer_fixture.py seed|cleanup (see test_credentials.md)."

## Iteration105 — Dream Share Card (WhatsApp)
agent_communication_iter105:
  - agent: main
    message: "User: 'Dream Share Card: WhatsApp share card after the celebration showing the college and score'. Choices: button at the celebration end AND on the Dream card (reached rows); card shows name, college, branch, score, target; simple elegant card (no cheerleaders): black-metal Rank-card style with big serif college, branch caps, diamond, 'TARGET CROSS · +N MARKS UPAR', Mock score X/300, Target, student name, mock title; caption = achievement + 'Tum bhi apna dream set karo 👉 <student share link>'. BUILT: src/dream/DreamShare.tsx (dreamShare() caption, DreamCard off-screen, useDreamShare hook -> shareCard()). DreamCheer done state: footer = dream-cheer-share (SHARE, Dost ko dikhao) + dream-cheer-continue; replay moved to top bar dream-cheer-again ('Phir se', hidden under reduced motion). DreamMeter: reached rows (last/this mock score >= need) get `${testID}-row-N-share` WhatsApp pill 'Dost ko dikhao' (+ `-share-note`). Off-screen card testIDs: dream-share-card, dream-share-card-college, -name, -score, -need. Web share path: navigator.share with file when supported, else WhatsApp link with the text (src/shareCard.ts)."

## Iteration106 — Analysis 2.0 Phase 1-2 (time sync verified on a real test + website card style in the app's light theme)
agent_communication_iter106:
  - agent: main
    message: "User: 'Analysis 2.0 Phase 1-2 shuru karo, asli test mein time ki sync pakki karo, exactly like jeelive.ai'. Choices: keep the app's WHITE look (only cards/charts like the website); YES do one real practice test with the QA account. PHASE 1 DONE BY MAIN (real attempt 9332443d-284c-4456-bf87-a4e506658971, set jee-main-pyq-2026-04-05-s1, QA 7004186276/5524): scripted Q1 14.1 s (answer at 12.1), Q2 12.1 s (A then B), Q3 6.1 s + 8 s app hidden (visibilitychange) + 3 s + revisit 5.6 s, Q4 6.1 s, submit at 55 s. Server analysis: Q1 time 14 at 13, Q2 12 changed '1→2', Q3 15 visits 2 marked, Q4 6, off_screen 9, time_used 56, journey visits/order correct -> recording matches within 1 s. PHASE 2 (frontend only, src/analysis/*): Roboto Mono number face added (assets/website-2026-10-26/roboto-mono-latin-400/700-normal.ttf, fonts.mono / fonts.monoRegular, T w='mono'|'monoRegular'); Tile = website stat tile (4px coloured left edge, CAPS tracked label, mono value, 'Sawaal dekho →'); Block radius 20 + soft shadow, kicker tracked 1.7; Overview score card = website 'Aapka Score' (kicker, title, ORIGINAL/REVISED badge, big centred ring with mono score '48' + '/ 300' + '16%' pill, 'Paper mein laga 11m 49s', 4 counts); action buttons now 2x2: 'Report download', 'Share', 'Galat + chhode dobara', 'Solutions dekho' (same testIDs); Potential tiles 2-col 'Abhi ka score / Realistic target / Maximum potential'; mono numbers in ledger, grid cells, StatRow right values, Difficulty cells, Qs-by-Qs time line, bottom-bar numbers. testIDs unchanged."

## Iteration107 — Analysis 2.0 Phase 3 (compare), Phase 4 (Solutions website layout), Phase 5 (full real mock + small screens)
agent_communication_iter107:
  - agent: main
    message: "User picked all 4: Phase 3 compare, Phase 4 Solutions/3 seekh/PDF/share, Phase 5 320/390 + one full real mock, then login 401 fix (after Analysis). Findings: compare/learnings/report/share were already ported from jeelive.ai (same testIDs + copy, verified against the website bundle). Every QA paper has only 1 student, so compare is honestly locked ('Compare abhi nahi khula'); the comparative UI was verified with a test-only Playwright route fixture (/app/.cmp_tmp/compare_fixture.json: available:true, Topper 212). CHANGES: Compare.tsx — colour key (Aap brand / label warn) in head + subject blocks, Duo values mono, caps labels, brand vs warn ink. result/[id].tsx Solutions — website layout: 'CHOOSE A SUBJECT' card (count, subject tabs, subject name + hint, Question grid, rail with mono numbers, legend solution-legend Correct/Incorrect/Skipped/Marked), 'UNDERSTAND THE WHY' + 'One question. A clearer understanding.' (solution-title) + solution-subject-position '<subject> · Question N · i of n', filters now wrap, card header 'Question N' + '<subject> · Single correct|Numerical' + outcome chip + '+4 marks'. report.pdf (294 KB) and share.png (66 KB) verified 200 via proxy. PHASE 5 real full mock (approved by user): attempt ed6543db-811c-4558-9485-c4a6425663c4 (JEE Main PYQ 08 Apr 2026 S2): 70 answered, 5 skipped (13,26,39,52,65), 8 marked, 5 changes; server analysis matched (changed 11,33,44,55,66; marked 9..72; per-question times = scripted 2.0-4.4 s). Q25/Q50 show 0 s only because each test chunk was a fresh browser (open stretch kept in phone storage, recovered on a real phone)."

## Iteration108 — Login session: number kept + short note when a session ends (7-day rule unchanged) + lint cleanup
agent_communication_iter108:
  - agent: main
    message: "User: keep the 7-day rule; when the session ends, the phone number must already be filled on the sign-in screen with a short note. Website check (read-only): access cookie 15 min, refresh cookie 7 days and SLIDING (every refresh/session read gives a new 7 days); proxy refresh with an expired/missing access cookie works (200). So no backend change. FRONTEND src/auth.tsx: phone storage keys jl_last_phone (number as typed, +91 stripped) and jl_session_ended (true). Every successful sign-in / sign-up / Forgot-PIN auto sign-in saves the number. A session that ends by itself (session check finds no user on a device that had one, or a 401 during use) keeps the number (older installs: taken from the saved profile jl_user.phone), sets expired + jl_session_ended (survives app restart until the next sign-in). A fresh install with no account shows no note. Explicit Sign out removes both keys (shared phone stays private). Context adds lastPhone + forgetPhone(). app/entry.tsx: phone field prefilled (still editable); row entry-remembered-phone ('Pichhli baar wala number') with entry-change-number ('Doosra number?' empties the field and forgets the number); entry-session-expired note is now tone info, Hinglish: 'Aapka session khatam ho gaya. Number pehle se bhara hai — bas PIN daal kar wapas aao. Aapke results aur saved kaam safe hain.' (without a kept number: 'Number aur PIN daal kar wapas aao...'); the PIN box gets focus automatically in that case. app/forgot-pin.tsx phone field also prefilled from the kept number. LINT: eslint 53 errors -> 0 (fixed non-literal useCallback deps in GangTab/LobbyTab/TrophyTab, catalogue module write moved into an effect, DreamCheer shared values use .set(); React-Compiler-only rules set-state-in-effect/refs/purity turned off in eslint.config.js because the compiler is not enabled). tsc clean, worklet check passes. Main verified in web preview: sign in -> server-side session killed (POST /api/jl/auth/logout with the page's X-JL-Sid, app state untouched) -> reload -> note + 7004186276 prefilled + PIN focused -> PIN -> Home, jl_session_ended removed."


## Iteration109 — Rapid Fire content expansion live (20 Nov 2026)
agent_communication_iter109:
  - agent: main
    message: "User: 'Sirf Rapid Fire poora karo' (no more questions). Rules in /app/memory/RAPID_FIRE_RULES.md (20 s per card everywhere; 30/50/100 cards picker rf-card-count-30|50|100 below the subject chips in the lobby and rf-scope-count-* in the battleground sheet; BITSAT English + Logical Reasoning subjects; no prompt twice in a round; unseen cards first). CONTENT NOW LIVE: Physics 5292, Chemistry 4492, Mathematics 4046, English 1416 (19 chapters), Logical Reasoning 912 (12 chapters) = 16158 cards (was 6155). Backend tests tests/test_rf_rules_june2026.py 8 pass (incl. 100-card English and LR solo rounds, bank integrity, catalog totals = files)."
  - agent: main
    message: "Fixed iteration_109: native RapidText turns letter+combining mark (U+20D7/0304/0305/0302…) into $\\vec{}$/$\\bar{}$/$\\overline{}$/$\\hat{}$ for the offline typesetter (web keeps Unicode, system font fallback); 10 English markdown prompts rewritten (WORD in capitals), 6de7d6fb blank fixed; rf-summary-exam says BITSAT for English/LR rounds; rf-card-counter '1 / 30' under 360 px (numberOfLines 1); timed-out card 2.4 s + scrollToEnd on lock; CardCount lights the fitted count; duel-exam-group prefixes 'BITSAT · ' when all picks are BITSAT. Verified at 320 px: BITSAT · English · Time & Tense, '1 / 30', explanation visible after answer."

## Iteration110 — All India card: 5 living scenes in the student's fire world + flicker fix + Weak Topic Sprint (20 Nov 2026)
agent_communication_iter110:
  - agent: main
    message: "User (Hinglish): 'Start with the All India Rapid Fire, show me 5 screens: spaceship animation, World Cup, Lions fight, horse racing, archery' + then sent a picture (riders as black silhouettes on a dark ridge against blazing red-orange smoke): 'Use this as the cards' theme and background of the All India Rapid Fire. Beautiful, perfect, elegant, and powerful.' Also agreed earlier: fix Trophy/Gang tab flicker, Weak Topic Sprint (20 s, only subtopics they keep missing), keep the glitter border. BUILT: src/rapid/DailyScenes.tsx (one fire world: th_fire_bg drifting + breathing glow + rising embers; 5 scenes on a 360 stage scaled to the card: 1 Space Race = rocket silhouette with flickering flame flying bottom-left→centre→top-right + star streaks; 2 World Cup = golden trophy floating over sil_army, rotating gold rays; 3 Lion Clash = two lion silhouettes lunge and crash, white-hot burst + shake + VS badge; 4 Cavalry Race = 3 rider silhouettes galloping and swapping the lead, dust, embers blown sideways; 5 Bullseye = archer silhouette, arrow flies into a glowing target, ring pulse, +10). AllIndiaCard renders DailyScene; DAILY_STYLES renamed (default 2 World Cup, storage key rf.dailyStyle.v2). Lobby order: tiles → Weak Topic Sprint strip (rf-weak-sprint) → Cup Night → All India card → pill rf-all-india-style ('World Cup · Change style ›' → /rapid/daily-styles, testIDs rf-daily-style-N, rf-daily-style-card-N, rf-daily-style-use-N). Popup rf-daily-popup unchanged (shows the chosen scene). FLICKER: Trophy/Gang lists no longer pop in row by row (Pop removed from leaderboard rows, BoardRow, FriendFeed, Gang notices; Gang action icons no hop); the whole tab fades in once (FadeIn 200 ms, key=tab); leaderboard, feed and friend code are prefetched from the lobby so tabs open with data. WEAK TOPIC SPRINT: GET /api/rf/weak-topics (topics ranked by misses, >=2 misses = frequent, fallback to most-missed when <3; cards count; seconds 20), POST /api/rf/sessions {weak_topics:true, count} → mode weak_topics, label 'Weak Topic Sprint · N subtopics', only those subtopics, own still-missed cards first, then unseen. Frontend src/rapid/WeakSprint.tsx: lobby strip (one tap → /rapid/session?weak=1&n=<picked count>) + panel in the Weak cards sheet (rf-weak-sprint-panel, rf-weak-topic-N, rf-weak-sprint-start). Session header 'Weak Topic Sprint · subject · topic', summary 'Weak Topic Sprint', history row label. Tests: backend/tests/test_rf_weak_topics.py 2 pass."
