"""
theme.py
Central place for colors, fonts and sizing so every page in
Memory Bridge looks consistent (an HCI "consistency" heuristic).
"""

import customtkinter as ctk

# ---------------------------------------------------------------
# COLOR PALETTE  (matches the design spec)
# ---------------------------------------------------------------
PRIMARY   = "#2E8BFF"   # buttons, active sidebar item
PRIMARY_DARK = "#1C6FDB"
SUCCESS   = "#4CAF50"   # taken / paid / completed
WARNING   = "#FFC107"   # due soon / pending
DANGER    = "#F44336"   # missed / emergency
BACKGROUND = "#F7F9FC"  # main window background
CARD      = "#FFFFFF"   # card background
CARD_HOVER = "#EEF3FC"
TEXT_DARK = "#2C3E50"
TEXT_MUTED = "#7A8794"
BORDER    = "#E3E8EF"
SIDEBAR_BG = "#FFFFFF"

# Dark mode variants (used when the user toggles dark mode in Settings)
DARK_BACKGROUND = "#1B1F27"
DARK_CARD = "#242A35"
DARK_TEXT = "#F1F3F6"
DARK_SIDEBAR = "#20242E"

# ---------------------------------------------------------------
# FONTS  (Segoe UI ships with Windows; falls back gracefully)
# ---------------------------------------------------------------
FONT_FAMILY = "Segoe UI"

def font_title(size=28, weight="bold"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)

def font_heading(size=20, weight="bold"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)

def font_body(size=16, weight="normal"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)

def font_small(size=13, weight="normal"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)

def font_button(size=17, weight="bold"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)

# ---------------------------------------------------------------
# SIZING (accessibility: large touch targets, min 48px per spec)
# ---------------------------------------------------------------
BUTTON_HEIGHT = 48
BIG_BUTTON_HEIGHT = 90
CORNER_RADIUS = 14
SIDEBAR_WIDTH = 250
RIGHT_PANEL_WIDTH = 300
HEADER_HEIGHT = 70
PAD = 20
