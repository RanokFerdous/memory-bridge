import customtkinter as ctk
from datetime import date

import theme
import database
from widgets import Card, SectionTitle, PillButton, StatCard

TYPES = ["Blood Pressure", "Heart Rate", "Blood Sugar", "Weight"]
TYPE_ICON = {"Blood Pressure": "🩸", "Heart Rate": "❤️", "Blood Sugar": "🍬", "Weight": "⚖️"}
TYPE_UNIT = {"Blood Pressure": "mmHg", "Heart Rate": "bpm", "Blood Sugar": "mg/dL", "Weight": "kg"}


class HealthPage(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.user_id = app.current_user_id
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=theme.PAD, pady=(theme.PAD, 10))
        SectionTitle(header, "❤️  Health Dashboard").pack(side="left")
        PillButton(header, "+ Add Reading", command=self._open_form, width=170).pack(side="right")

        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=theme.PAD, pady=10)
        for i in range(4):
            stats_row.grid_columnconfigure(i, weight=1)

        uid = self.user_id
        for i, t in enumerate(TYPES):
            latest = database.query(
                "SELECT value FROM health_records WHERE user_id=? AND type=? ORDER BY date DESC LIMIT 1",
                (uid, t))
            val = latest[0]["value"] if latest else "—"
            StatCard(stats_row, TYPE_ICON[t], t, val, theme.PRIMARY).grid(row=0, column=i, padx=8, sticky="ew")

        history_card = Card(self)
        history_card.pack(fill="both", expand=True, padx=theme.PAD, pady=(0, theme.PAD))
        SectionTitle(history_card, "📈  Recent Readings").pack(anchor="w", padx=20, pady=(18, 10))

        rows = database.query("SELECT * FROM health_records WHERE user_id=? ORDER BY date DESC LIMIT 20",
                              (self.user_id,))
        self.history_body = ctk.CTkFrame(history_card, fg_color="transparent")
        self.history_body.pack(fill="both", expand=True, padx=20, pady=(0, 18))
        self._render_history(rows)

    def _render_history(self, rows):
        for w in self.history_body.winfo_children():
            w.destroy()
        if not rows:
            ctk.CTkLabel(self.history_body, text="No readings recorded yet.",
                         text_color=theme.TEXT_MUTED).pack(pady=10)
            return
        for r in rows:
            row_f = ctk.CTkFrame(self.history_body, fg_color=theme.BACKGROUND, corner_radius=10)
            row_f.pack(fill="x", pady=4)
            ctk.CTkLabel(row_f, text=f"{TYPE_ICON.get(r['type'], '📊')} {r['type']}",
                         font=theme.font_body(14, "bold"), width=180, anchor="w").pack(side="left", padx=12, pady=10)
            ctk.CTkLabel(row_f, text=f"{r['value']} {TYPE_UNIT.get(r['type'], '')}",
                         font=theme.font_body(14), anchor="w").pack(side="left", padx=12)
            ctk.CTkLabel(row_f, text=r["date"], font=theme.font_small(12),
                         text_color=theme.TEXT_MUTED).pack(side="right", padx=12)

    def _open_form(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Add Health Reading")
        popup.geometry("400x360")
        popup.grab_set()

        ctk.CTkLabel(popup, text="Add Health Reading", font=theme.font_heading(18)).pack(pady=(20, 14))

        ctk.CTkLabel(popup, text="Type", text_color=theme.TEXT_MUTED).pack(anchor="w", padx=24)
        type_var = ctk.StringVar(value=TYPES[0])
        ctk.CTkOptionMenu(popup, values=TYPES, variable=type_var, height=40).pack(fill="x", padx=24, pady=(2, 14))

        ctk.CTkLabel(popup, text="Value (e.g. 120/80 or 72)", text_color=theme.TEXT_MUTED).pack(anchor="w", padx=24)
        value_entry = ctk.CTkEntry(popup, height=40)
        value_entry.pack(fill="x", padx=24, pady=(2, 14))

        def save():
            if not value_entry.get().strip():
                return
            database.execute("INSERT INTO health_records (user_id, type, value, date) VALUES (?,?,?,?)",
                              (self.user_id, type_var.get(), value_entry.get().strip(), date.today().isoformat()))
            popup.destroy()
            self.app.refresh_current_page()

        PillButton(popup, "Save Reading", command=save, width=200).pack(pady=10)
