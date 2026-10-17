{
  "design_completion_addendum": {
    "meta": {
      "date": "2026-10-17",
      "scope": "Addendum ONLY for remaining approved product features: Smart Upload wizard (/studio + /studio/auto-imports/:id) and deep Results analysis (/results/:id). Preserve existing brand, tokens, navigation, and all history in /app/design_guidelines.md and /app/design_simple_navigation.md.",
      "hard_constraints": [
        "NO new palette/photos. Keep matte maroon #5C0025 and existing tokens (App.css + index.css).",
        "React components are .js (NOT .tsx).",
        "Use shadcn/ui primitives from /app/frontend/src/components/ui (no raw HTML dropdown/calendar/toast).",
        "All interactive and key informational elements MUST include data-testid (kebab-case, role-based).",
        "No fabricated percentile/rank. No fake 2026 AIR mapping. If reference/calibration not verified, show ‘Unavailable’ + what’s needed.",
        "Stepwise solutions are supplements: versioned, do not overwrite grading; show provenance + verification status.",
        "Cohort analytics must respect privacy thresholds; hide/aggregate when n is small."
      ]
    },

    "brand_and_visual_system": {
      "reuse_existing_tokens": {
        "css_sources": [
          "/app/frontend/src/index.css",
          "/app/frontend/src/App.css"
        ],
        "do_not_change": [
          "--blue (#5C0025)",
          "--ink, --text-muted, --surface-card, --surface-alt, --line",
          "Figtree + Roboto Mono"
        ]
      },
      "optional_new_semantic_tokens_if_missing": {
        "rule": "Only add if a new state cannot be expressed with existing success/warning/danger/review tokens.",
        "suggested": {
          "--info": "#1D4ED8 (ONLY if needed; otherwise reuse muted + brand-soft)",
          "--info-soft": "#EFF6FF",
          "--info-line": "#BFDBFE"
        }
      },
      "typography": {
        "fonts": {
          "ui": "Figtree",
          "mono": "Roboto Mono",
          "usage": {
            "mono_only_for": ["IDs", "page refs", "confidence/threshold numbers", "timestamps", "bucket labels"]
          }
        },
        "scale": {
          "page_title": "text-2xl sm:text-3xl font-semibold tracking-tight",
          "section_title": "text-lg font-semibold",
          "card_title": "text-base font-semibold",
          "body": "text-sm sm:text-base",
          "meta": "text-xs text-muted-foreground",
          "numbers": "tabular-nums"
        }
      },
      "density": {
        "principle": "Premium-but-free: airy spacing, crisp borders, minimal decoration.",
        "spacing": {
          "card_padding": "p-5 sm:p-6",
          "grid_gap": "gap-4 md:gap-6",
          "section_spacing": "mt-6 sm:mt-8"
        }
      }
    },

    "studio_smart_upload_wizard": {
      "routes": {
        "primary": "/studio",
        "detail": "/studio/auto-imports/:id"
      },
      "design_goal": "Owner uploads PDF/Excel/Word → system detects paper rules/sections/questions → asks ONLY ambiguity questions → generates answer key + stepwise solutions (with provenance) → safe autopublish with issues gating.",

      "information_architecture": {
        "studio_overview": {
          "layout": "Two-column on desktop (existing .chapter-upload-layout pattern): left = SmartUploadPanel, right = ‘How it works’ + recent imports. Mobile stacks.",
          "primary_panel": {
            "name": "SmartUploadPanel",
            "card_structure": [
              "Header: ‘Smart Upload’ + helper line",
              "Import mode tabs: PDF | Excel | Word",
              "Dropzone area (changes by mode)",
              "Detected summary preview (disabled until file uploaded)",
              "Primary CTA: ‘Start auto-import’",
              "Fine print: rights + privacy + ‘We’ll ask only if ambiguous’"
            ],
            "data_testids": {
              "mode_tabs": "studio-smartupload-mode-tabs",
              "pdf_tab": "studio-smartupload-mode-pdf",
              "excel_tab": "studio-smartupload-mode-excel",
              "word_tab": "studio-smartupload-mode-word",
              "dropzone": "studio-smartupload-dropzone",
              "start_button": "studio-smartupload-start-button"
            }
          }
        },

        "auto_import_detail": {
          "layout": "Top: breadcrumb + import title + status badge + actions. Body: left = Processing timeline + Issues/Questions; right = Preview + Publish panel (sticky on desktop).",
          "top_actions": [
            "Open source viewer",
            "Download extracted CSV/JSON (optional)",
            "Restart import (danger confirm)",
            "Delete draft (danger confirm)"
          ],
          "data_testids": {
            "breadcrumb": "studio-autoimport-breadcrumb",
            "status_badge": "studio-autoimport-status-badge",
            "restart_button": "studio-autoimport-restart-button",
            "delete_button": "studio-autoimport-delete-button"
          }
        }
      },

      "status_model_and_badges": {
        "statuses": [
          {
            "key": "queued",
            "label": "Queued",
            "badge": "neutral",
            "meaning": "Upload received; waiting for worker."
          },
          {
            "key": "processing",
            "label": "Processing",
            "badge": "amber",
            "meaning": "Extracting + detecting rules + generating solutions."
          },
          {
            "key": "needs-clarification",
            "label": "Needs clarification",
            "badge": "review",
            "meaning": "Ambiguity questions require owner input."
          },
          {
            "key": "blocked",
            "label": "Blocked",
            "badge": "red",
            "meaning": "Cannot publish until blocking issues resolved."
          },
          {
            "key": "ready-to-publish",
            "label": "Ready",
            "badge": "green",
            "meaning": "All blocking issues resolved; safe to publish."
          },
          {
            "key": "published",
            "label": "Published",
            "badge": "live",
            "meaning": "Test is live/available per existing rules."
          }
        ],
        "badge_components": {
          "use": "/app/frontend/src/components/ui/badge.jsx",
          "mapping": "Reuse existing .badge green/amber/red/neutral + live style from design_guidelines.md"
        }
      },

      "processing_timeline_ui": {
        "component": "Tabs + Progress + Card list",
        "timeline_steps": [
          "Upload",
          "Detect paper rules",
          "Split sections",
          "Extract questions",
          "Extract marking scheme",
          "Generate answer key",
          "Generate stepwise solutions",
          "Validate + issues",
          "Ready to publish"
        ],
        "rules": [
          "Never show 100% unless status is ready-to-publish/published.",
          "Each step shows: state (done/running/blocked), timestamp, and ‘View evidence’ link.",
          "If a step is blocked, show the exact blocking issue card directly below (no hunting)."
        ],
        "data_testids": {
          "progress": "studio-autoimport-progress",
          "timeline": "studio-autoimport-timeline",
          "timeline_step": "studio-autoimport-timeline-step"
        }
      },

      "ambiguity_only_form": {
        "principle": "Ask ONLY when the system cannot deterministically proceed. Each question must be multiple-choice or short structured input; never open-ended essays.",
        "ui_pattern": "Card stack titled ‘Clarifications needed’ with 1 question per card; sticky ‘Submit clarifications’ bar on mobile.",
        "question_types": [
          {
            "type": "select-one",
            "examples": [
              "Which marking scheme applies to Section B? (+4/-1 or +3/-1)",
              "Is this paper single correct or multi-correct for these questions?"
            ]
          },
          {
            "type": "number",
            "examples": [
              "Total questions detected: 88. Confirm expected count?",
              "Section A question range start/end"
            ]
          },
          {
            "type": "confirm",
            "examples": [
              "We detected 2 versions in the PDF. Continue with Version 1 only?"
            ]
          }
        ],
        "components": {
          "use": [
            "/app/frontend/src/components/ui/card.jsx",
            "/app/frontend/src/components/ui/radio-group.jsx",
            "/app/frontend/src/components/ui/select.jsx",
            "/app/frontend/src/components/ui/input.jsx",
            "/app/frontend/src/components/ui/textarea.jsx",
            "/app/frontend/src/components/ui/button.jsx",
            "/app/frontend/src/components/ui/alert.jsx",
            "/app/frontend/src/components/ui/separator.jsx"
          ]
        },
        "data_testids": {
          "panel": "studio-clarifications-panel",
          "question_card": "studio-clarification-question-card",
          "submit": "studio-clarifications-submit-button"
        }
      },

      "source_viewer_and_provenance": {
        "principle": "Every extracted rule/answer/solution must show where it came from: (a) PDF page ref or (b) AI-generated with model + prompt hash + verification status.",
        "ui": {
          "pattern": "Side-by-side viewer: left = Source canvas (existing .source-pan-canvas), right = Extracted content card.",
          "provenance_chip": "Small Badge-like chip: ‘From PDF p.12’ | ‘AI generated’ | ‘AI cross-checked’ | ‘Human approved’.",
          "verification_rule": "Only show ‘AI cross-checked’ when two independent solutions agree; label clearly as not proof. Never imply official correctness."
        },
        "data_testids": {
          "viewer": "studio-source-viewer",
          "provenance": "studio-provenance-chip",
          "open_viewer": "studio-open-source-viewer-button"
        }
      },

      "publish_panel_safe_autopublish": {
        "principle": "Publishing is gated by blocking issues. Non-blocking warnings can publish with explicit acknowledgement.",
        "ui": {
          "card_title": "Publish",
          "sections": [
            "Readiness summary (counts: questions, sections, missing answers, conflicts)",
            "Blocking issues list (must be zero)",
            "Warnings list (acknowledge checkbox)",
            "Primary CTA: Publish test",
            "Secondary: Keep as draft"
          ]
        },
        "components": {
          "use": [
            "/app/frontend/src/components/ui/card.jsx",
            "/app/frontend/src/components/ui/alert.jsx",
            "/app/frontend/src/components/ui/checkbox.jsx",
            "/app/frontend/src/components/ui/button.jsx",
            "/app/frontend/src/components/ui/tooltip.jsx"
          ]
        },
        "data_testids": {
          "panel": "studio-publish-panel",
          "blocking_list": "studio-publish-blocking-issues",
          "warnings_ack": "studio-publish-warnings-ack-checkbox",
          "publish": "studio-publish-button"
        }
      },

      "micro_interactions": {
        "rules": [
          "No transition: all.",
          "Use skeletons for long processing lists; show step-level progress.",
          "When a clarification is submitted, animate the card collapse (height/opacity) and show a single Sonner toast: ‘Clarification saved’."
        ],
        "tailwind_snippets": {
          "card_hover": "transition-[background-color,border-color,box-shadow] duration-200 hover:shadow-[0_10px_24px_var(--shadow-tint)]",
          "button_press": "active:translate-y-[1px]",
          "muted_panel": "bg-[var(--surface-alt)] border border-[var(--line)] rounded-[var(--radius-card)]"
        }
      }
    },

    "results_deep_analysis": {
      "route": "/results/:id",
      "placement_rule": "Keep existing analytics workspace functional, but move the most actionable cohort graphs near the top of Results detail (below summary).",
      "top_of_page_modules_order": [
        "(Existing) Summary cards",
        "Cohort insight panel (NEW, compact)",
        "Question-wise analysis (NEW badges + drilldowns)",
        "Worked solutions (existing/extended)"
      ],

      "cohort_insight_panel": {
        "goal": "Show rank/percentile only when computed from real cohort data and privacy thresholds are met; otherwise show Unavailable with reason and next steps.",
        "layout": "Bento-like 2x2 on desktop, stacked on mobile. Each tile is a Card with a title, value/empty state, and ‘View details’ action.",
        "tiles": [
          {
            "id": "rank",
            "title": "Rank (cohort)",
            "value_rule": "Show only if cohort_size >= privacy_threshold AND ties handled; else Unavailable.",
            "data_testid": "results-cohort-rank-tile"
          },
          {
            "id": "percentile",
            "title": "Percentile (cohort)",
            "value_rule": "Show only if cohort_size >= privacy_threshold; else Unavailable.",
            "data_testid": "results-cohort-percentile-tile"
          },
          {
            "id": "score_histogram",
            "title": "Score distribution",
            "visual": "Histogram (Recharts BarChart) with accessible table fallback.",
            "data_testids": {
              "card": "results-score-histogram-card",
              "chart": "results-score-histogram-chart",
              "table": "results-score-histogram-table"
            }
          },
          {
            "id": "subject_topic",
            "title": "Subject & topic breakdown",
            "visual": "Stacked bars or table-first; only if tags exist.",
            "data_testids": {
              "card": "results-subject-topic-card",
              "table": "results-subject-topic-table"
            }
          }
        ],
        "privacy_thresholds": {
          "minimum_n_to_show": 20,
          "rule": "If n < minimum, hide distributions and show: ‘Unavailable: not enough attempts to protect privacy.’"
        }
      },

      "predicted_rank_2026_policy": {
        "principle": "Never pretend official NTA percentile/AIR mapping. Provide an owner-facing ‘Estimate’ module only when a verified reference dataset/calibration is configured.",
        "ui": {
          "placement": "Inside Cohort insight panel as a collapsible Card section titled ‘2026 AIR scenario estimate’.",
          "states": {
            "unconfigured": {
              "show": "Unavailable",
              "copy": "To estimate AIR, add an official reference table (percentile→AIR) for the target year/shift. You can also enter your official NTA percentile to see an approximate AIR range.",
              "inputs": ["Official NTA percentile (optional)"]
            },
            "configured": {
              "show": "Estimated AIR range",
              "must_show": ["reference_source", "population_size", "last_updated"],
              "disclaimer": "Estimate only. Not official."
            }
          }
        },
        "data_testids": {
          "card": "results-air-estimate-card",
          "nta_input": "results-air-estimate-nta-percentile-input",
          "estimate_value": "results-air-estimate-value"
        }
      },

      "question_wise_analysis": {
        "goal": "Per question: show correct/wrong/skipped %, option distribution A-D, and link to worked solution + source/provenance.",
        "ui_pattern": "Question list with badges + expandable row (Accordion/Collapsible).",
        "row_contents": [
          "Badges: Correct%, Wrong%, Skipped%",
          "Mini distribution bar (A/B/C/D) with counts",
          "CTA: Open worked solution",
          "CTA: View cohort evidence (if privacy threshold met)"
        ],
        "components": {
          "use": [
            "/app/frontend/src/components/ui/accordion.jsx",
            "/app/frontend/src/components/ui/badge.jsx",
            "/app/frontend/src/components/ui/progress.jsx",
            "/app/frontend/src/components/ui/table.jsx",
            "/app/frontend/src/components/ui/scroll-area.jsx",
            "/app/frontend/src/components/ui/tooltip.jsx",
            "/app/frontend/src/components/ui/dialog.jsx",
            "/app/frontend/src/components/ui/drawer.jsx"
          ]
        },
        "data_testids": {
          "list": "results-question-analysis-list",
          "row": "results-question-analysis-row",
          "expand": "results-question-analysis-expand-button",
          "option_dist": "results-question-option-distribution",
          "open_solution": "results-question-open-solution-button"
        }
      },

      "worked_solutions_and_versioning": {
        "principle": "Solutions can be: from source PDF, AI-generated, or human-approved. Always show provenance and version. Never overwrite the graded answer key.",
        "solution_card": {
          "header": ["Solution", "Provenance chip", "Version", "Last updated"],
          "body": ["Stepwise solution (10-mark style)", "Verification notes", "Source references"],
          "actions": ["Report issue", "Request re-generate (owner only)"]
        },
        "verification_labels": [
          "From PDF",
          "AI generated",
          "AI cross-checked (agreement only)",
          "Human approved"
        ],
        "data_testids": {
          "card": "results-worked-solution-card",
          "provenance": "results-solution-provenance-chip",
          "version": "results-solution-version",
          "report": "results-solution-report-issue-button"
        }
      },

      "charts_accessibility": {
        "rule": "Every chart must have an adjacent table or aria-described summary for screen readers and for low-data cases.",
        "recharts_guidance": {
          "container": "Wrap charts in Card; use ResponsiveContainer; colors from CSS vars (e.g., var(--blue), var(--text-muted)).",
          "tooltip": "Custom tooltip with clear labels; never rely on color alone.",
          "empty_state": "If insufficient data points, show Table-only + note."
        }
      }
    },

    "component_paths": {
      "shadcn_primary": [
        "/app/frontend/src/components/ui/card.jsx",
        "/app/frontend/src/components/ui/button.jsx",
        "/app/frontend/src/components/ui/badge.jsx",
        "/app/frontend/src/components/ui/tabs.jsx",
        "/app/frontend/src/components/ui/progress.jsx",
        "/app/frontend/src/components/ui/alert.jsx",
        "/app/frontend/src/components/ui/alert-dialog.jsx",
        "/app/frontend/src/components/ui/accordion.jsx",
        "/app/frontend/src/components/ui/collapsible.jsx",
        "/app/frontend/src/components/ui/checkbox.jsx",
        "/app/frontend/src/components/ui/input.jsx",
        "/app/frontend/src/components/ui/select.jsx",
        "/app/frontend/src/components/ui/calendar.jsx",
        "/app/frontend/src/components/ui/table.jsx",
        "/app/frontend/src/components/ui/scroll-area.jsx",
        "/app/frontend/src/components/ui/dialog.jsx",
        "/app/frontend/src/components/ui/drawer.jsx",
        "/app/frontend/src/components/ui/tooltip.jsx",
        "/app/frontend/src/components/ui/sonner.jsx",
        "/app/frontend/src/components/ui/skeleton.jsx"
      ]
    },

    "custom_components_to_create_js": {
      "studio": [
        {
          "name": "SmartUploadPanel",
          "file": "frontend/src/components/studio/SmartUploadPanel.js",
          "purpose": "Mode tabs (PDF/Excel/Word) + dropzone + start import CTA + detected summary preview.",
          "data_testids": [
            "studio-smartupload-mode-tabs",
            "studio-smartupload-dropzone",
            "studio-smartupload-start-button"
          ]
        },
        {
          "name": "AutoImportTimeline",
          "file": "frontend/src/components/studio/AutoImportTimeline.js",
          "purpose": "Processing timeline with step states + evidence links.",
          "data_testids": ["studio-autoimport-timeline", "studio-autoimport-timeline-step"]
        },
        {
          "name": "ClarificationsPanel",
          "file": "frontend/src/components/studio/ClarificationsPanel.js",
          "purpose": "Ambiguity-only form cards + submit clarifications.",
          "data_testids": ["studio-clarifications-panel", "studio-clarifications-submit-button"]
        },
        {
          "name": "PublishPanel",
          "file": "frontend/src/components/studio/PublishPanel.js",
          "purpose": "Readiness summary + blocking/warnings gating + publish CTA.",
          "data_testids": ["studio-publish-panel", "studio-publish-button"]
        }
      ],
      "results": [
        {
          "name": "CohortInsightPanel",
          "file": "frontend/src/components/results/CohortInsightPanel.js",
          "purpose": "Rank/percentile tiles + histogram + subject/topic breakdown near top.",
          "data_testids": ["results-cohort-rank-tile", "results-score-histogram-card"]
        },
        {
          "name": "QuestionWiseAnalysis",
          "file": "frontend/src/components/results/QuestionWiseAnalysis.js",
          "purpose": "Per-question % correct/wrong/skipped + A-D distribution + drilldowns.",
          "data_testids": ["results-question-analysis-list", "results-question-open-solution-button"]
        },
        {
          "name": "WorkedSolutionCard",
          "file": "frontend/src/components/results/WorkedSolutionCard.js",
          "purpose": "Stepwise solution with provenance + versioning + report issue.",
          "data_testids": ["results-worked-solution-card", "results-solution-provenance-chip"]
        }
      ]
    },

    "instructions_to_main_agent": [
      "Preserve existing navigation (3 exam home + 3 hub cards) and existing brand tokens; this addendum only adds Studio Smart Upload + Results deep analysis modules.",
      "Studio: implement SmartUploadPanel with PDF/Excel/Word modes; Word is allowed as upload type but must follow the same deterministic/issue-gated pipeline (no promises if extraction fails).",
      "Auto-import detail: show timeline + issues + ambiguity-only clarifications; do not ask routine metadata upfront.",
      "Always show provenance for extracted rules/answers/solutions; label AI cross-check as agreement only, not proof.",
      "Results: place CohortInsightPanel near top; enforce privacy thresholds and cohort minimums; never fabricate percentile/rank.",
      "Predicted rank/AIR 2026: show Unavailable unless verified reference/calibration exists; optionally accept user-entered official NTA percentile to compute an approximate AIR range with clear disclaimer.",
      "All charts must have accessible summaries/tables; prefer tables when data is sparse.",
      "All new components must be .js with named exports; pages default export; add data-testid to every interactive and key value element."
    ]
  },

  "general_ui_ux_design_guidelines": "    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals."
}
