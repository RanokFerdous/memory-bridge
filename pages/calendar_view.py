import customtkinter as ctk
from datetime import datetime, date

import theme
import database
from widgets import Card, SectionTitle, PillButton, StatusBadge, confirm_dialog

try:
    from tkcalendar import Calendar
    TKCALENDAR_AVAILABLE = True
except ImportError:
    TKCALENDAR_AVAILABLE = False


class CalendarPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.user_id = app.current_user_id
        self.selected_date = date.today().isoformat()
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=theme.PAD, pady=(theme.PAD, 10))
        SectionTitle(header, "📅  Calendar").pack(side="left")
        PillButton(header, "+ Appointment", command=lambda: self._open_form("Appointment"),
                   width=170).pack(side="right", padx=6)
        PillButton(header, "+ Bill", command=lambda: self._open_form("Bill"),
                   width=140, color=theme.WARNING).pack(side="right", padx=6)

        columns = ctk.CTkFrame(self, fg_color="transparent")
        columns.pack(fill="both", expand=True, padx=theme.PAD, pady=(0, theme.PAD))
        columns.grid_columnconfigure(0, weight=1)
        columns.grid_columnconfigure(1, weight=1)
        columns.grid_rowconfigure(0, weight=1)

        cal_card = Card(columns)
        cal_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        if TKCALENDAR_AVAILABLE:
            self.calendar = Calendar(cal_card, selectmode="day", date_pattern="yyyy-mm-dd",
                                      font=("Segoe UI", 12), background=theme.PRIMARY,
                                      foreground="white", headersbackground=theme.BACKGROUND,
                                      normalbackground="white", weekendbackground="#F0F4FA")
            self.calendar.pack(padx=20, pady=20, fill="both", expand=True)
            self.calendar.bind("<<CalendarSelected>>", self._on_date_selected)
            self._mark_calendar_events()
        else:
            ctk.CTkLabel(cal_card, text="tkcalendar is not installed.\nRun: pip install tkcalendar",
                         text_color=theme.DANGER, font=theme.font_body(14)).pack(padx=20, pady=40)

        self.details_card = Card(columns)
        self.details_card.grid(row=0, column=1, sticky="nsew")
        self._refresh_details()

    def _mark_calendar_events(self):
        uid = self.user_id
        appts = database.query("SELECT date FROM appointments WHERE user_id=?", (uid,))
        bills = database.query("SELECT due_date as date FROM bills WHERE user_id=?", (uid,))
        for r in appts + bills:
            try:
                y, m, d = map(int, r["date"].split("-"))
                self.calendar.calevent_create(datetime(y, m, d), "Event", "event")
            except Exception:
                pass
        self.calendar.tag_config("event", background=theme.PRIMARY, foreground="white")

    def _on_date_selected(self, event=None):
        self.selected_date = self.calendar.get_date()
        self._refresh_details()

    def _refresh_details(self):
        for w in self.details_card.winfo_children():
            w.destroy()

        friendly = self.selected_date
        SectionTitle(self.details_card, f"🗓️  {friendly}").pack(anchor="w", padx=20, pady=(18, 10))

        uid = self.user_id
        appts = database.query("SELECT * FROM appointments WHERE user_id=? AND date=? ORDER BY time", (uid, self.selected_date))
        bills = database.query("SELECT * FROM bills WHERE user_id=? AND due_date=? ORDER BY id", (uid, self.selected_date))

        if not appts and not bills:
            ctk.CTkLabel(self.details_card, text="Nothing scheduled on this date.",
                         text_color=theme.TEXT_MUTED).pack(padx=20, pady=10)

        for a in appts:
            row = ctk.CTkFrame(self.details_card, fg_color=theme.BACKGROUND, corner_radius=12)
            row.pack(fill="x", padx=20, pady=6)
            ctk.CTkLabel(row, text=f"📌 {a['kind']}: {a['title']}", font=theme.font_body(14, "bold"),
                         anchor="w").pack(anchor="w", padx=14, pady=(10, 0))
            ctk.CTkLabel(row, text=f"⏰ {a['time'] or '—'}   {a['description'] or ''}",
                         font=theme.font_small(13), text_color=theme.TEXT_MUTED, anchor="w").pack(
                anchor="w", padx=14, pady=(0, 10))
            ctk.CTkButton(row, text="🗑️ Remove", width=90, height=28, fg_color="transparent",
                         text_color=theme.DANGER, hover_color=theme.CARD_HOVER,
                         command=lambda aid=a["id"]: self._delete("appointments", aid)).pack(
                anchor="e", padx=10, pady=(0, 8))

        for b in bills:
            row = ctk.CTkFrame(self.details_card, fg_color=theme.BACKGROUND, corner_radius=12)
            row.pack(fill="x", padx=20, pady=6)
            top = ctk.CTkFrame(row, fg_color="transparent")
            top.pack(fill="x", padx=14, pady=(10, 0))
            ctk.CTkLabel(top, text=f"💳 {b['name']}  ({b['amount'] or 'N/A'})",
                         font=theme.font_body(14, "bold"), anchor="w").pack(side="left")
            StatusBadge(top, "Paid" if b["paid"] else "Due Soon").pack(side="right")

            btn_row = ctk.CTkFrame(row, fg_color="transparent")
            btn_row.pack(fill="x", padx=14, pady=(6, 10))
            if not b["paid"]:
                PillButton(btn_row, "Mark Paid", command=lambda bid=b["id"]: self._mark_paid(bid),
                           color=theme.SUCCESS, height=30, width=110).pack(side="left")
            ctk.CTkButton(btn_row, text="🗑️", width=34, height=30, fg_color="transparent",
                         text_color=theme.DANGER, hover_color=theme.CARD_HOVER,
                         command=lambda bid=b["id"]: self._delete("bills", bid)).pack(side="right")

    def _mark_paid(self, bill_id):
        database.execute("UPDATE bills SET paid=1 WHERE id=? AND user_id=?", (bill_id, self.user_id))
        self._refresh_details()
        self.app.refresh_right_panel()

    def _delete(self, table, row_id):
        uid = self.user_id
        def do():
            database.execute(f"DELETE FROM {table} WHERE id=? AND user_id=?", (row_id, uid))
            self._refresh_details()
            self.app.refresh_right_panel()
        confirm_dialog(self, "Remove Entry?", "Are you sure you want to remove this?", do)

    def _open_form(self, kind):
        popup = ctk.CTkToplevel(self)
        popup.title(f"Add {kind}")
        popup.geometry("420x480")
        popup.grab_set()
        ctk.CTkLabel(popup, text=f"Add {kind}", font=theme.font_heading(19)).pack(pady=(20, 14))

        form = ctk.CTkFrame(popup, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24)

        ctk.CTkLabel(form, text="Name / Title", anchor="w", text_color=theme.TEXT_MUTED).pack(anchor="w", pady=(6, 2))
        name_entry = ctk.CTkEntry(form, height=40)
        name_entry.pack(fill="x")

        ctk.CTkLabel(form, text="Date (YYYY-MM-DD)", anchor="w", text_color=theme.TEXT_MUTED).pack(anchor="w", pady=(14, 2))
        date_entry = ctk.CTkEntry(form, height=40)
        date_entry.insert(0, self.selected_date)
        date_entry.pack(fill="x")

        if kind == "Appointment":
            ctk.CTkLabel(form, text="Time (e.g. 03:00 PM)", anchor="w", text_color=theme.TEXT_MUTED).pack(anchor="w", pady=(14, 2))
            time_entry = ctk.CTkEntry(form, height=40)
            time_entry.pack(fill="x")

            ctk.CTkLabel(form, text="Notes", anchor="w", text_color=theme.TEXT_MUTED).pack(anchor="w", pady=(14, 2))
            notes_entry = ctk.CTkEntry(form, height=40)
            notes_entry.pack(fill="x")
        else:
            ctk.CTkLabel(form, text="Amount (e.g. 1200 BDT)", anchor="w", text_color=theme.TEXT_MUTED).pack(anchor="w", pady=(14, 2))
            amount_entry = ctk.CTkEntry(form, height=40)
            amount_entry.pack(fill="x")

        def save():
            if not name_entry.get().strip():
                return
            uid = self.user_id
            if kind == "Appointment":
                database.execute(
                    "INSERT INTO appointments (user_id, title, date, time, description, kind) VALUES (?,?,?,?,?,?)",
                    (uid, name_entry.get().strip(), date_entry.get().strip(), time_entry.get().strip(),
                     notes_entry.get().strip(), "Appointment"))
            else:
                database.execute("INSERT INTO bills (user_id, name, due_date, amount, paid) VALUES (?,?,?,?,0)",
                                  (uid, name_entry.get().strip(), date_entry.get().strip(), amount_entry.get().strip()))
            popup.destroy()
            if TKCALENDAR_AVAILABLE:
                self._mark_calendar_events()
            self._refresh_details()
            self.app.refresh_right_panel()

        PillButton(popup, f"Save {kind}", command=save, width=200).pack(pady=18)
