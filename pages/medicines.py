"""
pages/medicines.py
Enhanced Medicine Manager with:
  - Per-user data isolation (user_id)
  - 3-day tab view: Today / Tomorrow / Day After Tomorrow
  - Date-range medicine scheduling (start_date, end_date, frequency)
  - Per-day take tracking via medicine_logs
  - Improved add/edit form
"""

import customtkinter as ctk
from datetime import datetime, date, timedelta

import theme
import database
import services
from widgets import Card, SectionTitle, PillButton, confirm_dialog

DAYS = [
    ("Today",          0),
    ("Tomorrow",       1),
    ("Day After",      2),
]

FREQ_OPTIONS = ["Daily", "Weekly", "As Needed"]


class MedicinesPage(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.user_id = app.current_user_id
        self._active_day = 0          # 0 = today, 1 = tomorrow, 2 = day after
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────
    def _build(self):
        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=theme.PAD, pady=(theme.PAD, 6))
        SectionTitle(header, "💊  Medicine Manager").pack(side="left")
        PillButton(header, "+ Add Medicine", command=self._open_add_form, width=180).pack(side="right")

        # Search bar
        self.search_var = ctk.StringVar()
        search = ctk.CTkEntry(self, textvariable=self.search_var,
                              placeholder_text="🔍  Search medicine...",
                              height=42, corner_radius=12)
        search.pack(fill="x", padx=theme.PAD, pady=(0, 8))
        self.search_var.trace_add("write", lambda *a: self._refresh_list())

        # Day-tab selector
        tab_bar = ctk.CTkFrame(self, fg_color=theme.CARD, corner_radius=14,
                               border_width=1, border_color=theme.BORDER)
        tab_bar.pack(fill="x", padx=theme.PAD, pady=(0, 12))
        self._tab_btns = {}
        for label, offset in DAYS:
            d = date.today() + timedelta(days=offset)
            full_label = f"{label}\n{d.strftime('%d %b')}"
            btn = ctk.CTkButton(
                tab_bar, text=full_label,
                font=theme.font_small(12, "bold"),
                height=54, corner_radius=12,
                fg_color=theme.PRIMARY if offset == self._active_day else "transparent",
                text_color="white" if offset == self._active_day else theme.TEXT_DARK,
                hover_color=theme.CARD_HOVER if offset != self._active_day else theme.PRIMARY_DARK,
                command=lambda o=offset: self._switch_day(o))
            btn.pack(side="left", fill="x", expand=True, padx=6, pady=6)
            self._tab_btns[offset] = btn

        # Medicine list area
        self.list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=theme.PAD)

        # All medicines section
        all_hdr = ctk.CTkFrame(self, fg_color="transparent")
        all_hdr.pack(fill="x", padx=theme.PAD, pady=(16, 6))
        SectionTitle(all_hdr, "📋  All Medicines (Master List)").pack(side="left")
        self.all_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.all_frame.pack(fill="both", expand=True, padx=theme.PAD)

        self._refresh_list()

    # ── Tab switch ────────────────────────────────────────────────────────
    def _switch_day(self, offset: int):
        self._active_day = offset
        for o, btn in self._tab_btns.items():
            if o == offset:
                btn.configure(fg_color=theme.PRIMARY, text_color="white",
                              hover_color=theme.PRIMARY_DARK)
            else:
                btn.configure(fg_color="transparent", text_color=theme.TEXT_DARK,
                              hover_color=theme.CARD_HOVER)
        self._refresh_list()

    # ── Refresh ───────────────────────────────────────────────────────────
    def _refresh_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        for w in self.all_frame.winfo_children():
            w.destroy()

        target_date = (date.today() + timedelta(days=self._active_day)).isoformat()
        day_label = ["Today", "Tomorrow", "Day After Tomorrow"][self._active_day]

        # ── Day-specific view ─────────────────────────────────────────────
        meds = database.get_medicines_for_date(self.user_id, target_date)
        term = self.search_var.get().strip().lower()
        if term:
            meds = [m for m in meds if term in m["name"].lower()]

        day_card = Card(self.list_frame)
        day_card.pack(fill="x", pady=(0, 8))

        day_title_frame = ctk.CTkFrame(day_card, fg_color="transparent")
        day_title_frame.pack(fill="x", padx=20, pady=(14, 6))

        # Colored day badge
        badge_color = {0: theme.PRIMARY, 1: theme.SUCCESS, 2: theme.WARNING}[self._active_day]
        badge = ctk.CTkFrame(day_title_frame, fg_color=badge_color, corner_radius=10, width=10)
        badge.pack(side="left", fill="y", padx=(0, 10))
        badge.pack_propagate(False)

        target_dt = date.today() + timedelta(days=self._active_day)
        ctk.CTkLabel(day_title_frame,
                     text=f"💊 {day_label} — {target_dt.strftime('%A, %d %B %Y')}",
                     font=theme.font_heading(16), text_color=theme.TEXT_DARK).pack(side="left")

        taken_count = sum(1 for m in meds if m["taken_on_date"] > 0)
        ctk.CTkLabel(day_title_frame,
                     text=f"  {taken_count}/{len(meds)} taken",
                     font=theme.font_body(13), text_color=theme.TEXT_MUTED).pack(side="left", padx=8)

        if not meds:
            ctk.CTkLabel(day_card, text="No medicines scheduled for this day.",
                         text_color=theme.TEXT_MUTED, font=theme.font_body(14)).pack(pady=(4, 18))
        else:
            for m in meds:
                self._render_day_med_row(day_card, m, target_date)
            ctk.CTkFrame(day_card, fg_color="transparent", height=8).pack()

        # ── All medicines master list ──────────────────────────────────────
        all_meds = database.query(
            "SELECT * FROM medicines WHERE user_id=? ORDER BY timing", (self.user_id,))
        if term:
            all_meds = [m for m in all_meds if term in m["name"].lower()]

        if not all_meds:
            ctk.CTkLabel(self.all_frame,
                         text="No medicines added yet. Tap '+ Add Medicine' to add one.",
                         text_color=theme.TEXT_MUTED).pack(pady=20)
        else:
            for m in all_meds:
                self._render_master_row(m)

    def _render_day_med_row(self, parent, m, target_date: str):
        taken = m["taken_on_date"] > 0
        row_card = ctk.CTkFrame(parent,
                                fg_color=theme.BACKGROUND if not taken else "#f0fff4",
                                corner_radius=10)
        row_card.pack(fill="x", padx=16, pady=5)
        inner = ctk.CTkFrame(row_card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        # Time badge
        time_badge = ctk.CTkFrame(inner,
                                  fg_color=theme.SUCCESS if taken else theme.PRIMARY,
                                  corner_radius=8, width=90, height=36)
        time_badge.pack(side="left", padx=(0, 14))
        time_badge.pack_propagate(False)
        ctk.CTkLabel(time_badge, text=m["timing"] or "--:--",
                     font=theme.font_small(11, "bold"), text_color="white").place(
            relx=0.5, rely=0.5, anchor="center")

        # Info
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(info, text=m["name"], font=theme.font_body(15, "bold"),
                     text_color=theme.TEXT_DARK, anchor="w").pack(anchor="w")
        detail = f"{m['dosage'] or 'N/A'}  •  {m['food_instruction'] or ''}  •  {m['purpose'] or ''}"
        ctk.CTkLabel(info, text=detail, font=theme.font_small(12),
                     text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w")
        freq_info = f"📅 {m['frequency'] or 'Daily'}   🏥 Dr. {m['doctor'] or 'N/A'}   💊 {m['remaining_tablets']} left"
        ctk.CTkLabel(info, text=freq_info, font=theme.font_small(11),
                     text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w")

        # Action
        if taken:
            ctk.CTkLabel(inner, text="✅ Taken", font=theme.font_body(13, "bold"),
                         text_color=theme.SUCCESS).pack(side="right", padx=4)
        else:
            PillButton(inner, "Take Now",
                       command=lambda mid=m["id"], name=m["name"]: self._take(mid, name, target_date),
                       color=theme.SUCCESS, height=36, width=110).pack(side="right", padx=4)

    def _render_master_row(self, m):
        card = Card(self.all_frame)
        card.pack(fill="x", pady=6)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=14)
        row.grid_columnconfigure(1, weight=1)

        # Icon
        icon_box = ctk.CTkFrame(row, fg_color=theme.PRIMARY, width=52, height=52, corner_radius=12)
        icon_box.grid(row=0, column=0, rowspan=3, padx=(0, 14))
        icon_box.grid_propagate(False)
        ctk.CTkLabel(icon_box, text="💊", font=theme.font_heading(22),
                     text_color="white").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(row, text=m["name"], font=theme.font_heading(16), anchor="w").grid(
            row=0, column=1, sticky="w")
        details = f"{m['purpose'] or ''}  •  {m['dosage'] or ''}  •  ⏰ {m['timing'] or ''}"
        ctk.CTkLabel(row, text=details, font=theme.font_body(13),
                     text_color=theme.TEXT_MUTED, anchor="w").grid(row=1, column=1, sticky="w")
        extra = f"{m['food_instruction'] or ''}  •  {m['remaining_tablets']} tablets  •  {m['frequency'] or 'Daily'}  •  Dr. {m['doctor'] or 'N/A'}"
        ctk.CTkLabel(row, text=extra, font=theme.font_small(11),
                     text_color=theme.TEXT_MUTED, anchor="w").grid(row=2, column=1, sticky="w")

        # Date range
        date_range = f"📆 {m['start_date'] or '—'}  →  {m['end_date'] or '—'}"
        ctk.CTkLabel(row, text=date_range, font=theme.font_small(11),
                     text_color=theme.TEXT_MUTED, anchor="w").grid(row=3, column=1, sticky="w")

        # Buttons
        btns = ctk.CTkFrame(row, fg_color="transparent")
        btns.grid(row=0, column=2, rowspan=4, padx=(10, 0))
        if m["taken_today"]:
            ctk.CTkLabel(btns, text="✅ Today", font=theme.font_body(12, "bold"),
                         text_color=theme.SUCCESS).pack(pady=2)
        ctk.CTkButton(btns, text="✏️ Edit", width=74, height=32,
                      fg_color=theme.BACKGROUND, text_color=theme.TEXT_DARK,
                      hover_color=theme.CARD_HOVER,
                      command=lambda mm=m: self._open_edit_form(mm)).pack(pady=2)
        ctk.CTkButton(btns, text="🗑️ Del", width=74, height=32,
                      fg_color=theme.BACKGROUND, text_color=theme.DANGER,
                      hover_color=theme.CARD_HOVER,
                      command=lambda mid=m["id"]: self._delete(mid)).pack(pady=2)

    # ── Actions ───────────────────────────────────────────────────────────
    def _take(self, med_id, name, target_date: str):
        now = datetime.now().strftime("%I:%M %p")
        database.log_medicine_taken(self.user_id, med_id, target_date, now)
        services.speak(f"{name} marked as taken.")
        services.notify("Memory Bridge", f"{name} marked as taken at {now}")
        self._refresh_list()
        self.app.refresh_right_panel()

    def _delete(self, med_id):
        def do_delete():
            database.execute("DELETE FROM medicines WHERE id=? AND user_id=?", (med_id, self.user_id))
            database.execute("DELETE FROM medicine_logs WHERE medicine_id=? AND user_id=?",
                             (med_id, self.user_id))
            self._refresh_list()
            self.app.refresh_right_panel()
        confirm_dialog(self, "Delete Medicine?", "This cannot be undone. Are you sure?", do_delete)

    def _open_add_form(self):
        self._open_form(None)

    def _open_edit_form(self, med):
        self._open_form(med)

    def _open_form(self, med):
        popup = ctk.CTkToplevel(self)
        popup.title("Edit Medicine" if med else "Add Medicine")
        popup.geometry("500x720")
        popup.grab_set()

        ctk.CTkLabel(popup, text="Edit Medicine" if med else "Add New Medicine",
                     font=theme.font_heading(19)).pack(pady=(20, 6))

        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24)

        fields = {}
        specs = [
            ("name",              "Medicine Name *"),
            ("purpose",           "Purpose (e.g. Blood Pressure)"),
            ("dosage",            "Dosage (e.g. 1 tablet)"),
            ("timing",            "Reminder Time (e.g. 08:00 AM)"),
            ("food_instruction",  "Food Instruction (e.g. After breakfast)"),
            ("remaining_tablets", "Remaining Tablets"),
            ("doctor",            "Doctor's Name"),
            ("start_date",        "Start Date (YYYY-MM-DD)"),
            ("end_date",          "End Date (YYYY-MM-DD)"),
        ]

        for key, label in specs:
            ctk.CTkLabel(scroll, text=label, font=theme.font_small(13),
                         anchor="w", text_color=theme.TEXT_MUTED).pack(anchor="w", pady=(10, 2))
            entry = ctk.CTkEntry(scroll, height=42, corner_radius=10)
            entry.pack(fill="x")
            if med and key in med.keys() and med[key] is not None:
                entry.insert(0, str(med[key]))
            elif key == "start_date" and not med:
                entry.insert(0, date.today().isoformat())
            elif key == "end_date" and not med:
                entry.insert(0, (date.today() + timedelta(days=30)).isoformat())
            fields[key] = entry

        # Frequency dropdown
        ctk.CTkLabel(scroll, text="Frequency", font=theme.font_small(13),
                     anchor="w", text_color=theme.TEXT_MUTED).pack(anchor="w", pady=(10, 2))
        freq_var = ctk.StringVar(value=(med["frequency"] if med and med["frequency"] else "Daily"))
        freq_menu = ctk.CTkOptionMenu(scroll, values=FREQ_OPTIONS, variable=freq_var, height=42)
        freq_menu.pack(fill="x")

        def save():
            values = {k: e.get().strip() for k, e in fields.items()}
            if not values["name"]:
                return
            try:
                remaining = int(values["remaining_tablets"] or 0)
            except ValueError:
                remaining = 0

            if med:
                database.execute("""UPDATE medicines SET name=?, purpose=?, dosage=?, timing=?,
                    food_instruction=?, remaining_tablets=?, doctor=?,
                    start_date=?, end_date=?, frequency=?
                    WHERE id=? AND user_id=?""",
                    (values["name"], values["purpose"], values["dosage"], values["timing"],
                     values["food_instruction"], remaining, values["doctor"],
                     values["start_date"], values["end_date"], freq_var.get(),
                     med["id"], self.user_id))
            else:
                database.execute("""INSERT INTO medicines
                    (user_id, name, purpose, dosage, timing, food_instruction,
                     remaining_tablets, doctor, start_date, end_date, frequency)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (self.user_id, values["name"], values["purpose"], values["dosage"],
                     values["timing"], values["food_instruction"], remaining, values["doctor"],
                     values["start_date"], values["end_date"], freq_var.get()))
            popup.destroy()
            self._refresh_list()
            self.app.refresh_right_panel()

        PillButton(popup, "💾  Save Medicine", command=save, width=220).pack(pady=18)
