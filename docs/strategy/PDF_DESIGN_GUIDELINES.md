{
  "pdf_design_addendum_meta": {
    "purpose": "PDF-SPECIFIC ADDENDUM: define print-friendly, A4-first typography/layout tokens and component rules for generating a 10-packet strategy PDF. This does NOT change the web app UI and must preserve existing matte maroon brand from /app/design_guidelines.md.",
    "scope": [
      "Static downloadable PDF generated locally via Python PDF library",
      "Readable full-text strategy with bookmarks/TOC",
      "Exactly 10 implementation packets + appendices",
      "Traceability (source hashes), audit/errata, restart handoff"
    ],
    "non_goals": [
      "No new product features",
      "No redesign of the React/FastAPI app",
      "No secrets, credentials, or raw private test reports embedded"
    ],
    "brand_reference": {
      "source_of_truth": "/app/design_guidelines.md",
      "primary_matte_maroon_hex": "#5C0025",
      "note": "Use maroon as accent only (rules/section markers/links). Keep body text black/near-black for print legibility."
    }
  },

  "format_and_print_tokens": {
    "page": {
      "size": "A4",
      "orientation": "portrait",
      "margins_mm": {
        "top": 18,
        "right": 16,
        "bottom": 18,
        "left": 16
      },
      "gutter_mm": 4,
      "bleed_mm": 0,
      "baseline_grid_pt": 14
    },
    "typography": {
      "font_policy": {
        "requirement": "Use a Unicode-capable font that is reliably available locally OR embed it in the PDF.",
        "preferred_families": [
          {
            "family": "Noto Sans",
            "why": "Excellent Unicode coverage; consistent across platforms when embedded."
          },
          {
            "family": "DejaVu Sans",
            "why": "Common on Linux; good Unicode coverage; safe fallback."
          },
          {
            "family": "Liberation Sans",
            "why": "Often available; metrics similar to Arial; acceptable fallback."
          }
        ],
        "mono_preferred": [
          {
            "family": "DejaVu Sans Mono",
            "use_for": ["hashes", "code", "file paths", "commands"]
          }
        ],
        "fallback_stack": {
          "sans": ["Noto Sans", "DejaVu Sans", "Liberation Sans", "Helvetica", "Arial"],
          "mono": ["DejaVu Sans Mono", "Liberation Mono", "Courier"]
        }
      },
      "scale_pt": {
        "cover_title": 26,
        "cover_subtitle": 12,
        "h1": 18,
        "h2": 14,
        "h3": 12,
        "body": 10.5,
        "small": 9,
        "caption": 8,
        "code": 9
      },
      "line_height": {
        "body": 1.35,
        "headings": 1.2,
        "code": 1.25
      },
      "paragraph_spacing_pt": {
        "after_paragraph": 6,
        "after_heading": 8,
        "before_heading": 14
      },
      "hyphenation": {
        "policy": "off_by_default",
        "reason": "Hyphenation varies by library and can harm readability in technical docs. Prefer wrapping + slightly narrower measure."
      }
    },
    "color": {
      "ink": "#111827",
      "muted": "#4B5563",
      "rule": "#E5E7EB",
      "paper": "#FFFFFF",
      "accent_maroon": "#5C0025",
      "accent_soft": "#F6E9EE",
      "status": {
        "success": "#16714B",
        "warning": "#905515",
        "danger": "#B42332"
      },
      "print_rules": [
        "No gradients in PDF.",
        "Avoid large solid maroon blocks (ink-heavy). Use maroon for thin rules, small badges, and link color.",
        "All text must meet high contrast on white paper."
      ]
    },
    "radius_and_strokes": {
      "rule_stroke_pt": 0.75,
      "box_stroke_pt": 0.9,
      "corner_radius_pt": 6
    }
  },

  "document_structure_and_navigation": {
    "required_sections_in_order": [
      "Cover + Status",
      "How to use this PDF (Context Restore)",
      "Table of Contents (clickable)",
      "Packet 1",
      "Packet 2",
      "Packet 3",
      "Packet 4",
      "Packet 5",
      "Packet 6",
      "Packet 7",
      "Packet 8",
      "Packet 9",
      "Packet 10",
      "Appendix A: Workload + SLO",
      "Appendix B: Operator / WP / OPS-R Handoff",
      "Appendix C: Audit / Errata",
      "Appendix D: Traceability (Source Hashes)",
      "Appendix E: Current Implementation Status (honest)"
    ],
    "bookmarks_and_outlines": {
      "requirement": "Generate PDF outline/bookmarks mirroring the TOC.",
      "levels": {
        "level_1": "Packets + Appendices",
        "level_2": "Packet subsections (Goal, Preconditions, Steps, Verification, Rollback)",
        "level_3": "Optional: numbered steps if library supports"
      }
    },
    "toc_rules": {
      "toc_depth": 2,
      "include_page_numbers": true,
      "leader_dots": true,
      "wrap_long_titles": true,
      "max_title_line_count": 2
    },
    "running_elements": {
      "header": {
        "left": "Document title (short)",
        "right": "Packet/Appendix name",
        "style": "small muted text + thin rule"
      },
      "footer": {
        "left": "Version + generated date",
        "center": "Source hash short (first 8 chars)",
        "right": "Page X / Y"
      }
    }
  },

  "layout_components_pdf": {
    "cover_page": {
      "layout": "Centered title block with left-aligned metadata panel below.",
      "elements": [
        "Title",
        "Subtitle: '10 Implementation Packets (Portable Reference)'",
        "Status box: 'Current implementation status: <truthful summary>'",
        "Metadata: repo name, commit hash (if available), generated timestamp"
      ],
      "accent_usage": "Maroon 2–3pt vertical bar at left of title block; no full-bleed color."
    },
    "packet_template": {
      "packet_header": {
        "fields": ["Packet #", "Name", "Owner", "ETA", "Risk"],
        "risk_badge_colors": {
          "low": "accent_soft + ink",
          "medium": "warning_soft + warning",
          "high": "danger_soft + danger"
        }
      },
      "required_subsections": [
        "Goal",
        "Why now",
        "Preconditions",
        "Implementation Steps",
        "Verification (tests + manual checks)",
        "Rollback",
        "Notes / Edge cases"
      ],
      "step_format": {
        "style": "Numbered list with hanging indent",
        "indent_pt": 18,
        "spacing_pt": 4
      }
    },
    "callouts": {
      "types": {
        "note": {
          "label": "NOTE",
          "border": "rule",
          "fill": "#FFFFFF",
          "left_bar": "accent_maroon"
        },
        "warning": {
          "label": "WARNING",
          "border": "warning",
          "fill": "#FFF7E9",
          "left_bar": "warning"
        },
        "danger": {
          "label": "RISK",
          "border": "danger",
          "fill": "#FFF1F2",
          "left_bar": "danger"
        }
      },
      "padding_pt": 10,
      "title_style": "small caps / bold",
      "body_style": "body"
    },
    "tables": {
      "default": {
        "font_size_pt": 9,
        "header_fill": "#F3F4F6",
        "row_striping": "#FFFFFF / #FAFAFA",
        "cell_padding_pt": 5,
        "border_color": "#E5E7EB",
        "border_width_pt": 0.6
      },
      "wrapping_rules": [
        "Wrap cell text; never overflow page width.",
        "Prefer fixed column widths for predictable wrapping.",
        "For long identifiers (hashes/paths), allow mid-word breaks and use mono font."
      ],
      "avoid": [
        "Nested tables",
        "Tables wider than content box",
        "Tiny font below 8pt"
      ]
    },
    "code_blocks": {
      "font": "mono",
      "font_size_pt": 9,
      "background": "#F9FAFB",
      "border": "#E5E7EB",
      "padding_pt": 8,
      "wrapping": {
        "policy": "wrap_long_lines",
        "exceptions": "If wrapping harms meaning, allow horizontal scroll only if library supports; otherwise split lines with continuation markers."
      }
    },
    "links": {
      "color": "accent_maroon",
      "underline": true,
      "external_link_icon": "none (print-safe)",
      "pdf_behavior": "Clickable URLs; also print full URL in parentheses if critical."
    }
  },

  "content_integrity_and_honesty": {
    "status_language": {
      "requirement": "Be explicit about what is implemented vs planned.",
      "forbidden_claims": [
        "No '500k capacity' or unverified scale claims",
        "No implying staff credential/session rotation is automatic if it requires confirmation",
        "No implying student login changed beyond phone-number-only"
      ]
    },
    "traceability": {
      "include": [
        "Source file list (paths)",
        "SHA-256 hashes for exported packet sources (if applicable)",
        "Generation script version/hash"
      ],
      "hash_display": {
        "format": "SHA-256: <64 hex>",
        "short_format": "<first8>…<last6>",
        "font": "mono"
      }
    },
    "redaction": {
      "must_exclude": [
        "API keys",
        "tokens",
        "passwords",
        "private URLs",
        "raw internal test logs containing sensitive data"
      ],
      "safe_to_include": [
        "High-level test plan",
        "Public endpoints",
        "Non-sensitive example payloads"
      ]
    }
  },

  "implementation_notes_for_main_agent_python": {
    "library_options": {
      "preferred": [
        {
          "name": "borb",
          "why": "Good layout primitives, outlines/bookmarks support, tables; Pythonic."
        },
        {
          "name": "reportlab",
          "why": "Very mature; reliable; outlines possible; more manual layout."
        }
      ],
      "fallback": [
        {
          "name": "pypdf",
          "why": "Good for merging/stamping; not ideal for full layout generation alone."
        }
      ]
    },
    "font_embedding": {
      "requirement": "Embed fonts to guarantee Unicode rendering.",
      "suggested_font_files": [
        "NotoSans-Regular.ttf",
        "NotoSans-Bold.ttf",
        "NotoSans-Italic.ttf",
        "DejaVuSansMono.ttf"
      ],
      "note": "If fonts are not present in repo, document where the generator expects them (e.g., /app/assets/fonts/) and fail with a clear error message."
    },
    "toc_and_bookmarks": {
      "requirement": "TOC entries must link to destinations; bookmarks must match TOC.",
      "packet_anchor_naming": "packet-01 ... packet-10; appendix-a ... appendix-e"
    },
    "pagination": {
      "widows_orphans": "Avoid single-line headings at bottom of page; keep heading with at least 2 lines of following content.",
      "keep_with_next": "Headings + first paragraph; table header + first row"
    }
  },

  "data_testid_policy": {
    "note": "PDF itself does not use data-testid. However, any web UI controls that trigger PDF generation/download MUST include data-testid.",
    "required_testids_for_pdf_flow": [
      "pdf-download-button",
      "pdf-generate-button",
      "pdf-generation-status-text",
      "pdf-generation-error-text",
      "pdf-last-generated-timestamp"
    ]
  },

  "instructions_to_main_agent": [
    "Do NOT modify the existing web UI design system; this addendum is only for PDF export styling and structure.",
    "Use A4 portrait with generous margins; prioritize readability over brand color.",
    "Ensure the PDF contains exactly 10 packets, each starting on a new page.",
    "Generate clickable TOC + PDF bookmarks/outlines.",
    "Use embedded Unicode fonts (Noto/DejaVu) to avoid missing glyphs.",
    "No gradients; maroon only as accent (rules, small badges, link color).",
    "Include traceability appendix with hashes; exclude secrets and private logs.",
    "Any UI elements involved in generating/downloading the PDF must include data-testid attributes listed above."
  ]
}

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
