{
  "meta": {
    "product": "jeemains.ai",
    "scope": "Design-only guidelines for auto-publish SmartImport + Live links + Results/Analytics/Solutions. Preserve existing branding (matte maroon #5C0025) and Figtree. JS files (not TSX).",
    "non_goals": [
      "No backend/infra implementation details (but UI must communicate scale + reliability).",
      "No new branding or palette overhaul beyond existing tokens.",
      "No manual review gate UX; replace with automated validation + auto-publish messaging."
    ]
  },
  "brand_attributes": {
    "tone": [
      "authoritative (exam-grade)",
      "calm under pressure (5L concurrent)",
      "transparent (AI provenance + error disclosure)",
      "fast + frictionless (single upload → live link)"
    ],
    "visual_personality": [
      "editorial clarity (lots of whitespace)",
      "matte surfaces (no glossy gradients)",
      "data-first (charts + tables with strong hierarchy)",
      "trust cues (validation badges, audit trail, timestamps)"
    ]
  },
  "design_tokens": {
    "source_of_truth": {
      "css_vars": "Use existing CSS variables already defined in /app/frontend/src/App.css (:root block) and /app/frontend/src/index.css (:root HSL tokens). Do not introduce a new palette.",
      "primary_hex": "#5C0025",
      "font_ui": "Figtree (already imported in index.css)",
      "font_mono": "Roboto Mono (already imported in index.css)"
    },
    "recommended_additions_minimal": {
      "note": "Only add if needed for new UI states; keep consistent with existing naming.",
      "css_custom_properties": {
        "--publish": "var(--success)",
        "--publish-soft": "var(--success-soft)",
        "--publish-line": "var(--success-line)",
        "--processing": "var(--warning)",
        "--processing-soft": "var(--warning-soft)",
        "--processing-line": "var(--warning-line)"
      }
    },
    "radius_shadow_spacing": {
      "radius": {
        "sm": "var(--radius-sm)",
        "card": "var(--radius-card)",
        "shadcn_radius": "var(--radius)"
      },
      "shadow": {
        "hover": "0 10px 24px var(--shadow-tint)",
        "card": "0 8px 30px var(--shadow-tint)"
      },
      "spacing": "Use --space-* tokens already present; keep layouts airy (2–3x spacing)."
    }
  },
  "typography": {
    "font_pairing": {
      "headings": "Figtree 700–800",
      "body": "Figtree 400–600",
      "numbers_timers_codes": "Roboto Mono 400–600"
    },
    "tailwind_scale": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl",
      "h2": "text-base md:text-lg",
      "body": "text-sm md:text-base",
      "small": "text-xs"
    },
    "rules": [
      "Prefer sentence case labels (less shouty).",
      "Use mono for: attempt id, publish id, timestamps, progress %, question ids.",
      "Keep dense analytics readable: increase line-height (leading-relaxed) and use muted text for secondary metadata."
    ]
  },
  "layout_grid": {
    "global": {
      "container": "Use existing .container (max 1240px) for marketing-ish pages; for Studio/Results dashboards allow wider (max-w-[1480px]) like player layout patterns.",
      "page_padding": "Use existing .page top/bottom padding; avoid centered text blocks for dashboards."
    },
    "studio_upload_workspace": {
      "desktop": "Two-column: left = import + validation timeline; right = live publish card + cohort settings + audit trail. Use CSS grid similar to .chapter-upload-layout.",
      "mobile": "Single column; keep primary CTA sticky at bottom (Sheet/Drawer) if needed."
    },
    "results_workspace": {
      "top": "Summary strip (score/rank/percentile + correct/wrong/skipped) then tabs: Overview / Subjects / Topics / Solutions / Cohort.",
      "below": "Charts in 2-col grid on >=640px; single column on mobile."
    }
  },
  "component_path": {
    "primary_shadcn": {
      "button": "/app/frontend/src/components/ui/button.jsx",
      "card": "/app/frontend/src/components/ui/card.jsx",
      "tabs": "/app/frontend/src/components/ui/tabs.jsx",
      "progress": "/app/frontend/src/components/ui/progress.jsx",
      "badge": "/app/frontend/src/components/ui/badge.jsx",
      "alert": "/app/frontend/src/components/ui/alert.jsx",
      "dialog": "/app/frontend/src/components/ui/dialog.jsx",
      "alert_dialog": "/app/frontend/src/components/ui/alert-dialog.jsx",
      "table": "/app/frontend/src/components/ui/table.jsx",
      "separator": "/app/frontend/src/components/ui/separator.jsx",
      "tooltip": "/app/frontend/src/components/ui/tooltip.jsx",
      "switch": "/app/frontend/src/components/ui/switch.jsx",
      "checkbox": "/app/frontend/src/components/ui/checkbox.jsx",
      "select": "/app/frontend/src/components/ui/select.jsx",
      "scroll_area": "/app/frontend/src/components/ui/scroll-area.jsx",
      "collapsible": "/app/frontend/src/components/ui/collapsible.jsx",
      "accordion": "/app/frontend/src/components/ui/accordion.jsx",
      "sheet_drawer": [
        "/app/frontend/src/components/ui/sheet.jsx",
        "/app/frontend/src/components/ui/drawer.jsx"
      ],
      "sonner_toasts": "/app/frontend/src/components/ui/sonner.jsx",
      "calendar_if_needed": "/app/frontend/src/components/ui/calendar.jsx"
    },
    "charts": {
      "library": "Recharts (recommended)",
      "why": "Already Tailwind-friendly; good for subject/topic graphs and cohort distributions.",
      "install": "npm i recharts",
      "components": [
        "<ResponsiveContainer/>",
        "<LineChart/> for score trend",
        "<BarChart/> for subject/topic",
        "<PieChart/> for correct/wrong/skipped",
        "<Tooltip/> with custom content"
      ]
    },
    "motion": {
      "library": "framer-motion (recommended)",
      "install": "npm i framer-motion",
      "use_cases": [
        "Stepper stage transitions",
        "Card entrance on publish completion",
        "Subtle hover lift on exam cards",
        "Results tab content crossfade"
      ]
    }
  },
  "key_screens_and_ui_specs": {
    "A_studio_smartimport_auto_publish": {
      "goal": "Single upload (PDF/Word/Excel) → automated validation → auto-publish live link; show progress + provenance + errors without blocking publication.",
      "information_architecture": {
        "left_column": [
          "Upload dropzone + file picker",
          "Import configuration (exam type, duration, marking scheme, sections)",
          "Validation timeline (stepper)",
          "Detected issues list (actionable, non-blocking unless fatal)",
          "Preview sample questions (first N)"
        ],
        "right_column": [
          "Live publish card (status + link + QR + copy)",
          "Cohort settings (visibility, start time, capacity note)",
          "Auto-publish policy + AI provenance disclosure",
          "Audit trail (events: uploaded, extracted, validated, published, updated)"
        ]
      },
      "stepper_stages": {
        "labels": [
          "Upload received",
          "Extract text & structure",
          "Detect questions/options",
          "Validate answer keys & marking",
          "Generate solutions (AI)",
          "Publish live link"
        ],
        "states": {
          "pending": "Muted badge + skeleton rows",
          "running": "Progress bar + 'Processing page X/Y' (mono)",
          "success": "Green badge + timestamp",
          "warning": "Amber badge + 'Published with warnings'",
          "error_fatal": "Red badge + blocks publish; show 'Fix & retry' CTA"
        },
        "ui_components": [
          "Tabs (Import mode: PDF / Word / Excel)",
          "Progress",
          "Badge",
          "Alert (warnings/errors)",
          "Accordion/Collapsible for 'Show details' per stage"
        ]
      },
      "auto_publish_rules_ui": {
        "copy_blocks": [
          "Auto-publish is ON by default. After automated validation, your test is published immediately.",
          "If issues are detected, the test may still publish with warnings. Students will see disclosures in Results.",
          "Fatal errors (e.g., unreadable file, zero questions) prevent publishing and require re-upload."
        ],
        "controls": {
          "switch": "Optional: 'Auto-publish after validation' (default ON). Only allow turning OFF for admins; if OFF, show 'Publish now' button.",
          "data-testid": {
            "auto_publish_switch": "auto-publish-switch",
            "publish_now_button": "publish-now-button",
            "live_link_copy_button": "live-link-copy-button"
          }
        }
      },
      "live_link_card": {
        "must_include": [
          "Status pill: Draft / Processing / Live",
          "Primary live URL (mono) + Copy button",
          "Secondary: 'Open live page' button",
          "QR code (optional; can be later)",
          "Last updated timestamp"
        ],
        "visual": {
          "card": "Use shadcn Card with subtle border; status strip at top using brand-soft background.",
          "cta": "Primary button uses matte maroon; secondary is outline/ghost."
        },
        "data-testid": {
          "live_link_value": "live-link-value",
          "open_live_link": "open-live-link-button",
          "publish_status_badge": "publish-status-badge"
        }
      },
      "issues_panel": {
        "structure": [
          "Summary counts: Fatal / Warnings / Suggestions",
          "List rows with: issue title, affected pages/questions, recommended fix, 'View evidence' action",
          "Evidence opens Dialog with source snippet image/text"
        ],
        "severity_colors": {
          "fatal": "var(--danger)",
          "warning": "var(--warning)",
          "info": "var(--text-muted)"
        },
        "data-testid": {
          "issues_panel": "import-issues-panel",
          "issue_row": "import-issue-row",
          "issue_evidence_button": "import-issue-evidence-button"
        }
      }
    },
    "B_student_exam_cards_home": {
      "requirement": "Three exam cards: JEE Main / BITSAT / COMEDK → each has Mock Tests / Chapter-wise / Results.",
      "layout": {
        "grid": "Use existing .exam-card-grid patterns; on mobile stack cards; on desktop 2-col then 3-col at xl if desired.",
        "card_content": [
          "Title + short descriptor",
          "Three action links/buttons",
          "Small metadata row (free, updated, attempts)"
        ]
      },
      "micro_interactions": [
        "Hover: border-color shift + shadow (already in .exam-card:hover)",
        "Action buttons: press scale 0.98 (framer-motion optional)"
      ],
      "data-testid": {
        "jee_card": "exam-card-jee-main",
        "bitsat_card": "exam-card-bitsat",
        "comedk_card": "exam-card-comedk",
        "mock_tests_link": "exam-card-mock-tests-link",
        "chapter_wise_link": "exam-card-chapter-wise-link",
        "results_link": "exam-card-results-link"
      }
    },
    "C_results_and_reports": {
      "goal": "Show rank/percentile, correct/wrong/skipped %, subject/topic graphs, and step-by-step solutions with AI provenance + error disclosure.",
      "top_summary": {
        "components": [
          "Existing results summary strip style (score-card + stat tiles)",
          "Add percentile + rank tiles (same visual weight as correct/wrong)"
        ],
        "data-testid": {
          "rank_value": "results-rank-value",
          "percentile_value": "results-percentile-value",
          "correct_value": "results-correct-value",
          "wrong_value": "results-wrong-value",
          "skipped_value": "results-skipped-value"
        }
      },
      "tabs": {
        "tabs_list": [
          "Overview",
          "Subjects",
          "Topics",
          "Solutions",
          "Cohort"
        ],
        "components": [
          "shadcn Tabs",
          "shadcn Table for breakdowns",
          "Recharts for graphs"
        ],
        "data-testid": {
          "results-tabs": "results-tabs",
          "results-tab-overview": "results-tab-overview",
          "results-tab-solutions": "results-tab-solutions"
        }
      },
      "solutions_view": {
        "structure": [
          "Question header row: Q#, status badge (Correct/Wrong/Skipped), time spent",
          "Student answer vs correct answer",
          "Step-by-step solution (collapsible sections)",
          "Provenance block (always visible): model, confidence band, known limitations",
          "Error reporting CTA: 'Report an issue in solution'"
        ],
        "provenance_disclosure": {
          "component": "Alert (variant: neutral/amber) + small mono metadata",
          "copy": [
            "Solutions are AI-generated from your uploaded source. They may contain mistakes.",
            "If a solution conflicts with the official key, the key is authoritative.",
            "We show evidence (source snippet) where possible."
          ],
          "data-testid": {
            "solution-provenance-alert": "solution-provenance-alert",
            "solution-report-issue-button": "solution-report-issue-button"
          }
        }
      },
      "cohort_analytics": {
        "rule": "Honor existing authoritative cohort threshold >= 100 attempts before showing rank/percentile distribution; below that show 'insufficient cohort' state.",
        "empty_state": {
          "copy": "Cohort analytics unlock after 100+ attempts to keep percentiles stable.",
          "component": "Card + Badge(neutral) + small explanation",
          "data-testid": "cohort-threshold-empty-state"
        },
        "charts": [
          "Percentile distribution (histogram bar chart)",
          "Subject-wise accuracy distribution",
          "Top mistakes/topics (table)"
        ]
      }
    },
    "D_exam_player_fit_reset": {
      "requirement": "Fit reset on every question (source image zoom/pan resets).",
      "ui_affordance": {
        "control": "Add a small 'Fit' button near zoom controls; on question change, animate a brief 'Fit applied' toast (sonner).",
        "data-testid": {
          "fit_button": "question-fit-button",
          "zoom_in": "question-zoom-in-button",
          "zoom_out": "question-zoom-out-button"
        }
      }
    }
  },
  "micro_interactions_motion": {
    "principles": [
      "Motion communicates state changes (processing → live), not decoration.",
      "Use short durations: 160–220ms; ease-out for entrances; ease-in for exits.",
      "Never use transition: all. Only transition background-color, border-color, box-shadow, opacity."
    ],
    "patterns": {
      "stepper": "Animate stage completion with a subtle checkmark fade + progress bar fill.",
      "copy_link": "On copy: button label changes to 'Copied' for 1.2s + sonner toast.",
      "publish_complete": "Right-column Live card does a gentle scale-in (1.00→1.02→1.00) once.",
      "charts": "Animate chart reveal on tab switch (opacity + y translate 6px)."
    }
  },
  "accessibility": {
    "requirements": [
      "WCAG AA contrast: maroon on white is fine; avoid maroon text on brand-soft if too low—use navy for body.",
      "All controls must be keyboard reachable; focus-visible outline already defined globally.",
      "Use aria-label for icon-only buttons (copy, open, fit).",
      "Tables must have proper headers; charts must have textual summaries below for screen readers."
    ],
    "touch_targets": "Minimum 44px height (already aligned with --touch-target and existing .btn)."
  },
  "data_testid_conventions": {
    "rules": [
      "kebab-case",
      "describe role not appearance",
      "apply to: buttons, links, inputs, tabs, dialogs, key metrics, error messages"
    ],
    "examples": [
      "smartimport-upload-input",
      "smartimport-start-import-button",
      "import-progress-stage-generate-solutions",
      "results-percentile-value",
      "solution-step-collapsible-trigger"
    ]
  },
  "image_urls": {
    "policy": "No stock photography required; prefer UI-native illustrations already present (grid/orbital) or simple SVG icons. If images are needed later, use neutral academic textures (paper, grid) without gradients.",
    "categories": []
  },
  "instructions_to_main_agent": {
    "binding_addendum_auto_publish": [
      "Remove/avoid any UI copy that implies 'manual review' or 'approval required'. Replace with 'automated validation' and 'auto-publish'.",
      "Auto-publish default ON; only fatal validation blocks publishing.",
      "Always show disclosures: AI-generated solutions + potential errors + evidence links.",
      "Preserve existing matte maroon (#5C0025) and Figtree; do not introduce purple or saturated gradients.",
      "Use shadcn/ui components from /src/components/ui (JS). Do not use raw HTML dropdowns/calendars/toasts.",
      "All interactive + key informational elements must include data-testid.",
      "Honor cohort analytics threshold >=100 attempts; below that show stable empty state."
    ],
    "implementation_notes_js": [
      "Components are .jsx; keep examples and imports in JS (not TSX).",
      "Prefer composition: <Card><CardHeader/><CardContent/></Card> etc.",
      "Use sonner for toasts (existing shadcn wrapper)."
    ]
  },
  "general_ui_ux_design_guidelines_appendix": "<General UI UX Design Guidelines>  \n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
