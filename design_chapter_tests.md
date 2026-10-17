{
  "doc_type": "additive_design_chapter_tests",
  "target_file": "/app/design_chapter_tests.md",
  "scope_note": "Additive chapter-tests design chapter. Do NOT rewrite existing design_guidelines.md. Keep existing palette (matte maroon #5C0025), tokens, Figtree/Roboto Mono, shadcn/ui + Lucide. No decorative images/new identity.",
  "brand_and_constraints": {
    "audience": ["BITSAT students", "Owner/Admin"],
    "product_truth": {
      "no_solutions": "Books contain ANSWER KEYS ONLY. UI must disclose this clearly and never fabricate solutions.",
      "answer_key_visibility": "Answer-key pages must NEVER be shown inside active Player.",
      "attempts": "Persisted attempts are immutable; UI must communicate immutability in results/review screens."
    },
    "test_rules": {
      "questions_per_test": 50,
      "duration_minutes": 60,
      "marking": {"correct": 3, "wrong": -1, "unanswered": 0},
      "availability": "Each published test has 1-year validity window (live/unlive independent of timer).",
      "results": "Immediate results after submission (no embargo)."
    },
    "tech": {
      "frontend": "React (.js), Tailwind, shadcn/ui primitives in /frontend/src/components/ui",
      "backend": "FastAPI + Mongo",
      "state": "Prefer existing patterns; if adding, use TanStack Query for server state + lightweight local draft persistence (localStorage)."
    },
    "testing": {
      "data_testid": "All interactive + key informational elements MUST include data-testid in kebab-case describing role."
    }
  },
  "information_architecture": {
    "nav": {
      "add_entry": {
        "label": "Exams",
        "route": "/exams",
        "icon": "lucide:GraduationCap",
        "data-testid": "nav-exams-link"
      },
      "studio": {
        "existing": "Studio/StudioImport remains; add a new import mode: Chapter-book (single combined PDF)."
      }
    },
    "routes": {
      "admin": [
        {
          "path": "/studio/import",
          "add_section": "Chapter-book mode",
          "purpose": "Upload one combined chapter book PDF (with answer keys), auto-split chapters, generate chapter-wise tests, verify counts/keys, publish with 1-year validity."
        },
        {
          "path": "/studio/sets/:setId",
          "add_section": "Chapter tests verification + publish controls",
          "purpose": "Per-test recheck workflow + live/unlive + validity dates."
        }
      ],
      "student": [
        {
          "path": "/exams",
          "purpose": "Catalog of available chapter-wise tests by Subject → Chapter → Test."
        },
        {
          "path": "/exams/:examId/preflight",
          "note": "Reuse existing preflight/player/results engine; do not duplicate."
        }
      ]
    }
  },
  "layout_blueprints": {
    "student_catalog_exams_page": {
      "layout": "Mobile-first single column; on lg: two-column with filters left (sticky) and results right.",
      "structure": [
        {
          "block": "PageHeader",
          "components": ["Breadcrumb", "Input", "Select", "Badge"],
          "content": {
            "title": "Exams",
            "subtitle": "Chapter-wise tests (50 questions • 60 min • +3/−1)",
            "disclosure": "Answer keys only. No worked solutions provided."
          },
          "data-testid": {
            "search": "exams-catalog-search-input",
            "subject": "exams-catalog-subject-select",
            "chapter": "exams-catalog-chapter-select"
          }
        },
        {
          "block": "CatalogList",
          "pattern": "Card list with compact metadata row + primary CTA",
          "card_fields": [
            "Subject",
            "Chapter name",
            "Questions: 50",
            "Time: 60 min",
            "Marking: +3/−1",
            "Availability badge: Live / Unavailable / Expired",
            "Attempt status: Not started / In progress / Completed"
          ],
          "cta": {
            "primary": "Start",
            "secondary": "Resume (if draft exists)",
            "tertiary": "View results (if completed)"
          },
          "data-testid": {
            "card": "exams-catalog-test-card",
            "start": "exams-catalog-start-button",
            "resume": "exams-catalog-resume-button",
            "results": "exams-catalog-results-link"
          }
        }
      ],
      "empty_loading_error": {
        "loading": "Use <Skeleton> list rows (3–6) with shimmer; keep layout stable.",
        "empty": "Use existing .empty-state styling: 'No tests found' + reset filters button.",
        "error": "Inline <Alert variant=destructive> with retry button."
      }
    },
    "admin_chapter_book_import": {
      "layout": "Wizard-like within existing StudioImport page: 3 stages shown as a horizontal stepper (existing .studio-stage style).",
      "stages": [
        {
          "name": "Upload",
          "goal": "Upload single combined PDF (chapter book).",
          "ui": [
            "Card: Upload dropzone",
            "Input: Set name",
            "Select: Subject (Physics/Chemistry/Math)",
            "Switch: 'Contains answer key pages' (default ON)",
            "Button: Upload & Analyze"
          ],
          "data-testid": {
            "file": "chapter-book-upload-input",
            "subject": "chapter-book-subject-select",
            "set-name": "chapter-book-set-name-input",
            "upload": "chapter-book-upload-submit-button"
          }
        },
        {
          "name": "Split & Map Chapters",
          "goal": "Auto-detect chapters; allow manual corrections.",
          "ui": [
            "Left: Chapter list (ScrollArea) with status chips",
            "Right: PDF preview (page thumbnails + current page) for boundary verification",
            "Per chapter row: startPage/endPage inputs + 'Re-run split for this chapter'",
            "Button: Confirm chapter boundaries"
          ],
          "chapter_row_fields": ["chapterTitle", "startPage", "endPage", "questionCountEstimate", "answerKeyPagesDetected"],
          "data-testid": {
            "chapter-list": "chapter-split-chapter-list",
            "chapter-row": "chapter-split-chapter-row",
            "confirm": "chapter-split-confirm-button"
          }
        },
        {
          "name": "Generate Tests & Verify",
          "goal": "Create 50Q/60min tests per chapter; verify answer keys and counts before publish.",
          "ui": [
            "Table: chapters → generated tests",
            "Per test: status (Draft/Needs review/Ready/Published)",
            "Per test actions: Open verification, Run recheck, Publish toggle",
            "Global: 'Publish all ready' disabled until all tests pass verification"
          ],
          "data-testid": {
            "tests-table": "chapter-tests-table",
            "publish-all": "chapter-tests-publish-all-button"
          }
        }
      ],
      "progress_and_jobs": {
        "pattern": "Upload → async processing job → poll/SSE updates",
        "components": ["Progress", "Alert", "Sonner toast"],
        "copy": {
          "processing": "Analyzing PDF… This can take a few minutes for large books.",
          "warning": "Do not close this tab during upload. You can safely leave during analysis; progress will resume when you return."
        },
        "data-testid": {
          "job-status": "chapter-book-job-status",
          "job-progress": "chapter-book-job-progress"
        }
      }
    },
    "admin_test_verification_drawer": {
      "container": "Use <Drawer> on mobile, <Dialog> on desktop (max-w ~ 56rem).",
      "layout": "Split view: left verification checklist, right question preview.",
      "left_panel": {
        "sections": [
          {
            "title": "Hard checks (must pass)",
            "items": [
              "Exactly 50 questions",
              "Timer set to 60 minutes",
              "Marking rule +3/−1/0",
              "Answer key present for all questions",
              "No answer-key pages included in player question images",
              "Formula safety: if OCR/typed extraction uncertain, attach source image"
            ]
          },
          {
            "title": "Spot checks (recommended)",
            "items": [
              "Random 5 questions: options visible and not cropped",
              "No duplicate questions",
              "Chapter label matches content"
            ]
          }
        ],
        "controls": [
          "Checkbox list with per-item status",
          "Button: Run automated recheck",
          "Button: Mark as Ready",
          "Button: Publish (only when Ready)"
        ],
        "data-testid": {
          "recheck": "test-verification-recheck-button",
          "mark-ready": "test-verification-mark-ready-button",
          "publish": "test-verification-publish-button"
        }
      },
      "right_panel": {
        "components": ["Tabs", "ScrollArea", "AspectRatio"],
        "tabs": [
          {
            "name": "Question images",
            "behavior": "Show question+options images only. Never show answer-key pages."
          },
          {
            "name": "Answer key",
            "behavior": "Admin-only view: show extracted answer key mapping (Q1→A etc)."
          },
          {
            "name": "Issues",
            "behavior": "List detected problems with jump links to question numbers."
          }
        ],
        "data-testid": {
          "preview": "test-verification-preview-panel",
          "answer-key": "test-verification-answer-key-panel"
        }
      }
    }
  },
  "component_usage_shadcn": {
    "primary_components": {
      "navigation": [
        {"name": "breadcrumb", "path": "/app/frontend/src/components/ui/breadcrumb.jsx"},
        {"name": "navigation-menu", "path": "/app/frontend/src/components/ui/navigation-menu.jsx"}
      ],
      "forms": [
        {"name": "input", "path": "/app/frontend/src/components/ui/input.jsx"},
        {"name": "select", "path": "/app/frontend/src/components/ui/select.jsx"},
        {"name": "switch", "path": "/app/frontend/src/components/ui/switch.jsx"},
        {"name": "checkbox", "path": "/app/frontend/src/components/ui/checkbox.jsx"},
        {"name": "textarea", "path": "/app/frontend/src/components/ui/textarea.jsx"}
      ],
      "feedback": [
        {"name": "alert", "path": "/app/frontend/src/components/ui/alert.jsx"},
        {"name": "progress", "path": "/app/frontend/src/components/ui/progress.jsx"},
        {"name": "skeleton", "path": "/app/frontend/src/components/ui/skeleton.jsx"},
        {"name": "sonner", "path": "/app/frontend/src/components/ui/sonner.jsx"}
      ],
      "overlays": [
        {"name": "dialog", "path": "/app/frontend/src/components/ui/dialog.jsx"},
        {"name": "drawer", "path": "/app/frontend/src/components/ui/drawer.jsx"},
        {"name": "sheet", "path": "/app/frontend/src/components/ui/sheet.jsx"},
        {"name": "tooltip", "path": "/app/frontend/src/components/ui/tooltip.jsx"}
      ],
      "data_display": [
        {"name": "card", "path": "/app/frontend/src/components/ui/card.jsx"},
        {"name": "badge", "path": "/app/frontend/src/components/ui/badge.jsx"},
        {"name": "table", "path": "/app/frontend/src/components/ui/table.jsx"},
        {"name": "tabs", "path": "/app/frontend/src/components/ui/tabs.jsx"},
        {"name": "scroll-area", "path": "/app/frontend/src/components/ui/scroll-area.jsx"}
      ]
    },
    "do_not_use": {
      "note": "Do not use raw HTML dropdown/calendar/toast; always use shadcn components. Calendar if needed: /components/ui/calendar.jsx"
    }
  },
  "ui_tokens_and_styles_additions": {
    "principle": "Do not change existing tokens; only add small additive utility classes in new components. Keep matte maroon brand.",
    "tailwind_patterns": {
      "page_shell": "container mx-auto px-4 sm:px-6 lg:px-8",
      "section_stack": "space-y-6 sm:space-y-8",
      "card": "bg-white border border-slate-200 rounded-2xl shadow-sm",
      "muted_panel": "bg-[color:var(--surface-alt)] border border-[color:var(--line)] rounded-xl",
      "meta_row": "flex flex-wrap items-center gap-2 text-xs text-slate-600",
      "primary_button": "bg-[color:var(--blue)] text-white hover:bg-[color:var(--brand-hover)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--focus-ring)] focus-visible:ring-offset-2",
      "danger_inline": "text-[color:var(--danger)] bg-[color:var(--danger-soft)] border border-[color:var(--danger-line)]",
      "success_inline": "text-[color:var(--success)] bg-[color:var(--success-soft)] border border-[color:var(--success-line)]"
    },
    "micro_interactions": {
      "buttons": "Use existing button transitions (background-color/border-color/box-shadow only). Add active:scale-[0.98] only on primary CTAs.",
      "cards": "Hover: shadow-md + border-slate-300; keep motion-fast 180ms.",
      "lists": "When filtering/searching, animate height/opacity with Framer Motion only if already installed; otherwise keep instant updates to avoid jank.",
      "job_progress": "Progress bar increments smoothly; show 'Last updated Xs ago' in mono font."
    }
  },
  "states_and_copy": {
    "catalog_badges": {
      "live": {"label": "Live", "variant": "green"},
      "unavailable": {"label": "Unavailable", "variant": "neutral"},
      "expired": {"label": "Expired", "variant": "amber"},
      "draft": {"label": "Draft", "variant": "neutral"}
    },
    "critical_disclosures": [
      {
        "where": "Exams catalog header + preflight",
        "copy": "These tests include answer keys only. Worked solutions are not provided.",
        "data-testid": "answer-keys-only-disclosure"
      }
    ],
    "verification_states": {
      "needs_review": {
        "title": "Needs review",
        "body": "Automated checks found issues. Open verification to fix before publishing.",
        "cta": "Open verification",
        "data-testid": "test-status-needs-review"
      },
      "ready": {
        "title": "Ready",
        "body": "All hard checks passed. You can publish now.",
        "data-testid": "test-status-ready"
      },
      "published": {
        "title": "Published",
        "body": "Live for students. Validity: 1 year from publish date (unless manually unlisted).",
        "data-testid": "test-status-published"
      }
    }
  },
  "data_testid_blueprint": {
    "conventions": {
      "format": "kebab-case",
      "rule": "Describe role not appearance",
      "examples": [
        "chapter-book-upload-submit-button",
        "chapter-split-confirm-button",
        "exams-catalog-search-input",
        "test-verification-publish-button"
      ]
    },
    "must_tag": [
      "All Buttons",
      "All Inputs/Selects/Switches/Checkboxes",
      "Primary navigation links",
      "Job status/progress text",
      "Empty/error state messages",
      "Publish toggles and validity date fields",
      "Start/Resume/Submit actions"
    ]
  },
  "implementation_notes_for_main_agent": {
    "reuse_existing_engine": [
      "Student /exams should route into existing preflight/player/results components; do not create a second player.",
      "Ensure API responses for active player never include correct answers; only return correct answers after submission for results/review."
    ],
    "chapter_book_mode": [
      "Add a new import mode tab/button in StudioImport: 'Chapter book (single PDF)'. Keep existing PDF-pair/Excel modes unchanged.",
      "Use async job model: upload → jobId → poll status; show Progress + logs.",
      "Provide chapter boundary editor with start/end page fields and PDF preview; store boundaries before generating tests.",
      "Per-test verification drawer/dialog required before publish; include automated recheck button and checklist gating publish.",
      "Validity: store publishAt + expiresAt = publishAt + 365 days; allow manual unlist without changing expiresAt."
    ],
    "formula_image_policy": [
      "If OCR/typed extraction is unsafe for formulas, show source image snippet for question/options. Prefer image-first rendering for questions.",
      "Never show answer-key pages in player; admin-only verification can show answer key mapping."
    ],
    "attempt_immutability": [
      "Results page should show a small notice: 'Attempts are saved and cannot be edited.'"
    ]
  }
}

