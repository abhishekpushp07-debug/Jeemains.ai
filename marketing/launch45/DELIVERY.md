# JEELIVE — launch-film delivery

Two independently composed45s/1080p/30fps films with originalinstrumentalmusic andHinglishcopy.27sRapidFire +12sAllIndia +6sbrand. Sourceandbriefeditablehere; mobileUIunchanged.

Currentbase:https://jeelive-feature-book--3o05z2vs.preview.emergentagent.com (futureforks: usecurrentEXPO_PUBLIC_BACKEND_URL).

**Preferred single-file download:** `/api/marketing/launch/launch-pack.zip` (15.1MB). Alwaysdownloadsasanattachment;extracttoobtainBOTHoriginalMP4s,nore-encoding. Noappinstallorloginneeded. ExplicitMP4`?download=1`nowreturnsbinaryattachmenttoavoidinvoluntaryinlineplayback. Defaultpreviewlinksunchanged.

Iteration54:58/58scopeddeliverytestsand3/3actualbrowserZIP/MP4downloadspass,includingarchiveCRC/individualSHAchecks. Userdevice/browserstillunknown;openinChrome/Safariifchatrestrictsdownloads,andrequesterrorcreenshotifstillblocked. Don'tclaimWhatsApporcodecascertainrootcause.

| Format | Preview | MP4 master |
|---|---|---|
| VerticalReel/Shorts1080×1920 | `/api/marketing/launch/vertical.webm` | `/api/marketing/launch/vertical.mp4?download=1` (7.72MB) |
| LandscapeYouTube1920×1080 | `/api/marketing/launch/landscape.webm` | `/api/marketing/launch/landscape.mp4?download=1` (7.37MB) |

Posters:`/api/marketing/launch/poster-vertical.jpg`and`poster-landscape.jpg`.

67publicdelivery/mediatestsPASS; full4videodecodes,1350frames, exact45sMP4, stereo48kHz, correctdimensions,faststart, audiofinite/non-silent, SHAchecks, playback/seekingVP9browserproof. ThisbrowsercannotdecodeH264/AAC(knowncodecerror), soWebMispreviewfallback. MP4mastersarevalidfornormalplayers/uploads; realphoneQAseparate. Notasignedappbuild orsocialpost.

Re-render:`python music.py`, `python render.py stills`, `python render.py vertical`, `python render.py landscape`. Renderbothformatsseparately; don'tcroponeintotheother. FFmpegrequiredonlyforofflineproduction, notruntimeAPI/nativeapp. WebMconversionuseslibvpx-vp9CRF30/cpu-used5/row-mt1 andlibopus128k. `python publish.py --publish`validatesformat/duration, deduplicatesSHA, uploadsnewUUIDobjects andverifiesreadbackbeforeupdatingpublicallowlist. UsesexistingmanagedstoragecredentialsSERVER-SIDEONLY.

Originalbrand/logo/avatarsareexistingownerapprovedassets; generatedbackdropsobjectstored. Musicisoriginalsynthesis; nocommercialtracksamplescopied. Conceptpreviewisillustrative,notlivestudentdata. No fabricatedranks/points/newscoreguarantee. Originalbrandtaglinepreserved.