{
  "design_simple_navigation_addendum": {
    "brand": {
      "name": "jeemains.ai",
      "positioning": {
        "primary_claim": "100% free for all students",
        "claim_rules": {
          "rule": "If mentioning 60/75 or 120+ overlap numbers, label them as PREPARATION TARGETS (not guarantees) and show disclaimer on the same poster block (not fine print).",
          "required_disclaimer_copy": "Preparation targets (not a guarantee): these numbers describe our goal for concept coverage based on PYQ-style practice. Actual exam questions may differ."
        }
      },
      "visual_personality": {
        "keywords": [
          "exam-serious",
          "premium-but-free",
          "poster-led",
          "matte",
          "high-contrast",
          "mobile-first"
        ],
        "do_not": [
          "No purple gradients",
          "No centered app-wide text alignment",
          "No busy nav after login",
          "No stock photos required"
        ]
      }
    },
    "scope": {
      "goal": "Implement extremely simple logged-in navigation (3 exam cards → 3 hub cards) and a public pre-signup landing that foregrounds 100% free with poster-style blocks. Also enforce FIT (not readable) as default question view mode across question changes.",
      "pages": {
        "public": ["/"],
        "auth": ["/login", "/signup"],
        "app_logged_in": [
          "/home",
          "/exams/:examSlug",
          "/exams/:examSlug/mocks",
          "/exams/:examSlug/chapters",
          "/exams/:examSlug/results"
        ],
        "unchanged": ["player", "resultdetail"]
      }
    },
    "information_architecture": {
      "header_rules": {
        "public_header": {
          "left": "Logo jeemains.ai",
          "right": [
            "Login (text link)",
            "Start free (primary button)"
          ],
          "no": ["My Practice", "complex menus"],
          "data_testids": {
            "logo": "public-header-logo",
            "login_link": "public-header-login-link",
            "start_free_button": "public-header-start-free-button"
          }
        },
        "logged_in_header": {
          "principle": "Keep header minimal; avoid multi-link nav. Prefer breadcrumb + page title + profile menu only.",
          "allowed_items": ["Logo", "Breadcrumb", "Profile dropdown"],
          "data_testids": {
            "logo": "app-header-logo",
            "breadcrumb": "app-header-breadcrumb",
            "profile_menu": "app-header-profile-menu"
          }
        }
      },
      "logged_in_primary_flow": {
        "home": {
          "layout": "Single section: ‘Choose your exam’ + 3 large cards (JEE Main, BITSAT, COMEDK).",
          "cards": {
            "pattern": "Entire card clickable (Card as link) + explicit CTA button inside for clarity.",
            "grid": "mobile: 1-col; md+: 3-col; generous gaps.",
            "data_testids": {
              "grid": "exam-home-exam-card-grid",
              "jee": "exam-home-exam-card-jee-main",
              "bitsat": "exam-home-exam-card-bitsat",
              "comedk": "exam-home-exam-card-comedk"
            }
          }
        },
        "exam_hub": {
          "route": "/exams/:examSlug",
          "layout": "Top: breadcrumb (Home → Exam). Body: 3 hub cards only: Mock tests, Chapter-wise tests, Results.",
          "hub_cards": {
            "data_testids": {
              "mock": "exam-hub-card-mocks",
              "chapters": "exam-hub-card-chapters",
              "results": "exam-hub-card-results"
            }
          }
        },
        "mocks": {
          "route": "/exams/:examSlug/mocks",
          "layout": "List of Live mocks + Full tests (if applicable). Use filters as Tabs: Live | Upcoming | Ended | All.",
          "data_testids": {
            "tabs": "mocks-filter-tabs",
            "list": "mocks-list",
            "mock_card": "mocks-mock-card",
            "start_button": "mocks-start-button"
          }
        },
        "chapters": {
          "route": "/exams/:examSlug/chapters",
          "layout": "Subject-wise → chapter-wise catalogue. First show subject cards (Physics/Chem/Math etc), then chapter list.",
          "navigation_rule": "No extra navigation items; keep within page using Breadcrumb + Tabs/Accordion.",
          "data_testids": {
            "subject_grid": "chapters-subject-grid",
            "subject_card": "chapters-subject-card",
            "chapter_list": "chapters-chapter-list",
            "chapter_row": "chapters-chapter-row"
          }
        },
        "results": {
          "route": "/exams/:examSlug/results",
          "layout": "Two filters: Attempt type (Mock/Chapter-wise) + Time range. Then list previous attempts. Each attempt opens detailed solutions + analysis.",
          "immediacy_rule": "After exam submission, show result + analysis immediately (no waiting screen beyond necessary scoring).",
          "data_testids": {
            "attempt_type_tabs": "results-attempt-type-tabs",
            "attempt_list": "results-attempt-list",
            "attempt_row": "results-attempt-row",
            "open_attempt": "results-open-attempt-button"
          }
        }
      },
      "breadcrumbs": {
        "pattern": "Home → Exam → Section (Mocks/Chapters/Results)",
        "component": "/app/frontend/src/components/ui/breadcrumb.jsx",
        "data_testid": "app-breadcrumb"
      }
    },
    "public_landing_posters": {
      "first_viewport_requirement": {
        "must_show": [
          "100% free for all students (primary)",
          "Brand name jeemains.ai",
          "Start free CTA",
          "Short value prop: mock tests + chapter-wise + instant results"
        ],
        "no": ["long paragraphs", "multiple competing CTAs"]
      },
      "poster_block_system": {
        "principle": "Use 3–5 distinct poster blocks (different compositions) instead of three identical cards. No stock photos needed; use typographic posters + subtle grid/noise.",
        "poster_blocks": [
          {
            "id": "poster-free",
            "headline": "100% free for all students",
            "layout": "Big type left, stamp-style badge right, small supporting bullets below.",
            "badge_copy": "FREE",
            "data_testid": "poster-free"
          },
          {
            "id": "poster-jee-target",
            "headline": "JEE Main: concept-first mock tests",
            "highlight_line": "Preparation target: 60/75 questions will share core concepts",
            "disclaimer": "Preparation targets (not a guarantee): these numbers describe our goal for concept coverage based on PYQ-style practice. Actual exam questions may differ.",
            "layout": "Split panel: left headline + disclaimer, right big number ‘60/75’ in mono.",
            "data_testid": "poster-jee-target"
          },
          {
            "id": "poster-bitsat-target",
            "headline": "BITSAT: speed + coverage",
            "highlight_line": "Preparation target: 120+ questions will share core concepts",
            "disclaimer": "Preparation targets (not a guarantee): these numbers describe our goal for concept coverage based on PYQ-style practice. Actual exam questions may differ.",
            "layout": "Diagonal accent stripe (very mild) + stacked text; big ‘120+’ as anchor.",
            "data_testid": "poster-bitsat-target"
          },
          {
            "id": "poster-how-it-works",
            "headline": "Practice → Submit → Instant analysis",
            "layout": "3-step mini timeline using icons + short lines.",
            "data_testid": "poster-how-it-works"
          },
          {
            "id": "poster-comedk",
            "headline": "COMEDK: clean chapter-wise practice",
            "layout": "Compact poster with subject chips + CTA.",
            "data_testid": "poster-comedk"
          }
        ]
      }
    },
    "question_view_mode_fit_default": {
      "problem": "Currently question text renders in readable default; user wants FIT default and it must persist when moving to next question.",
      "design_rule": {
        "default": "FIT",
        "persistence": "User requirement takes precedence: reset to FIT with zoom 1 and pan 0 on EVERY question/source change, including Next, Previous, jump and refresh. Optional Readable must never persist across questions; no localStorage preference.",
        "control": "A small ToggleGroup in player header or question top line: Fit | Readable.",
        "copy": "Fit keeps the whole question visible. Switch to Readable if you want larger text.",
        "data_testids": {
          "toggle_group": "player-viewmode-toggle",
          "fit": "player-viewmode-fit",
          "readable": "player-viewmode-readable"
        }
      },
      "css_behavior": {
        "fit": "Reduce base font-size slightly and tighten line-height; ensure KaTeX display remains scrollable.",
        "readable": "Increase font-size and spacing; never overflow horizontally.",
        "no_transition_all": true
      }
    },
    "design_tokens_additions": {
      "instruction": "Do not replace existing matte maroon palette. Add only a few semantic tokens for poster accents and stamps.",
      "css_custom_properties_to_add": {
        "--poster-paper": "#FFFFFF",
        "--poster-ink": "#0B1F2A",
        "--poster-wash": "#FBF7F5",
        "--poster-stamp": "#5C0025",
        "--poster-stamp-soft": "#F6E9EE",
        "--noise-opacity": "0.06"
      }
    },
    "layout_specs": {
      "containers": {
        "public": "Use existing .container; hero uses .hero-grid but simplify copy blocks.",
        "logged_in": "Use .page + .container; avoid center alignment; keep max widths readable."
      },
      "grids": {
        "exam_cards": "grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6",
        "hub_cards": "grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6",
        "poster_blocks": "grid grid-cols-1 lg:grid-cols-12 gap-4 md:gap-6"
      },
      "spacing": {
        "rule": "Use 2–3x more spacing than feels comfortable; prefer p-5 sm:p-6 for cards; section spacing mt-8 sm:mt-10."
      }
    },
    "components_to_use": {
      "shadcn_paths": [
        "/app/frontend/src/components/ui/card.jsx",
        "/app/frontend/src/components/ui/button.jsx",
        "/app/frontend/src/components/ui/badge.jsx",
        "/app/frontend/src/components/ui/breadcrumb.jsx",
        "/app/frontend/src/components/ui/tabs.jsx",
        "/app/frontend/src/components/ui/separator.jsx",
        "/app/frontend/src/components/ui/accordion.jsx",
        "/app/frontend/src/components/ui/toggle-group.jsx",
        "/app/frontend/src/components/ui/scroll-area.jsx",
        "/app/frontend/src/components/ui/skeleton.jsx"
      ],
      "custom_components_to_create_js": [
        {
          "name": "ExamHomeCards",
          "file": "frontend/src/components/exams/ExamHomeCards.js",
          "purpose": "Render the 3 large exam cards with consistent hover/press states.",
          "data_testids": ["exam-home-exam-card-grid", "exam-home-exam-card-jee-main"]
        },
        {
          "name": "ExamHubCards",
          "file": "frontend/src/components/exams/ExamHubCards.js",
          "purpose": "Render the 3 hub cards (Mocks/Chapters/Results) for a selected exam.",
          "data_testids": ["exam-hub-card-mocks", "exam-hub-card-results"]
        },
        {
          "name": "PosterBlock",
          "file": "frontend/src/components/marketing/PosterBlock.js",
          "purpose": "Reusable poster-style block with variants (stamp, split, diagonal stripe).",
          "data_testids": ["poster-free", "poster-jee-target"]
        },
        {
          "name": "PlayerViewModeToggle",
          "file": "frontend/src/components/player/PlayerViewModeToggle.js",
          "purpose": "Fit/Readable toggle persisted across question navigation.",
          "data_testids": ["player-viewmode-toggle", "player-viewmode-fit"]
        }
      ]
    },
    "motion_microinteractions": {
      "card_hover": "transition-[background-color,border-color,box-shadow] duration-200 hover:shadow-[0_10px_24px_var(--shadow-tint)]",
      "card_press": "active:translate-y-[1px]",
      "poster_stamp": "On hover: slight rotate (1deg) + shadow increase; keep subtle.",
      "scroll": "Poster blocks can fade-up on scroll using IntersectionObserver (no heavy libs required)."
    },
    "accessibility": {
      "rules": [
        "All cards that are links must have visible focus ring and an internal CTA button for clarity.",
        "Touch targets >= 44px.",
        "Disclaimers must be readable (>= text-xs) and placed inside the same poster block as the target claim.",
        "Do not rely on color alone for status; use text + icon."
      ]
    },
    "data_testid_policy": {
      "rule": "All interactive and key informational elements MUST include data-testid (kebab-case, role-based).",
      "minimum_new": [
        "public-header-start-free-button",
        "poster-free",
        "exam-home-exam-card-jee-main",
        "exam-hub-card-mocks",
        "player-viewmode-toggle",
        "results-attempt-list"
      ]
    },
    "instructions_to_main_agent": [
      "Rename platform to jeemains.ai everywhere in UI (logo, titles, metadata) without changing backend namespaces/storage attribution.",
      "Public landing: first viewport must clearly show ‘100% free for all students’ + Start free CTA.",
      "Use poster-style blocks (distinct layouts) for JEE/BITSAT/COMEDK messaging; if using 60/75 or 120+ numbers, label as PREPARATION TARGETS and include disclaimer in the same block.",
      "Logged-in: remove ‘My Practice’ from top nav; implement simple flow: /home shows 3 exam cards → /exams/:examSlug shows 3 hub cards → section pages.",
      "Player: default question view mode must be FIT and must persist across next/prev question navigation.",
      "All new components must be .js (not .tsx) and use shadcn/ui primitives; add data-testid to every interactive and key info element.",
      "No universal transitions; do not use gradients beyond mild decorative accents under 20% viewport."
    ]
  }
}