---

<General UI UX Design Guidelines>  
    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms
    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text
   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json

 **GRADIENT RESTRICTION RULE**
NEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc
NEVER use dark gradients for logo, testimonial, footer etc
NEVER let gradients cover more than 20% of the viewport.
NEVER apply gradients to text-heavy content or reading areas.
NEVER use gradients on small UI elements (<100px width).
NEVER stack multiple gradient layers in the same viewport.

**ENFORCEMENT RULE:**
    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors

**How and where to use:**
   • Section backgrounds (not content backgrounds)
   • Hero section header content. Eg: dark to light to dark color
   • Decorative overlays and accent elements only
   • Hero section with 2-3 mild color
   • Gradients creation can be done for any angle say horizontal, vertical or diagonal

- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**

</Font Guidelines>

- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. 
   
- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.

- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.
   
- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly
    Eg: - if it implies playful/energetic, choose a colorful scheme
           - if it implies monochrome/minimal, choose a black–white/neutral scheme

**Component Reuse:**
	- Prioritize using pre-existing components from src/components/ui when applicable
	- Create new components that match the style and conventions of existing components when needed
	- Examine existing components to understand the project's component patterns before creating new ones

**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component

**Best Practices:**
	- Use Shadcn/UI as the primary component library for consistency and accessibility
	- Import path: ./components/[component-name]

**Export Conventions:**
	- Components MUST use named exports (export const ComponentName = ...)
	- Pages MUST use default exports (export default function PageName() {...})

**Toasts:**
  - Use `sonner` for toasts"
  - Sonner component are located in `/app/src/components/ui/sonner.tsx`

Use 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.
</General UI UX Design Guidelines>
