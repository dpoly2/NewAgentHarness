"""UI colour and style constants shared across all page mixin modules."""

BG_CANVAS   = "#0B0F17"
BG_RAIL     = "#080C13"
BG_DARK     = "#080C13"   # alias for BG_RAIL used in device-code dialog
BG_PANEL    = "#111827"
BG_CARD     = "#0A1F44"
BG_INPUT    = "#0d1520"
BG_HOVER    = "#0e2444"
BG_SELECTED = "#0f2d57"
ACCENT      = "#00B8FF"
ACCENT_LIGHT= "#2DD4FF"
ACCENT_DARK = "#0090cc"
SUCCESS     = "#22c55e"
WARNING     = "#f59e0b"
ERROR       = "#ef4444"
INFO        = "#6b7a99"
TEXT_PRIMARY= "#D9E3F0"
TEXT_BODY   = "#a0b4cc"
TEXT_MUTED  = "#4a6080"
DIVIDER     = "#0A1F44"
BORDER_CARD = "#0e2a55"

STATUS_COLORS = {
    "running": ACCENT,
    "queued": WARNING,
    "complete": SUCCESS,
    "completed": SUCCESS,
    "done": SUCCESS,
    "pending": TEXT_BODY,
    "in_progress": ACCENT_LIGHT,
    "failed": ERROR,
    "cancelled": ERROR,
    "offline": ERROR,
    "online": SUCCESS,
    "active": SUCCESS,
    "paused": WARNING,
}
PRIORITY_COLORS = {
    "urgent": ERROR,
    "high": WARNING,
    "medium": ACCENT,
    "normal": ACCENT,
    "low": SUCCESS,
}

GRAPH_LAYOUTS = {
    "reflexion": ["load_memory", "act", "evaluate", "revise", "save_memory", "END"],
    "research": ["plan", "search", "synthesize", "save_memory", "END"],
    "wordpress": ["wp_plan", "wp_implement", "wp_verify", "save_memory", "END"],
    "business-law": ["legal_analyze", "legal_draft", "legal_review", "save_memory", "END"],
}
