# NEETLIVE.AI — independent, portable NEET data

Give the **entire `/app/neetlive/` folder** (or `exports/neetlive-content.zip`) to the future NEETLIVE.AI app/website builder.

## What is here
- `content/cards/`: independent NEET Physics, Chemistry and Biology Rapid Fire JSON files, including answer keys, explanations and original diagram definitions. **Private owner content — do not serve these raw files publicly.**
- `content/chapters.json`: the NEET subject/chapter catalogue; future subjects can be added here with their own card files.
- `content/diagrams.json`: original heart, nephron and flower vector schematics. They are NCERT-aligned learning illustrations, **not official NCERT scans**. The cards contain the complete vector definition so they travel without image URLs or external assets.
- `archive/`: text cards displaced to preserve the 90-card Biology chapter limit. They are not served in the active bank.
- `tools/prepare_content.py`: one-time bank fork; never overwrites existing NEET files. Physics/Chemistry start as independent copies of the existing curated conceptual bank, **not a newly validated NEET-specific syllabus**.
- `tools/export_bundle.py`: refreshes the transferable ZIP, manifest, checksums and integration notes.
- `integration/`: generated snapshots of the renderer/backend contracts for the next builder, not a standalone runnable app.

## Source of truth and live records
The current app reads NEET content directly from this folder. JEE stays in `backend/rapidfire/cards/` (Biology there is a legacy source copy and is no longer synced).

MongoDB holds the live, private progress; it is **not automatically saved inside a content ZIP**:
- `rf_cards`: `exam: "NEET"`, independent IDs (Physics/Chemistry IDs have `neet-` prefix; Biology IDs remain compatible with old sessions).
- `rf_sessions`, `rf_duels`, `rf_awards`, `rf_learning_events`: query `exam: "NEET"`.
- `rf_profiles`: NEET ranking counters under `exam_stats.NEET`. Currency, inventory and streak remain shared in JEELIVE; they must not be silently copied as NEET-only entitlements.
- Shared infrastructure (`rf_events`, session cookies, authentication) is not NEET content and is not exported.

Old Biology play is classified as NEET. Old Physics/Chemistry play did not record an exam; it stays in JEE rather than guessing NEET ownership. New play records the arena's exam choice on creation and cannot change group later.

## Refresh / transfer
Run from the repository root:

```
python neetlive/tools/export_bundle.py
```

For an authorized private migration only, export NEET learner records to a protected directory outside the public bundle:

```
python neetlive/tools/export_bundle.py --private-output /secure/neet-transfer
```

This requires the existing backend database environment. It exports pseudonymous user IDs and their NEET progress, never phone numbers, cookies, tokens or credentials. Keep it private and obtain appropriate permission before importing student records into a different service.

No NEET mock tests, payments, other subjects, NEETLIVE frontend or independent identity system have been invented. Add those to the future product explicitly. Pilot content still needs owner/subject-expert review. The existing unverified-phone identity model is not public-release security.