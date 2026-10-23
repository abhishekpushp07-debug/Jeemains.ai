# Auto-publish update
For current PDF/Word/Excel automatic publishing and results additions, read `/app/design_auto_publish.md`. It supersedes historical manual-gate instructions only; all existing navigation, Fit defaults and theme tokens remain unchanged.

# Current navigation/brand override — jeemains.ai (17 October 2026)

Read `/app/design_simple_navigation.md` for the complete approved current-phase addendum. Preserve all historical guidelines below. Latest user requirement overrides earlier readable-default advice: **FIT is the default and resets on every question change; do not persist Readable mode across questions**. Home has JEE Main, BITSAT and COMEDK cards; each exam has Mock Tests, Chapter-wise Tests and Results. Primary matte maroon remains #5C0025, Figtree/Roboto Mono, existing light/dark surfaces. 100% free student access may be prominent; future 60/75 and120+ concept overlap are labelled aspirational targets, never guaranteed predictions or measured outcomes. Actual AI/PYQ generation remains unfinished and must not be advertised as delivered.

---

{
  "product_flow_addendum": {
    "scope": {
      "goal": "Define a concrete PRODUCT-FIRST Studio flow for creating tests from two PDFs (Questions + Solutions), auto-organising, then scheduling + manual live/unlive, plus competitions + analytics. Preserve existing light/dark identity and matte maroon brand (#5C0025). Do not redesign landing/auth/player or phone-only login. Do not implement code—design + UI behavior only.",
      "non_goals": [
        "No multi-step forms that ask routine metadata (title/exam/duration/rights/approval) before organisation.",
        "No fabricated analytics (rank/percentile) when data is missing.",
        "No pretending uncertain pairings are correct—block readiness with actionable review/replace.",
        "No new marketing/landing visuals; no image-heavy UI. Use PDF tiles + Lucide icons."
      ]
    },
    "brand_personality": {
      "keywords": [
        "product-first",
        "fast",
        "no-nonsense",
        "trustworthy",
        "exam-serious",
        "teacher-efficient"
      ],
      "tone": "Minimal friction. The UI should feel like a tool: upload → organise → schedule → live. Every screen answers: ‘what’s happening, what’s blocked, what can I do next?’",
      "visual_style": "Matte surfaces, crisp borders, subtle shadows tinted by maroon. No loud gradients. Use restrained accent color only for primary actions and status."
    },
    "design_tokens": {
      "source_of_truth": {
        "existing_css": [
          "/app/frontend/src/index.css",
          "/app/frontend/src/App.css"
        ],
        "instruction": "Reuse existing tokens; do not introduce a new palette system. Extend only if a missing semantic token is required for new states (e.g., ‘info’)."
      },
      "colors": {
        "brand": {
          "primary_hex": "#5C0025",
          "primary_hsl_token": "--primary (338 100% 18%)",
          "primary_usage": [
            "Primary CTA buttons (Organise, Schedule, Go Live)",
            "Active tab/step indicator",
            "Key numbers in analytics (sparingly)"
          ]
        },
        "surfaces": {
          "page": "var(--page) / hsl(var(--background))",
          "card": "var(--surface-card) / hsl(var(--card))",
          "muted": "var(--surface-alt) / hsl(var(--muted))",
          "border": "var(--line) / hsl(var(--border))"
        },
        "text": {
          "primary": "var(--ink) / hsl(var(--foreground))",
          "muted": "var(--text-muted) / hsl(var(--muted-foreground))"
        },
        "status_semantics": {
          "success": "var(--success)",
          "warning": "var(--warning)",
          "danger": "var(--danger)",
          "review": "var(--review)",
          "focus_ring": "var(--focus-ring) / hsl(var(--ring))"
        },
        "studio_specific_status_badges": {
          "draft": {
            "bg": "var(--surface-alt)",
            "fg": "var(--text-muted)",
            "border": "var(--line)"
          },
          "organising": {
            "bg": "var(--warning-soft)",
            "fg": "var(--warning)",
            "border": "var(--warning-line)"
          },
          "blocked": {
            "bg": "var(--danger-soft)",
            "fg": "var(--danger)",
            "border": "var(--danger-line)"
          },
          "ready": {
            "bg": "var(--success-soft)",
            "fg": "var(--success)",
            "border": "var(--success-line)"
          },
          "scheduled": {
            "bg": "var(--brand-soft)",
            "fg": "var(--brand-text)",
            "border": "var(--brand-line)"
          },
          "live": {
            "bg": "var(--hero-dark)",
            "fg": "var(--on-brand)",
            "border": "var(--hero-dark)"
          }
        }
      },
      "radius_shadow": {
        "radius": {
          "global": "var(--radius) (0.875rem)",
          "card": "14px (matches .card)",
          "button": "8px (matches .btn)"
        },
        "shadow": {
          "tint": "var(--shadow-tint)",
          "hover": "0 4px 12px var(--shadow-tint)",
          "card": "0 8px 30px var(--shadow-tint) (already used in auth-card)"
        }
      },
      "gradients": {
        "policy": "Avoid gradients in Studio. If used at all, only as a thin decorative header strip (<20% viewport) using very mild neutrals + brand-soft; never on text-heavy areas.",
        "allowed_example": "background: linear-gradient(90deg, rgba(92,0,37,0.06), rgba(251,247,245,0.0));"
      }
    },
    "typography": {
      "fonts": {
        "ui": "Figtree (already in index.css)",
        "mono": "Roboto Mono (already in index.css)",
        "instruction": "Keep Figtree for continuity. Use mono only for file hashes, IDs, and timestamps."
      },
      "scale": {
        "h1": "text-4xl sm:text-5xl lg:text-6xl (use only on marketing/landing; Studio should cap at ~text-3xl equivalent)",
        "studio_page_title": "Tailwind: text-2xl sm:text-3xl font-semibold tracking-tight",
        "section_title": "text-lg font-semibold",
        "body": "text-sm sm:text-base",
        "meta": "text-xs text-muted-foreground",
        "numbers": "Use tabular-nums for timers, counts, and schedule times"
      }
    },
    "layout_and_grid": {
      "studio_overview": {
        "pattern": "Two-column on desktop: left = Create Test (primary), right = Recent/All tests list + competitions quick panel. Mobile collapses to single column with Create Test first.",
        "container": "Use existing .container widths; avoid centered text blocks.",
        "spacing": "Prefer generous spacing: gap-4/6/8; card padding p-5 sm:p-6; section spacing mt-6 sm:mt-8"
      },
      "organiser_detail": {
        "pattern": "Top: breadcrumb + title + status badge + actions. Body: left = progress + pairing preview; right = schedule panel (disabled until ready) + live/unlive controls.",
        "sticky": "On desktop, schedule panel can be sticky (top aligned below header). On mobile, schedule panel becomes a bottom sheet/drawer."
      },
      "mobile_390": {
        "rules": [
          "Primary CTA always visible without scrolling when possible (use sticky bottom action bar).",
          "Dropzones become full-width stacked cards.",
          "Tables become cards or horizontal scroll with ScrollArea.",
          "Minimum touch target: var(--touch-target) ~ 44px."
        ]
      }
    },
    "core_pages_and_flow": {
      "1_studio_overview": {
        "page_goal": "Single place to upload Questions PDF + Solutions PDF and start Organise. No extra questions.",
        "primary_card": {
          "name": "CreateTestCard",
          "layout": "Card with two equal dropzones side-by-side on desktop; stacked on mobile.",
          "dropzones": {
            "questions_pdf": {
              "label": "Questions PDF",
              "helper": "Drop PDF here or browse",
              "states": [
                "empty",
                "selected",
                "uploading",
                "uploaded",
                "error"
              ],
              "file_tile": "Show filename, size, last modified; allow Replace + Remove.",
              "data_testids": {
                "dropzone": "studio-create-test-questions-dropzone",
                "browse_button": "studio-create-test-questions-browse-button",
                "replace_button": "studio-create-test-questions-replace-button",
                "remove_button": "studio-create-test-questions-remove-button"
              }
            },
            "solutions_pdf": {
              "label": "Solutions PDF",
              "helper": "Drop PDF here or browse",
              "states": [
                "empty",
                "selected",
                "uploading",
                "uploaded",
                "error"
              ],
              "file_tile": "Same as questions.",
              "data_testids": {
                "dropzone": "studio-create-test-solutions-dropzone",
                "browse_button": "studio-create-test-solutions-browse-button",
                "replace_button": "studio-create-test-solutions-replace-button",
                "remove_button": "studio-create-test-solutions-remove-button"
              }
            }
          },
          "organise_cta": {
            "button_label": "Organise & Preview",
            "enabled_when": "Both PDFs uploaded successfully.",
            "secondary_link": "Use old Studio Editor (fallback)",
            "attestation_copy": "Inline text under CTA: ‘By uploading, you confirm you have rights to use these PDFs for your students.’ (no forced checkbox step)",
            "data_testids": {
              "organise_button": "studio-create-test-organise-button",
              "fallback_link": "studio-create-test-fallback-editor-link"
            }
          },
          "micro_interactions": [
            "Dropzone hover: border color shifts to brand-line; background to surface-alt (no scale).",
            "On file drop: show immediate file tile + optimistic ‘Queued’ badge.",
            "Upload progress: Progress component with percent + bytes; allow Cancel.",
            "Error: Alert component with actionable ‘Replace file’ button."
          ]
        },
        "test_list": {
          "list_goal": "Show existing tests with clear status: Draft/Organising/Blocked/Ready/Scheduled/Live.",
          "row_pattern": "Card rows (not dense table) with: title (derived), counts, schedule, status badge, actions.",
          "actions": [
            "Open",
            "Live/Unlive toggle (if allowed)",
            "Copy link (if live)"
          ]
        }
      },
      "2_organiser_detail_progress": {
        "page_goal": "Show organisation progress, pairing preview, and what’s blocking readiness. Only after ready, ask for start date/time.",
        "top_bar": {
          "elements": [
            "Breadcrumb",
            "Derived test name (editable optional, not required)",
            "Status badge",
            "Owner actions"
          ],
          "data_testids": {
            "breadcrumb": "studio-organiser-breadcrumb",
            "status_badge": "studio-organiser-status-badge",
            "rename_button": "studio-organiser-rename-button"
          }
        },
        "progress_block": {
          "visual": "Use Progress + step labels: Upload → Extract → Pair → Validate → Ready",
          "rule": "Never show 100% unless Ready. If blocked, show ‘Blocked’ badge and list blockers.",
          "data_testids": {
            "progress": "studio-organiser-progress",
            "stepper": "studio-organiser-stepper"
          }
        },
        "pairing_preview": {
          "principle": "Preview pairings without guessing. Unmatched questions/solutions must be explicit.",
          "ui": "Tabs: Matched / Unmatched Questions / Unmatched Solutions / Conflicts",
          "matched_view": "Paginated list with question #, detected topic (if available), solution page reference; click opens side-by-side preview modal/drawer.",
          "blocked_states": [
            "No solution found for question #X",
            "Multiple candidate solutions for question #X",
            "Low confidence pairing (below threshold)"
          ],
          "actions": [
            "Replace Questions PDF",
            "Replace Solutions PDF",
            "Open in old Studio Editor (fallback)",
            "Download pairing CSV (optional)"
          ],
          "data_testids": {
            "tabs": "studio-organiser-pairing-tabs",
            "matched_tab": "studio-organiser-pairing-tab-matched",
            "unmatched_questions_tab": "studio-organiser-pairing-tab-unmatched-questions",
            "unmatched_solutions_tab": "studio-organiser-pairing-tab-unmatched-solutions",
            "conflicts_tab": "studio-organiser-pairing-tab-conflicts",
            "replace_questions": "studio-organiser-replace-questions-button",
            "replace_solutions": "studio-organiser-replace-solutions-button"
          }
        },
        "schedule_panel": {
          "rule": "Schedule inputs are disabled/hidden until status == Ready.",
          "when_ready": {
            "fields": [
              "Start date (Calendar)",
              "Start time (Select or Input with validation)",
              "Timezone label fixed: Asia/Kolkata"
            ],
            "cta": "Schedule",
            "data_testids": {
              "start_date": "studio-schedule-start-date",
              "start_time": "studio-schedule-start-time",
              "timezone_label": "studio-schedule-timezone-label",
              "schedule_button": "studio-schedule-submit-button"
            }
          },
          "after_scheduled": {
            "show": [
              "Scheduled for …",
              "Edit schedule",
              "Unschedule"
            ],
            "data_testids": {
              "scheduled_summary": "studio-schedule-summary",
              "edit_button": "studio-schedule-edit-button",
              "unschedule_button": "studio-schedule-unschedule-button"
            }
          }
        },
        "live_unlive_controls": {
          "rule": "Manual live/unlive only. Live toggle is disabled unless Ready AND (if scheduled) current time >= start time.",
          "ui": "Switch with confirmation AlertDialog when going Live/Unlive.",
          "copy": {
            "live": "Students can attempt now.",
            "unlive": "Students can’t start new attempts. Existing attempts continue per policy (show exact behavior)."
          },
          "data_testids": {
            "live_switch": "studio-live-toggle-switch",
            "live_confirm": "studio-live-toggle-confirm-button",
            "unlive_confirm": "studio-unlive-toggle-confirm-button"
          }
        }
      },
      "3_student_competitions": {
        "page_goal": "List competitions/tests students can join; show time-gated states and leaderboard after window.",
        "list_cards": {
          "fields": [
            "Test name",
            "Starts at (IST)",
            "Status badge (Upcoming/Live/Ended)",
            "CTA"
          ],
          "cta_rules": {
            "upcoming": "Show ‘Starts in …’ + disabled Attempt button",
            "live": "Show Attempt button",
            "ended": "Show View Results (if available)"
          },
          "data_testids": {
            "competition_list": "student-competitions-list",
            "competition_card": "student-competitions-card",
            "attempt_button": "student-competitions-attempt-button"
          }
        },
        "detail": {
          "solutions_embargo": "Hide solutions until competition window ends. Show lock copy + unlock time.",
          "leaderboard": "Table with rank only when computed; otherwise show ‘Processing’ state. Never fabricate percentile.",
          "data_testids": {
            "solutions_lock": "student-competition-solutions-locked",
            "leaderboard_table": "student-competition-leaderboard-table"
          }
        }
      },
      "4_results_analysis_additions": {
        "goal": "Add evidence-based analysis context to existing Results without changing core player/report continuity.",
        "modules": [
          "Accuracy vs Time scatter (if data exists)",
          "Subject-wise breakdown",
          "Question difficulty buckets (only if inferred with confidence; else omit)",
          "Recovery indicator: ‘Offline saved at …, synced at …’"
        ],
        "empty_states": {
          "rule": "If data missing, show neutral empty state with what will appear once enough attempts exist.",
          "copy_example": "Not enough attempts to compute percentile. Keep practicing—this section will unlock after 50+ attempts."
        }
      }
    },
    "excel_import_addendum": {
      "goal": "Add Excel import alongside PDF so staff can directly import typed questions/options/answers/solutions without image extraction. Must be deterministic, bounded parsing (no guessed keys), and incremental (no redesign).",
      "supported_inputs": {
        "modes": [
          {
            "mode": "single_workbook",
            "label": "Excel workbook (Questions + Solutions)",
            "description": "One .xlsx containing a Questions sheet and a Solutions sheet (or a single combined sheet)."
          },
          {
            "mode": "two_workbooks",
            "label": "Two Excel files (Questions + Solutions)",
            "description": "Upload questions.xlsx and solutions.xlsx separately; pairing happens by question_id or question_no."
          }
        ],
        "file_types": [
          ".xlsx"
        ],
        "non_goals": [
          "No OCR inside Excel images.",
          "No auto-detecting arbitrary column names beyond a strict allowlist.",
          "No importing macros (.xlsm) in v1."
        ]
      },
      "studio_overview_ui_extension": {
        "placement": "Inside existing CreateTestCard, add a compact segmented control above dropzones: ‘PDF’ | ‘Excel’. Default stays ‘PDF’.",
        "segmented_control": {
          "component": "Tabs (shadcn) or ToggleGroup (shadcn)",
          "data_testids": {
            "mode_tabs": "studio-create-test-import-mode-tabs",
            "pdf_tab": "studio-create-test-import-mode-pdf",
            "excel_tab": "studio-create-test-import-mode-excel"
          }
        },
        "excel_dropzones": {
          "layout": "Mirror the PDF dual-dropzone layout. If single_workbook selected, show one dropzone; if two_workbooks selected, show two dropzones.",
          "data_testids": {
            "single_workbook_dropzone": "studio-create-test-excel-workbook-dropzone",
            "questions_workbook_dropzone": "studio-create-test-excel-questions-dropzone",
            "solutions_workbook_dropzone": "studio-create-test-excel-solutions-dropzone",
            "template_download_button": "studio-create-test-excel-template-download-button"
          },
          "helper_copy": [
            "Import typed questions/options/answer/solution from Excel.",
            "Use the template to avoid column mismatch.",
            "We will show row-level errors before anything goes live."
          ]
        },
        "primary_cta": {
          "label": "Validate & Preview",
          "enabled_when": "Required Excel file(s) uploaded successfully.",
          "data_testid": "studio-create-test-excel-validate-button"
        }
      },
      "template_download": {
        "principle": "Template is the contract. Parsing is strict: only template headers are accepted.",
        "ui": {
          "component": "Button (secondary) + Tooltip",
          "copy": "Download Excel template",
          "data_testid": "studio-excel-template-download"
        },
        "template_variants": [
          {
            "name": "combined_sheet",
            "sheets": [
              "Questions"
            ],
            "when_to_use": "Small sets or when solutions are short.",
            "required_columns": [
              "question_id",
              "question_no",
              "subject",
              "question_text",
              "option_a",
              "option_b",
              "option_c",
              "option_d",
              "correct_option",
              "solution_text"
            ],
            "optional_columns": [
              "topic",
              "difficulty",
              "marks",
              "negative_marks",
              "source"
            ],
            "rules": [
              "correct_option must be one of: A, B, C, D (uppercase).",
              "question_id must be unique if provided.",
              "question_no must be integer >= 1."
            ]
          },
          {
            "name": "two_sheets",
            "sheets": [
              "Questions",
              "Solutions"
            ],
            "when_to_use": "Long solutions or when solutions are maintained separately.",
            "questions_required_columns": [
              "question_id",
              "question_no",
              "subject",
              "question_text",
              "option_a",
              "option_b",
              "option_c",
              "option_d",
              "correct_option"
            ],
            "solutions_required_columns": [
              "question_id",
              "question_no",
              "solution_text"
            ],
            "pairing_rule": "Pair by question_id if present in both; else pair by question_no. If both present but disagree → conflict.",
            "rules": [
              "No fuzzy matching.",
              "If a question has no solution row → Blocked.",
              "If multiple solution rows match same question_id/question_no → Conflict."
            ]
          }
        ]
      },
      "validation_and_preview": {
        "principle": "Deterministic import with row-level errors. Nothing is created as Ready until all blocking errors are resolved.",
        "preview_layout": {
          "pattern": "Same Organiser Detail page, but PairingPreviewTabs becomes ‘Rows’ preview.",
          "tabs": [
            "Valid",
            "Errors",
            "Warnings"
          ],
          "right_panel": "SchedulePanel remains locked until Valid rows cover 100% of required questions.",
          "data_testids": {
            "rows_tabs": "studio-excel-preview-tabs",
            "errors_tab": "studio-excel-preview-tab-errors",
            "warnings_tab": "studio-excel-preview-tab-warnings",
            "valid_tab": "studio-excel-preview-tab-valid"
          }
        },
        "error_table": {
          "component": "Table + ScrollArea (shadcn)",
          "columns": [
            "row",
            "sheet",
            "field",
            "message",
            "action"
          ],
          "actions": [
            "Download error report (.csv)",
            "Replace Excel file",
            "Open template"
          ],
          "data_testids": {
            "error_table": "studio-excel-error-table",
            "download_error_report": "studio-excel-download-error-report-button",
            "replace_excel": "studio-excel-replace-file-button"
          }
        },
        "blocking_errors": [
          "Missing required column",
          "Empty question_text",
          "Missing any of option_a/option_b/option_c/option_d",
          "correct_option not in {A,B,C,D}",
          "Duplicate question_id",
          "Unpaired solution (two-sheet mode)",
          "Conflicting pair (question_id vs question_no mismatch)"
        ],
        "warnings": [
          "Very long question_text (> N chars) — may affect mobile readability",
          "solution_text empty (allowed only if solutions embargoed / optional per test policy)",
          "subject missing — will default to ‘General’ (only if product allows; otherwise treat as blocking)"
        ]
      },
      "imported_question_rendering_rules": {
        "principle": "Excel content is text-first. Preserve line breaks. Support basic math via existing KaTeX pipeline if present.",
        "question_text": {
          "render": "Use existing .math-text styling; preserve \\n as line breaks.",
          "sanitization": "Escape HTML; do not render raw HTML from Excel."
        },
        "options": {
          "layout": "Same 2-column options grid on desktop; 1-column on mobile 390px.",
          "data_testid_pattern": "question-option-{questionNo}-{optionKey} (e.g., question-option-12-a)"
        },
        "solution": {
          "embargo": "Follow existing competition embargo rules: hide solution_text until competition ends.",
          "data_testid": "student-solution-text"
        }
      },
      "components": {
        "component_path": {
          "shadcn_primary": [
            "/app/frontend/src/components/ui/tabs.jsx",
            "/app/frontend/src/components/ui/toggle-group.jsx",
            "/app/frontend/src/components/ui/button.jsx",
            "/app/frontend/src/components/ui/card.jsx",
            "/app/frontend/src/components/ui/alert.jsx",
            "/app/frontend/src/components/ui/table.jsx",
            "/app/frontend/src/components/ui/scroll-area.jsx",
            "/app/frontend/src/components/ui/tooltip.jsx",
            "/app/frontend/src/components/ui/progress.jsx",
            "/app/frontend/src/components/ui/dialog.jsx",
            "/app/frontend/src/components/ui/drawer.jsx",
            "/app/frontend/src/components/ui/input.jsx"
          ]
        },
        "studio_custom_components_to_create": [
          {
            "name": "ExcelImportMode",
            "purpose": "Segmented control + dropzones + template download + validate CTA.",
            "file": "frontend/src/components/studio/ExcelImportMode.js",
            "export": "named",
            "data_testids": [
              "studio-create-test-import-mode-tabs",
              "studio-create-test-excel-validate-button"
            ]
          },
          {
            "name": "ExcelRowErrorsTable",
            "purpose": "Row-level errors/warnings table with download report action.",
            "file": "frontend/src/components/studio/ExcelRowErrorsTable.js",
            "export": "named",
            "data_testids": [
              "studio-excel-error-table",
              "studio-excel-download-error-report-button"
            ]
          }
        ]
      },
      "api_contract_notes_for_main_agent": {
        "principle": "No guessed keys. Backend should reject unknown headers and return structured errors.",
        "suggested_endpoints": [
          {
            "method": "GET",
            "path": "/api/studio/import/excel/template",
            "returns": "xlsx file (template variant selectable via query param)"
          },
          {
            "method": "POST",
            "path": "/api/studio/import/excel/validate",
            "returns": "{ summary: { total_rows, valid_rows, error_rows, warning_rows }, errors: [...], warnings: [...], preview: [...] }"
          },
          {
            "method": "POST",
            "path": "/api/studio/import/excel/commit",
            "returns": "Creates/updates test draft only when validate passes; returns organiser_id"
          }
        ],
        "error_shape": {
          "fields": [
            "row",
            "sheet",
            "field",
            "code",
            "message"
          ],
          "ui_mapping": "Map code → human message; keep message short; show field + row always."
        }
      },
      "data_testid_requirements": {
        "rule": "All Excel import controls and error outputs must be testable.",
        "minimum": [
          "studio-create-test-import-mode-tabs",
          "studio-create-test-excel-workbook-dropzone",
          "studio-create-test-excel-template-download-button",
          "studio-create-test-excel-validate-button",
          "studio-excel-error-table",
          "studio-excel-download-error-report-button"
        ]
      },
      "instructions_to_main_agent": [
        "Do NOT change existing maroon tokens or typography; Excel import is an additive mode inside CreateTestCard.",
        "Keep parsing strict: accept only template headers; reject unknown/missing headers with row-level errors.",
        "Implement deterministic pairing by question_id then question_no; no fuzzy matching.",
        "Reuse Organiser Detail page for preview; schedule/live gates remain identical to PDF flow.",
        "All new React components must be .js (not .tsx) and include data-testid on interactive elements.",
        "No new images or visual identity changes."
      ]
    },
    "components": {
      "component_path": {
        "shadcn_primary": [
          "/app/frontend/src/components/ui/button.jsx",
          "/app/frontend/src/components/ui/card.jsx",
          "/app/frontend/src/components/ui/badge.jsx",
          "/app/frontend/src/components/ui/progress.jsx",
          "/app/frontend/src/components/ui/tabs.jsx",
          "/app/frontend/src/components/ui/dialog.jsx",
          "/app/frontend/src/components/ui/drawer.jsx",
          "/app/frontend/src/components/ui/alert.jsx",
          "/app/frontend/src/components/ui/alert-dialog.jsx",
          "/app/frontend/src/components/ui/switch.jsx",
          "/app/frontend/src/components/ui/calendar.jsx",
          "/app/frontend/src/components/ui/select.jsx",
          "/app/frontend/src/components/ui/scroll-area.jsx",
          "/app/frontend/src/components/ui/separator.jsx",
          "/app/frontend/src/components/ui/table.jsx",
          "/app/frontend/src/components/ui/tooltip.jsx",
          "/app/frontend/src/components/ui/sonner.jsx"
        ]
      },
      "studio_custom_components_to_create": {
        "note": "Create as React .js components (NOT .tsx). Named exports for components; pages default export.",
        "list": [
          {
            "name": "DualPdfDropzone",
            "purpose": "Two dropzones with shared validation + progress + replace/remove.",
            "uses": [
              "Card",
              "Button",
              "Progress",
              "Alert"
            ],
            "data_testids": [
              "studio-create-test-questions-dropzone",
              "studio-create-test-solutions-dropzone"
            ]
          },
          {
            "name": "OrganiserStepper",
            "purpose": "Upload→Extract→Pair→Validate→Ready stepper with blocked state.",
            "uses": [
              "Progress",
              "Badge",
              "Tooltip"
            ]
          },
          {
            "name": "PairingPreviewTabs",
            "purpose": "Matched/Unmatched/Conflicts views with actionable blockers.",
            "uses": [
              "Tabs",
              "Table or card list",
              "ScrollArea"
            ]
          },
          {
            "name": "SchedulePanel",
            "purpose": "Calendar + time select + IST label; disabled until Ready.",
            "uses": [
              "Calendar",
              "Select",
              "Button",
              "AlertDialog"
            ]
          },
          {
            "name": "LiveToggle",
            "purpose": "Manual live/unlive with confirmation and clear policy copy.",
            "uses": [
              "Switch",
              "AlertDialog",
              "Badge"
            ]
          }
        ]
      }
    },
    "states_and_error_handling": {
      "upload": {
        "validation": [
          "PDF only",
          "max size (define in UI copy)",
          "show filename + size"
        ],
        "errors": {
          "network": "Alert: ‘Upload failed. Retry or replace file.’",
          "parse_failed": "Alert: ‘We couldn’t read this PDF. Try exporting again or upload a clearer scan.’",
          "mismatch": "Alert: ‘This looks like solutions in the Questions slot (or vice versa). Please swap/replace.’ (only if detection confidence high)"
        }
      },
      "organisation": {
        "blocked": {
          "principle": "Blocked means user action required. Provide the action in the same panel.",
          "examples": [
            "Unmatched questions > 0 → show ‘Replace Solutions PDF’ primary action",
            "Conflicts > 0 → show ‘Review conflicts’ action"
          ]
        },
        "ready": {
          "principle": "Ready means schedule panel unlocks. Still allow optional edits, but never force them."
        }
      },
      "live": {
        "gates": [
          "Cannot go Live if Blocked/Organising",
          "If Scheduled and start time not reached: disable switch + show tooltip ‘Available at … IST’"
        ]
      }
    },
    "motion_microinteractions": {
      "principles": [
        "No ‘transition: all’. Only transition background-color, border-color, box-shadow, opacity.",
        "Use subtle elevation on hover for cards/rows.",
        "Use skeletons for loading lists; progress for long tasks."
      ],
      "recommended": {
        "hover": "transition-[background-color,border-color,box-shadow] duration-200",
        "press": "active:translate-y-[1px] (only on buttons)",
        "loading": "Skeleton + Progress; avoid spinners-only for >2s tasks"
      },
      "optional_library": {
        "name": "framer-motion",
        "use_cases": [
          "organiser step transitions",
          "drawer entrance",
          "list item appear"
        ],
        "install": "npm i framer-motion",
        "note": "Keep motion minimal; Studio is productivity-first."
      }
    },
    "accessibility": {
      "requirements": [
        "All interactive elements must have visible focus (already via :focus-visible).",
        "Dropzones must be keyboard operable (Enter/Space triggers file picker).",
        "Status conveyed by text + icon, not color alone.",
        "Use aria-live polite region for upload/progress updates.",
        "Ensure contrast on maroon buttons with white text (already --on-brand)."
      ]
    },
    "data_testid_schema": {
      "convention": "kebab-case, role-based, stable. Prefix by area: studio-, student-, results-.",
      "examples": [
        "studio-create-test-organise-button",
        "studio-organiser-pairing-tab-conflicts",
        "studio-schedule-submit-button",
        "student-competitions-attempt-button",
        "results-analysis-subject-breakdown-card"
      ]
    },
    "instructions_to_main_agent": [
      "Preserve existing tokens in index.css/App.css; do not change global identity.",
      "Implement the new Studio flow as: Studio Overview → Organiser Detail (progress + pairing preview) → Schedule (only after Ready) → Manual Live/Unlive.",
      "Do not add extra required metadata steps. Derived title/exam/duration can be shown read-only with optional edit.",
      "Use shadcn/ui components from /frontend/src/components/ui (JS versions). Avoid raw HTML dropdowns/calendars.",
      "Every button/input/toggle/tab trigger must include data-testid.",
      "Competitions: enforce solutions embargo until end; leaderboard shows only computed values; no fake percentile/rank.",
      "Keep old advanced Studio Editor accessible as a secondary fallback link; do not remove it.",
      "No mocked integrations: if an API isn’t ready, show ‘Coming soon’ only if backed by real feature flag; otherwise keep UI hidden/disabled with clear copy."
    ]
  },
  "results_analytics_offline_safety_addendum": {
    "scope": {
      "goal": "Extend existing Results with an Analytics Workspace + Offline Safety behaviors. This is an addendum only: preserve matte maroon theme (#5C0025), existing Results summary/review UI, and existing navigation. No new images. No decorative charts without evidence.",
      "non_goals": [
        "No redesign of Results header/summary cards.",
        "No new global palette/typography changes.",
        "No analytics values shown as 0 when telemetry is missing—must show ‘Unavailable’ with reason.",
        "No cohort percentile/rank unless cohort size >= 100 (authoritative rule)."
      ]
    },
    "information_architecture": {
      "entry_point": {
        "placement": "Inside existing Results page, add a new section below the current summary: ‘Analytics workspace’.",
        "pattern": "Tabs (shadcn) with 3 tabs: Overview, Metrics ledger, Offline & drafts.",
        "data_testids": {
          "tabs": "results-analytics-tabs",
          "tab_overview": "results-analytics-tab-overview",
          "tab_ledger": "results-analytics-tab-ledger",
          "tab_offline": "results-analytics-tab-offline"
        }
      },
      "drillthrough_rule": {
        "principle": "All analytics must drill through to existing question review (the canonical evidence). Do not create a parallel review UI.",
        "interaction": "Clicking any metric row or chart point opens an Evidence Drawer with the exact question list filtered to the evidence set.",
        "state_preservation": "Keep current tab + filters when opening/closing drawer. Do not navigate away unless user clicks ‘Open full review’."
      }
    },
    "metric_registry_A01_A60": {
      "principle": "Metrics are registered and displayed only if backed by stored telemetry. If missing, show ‘Unavailable’ and explain what evidence is required.",
      "display_contract": {
        "must_show": [
          "metric_id (A01…A60)",
          "metric_name",
          "value OR Unavailable",
          "unit",
          "evidence_count (n)",
          "time_window (attempt scope)",
          "cohort_scope (if applicable)",
          "last_computed_at"
        ],
        "never_show": [
          "fake zeros",
          "percentile/rank when cohort < 100",
          "difficulty buckets unless difficulty tags are approved and present"
        ]
      },
      "ui_modules": {
        "overview_cards": {
          "pattern": "A compact 2x2 grid of Cards on desktop, 1-column on mobile. Each card is a metric tile with a ‘View evidence’ link.",
          "card_states": {
            "available": "Show value + unit + n evidence.",
            "unavailable": "Show ‘Unavailable’ + short reason + ‘What’s needed’ link opening Evidence Drawer in ‘Requirements’ mode."
          },
          "data_testids": {
            "grid": "results-analytics-overview-grid",
            "metric_card": "results-analytics-metric-card",
            "metric_view_evidence": "results-analytics-metric-view-evidence-button"
          }
        },
        "metrics_ledger": {
          "pattern": "Table (shadcn) with sticky header inside ScrollArea. Rows are clickable if drillthrough is supported.",
          "columns": [
            "Metric",
            "Value",
            "Unit",
            "Evidence (n)",
            "Scope",
            "Updated",
            "Status"
          ],
          "row_affordance": "If drillable: show chevron icon + hover background. If not drillable: no chevron and cursor-default.",
          "data_testids": {
            "table": "results-analytics-ledger-table",
            "row": "results-analytics-ledger-row",
            "filter_input": "results-analytics-ledger-filter-input"
          }
        }
      }
    },
    "evidence_drawer": {
      "purpose": "Explain ‘why this metric is what it is’ with traceable evidence. Also used to explain why a metric is unavailable.",
      "component": "Drawer (shadcn) on mobile; Dialog or Sheet on desktop (prefer Sheet if available; otherwise Dialog).",
      "layout": {
        "header": [
          "Metric ID + name",
          "Scope chips (Attempt, Subject, Topic, Time window)",
          "Status badge (Available/Unavailable)",
          "Actions: Copy link, Open full review"
        ],
        "body_sections": [
          "Definition (plain language)",
          "Calculation (short formula + assumptions)",
          "Evidence list (questions) OR Requirements list (what telemetry is missing)",
          "Notes (edge cases, exclusions)"
        ]
      },
      "evidence_list": {
        "pattern": "Use existing question list component if present; otherwise a Table/Card list with: Q#, outcome, time_spent, subject/topic tags, ‘Open’ button.",
        "drillthrough": "Open button navigates to existing Results question review anchored to that question.",
        "data_testids": {
          "drawer": "results-evidence-drawer",
          "copy_link": "results-evidence-copy-link-button",
          "open_full_review": "results-evidence-open-full-review-button",
          "evidence_list": "results-evidence-question-list",
          "evidence_row": "results-evidence-question-row"
        }
      },
      "accessibility": {
        "rules": [
          "Drawer/Dialog must include a title element (can be sr-only).",
          "Focus trap must work; Esc closes.",
          "Announce drawer open/close via aria-live polite region."
        ]
      }
    },
    "analytics_modules_allowed": {
      "rule": "Only show modules when their required evidence exists. Otherwise show an empty state with ‘Unavailable’ and a reason.",
      "modules": [
        {
          "id": "A-TimeAccuracy",
          "name": "Accuracy vs Time",
          "allowed_visual": "Scatter plot ONLY if per-question time_spent exists for enough questions; otherwise show table summary.",
          "no_decorative_charts": "If fewer than 20 evidence points, prefer table/list over chart.",
          "data_testids": {
            "card": "results-analytics-accuracy-time-card",
            "chart": "results-analytics-accuracy-time-chart",
            "empty": "results-analytics-accuracy-time-empty"
          }
        },
        {
          "id": "A-SubjectBreakdown",
          "name": "Subject breakdown",
          "allowed_visual": "Stacked bars or simple table; must match existing subject taxonomy.",
          "data_testids": {
            "card": "results-analytics-subject-breakdown-card",
            "table": "results-analytics-subject-breakdown-table"
          }
        },
        {
          "id": "A-TopicBreakdown",
          "name": "Topic breakdown",
          "allowed_visual": "Table first; optional bar chart if topic tags exist and are approved.",
          "data_testids": {
            "card": "results-analytics-topic-breakdown-card",
            "table": "results-analytics-topic-breakdown-table"
          }
        }
      ]
    },
    "cohort_and_competition_rules": {
      "cohort_minimum": 100,
      "rule": "Any cohort-based metric (percentile, rank, cohort average) must be hidden or marked Unavailable unless cohort_size >= 100.",
      "ui_copy": {
        "unavailable_example": "Unavailable: cohort size is below 100 for this test window."
      },
      "data_testids": {
        "cohort_badge": "results-analytics-cohort-badge",
        "cohort_unavailable": "results-analytics-cohort-unavailable"
      }
    },
    "offline_safety_and_draft_recovery": {
      "principle": "Never lose a student’s answers. Offline-first behavior must be explicit, testable, and reversible.",
      "player_save_states": {
        "states": [
          {
            "key": "synced",
            "label": "Saved",
            "meaning": "Server has confirmed receipt.",
            "ui": "Green text + timestamp."
          },
          {
            "key": "pending",
            "label": "Saving…",
            "meaning": "Queued locally; will sync when online.",
            "ui": "Amber text + ‘Offline safe’ hint."
          },
          {
            "key": "offline",
            "label": "Offline",
            "meaning": "No network; answers stored locally.",
            "ui": "Amber badge + ‘We’ll sync automatically’."
          },
          {
            "key": "conflict",
            "label": "Needs review",
            "meaning": "Local draft differs from server state.",
            "ui": "Red badge + ‘Resolve’ button opens dialog."
          }
        ],
        "data_testids": {
          "save_status": "player-save-status",
          "save_status_timestamp": "player-save-status-timestamp",
          "resolve_conflict": "player-save-conflict-resolve-button"
        }
      },
      "draft_quarantine_recovery": {
        "rule": "If an attempt ends unexpectedly (tab close/crash), keep a quarantined draft scoped to the profile until user decides.",
        "entry_points": [
          "On next app open: show a non-blocking banner ‘Recovered draft available’.",
          "On Results page: show ‘Offline & drafts’ tab with a Drafts list."
        ],
        "drafts_list": {
          "fields": [
            "Test",
            "Attempt started",
            "Last saved locally",
            "Questions answered",
            "Actions"
          ],
          "actions": [
            "Resume",
            "Discard"
          ],
          "data_testids": {
            "banner": "draft-recovery-banner",
            "open": "draft-recovery-open-button",
            "list": "draft-recovery-list",
            "resume": "draft-recovery-resume-button",
            "discard": "draft-recovery-discard-button"
          }
        }
      },
      "profile_scoped_signout_dialog": {
        "rule": "On sign out, if there is any pending draft/unsynced answers for this profile, show a blocking dialog: Keep draft or Discard.",
        "component": "AlertDialog (shadcn)",
        "copy": {
          "title": "Unsynced answers found",
          "body": "You have answers saved on this device that haven’t synced yet. Choose what to do before signing out.",
          "keep": "Keep draft on this device",
          "discard": "Discard draft and sign out"
        },
        "data_testids": {
          "dialog": "signout-draft-dialog",
          "keep": "signout-draft-keep-button",
          "discard": "signout-draft-discard-button"
        }
      }
    },
    "typed_option_math_fix": {
      "goal": "Ensure typed options (A/B/C/D) render math consistently and do not break layout on mobile.",
      "rules": [
        "Options must wrap: use existing .math-text with overflow-wrap:anywhere.",
        "KaTeX blocks must be horizontally scrollable (already via .katex-display overflow-x:auto).",
        "Never shrink option index below 24px; keep touch target >= 44px height.",
        "If option contains long inline math, allow line breaks at operators where possible (KaTeX default) and provide horizontal scroll fallback."
      ],
      "data_testids": {
        "option": "question-option",
        "option_math": "question-option-math"
      }
    },
    "components": {
      "component_path": {
        "shadcn_primary": [
          "/app/frontend/src/components/ui/tabs.jsx",
          "/app/frontend/src/components/ui/card.jsx",
          "/app/frontend/src/components/ui/table.jsx",
          "/app/frontend/src/components/ui/scroll-area.jsx",
          "/app/frontend/src/components/ui/badge.jsx",
          "/app/frontend/src/components/ui/drawer.jsx",
          "/app/frontend/src/components/ui/dialog.jsx",
          "/app/frontend/src/components/ui/alert-dialog.jsx",
          "/app/frontend/src/components/ui/button.jsx",
          "/app/frontend/src/components/ui/input.jsx",
          "/app/frontend/src/components/ui/separator.jsx",
          "/app/frontend/src/components/ui/skeleton.jsx",
          "/app/frontend/src/components/ui/tooltip.jsx",
          "/app/frontend/src/components/ui/sonner.jsx"
        ]
      },
      "custom_components_to_create_js": [
        {
          "name": "ResultsAnalyticsWorkspace",
          "file": "frontend/src/components/results/ResultsAnalyticsWorkspace.js",
          "purpose": "Tabs wrapper + Overview cards + Metrics ledger + Offline & drafts tab.",
          "data_testids": [
            "results-analytics-tabs",
            "results-analytics-ledger-table"
          ]
        },
        {
          "name": "MetricEvidenceDrawer",
          "file": "frontend/src/components/results/MetricEvidenceDrawer.js",
          "purpose": "Evidence Drawer/Sheet with definition, calculation, evidence list, and requirements mode.",
          "data_testids": [
            "results-evidence-drawer",
            "results-evidence-question-list"
          ]
        },
        {
          "name": "DraftRecoveryPanel",
          "file": "frontend/src/components/offline/DraftRecoveryPanel.js",
          "purpose": "List quarantined drafts + resume/discard actions.",
          "data_testids": [
            "draft-recovery-list",
            "draft-recovery-resume-button"
          ]
        },
        {
          "name": "SignoutDraftGuardDialog",
          "file": "frontend/src/components/auth/SignoutDraftGuardDialog.js",
          "purpose": "Blocking keep/discard dialog when signing out with pending drafts.",
          "data_testids": [
            "signout-draft-dialog",
            "signout-draft-keep-button",
            "signout-draft-discard-button"
          ]
        }
      ]
    },
    "data_testid_minimums": {
      "rule": "All interactive and key informational elements must include data-testid.",
      "minimum": [
        "results-analytics-tabs",
        "results-analytics-ledger-table",
        "results-evidence-drawer",
        "results-evidence-open-full-review-button",
        "results-analytics-cohort-unavailable",
        "draft-recovery-banner",
        "draft-recovery-resume-button",
        "signout-draft-dialog",
        "player-save-status"
      ]
    },
    "instructions_to_main_agent": [
      "This is an addendum only—do not restyle existing Results components; only add the Analytics workspace section and drawers/dialogs.",
      "Implement metric registry A01–A60 as a data-driven list; render only metrics with evidence. Missing telemetry must show ‘Unavailable’ with reason.",
      "Cohort-based metrics must enforce cohort_size >= 100; otherwise hide/mark Unavailable.",
      "All analytics drillthrough must open Evidence Drawer and link to existing question review; do not duplicate review UI.",
      "Offline safety: implement quarantined draft recovery + profile-scoped signout guard dialog; never discard drafts silently.",
      "All new React components must be .js (not .tsx) and include data-testid on buttons/inputs/tabs/rows and key values.",
      "No new images; no decorative charts without evidence; prefer tables when data is sparse."
    ]
  },
  "guide04_confidence_calibration_addendum": {
    "scope": {
      "goal": "Add a minimal, optional confidence-probability collection to the existing Player, plus post-result calibration analytics and mistake-review workflow. Preserve existing matte maroon identity (#5C0025), existing Player layout, and strict scoring/submission contracts. No new navigation. No new Studio credential flows.",
      "non_goals": [
        "Do not change metric IDs, formulas, or thresholds from guide04/source04.",
        "Do not delay scoring/submission; confidence collection must be optional and non-blocking.",
        "Do not invent confidence values or diagnosis categories; only collect what user explicitly provides.",
        "Do not add routine review questions (per user choice)."
      ]
    },
    "visual_constraints": {
      "identity": "No theme redesign. Keep existing Figtree + maroon tokens + light/dark.",
      "mobile_first": "Phone-only student login; design for 390px width and 44px touch targets.",
      "placement_rule": "Confidence UI must live inside existing Player question card (small panel) and Results review controls; no new top-level pages.",
      "embargo_rule": "Competition embargo rules remain: do not reveal solutions early; confidence UI must not leak correctness."
    },
    "player_confidence_panel": {
      "principle": "Optional, fast, and skippable. The student can answer without ever touching confidence.",
      "when_shown": {
        "default": "Collapsed (shows a one-line prompt + optional toggle).",
        "auto_expand": "Never auto-expand on first render; only expand when user taps.",
        "hide_when": [
          "question is unattempted and user is scrolling quickly (avoid sticky overlays)"
        ]
      },
      "ui": {
        "component": "Collapsible (shadcn) inside the question card, below options and above navigation.",
        "collapsed_row": {
          "copy": "Add confidence (optional)",
          "right_meta": "‘Takes 1 tap’",
          "icon": "Lucide ChevronDown",
          "data_testids": {
            "toggle": "player-confidence-collapsible-toggle",
            "summary": "player-confidence-collapsible-summary"
          }
        },
        "expanded_content": {
          "prompt": "How likely is your answer correct?",
          "input": {
            "primary": {
              "type": "Slider (shadcn)",
              "range": "0.50 → 1.00 (step 0.05)",
              "default_value": "No default; show placeholder state until user moves slider.",
              "labels": [
                "50%",
                "70%",
                "80%",
                "90%",
                "100%"
              ],
              "helper": "Only rate if you didn’t change your answer after seeing hints. (We exclude changed responses from calibration.)",
              "data_testids": {
                "slider": "player-confidence-slider",
                "value": "player-confidence-value"
              }
            },
            "secondary": {
              "type": "ToggleGroup (shadcn)",
              "options": [
                "50%",
                "70%",
                "80%",
                "90%",
                "100%"
              ],
              "use_when": "If slider feels fiddly on small screens; keep one input method in UI at a time.",
              "data_testids": {
                "toggle_group": "player-confidence-toggle-group",
                "option": "player-confidence-toggle-option"
              }
            }
          },
          "actions": {
            "save": {
              "label": "Save confidence",
              "variant": "secondary (not primary)",
              "behavior": "Saves locally immediately; sync async. Never blocks Next/Submit.",
              "data_testid": "player-confidence-save-button"
            },
            "clear": {
              "label": "Clear",
              "variant": "ghost/quiet",
              "behavior": "Removes confidence for this question.",
              "data_testid": "player-confidence-clear-button"
            }
          },
          "state_badges": {
            "saved": "Show small ‘Saved’ meta next to panel title (no toast spam).",
            "offline": "If offline, show ‘Saved on device’ (amber) using existing offline save language.",
            "data_testids": {
              "saved_badge": "player-confidence-saved-bge",
              "offline_badge": "player-confidence-offline-badge"
            }
          }
        }
      },
      "interaction_rules": {
        "no_delay": "Confidence save must not delay answer submission or scoring.",
        "changed_response_exclusion": "If user changes selected option after saving confidence, mark confidence as ‘changed-response’ and exclude from A41/A42/A43 computations (per guide04). UI should show a subtle note: ‘Excluded (answer changed)’ without implying correctness.",
        "data_testids": {
          "excluded_note": "player-confidence-excluded-note"
        }
      }
    },
    "results_review_controls": {
      "placement": "Inside existing Results per-question expanded review panel (where options/solution appear), add a compact ‘Confidence & reflection’ strip.",
      "elements": {
        "confidence_readonly": {
          "label": "Your confidence",
          "value": "Show saved % if present; else ‘Not rated’.",
          "data_testid": "results-question-confidence-value"
        },
        "error_category": {
          "label": "What went wrong? (optional)",
          "component": "Select (shadcn)",
          "options": [
            "Concept gap",
            "Calculation error",
            "Silly mistake",
            "Time pressure",
            "Misread question",
            "Guess",
            "Other"
          ],
          "note": "These are self-reported categories; do not auto-assign.",
          "data_testids": {
            "select": "results-error-category-select",
            "option": "results-error-category-option"
          }
        },
        "notes": {
          "label": "Notes (optional)",
          "component": "Textarea (shadcn)",
          "placeholder": "Write 1 line: what you’ll do differently next time…",
          "data_testid": "results-error-notes-textarea"
        },
        "save": {
          "label": "Save reflection",
          "variant": "secondary",
          "data_testid": "results-reflection-save-button"
        }
      },
      "microcopy": {
        "privacy": "Only you can see these notes.",
        "exclusion": "Calibration excludes questions where you changed your answer after rating confidence."
      }
    },
    "analytics_workspace_extensions": {
      "placement": "Inside existing analytics workspace (Results addendum), add Guide04 metric tiles/rows for A41/A42/A43 and mistake-review progress A45/A50.",
      "metric_ids_and_thresholds": {
        "A41": "Calibration (requires >=20 rated unchanged single-correct binary outcomes)",
        "A42": "High-confidence errors (requires >=5 items with p>=0.8)",
        "A43": "Brier score (requires >=50 rated unchanged binary)",
        "A45": "Learner error labels count (requires >=5 learner labels)",
        "A50": "Assigned mistake tasks completed (positive assigned mistake tasks)"
      },
      "ui_rules": {
        "availability": "If minimum samples not met, show ‘Unavailable’ with exact requirement (e.g., ‘Need 20 rated unchanged questions’).",
        "evidence_dialog": "A44 calculator must live inside the Metric Evidence dialog/drawer for the relevant metric (not a separate page).",
        "data_testids": {
          "a41_tile": "results-metric-a41-tile",
          "a42_tile": "results-metric-a42-tile",
          "a43_tile": "results-metric-a43-tile",
          "a45_tile": "results-metric-a45-tile",
          "a50_tile": "results-metric-a50-tile",
          "a44_open": "results-a44-open-calculator-button"
        }
      }
    },
    "A44_expected_value_calculator": {
      "purpose": "Let the student input their own probability (p) and see expected value under frozen scoring rules. This is hypothetical and must not change scoring.",
      "placement": "Inside MetricEvidenceDrawer body as a collapsible section titled ‘Expected value (what-if)’.",
      "inputs": {
        "probability": {
          "component": "Input (shadcn)",
          "type": "number",
          "constraints": "0.00–1.00 step 0.01",
          "data_testid": "results-a44-probability-input"
        },
        "scoring_rules": {
          "display": "Read-only summary of frozen scoring rules for this test (correct marks, negative marks, unattempted).",
          "data_testid": "results-a44-scoring-rules-summary"
        }
      },
      "outputs": {
        "expected_value": {
          "display": "EV = p*(+marks) + (1-p)*(-negMarks)",
          "data_testid": "results-a44-expected-value"
        },
        "recommendation": {
          "rule": "Do not give prescriptive advice like ‘always attempt’. Only show neutral interpretation: ‘Positive EV’ / ‘Negative EV’.",
          "data_testid": "results-a44-ev-interpretation"
        }
      },
      "actions": {
        "reset": {
          "label": "Reset",
          "variant": "ghost",
          "data_testid": "results-a44-reset-button"
        }
      }
    },
    "mistake_review_checklist": {
      "principle": "Checklist tracks completion, not mastery. Explicit completion required (A45/A50).",
      "placement": "In Results per-question review panel, add a ‘Mistake review’ checklist card when the question is incorrect or marked for review.",
      "items": [
        "I identified the error category",
        "I wrote a 1-line note",
        "I reviewed the correct solution",
        "I will retry a similar question"
      ],
      "ui": {
        "component": "Checkbox (shadcn) list inside Card",
        "completion": "Show ‘Completed’ only when all items checked; do not infer.",
        "data_testids": {
          "card": "results-mistake-review-card",
          "item": "results-mistake-review-item",
          "complete_badge": "results-mistake-review-complete-badge"
        }
      }
    },
    "components": {
      "component_path": {
        "shadcn_primary": [
          "/app/frontend/src/components/ui/collapsible.jsx",
          "/app/frontend/src/components/ui/slider.jsx",
          "/app/frontend/src/components/ui/toggle-group.jsx",
          "/app/frontend/src/components/ui/select.jsx",
          "/app/frontend/src/components/ui/textarea.jsx",
          "/app/frontend/src/components/ui/checkbox.jsx",
          "/app/frontend/src/components/ui/card.jsx",
          "/app/frontend/src/components/ui/button.jsx",
          "/app/frontend/src/components/ui/badge.jsx",
          "/app/frontend/src/components/ui/tooltip.jsx"
        ]
      },
      "custom_components_to_create_js": [
        {
          "name": "PlayerConfidencePanel",
          "file": "frontend/src/components/player/PlayerConfidencePanel.js",
          "purpose": "Optional collapsible confidence UI with slider/toggles and save/clear.",
          "data_testids": [
            "player-confidence-collapsible-toggle",
            "player-confidence-slider",
            "player-confidence-save-button"
          ]
        },
        {
          "name": "ResultsReflectionStrip",
          "file": "frontend/src/components/results/ResultsReflectionStrip.js",
          "purpose": "Per-question reflection controls (error category + notes + save).",
          "data_testids": [
            "results-error-category-select",
            "results-error-notes-textarea",
            "results-reflection-save-button"
          ]
        },
        {
          "name": "MistakeReviewChecklist",
          "file": "frontend/src/components/results/MistakeReviewChecklist.js",
          "purpose": "Explicit completion checklist for mistake review (A45/A50).",
          "data_testids": [
            "results-mistake-review-card",
            "results-mistake-review-item"
          ]
        },
        {
          "name": "A44ExpectedValueCalculator",
          "file": "frontend/src/components/results/A44ExpectedValueCalculator.js",
          "purpose": "What-if EV calculator embedded inside MetricEvidenceDrawer.",
          "data_testids": [
            "results-a44-probability-input",
            "results-a44-expected-value"
          ]
        }
      ]
    },
    "instructions_to_main_agent": [
      "Add confidence UI as an OPTIONAL Collapsible panel inside existing Player question card; do not change navigation or submission flow.",
      "Confidence collection must be non-blocking and must not delay scoring/submission.",
      "Respect guide04/source04 thresholds and exclusions exactly: A41>=20 rated unchanged single-correct binary; A42>=5 p>=0.8; A43>=50 rated unchanged binary; exclude changed-response items.",
      "Add per-question reflection controls in Results: error category Select + notes Textarea + explicit Save.",
      "Add mistake-review checklist with explicit completion (not mastery) and wire to A45/A50 counts.",
      "Embed A44 expected-value calculator inside MetricEvidenceDrawer (collapsible section).",
      "All new components must be .js (not .tsx) and every interactive/value element must include data-testid."
    ]
  },
  "general_ui_ux_design_guidelines": "    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.",
  "scoped_correction_addendum_guide04_metrics_alignment": {
    "scope": {
      "goal": "Correct ONLY the previously-added Guide04 confidence/mistake-review analytics guidelines so they match the authoritative source guide (docs/source_guides/04_Results_60_Analyses_and_Question_Insights.pdf.txt) and backend registry (backend/tejas/analytics_registry.json). Preserve the rest of this file verbatim; do not rename metric IDs or invent new formulas. No UI redesign; only additive corrections + responsive class guidance for already-created but unintegrated panels.",
      "non_goals": [
        "Do not change global tokens, typography, or matte maroon identity (#5C0025).",
        "Do not relabel or reorder the authoritative metric registry; UI must reflect it.",
        "Do not add imagery or decorative charts; evidence-first drillthrough remains mandatory.",
        "Do not implement frontend; provide guidance only."
      ],
      "authoritative_sources": {
        "source_guide": "/app/docs/source_guides/04_Results_60_Analyses_and_Question_Insights.pdf.txt",
        "registry": "/app/backend/tejas/analytics_registry.json",
        "notes": "If any existing UI copy conflicts with these sources, update copy/labels to match sources (not vice versa)."
      }
    },
    "critical_metric_definition_fixes": {
      "A41_confidence_calibration_by_bin": {
        "correct_name": "Confidence calibration by bin",
        "evidence_gate": {
          "overall_min_rated_items": 20,
          "per_bin_min_items": 10,
          "binning": "Declared probability bins (product-defined). Only display bins that meet n>=10; still show overall n.",
          "eligibility": "Use ONLY genuine precommit probability ratings p and binary outcomes y (full-correct=1 else 0). Exclude retrospective ratings and exclude changed-response items if product marks them as not genuine precommit."
        },
        "display_contract": {
          "must_show": [
            "mean(p) per displayed bin",
            "mean(y) per displayed bin",
            "n per bin",
            "overall rated n",
            "exclusions count (e.g., changed-response excluded)"
          ],
          "must_not": [
            "Do not show calibration as a single score replacing the bin table.",
            "Do not show bins with n<10.",
            "Do not clamp probabilities; accept full [0,1]."
          ]
        },
        "evidence_drawer_copy": {
          "definition": "Compares what you predicted (p) vs what happened (y) inside probability bins.",
          "calculation": "For each bin: mean(p) and mean(y).",
          "limitations": "Self-reported probabilities are noisy; calibration is evidence, not a stable trait."
        }
      },
      "A42_binary_brier_score": {
        "correct_name": "Binary Brier score",
        "evidence_gate": {
          "min_rated_items": 20,
          "eligibility": "Use genuine precommit p in [0,1] and y=1 for full correctness. Omit partial-credit items. Exclude retrospective ratings."
        },
        "formula": "mean((p - y)^2)",
        "display_rules": {
          "must_show": [
            "value",
            "n",
            "eligibility notes (binary-only, excludes partial-credit)"
          ]
        }
      },
      "A43_low_confidence_penalty_exposure": {
        "correct_name": "Low-confidence penalty exposure",
        "evidence_gate": {
          "min_genuinely_rated_attempts": 10,
          "threshold": {
            "symbol": "c",
            "default": 0.2,
            "note": "c=0.20 is a product proposal; UI must show it as configurable and display the active c used for the calculation."
          },
          "eligibility": "Use rated items with genuine precommit p in [0,1] and signed contributions s_q. Exclude retrospective ratings."
        },
        "formula": "sum(max(-s_q,0) where p_q < c) + rated attempt count",
        "display_contract": {
          "must_show": [
            "penalty_sum",
            "rated_count",
            "active_threshold_c"
          ],
          "must_not": [
            "Do not hide low p values; allow p near 0.00 because this metric depends on low-confidence behavior."
          ]
        }
      },
      "A45_confirmed_error_cause_distribution": {
        "correct_name": "Confirmed error-cause distribution",
        "evidence_gate": {
          "min_labeled_wrong_items": 5,
          "eligibility": "Only WRONG items that have learner-confirmed or teacher-reviewed cause labels. Keep unknown/unlabeled counts separate."
        },
        "formula": "count(cause) / number of labeled wrong items",
        "ui_implication": "The distribution panel MUST filter to WRONG items only (not all incorrect+omitted, not correct). If fewer than 5 labeled wrong items, show Unavailable with requirement copy."
      },
      "A50_unresolved_review_backlog": {
        "correct_name": "Unresolved review backlog",
        "evidence_gate": {
          "min_tasks": 1,
          "eligibility": "Wrong OR omitted first-exposure items that have explicit review-task states."
        },
        "formula": "count(open review tasks)",
        "must_include_breakdowns": [
          "age since attempt (e.g., days)",
          "topic breakdown (if approved topic tags exist)"
        ],
        "must_not": [
          "Do NOT represent A50 as a completion percentage.",
          "Do NOT conflate checklist completion with mastery."
        ]
      }
    },
    "player_confidence_input_correction": {
      "required_change": "Previously the confidence UI constrained p to 0.50→1.00. This conflicts with Guide04 which requires p in [0,1]. Update guidelines so the confidence input supports full probability range 0.00–1.00 with step 0.01 (or 0.05 if using discrete toggles), and still has NO default value.",
      "ui_behavior": {
        "no_default": "Render an unset state until the learner explicitly sets a value.",
        "optional": "Confidence remains optional and non-blocking.",
        "changed_response_exclusion": "If answer changes after rating, mark as excluded from A41/A42/A43 computations (genuine precommit requirement)."
      },
      "component_guidance": {
        "preferred": "Slider (shadcn) with min=0 max=1 step=0.01; show tick labels at 0, 0.2, 0.5, 0.8, 1.0.",
        "mobile_alt": "ToggleGroup with discrete options [0.0,0.2,0.5,0.8,1.0] ONLY if slider is too fiddly; keep one method at a time.",
        "data_testids": {
          "slider": "player-confidence-slider",
          "value": "player-confidence-value",
          "save": "player-confidence-save-button",
          "clear": "player-confidence-clear-button"
        }
      }
    },
    "responsive_integration_classes_for_existing_panels": {
      "intent": "Existing panels were created but not integrated; provide scoped Tailwind class guidance that matches existing matte surfaces/tokens and avoids layout regressions. Use these classes when wiring panels into Player + Results.",
      "player_confidence_panel_container": {
        "wrapper": "mt-4 rounded-[14px] border border-border bg-card p-4 sm:p-5",
        "collapsed_row": "flex items-center justify-between gap-3 text-sm",
        "helper_text": "text-xs text-muted-foreground",
        "actions_row": "mt-3 flex flex-wrap items-center gap-2",
        "avoid": [
          "Do not use sticky overlays inside question card.",
          "Do not use gradients."
        ]
      },
      "results_reflection_strip": {
        "wrapper": "mt-4 rounded-[14px] border border-border bg-card p-4 sm:p-5",
        "grid": "grid grid-cols-1 gap-3 sm:grid-cols-2",
        "textarea": "sm:col-span-2",
        "save_row": "mt-3 flex items-center justify-end gap-2"
      },
      "mistake_review_checklist_card": {
        "wrapper": "mt-4 rounded-[14px] border border-border bg-card p-4 sm:p-5",
        "list": "mt-3 space-y-2",
        "item": "flex items-start gap-3",
        "label": "text-sm leading-6",
        "badge_row": "mt-3 flex items-center justify-between gap-2"
      },
      "evidence_drawer_expected_value_section": {
        "wrapper": "mt-5 rounded-[12px] border border-border bg-muted/40 p-4",
        "grid": "grid grid-cols-1 gap-3 sm:grid-cols-2",
        "output": "sm:col-span-2",
        "note": "Keep EV section collapsible; never make it the primary focus of the drawer."
      }
    },
    "data_testid_enforcement_reminders": {
      "rule": "All interactive and key informational elements MUST include data-testid (kebab-case, role-based).",
      "specifically_for_this_addendum": [
        "results-metric-a41-tile",
        "results-metric-a42-tile",
        "results-metric-a43-tile",
        "results-metric-a45-tile",
        "results-metric-a50-tile",
        "results-a44-probability-input",
        "results-a44-expected-value",
        "results-mistake-review-card",
        "results-mistake-review-item",
        "player-confidence-slider",
        "player-confidence-save-button"
      ]
    },
    "instructions_to_main_agent": [
      "Do NOT change metric IDs or rename registry entries; update UI labels/copy to match source guide + analytics_registry.json.",
      "Fix confidence probability input to support full [0,1] with NO default; low values must be allowed because A43 depends on them.",
      "A41: enforce evidence gates (>=20 overall, >=10 per displayed bin) and show mean(p) + mean(y) per bin; hide bins that fail n>=10.",
      "A42: Brier score requires >=20 rated binary items; exclude partial-credit items.",
      "A43: low-confidence penalty exposure requires >=10 genuinely rated attempts; show active threshold c (default 0.20 proposal) and penalty sum.",
      "A45: distribution is ONLY for labeled WRONG items; require >=5 labeled wrong items; keep unknown/unlabeled separate.",
      "A50: show COUNT of open review tasks + age/topic breakdown; never show completion % and never conflate checklist completion with mastery.",
      "Use the provided Tailwind class scaffolds to integrate existing panels responsively without changing global styling.",
      "All new/updated React components are .js (not .tsx) and must include data-testid on interactive + key value elements."
    ]
  },
  "premium_exam_refinement_addendum": {
    "scope": {
      "goal": "Premium exam refinement addendum: tighten hierarchy and density for chapter-wise tests (94 items), improve source readability in Player without changing protected assets, and calibrate trust copy (no overclaims). Incremental only.",
      "constraints": [
        "Preserve matte maroon #5C0025 and existing tokens (index.css/App.css)",
        "Preserve Figtree/Roboto Mono and light/dark",
        "No photos/new palette",
        "No re-architecture; no scoring/safety changes",
        "React components are .js (not .tsx)",
        "All interactive + key informational elements must include data-testid"
      ]
    },
    "priority_changes_P0_P2": {
      "P0_trust_copy": [
        {
          "where": "/sets/:id preflight",
          "change": "Replace absolute ‘verified’ language with scoped ‘check passed’ language.",
          "copy": "Connection check passed. Saving is enabled on this device. You can zoom source images during the attempt.",
          "add": "If any source image fails to load during the attempt, answering will pause until it loads.",
          "data_testids": {
            "success": "preflight-device-check-success",
            "disclosure": "preflight-source-image-disclosure"
          }
        }
      ],
      "P1_catalog_density": [
        {
          "where": "/exams",
          "change": "Default to compact rows (not large cards) + sticky filter/search bar on mobile.",
          "acceptance": [
            "On 390×844, first row title visible within ~400px scroll.",
            "Open a specific chapter via: 1 subject tap + 1 search + 1 tap (no pagination hunting)."
          ],
          "data_testids": {
            "search": "exams-catalog-search-input",
            "subject_tabs": "exams-catalog-subject-tabs",
            "row": "exams-catalog-row",
            "start": "exams-catalog-start-button"
          }
        }
      ],
      "P1_source_readability": [
        {
          "where": "/attempts/:id",
          "change": "Avoid tiny shrink-to-fit source images. Provide an inline Source Viewport with Fit/Readable controls and full-screen fallback.",
          "controls": [
            "Fit",
            "Readable",
            "Zoom -/+",
            "Pan drag",
            "Full-screen"
          ],
          "rule": "Default to Readable on phones when possible; otherwise Fit with one-tap switch.",
          "data_testids": {
            "viewport": "player-source-viewport",
            "fit": "player-source-fit-toggle",
            "readable": "player-source-readable-toggle",
            "zoom_in": "player-source-zoom-in-button",
            "zoom_out": "player-source-zoom-out-button",
            "fullscreen": "player-source-fullscreen-button"
          }
        }
      ],
      "P1_source_options_one_zoom": [
        {
          "where": "Player when render_mode === 'source'",
          "policy": "One-zoom rule: student can view all options with one zoom action maximum.",
          "allowed": [
            "Options strip image anchored below stem (single zoom target)",
            "Option-region thumbnails ONLY if backed by real source refs (no guessed crops)"
          ],
          "data_testids": {
            "options_strip": "player-options-strip-image",
            "options_strip_open": "player-options-strip-open-button"
          }
        }
      ],
      "P2_touch_targets": [
        {
          "where": "Header actions + brand link",
          "rule": "Enforce min-height: var(--touch-target) for tappable header items; avoid 40–42px targets.",
          "data_testids": {
            "brand": "header-brand-link",
            "login": "header-login-link"
          }
        }
      ]
    },
    "component_usage": {
      "shadcn_primary": [
        "/app/frontend/src/components/ui/tabs.jsx",
        "/app/frontend/src/components/ui/input.jsx",
        "/app/frontend/src/components/ui/select.jsx",
        "/app/frontend/src/components/ui/card.jsx",
        "/app/frontend/src/components/ui/badge.jsx",
        "/app/frontend/src/components/ui/scroll-area.jsx",
        "/app/frontend/src/components/ui/skeleton.jsx",
        "/app/frontend/src/components/ui/button.jsx",
        "/app/frontend/src/components/ui/dialog.jsx",
        "/app/frontend/src/components/ui/drawer.jsx",
        "/app/frontend/src/components/ui/toggle-group.jsx",
        "/app/frontend/src/components/ui/separator.jsx"
      ],
      "notes": [
        "Do not use raw HTML dropdown/calendar/toast; use shadcn components.",
        "All new components must be .js and use named exports; pages default export."
      ]
    },
    "layout_specs_mobile_first": {
      "catalog_header": {
        "rule": "Compact header: title + subtitle + always-visible ‘Answer keys only’ disclosure; move long rules into details.",
        "max_height_mobile": "~220px target",
        "data_testid": "answer-keys-only-disclosure"
      },
      "sticky_filter_bar": {
        "rule": "Sticky filter/search below site header; keep search always reachable.",
        "avoid": "Double-sticky stacking that consumes vertical space.",
        "data_testids": {
          "bar": "exams-catalog-sticky-filterbar",
          "clear": "exams-catalog-clear-filters-button"
        }
      },
      "row_density": {
        "row_height": "Aim ~72–88px per row on mobile; CTA remains 44px+.",
        "meta": "Use mono chips for 50Q/60m/+3/-1; keep to one line with wrap."
      }
    },
    "results_refinement": {
      "immutability_notice": {
        "copy": "Attempts are saved and cannot be edited.",
        "placement": "Near results header/summary and near review list.",
        "data_testid": "results-attempt-immutable-notice"
      },
      "key_only_disclosure": {
        "copy": "Answer keys only. Worked solutions are not provided.",
        "placement": "Near any answer reveal/solution area.",
        "data_testid": "results-answer-keys-only-disclosure"
      }
    },
    "instructions_to_main_agent": [
      "Implement /exams compaction + default compact rows; keep existing tokens and matte maroon.",
      "Replace preflight ‘verified’ copy with scoped language.",
      "Player: implement inline Source Viewport with Fit/Readable controls; avoid tiny shrink-to-fit.",
      "Enforce one-zoom rule for source-rendered options via options strip or real source-backed thumbnails.",
      "Ensure touch targets >= var(--touch-target) in header actions.",
      "All interactive + key informational elements must include data-testid (kebab-case)."
    ]
  }
}