"""
widgets.py
Small reusable UI building blocks so every page shares the same
look (cards, stat tiles, section titles) -- HCI "consistency".
"""

import customtkinter as ctk
import theme


class Card(ctk.CTkFrame):
    """A plain white rounded card container."""
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.CARD, corner_radius=theme.CORNER_RADIUS,
                          border_width=1, border_color=theme.BORDER, **kwargs)


class SectionTitle(ctk.CTkLabel):
    def __init__(self, master, text, **kwargs):
        super().__init__(master, text=text, font=theme.font_heading(),
                          text_color=theme.TEXT_DARK, anchor="w", **kwargs)


class StatCard(ctk.CTkFrame):
    """Small dashboard statistic tile, e.g. 'Medicines Today: 2'."""
    def __init__(self, master, icon, title, value, color=theme.PRIMARY, **kwargs):
        super().__init__(master, fg_color=theme.CARD, corner_radius=theme.CORNER_RADIUS,
                          border_width=1, border_color=theme.BORDER, **kwargs)
        self.grid_columnconfigure(1, weight=1)

        icon_box = ctk.CTkFrame(self, fg_color=color, corner_radius=12, width=48, height=48)
        icon_box.grid(row=0, column=0, rowspan=2, padx=16, pady=16, sticky="n")
        icon_box.grid_propagate(False)
        ctk.CTkLabel(icon_box, text=icon, font=theme.font_heading(22), text_color="white").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self, text=str(value), font=theme.font_title(26), text_color=theme.TEXT_DARK, anchor="w").grid(
            row=0, column=1, sticky="sw", padx=(0, 16), pady=(16, 0))
        ctk.CTkLabel(self, text=title, font=theme.font_body(14), text_color=theme.TEXT_MUTED, anchor="w").grid(
            row=1, column=1, sticky="nw", padx=(0, 16), pady=(0, 16))


class PillButton(ctk.CTkButton):
    """A rounded, high-contrast, large-touch-target button."""
    def __init__(self, master, text, command=None, color=theme.PRIMARY, text_color="white",
                 height=theme.BUTTON_HEIGHT, **kwargs):
        super().__init__(master, text=text, command=command, fg_color=color,
                          hover_color=_darken(color), text_color=text_color,
                          corner_radius=theme.CORNER_RADIUS, height=height,
                          font=theme.font_button(15), **kwargs)


class StatusBadge(ctk.CTkLabel):
    COLORS = {
        "Completed": theme.SUCCESS,
        "Taken": theme.SUCCESS,
        "Paid": theme.SUCCESS,
        "Pending": theme.WARNING,
        "Due Soon": theme.WARNING,
        "Missed": theme.DANGER,
        "Overdue": theme.DANGER,
    }

    def __init__(self, master, status, **kwargs):
        color = self.COLORS.get(status, theme.TEXT_MUTED)
        super().__init__(master, text=f"  {status}  ", font=theme.font_small(13, "bold"),
                          fg_color=color, text_color="white", corner_radius=10, **kwargs)


def _darken(hex_color):
    hex_color = hex_color.lstrip('#')
    try:
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return hex_color
    factor = 0.85
    r, g, b = int(r * factor), int(g * factor), int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def confirm_dialog(master, title, message, on_yes):
    """A simple accessible confirmation popup (error-prevention heuristic)."""
    win = ctk.CTkToplevel(master)
    win.title(title)
    win.geometry("420x200")
    win.grab_set()
    win.resizable(False, False)

    ctk.CTkLabel(win, text=title, font=theme.font_heading(18)).pack(pady=(24, 8))
    ctk.CTkLabel(win, text=message, font=theme.font_body(14), wraplength=360,
                 text_color=theme.TEXT_MUTED).pack(pady=(0, 20))

    btn_frame = ctk.CTkFrame(win, fg_color="transparent")
    btn_frame.pack()

    def _yes():
        win.destroy()
        on_yes()

    PillButton(btn_frame, "Yes, Continue", command=_yes, color=theme.DANGER, width=150).grid(row=0, column=0, padx=10)
    PillButton(btn_frame, "Cancel", command=win.destroy, color=theme.TEXT_MUTED, width=150).grid(row=0, column=1, padx=10)
