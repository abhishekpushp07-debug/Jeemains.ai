{
  "design_exam_refinement": {
    "doc_type": "standalone_design_exam_refinement",
    "scope": {
      "goal": "Concrete incremental UI/UX refinement directions for the chapter-wise exam experience (catalog → preflight → player → results) and owner verification surfaces, without re-architecture, without palette reset, and without adding photos/new brand assets.",
      "must_preserve": [
        "Matte maroon brand #5C0025 (already mapped to --blue/--brand-text and --primary)",
        "Existing tokens in /app/frontend/src/index.css and /app/frontend/src/App.css",
        "Existing typography: Figtree UI + Roboto Mono for numeric/meta",
        "Existing scoring/safety contracts (no changes)",
        "Phone-only student login",
        "All 94 live tests"
      ],
      "non_goals": [
        "No new palette, no new fonts, no photos/illustrations",
        "No new marketing hero blocks on /exams",
        "No invented solutions or option crops unless backed by real source refs",
        "No changes to protected source assets",
        "No generic audit essay—only implementable layout/token/component guidance"
      ]
    },

    "brand_personality": {
      "keywords": ["exam-serious", "matte", "trust-first", "dense-but-readable", "mobile-first", "evidence-driven"],
      "tone": "Authoritative and calm. Prefer compact, scannable rows and explicit disclosures over decorative UI.",
      "visual_rules": [
        "No gradients beyond existing minimal usage; never on reading areas.",
        "Use borders + subtle shadow tint (var(--shadow-tint)) for hierarchy.",
        "Prefer mono numerals for time, counts, IDs, and validity dates."
      ]
    },

    "design_tokens_and_css": {
      "source_of_truth": ["/app/frontend/src/index.css", "/app/frontend/src/App.css"],
      "do_not_change": [
        "--blue / --brand-text mapping to #5C0025",
        "--surface-card, --surface-alt, --line, --shadow-tint",
        "--touch-target (2.75rem)"
      ],
      "additive_tokens_allowed": {
        "note": "Only add if a missing semantic is required for exam refinement; otherwise use existing tokens.",
        "suggested": {
          "--chip-bg": "var(--surface-alt)",
          "--chip-border": "var(--line)",
          "--chip-fg": "var(--text-muted)",
          "--sticky-scrim": "linear-gradient(to top, rgba(248,250,252,0.96), rgba(248,250,252,0))"
        }
      },
      "css_rules": [
        "Never use transition: all.",
        "Touch targets: min-height >= var(--touch-target) for any tappable control.",
        "Avoid shrink-to-fit for source images; prefer a dedicated readable viewport with Fit/Readable controls.",
        "Keep scroll-padding-top consistent with sticky headers (already set in App.css)."
      ]
    },

    "typography": {
      "fonts": {
        "ui": "Figtree",
        "mono": "Roboto Mono"
      },
      "hierarchy": {
        "page_title": "text-2xl sm:text-3xl font-semibold tracking-tight",
        "compact_subtitle": "text-sm text-muted-foreground",
        "row_title": "text-base font-semibold leading-snug",
        "meta": "text-xs text-muted-foreground",
        "numbers": "tabular-nums font-mono"
      },
      "copy_rules": [
        "Avoid absolute claims like ‘verified’. Use scoped language: ‘check passed’.",
        "Repeat critical disclosures near actions (Start attempt, Submit, Results review).",
        "Never imply worked solutions exist; always say ‘answer keys only’."
      ]
    },

    "layout_and_components": {
      "component_paths_shadcn": {
        "catalog": [
          "/app/frontend/src/components/ui/input.jsx",
          "/app/frontend/src/components/ui/select.jsx",
          "/app/frontend/src/components/ui/tabs.jsx",
          "/app/frontend/src/components/ui/card.jsx",
          "/app/frontend/src/components/ui/badge.jsx",
          "/app/frontend/src/components/ui/scroll-area.jsx",
          "/app/frontend/src/components/ui/skeleton.jsx",
          "/app/frontend/src/components/ui/separator.jsx",
          "/app/frontend/src/components/ui/button.jsx"
        ],
        "preflight": [
          "/app/frontend/src/components/ui/alert.jsx",
          "/app/frontend/src/components/ui/checkbox.jsx",
          "/app/frontend/src/components/ui/button.jsx",
          "/app/frontend/src/components/ui/card.jsx"
        ],
        "player": [
          "/app/frontend/src/components/ui/tabs.jsx",
          "/app/frontend/src/components/ui/toggle-group.jsx",
          "/app/frontend/src/components/ui/button.jsx",
          "/app/frontend/src/components/ui/dialog.jsx",
          "/app/frontend/src/components/ui/drawer.jsx",
          "/app/frontend/src/components/ui/scroll-area.jsx",
          "/app/frontend/src/components/ui/separator.jsx"
        ],
        "results": [
          "/app/frontend/src/components/ui/tabs.jsx",
          "/app/frontend/src/components/ui/table.jsx",
          "/app/frontend/src/components/ui/drawer.jsx",
          "/app/frontend/src/components/ui/dialog.jsx",
          "/app/frontend/src/components/ui/badge.jsx",
          "/app/frontend/src/components/ui/button.jsx",
          "/app/frontend/src/components/ui/input.jsx"
        ]
      },

      "page_blueprints": {
        "student_exams_catalog": {
          "route": "/exams",
          "primary_goal": "First actionable test row visible quickly on mobile; search + subject filter always within reach.",
          "header_compaction": {
            "problem": "Current .chapter-exams-heading + rules panel can consume too much above-the-fold height on mobile.",
            "solution": [
              "Convert header into a compact stack: Title (1 line) + subtitle (1 line) + a single disclosure row.",
              "Move long rules into a <details> disclosure ‘About chapter tests’.",
              "Keep the disclosure ‘Answer keys only’ always visible (not inside details)."
            ],
            "acceptance_criteria": [
              "On 390×844, first test row title is visible within ~400px scroll.",
              "Header block height target: <= 220px on mobile (excluding sticky filter bar)."
            ]
          },
          "sticky_filter_bar": {
            "pattern": "Sticky top filter/search bar below site header; includes Subject tabs + Search input + optional Chapter select.",
            "behavior": [
              "Sticky only after user scrolls past header; avoid double-sticky with site header.",
              "Search input uses existing debounce; show result count next to it in mono.",
              "Provide ‘Clear’ as a quiet button when filters active."
            ],
            "data_testids": {
              "search": "exams-catalog-search-input",
              "subject_tabs": "exams-catalog-subject-tabs",
              "clear": "exams-catalog-clear-filters-button",
              "result_count": "exams-catalog-result-count"
            }
          },
          "default_density": {
            "rule": "Default view must be compact rows (not large cards) for 94 items.",
            "row_anatomy": [
              "Left: Chapter badge (mono) + Chapter title",
              "Middle: meta chips: ‘50Q’, ‘60m’, ‘+3/−1’, ‘Valid until …’ (if applicable)",
              "Right: primary CTA (Start/Resume/View results)"
            ],
            "row_interactions": [
              "Row hover (desktop): background var(--surface-alt), border-color var(--text-muted) (subtle).",
              "Primary CTA is the only filled button; secondary actions are outline/quiet.",
              "Entire row may be clickable only if it does not conflict with CTA; otherwise keep CTA-only to avoid mis-taps on mobile."
            ],
            "data_testids": {
              "row": "exams-catalog-row",
              "start": "exams-catalog-start-button",
              "resume": "exams-catalog-resume-button",
              "results": "exams-catalog-results-link"
            }
          }
        },

        "set_preflight": {
          "route": "/sets/:id",
          "copy_corrections": {
            "replace": {
              "from": "Connection, source images and saving verified.",
              "to": "Connection check passed. Saving is enabled on this device. You can zoom source images during the attempt."
            },
            "add_disclosure": "If any source image fails to load during the attempt, answering will pause until it loads."
          },
          "mobile_cta": {
            "pattern": "Sticky bottom Start button once checks pass + user acknowledges rules.",
            "safe_area": "Add padding-bottom: env(safe-area-inset-bottom) where supported.",
            "data_testids": {
              "start": "preflight-start-attempt-button",
              "sticky_bar": "preflight-sticky-actionbar"
            }
          }
        },

        "attempt_player": {
          "route": "/attempts/:id",
          "source_readability": {
            "problem": "Source images can appear tiny due to shrink-to-fit patterns; students need a readable horizontal viewport on mobile.",
            "pattern": "Inline Source Viewport (not full-screen by default) with Fit/Readable controls.",
            "controls": [
              "ToggleGroup: Fit | Readable",
              "Zoom: − / +",
              "Pan: drag canvas (already supported by .source-pan-canvas)",
              "Open full-screen (Dialog/Drawer)"
            ],
            "mobile_rule": "Default to ‘Readable’ on phones if it does not exceed viewport height; otherwise Fit with a one-tap switch.",
            "data_testids": {
              "viewport": "player-source-viewport",
              "fit": "player-source-fit-toggle",
              "readable": "player-source-readable-toggle",
              "zoom_in": "player-source-zoom-in-button",
              "zoom_out": "player-source-zoom-out-button",
              "fullscreen": "player-source-fullscreen-button"
            }
          },
          "source_rendered_options_one_zoom_rule": {
            "policy": [
              "Never invent typed options if extraction is uncertain.",
              "If render_mode === 'source' and options are not typed, ensure the student can see all options with one zoom action maximum."
            ],
            "allowed_patterns": [
              "Options strip image anchored below stem (single zoom target).",
              "Option-region thumbnails ONLY if backed by real source refs (no guessed crops)."
            ],
            "data_testids": {
              "options_strip": "player-options-strip-image",
              "options_strip_open": "player-options-strip-open-button"
            }
          },
          "keyboard_shortcuts_desktop": {
            "note": "Optional but recommended; must not interfere with typing in inputs.",
            "bindings": [
              {"key": "ArrowLeft", "action": "Previous question"},
              {"key": "ArrowRight", "action": "Next question"},
              {"key": "A/B/C/D", "action": "Select option"},
              {"key": "M", "action": "Toggle mark for review"}
            ],
            "data_testids": {
              "shortcut_help": "player-shortcuts-help"
            }
          }
        },

        "results": {
          "route": "/results/:id",
          "progressive_disclosure": {
            "rule": "Keep summary + report CTA prominent; collapse heavy tables by default; keep review list scannable.",
            "add_notice": "Attempts are saved and cannot be edited.",
            "data_testid": "results-attempt-immutable-notice"
          },
          "key_only_disclosure": {
            "rule": "Repeat ‘Answer keys only’ near any solution/answer reveal area.",
            "data_testid": "results-answer-keys-only-disclosure"
          }
        }
      }
    },

    "motion_and_microinteractions": {
      "principles": [
        "Micro-animations only where they clarify state: hover elevation, pressed state, skeleton shimmer.",
        "No parallax; this is an exam tool.",
        "Prefer instant list updates over animated reflow to avoid jank on low-end phones."
      ],
      "recommended_classes": {
        "row_hover": "transition-[background-color,border-color,box-shadow] duration-200 hover:bg-[color:var(--surface-alt)] hover:shadow-sm",
        "button_press": "active:translate-y-[1px]",
        "focus": "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--focus-ring)] focus-visible:ring-offset-2"
      }
    },

    "accessibility_and_testing": {
      "a11y": [
        "Touch targets >= 44px (var(--touch-target)).",
        "Focus-visible must remain strong; do not remove outlines.",
        "Do not rely on color alone for status; pair with text/badge labels.",
        "Dialogs/Drawers must have titles (sr-only acceptable) and Esc-to-close."
      ],
      "data_testid": {
        "rule": "All interactive and key informational elements MUST include data-testid in kebab-case describing role.",
        "examples": [
          "exams-catalog-search-input",
          "exams-catalog-start-button",
          "preflight-start-attempt-button",
          "player-source-readable-toggle",
          "results-attempt-immutable-notice"
        ]
      }
    },

    "image_urls": {
      "policy": "No photos/new palette. Use no new images beyond existing source assets. If any decorative texture is needed, use CSS-only noise at extremely low opacity and only on non-reading backgrounds.",
      "urls": []
    },

    "instructions_to_main_agent": [
      "Treat this as an incremental refinement: compact /exams header, sticky filter bar, default compact rows.",
      "Do not change global tokens; use existing matte maroon system.",
      "Preflight copy must remove absolute ‘verified’ language.",
      "Player must prioritize source readability: inline viewport with Fit/Readable controls; avoid tiny shrink-to-fit.",
      "For source-rendered MCQ options, enforce one-zoom rule via options strip or real source-backed thumbnails—never guessed crops.",
      "All new/modified React components must be .js (not .tsx) and include data-testid on interactive + key informational elements."
    ]
  },

  "general_ui_ux_design_guidelines": "    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
