import customtkinter as ctk
from datetime import date

import theme
import database
import services
from widgets import Card, SectionTitle, StatCard, PillButton, StatusBadge


class DashboardPage(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.user_id = app.current_user_id
        self._build()

    def _build(self):
        user_name = database.get_setting("user_name", "Friend", self.user_id)

        # ---------- Welcome ----------
        welcome = Card(self)
        welcome.pack(fill="x", padx=theme.PAD, pady=(theme.PAD, 10))
        inner = ctk.CTkFrame(welcome, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=24)
        ctk.CTkLabel(inner, text=f"Good day, {user_name} 👋", font=theme.font_title(26),
                     text_color=theme.TEXT_DARK, anchor="w").pack(anchor="w")
        ctk.CTkLabel(inner, text="Have a wonderful day. Here is everything you need to know.",
                     font=theme.font_body(15), text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w", pady=(4, 12))

        PillButton(inner, "▶  Start My Day", command=self._start_my_day, width=220,
                   height=52).pack(anchor="w")

        # ---------- Stat cards ----------
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=theme.PAD, pady=10)
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)

        uid = self.user_id
        meds_today = database.query("SELECT COUNT(*) as c FROM medicines WHERE user_id=?", (uid,))[0]["c"]
        meds_taken = database.query("SELECT COUNT(*) as c FROM medicines WHERE user_id=? AND taken_today=1", (uid,))[0]["c"]
        appts_today = database.query("SELECT COUNT(*) as c FROM appointments WHERE user_id=? AND date=date('now')", (uid,))[0]["c"]
        bills_due = database.query("SELECT COUNT(*) as c FROM bills WHERE user_id=? AND paid=0", (uid,))[0]["c"]

        StatCard(stats_frame, "💊", "Medicines Today", f"{meds_taken}/{meds_today}", theme.PRIMARY).grid(
            row=0, column=0, padx=8, sticky="ew")
        StatCard(stats_frame, "📅", "Appointments", appts_today, theme.SUCCESS).grid(
            row=0, column=1, padx=8, sticky="ew")
        StatCard(stats_frame, "💳", "Bills Due", bills_due, theme.WARNING).grid(
            row=0, column=2, padx=8, sticky="ew")
        water = database.get_setting("water_count", 0, uid)
        StatCard(stats_frame, "💧", "Water Glasses", water, theme.PRIMARY).grid(
            row=0, column=3, padx=8, sticky="ew")

        # ---------- Timeline + Quick actions (2 columns) ----------
        columns = ctk.CTkFrame(self, fg_color="transparent")
        columns.pack(fill="both", expand=True, padx=theme.PAD, pady=10)
        columns.grid_columnconfigure(0, weight=2)
        columns.grid_columnconfigure(1, weight=1)

        # Timeline
        timeline_card = Card(columns)
        timeline_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        SectionTitle(timeline_card, "📋  Today's Timeline").pack(anchor="w", padx=20, pady=(18, 10))

        rows = database.query("SELECT * FROM schedule WHERE user_id=? AND date=date('now') ORDER BY time", (self.user_id,))
        if not rows:
            ctk.CTkLabel(timeline_card, text="Nothing scheduled for today yet.",
                         text_color=theme.TEXT_MUTED).pack(padx=20, pady=10)
        for r in rows:
            row_f = ctk.CTkFrame(timeline_card, fg_color="transparent")
            row_f.pack(fill="x", padx=20, pady=6)
            ctk.CTkLabel(row_f, text=r["time"], font=theme.font_body(14, "bold"),
                         width=90, anchor="w", text_color=theme.TEXT_DARK).pack(side="left")
            ctk.CTkLabel(row_f, text=r["title"], font=theme.font_body(14), anchor="w").pack(
                side="left", fill="x", expand=True)
            StatusBadge(row_f, r["status"]).pack(side="right")
        ctk.CTkFrame(timeline_card, fg_color="transparent", height=10).pack()

        # Quick actions + recent activity
        right_col = ctk.CTkFrame(columns, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew")

        actions_card = Card(right_col)
        actions_card.pack(fill="x", pady=(0, 10))
        SectionTitle(actions_card, "⚡  Quick Actions").pack(anchor="w", padx=20, pady=(18, 10))
        actions_inner = ctk.CTkFrame(actions_card, fg_color="transparent")
        actions_inner.pack(fill="x", padx=20, pady=(0, 18))
        PillButton(actions_inner, "💊 Medicines", command=lambda: self.app.show_page("Medicines"),
                   height=44).pack(fill="x", pady=4)
        PillButton(actions_inner, "📅 Add Appointment", command=lambda: self.app.show_page("Calendar"),
                   height=44, color=theme.SUCCESS).pack(fill="x", pady=4)
        PillButton(actions_inner, "🎙️ Voice Note", command=lambda: self.app.show_page("Voice Notes"),
                   height=44, color=theme.WARNING).pack(fill="x", pady=4)
        PillButton(actions_inner, "🚨 Emergency", command=lambda: self.app.show_page("Emergency"),
                   height=44, color=theme.DANGER).pack(fill="x", pady=4)

        mood_card = Card(right_col)
        mood_card.pack(fill="x")
        SectionTitle(mood_card, "🙂  How do you feel today?").pack(anchor="w", padx=20, pady=(18, 10))
        mood_row = ctk.CTkFrame(mood_card, fg_color="transparent")
        mood_row.pack(padx=20, pady=(0, 18))
        for emoji, mood in [("🙂", "Happy"), ("😐", "Okay"), ("😟", "Sad")]:
            ctk.CTkButton(mood_row, text=emoji, width=60, height=50, font=theme.font_heading(22),
                         fg_color=theme.BACKGROUND, hover_color=theme.CARD_HOVER,
                         text_color=theme.TEXT_DARK, corner_radius=12,
                         command=lambda m=mood: self._log_mood(m)).pack(side="left", padx=6)

    def _log_mood(self, mood):
        uid = self.user_id
        today = date.today().isoformat()
        existing = database.query("SELECT id FROM mood_log WHERE user_id=? AND date=?", (uid, today))
        if existing:
            database.execute("UPDATE mood_log SET mood=? WHERE user_id=? AND date=?", (mood, uid, today))
        else:
            database.execute("INSERT INTO mood_log (user_id, date, mood) VALUES (?,?,?)", (uid, today, mood))

    def _start_my_day(self):
        uid = self.user_id
        user_name = database.get_setting("user_name", "Friend", uid)
        meds = database.query("SELECT name, timing FROM medicines WHERE user_id=? AND taken_today=0", (uid,))
        appts = database.query("SELECT title, time FROM appointments WHERE user_id=? AND date=date('now')", (uid,))
        bills = database.query("SELECT name FROM bills WHERE user_id=? AND paid=0", (uid,))

        parts = [f"Good morning, {user_name}. Today is {date.today().strftime('%A, %B %d')}."]
        if meds:
            parts.append(f"You have {len(meds)} medicine reminder{'s' if len(meds)!=1 else ''} today.")
        if appts:
            a = appts[0]
            parts.append(f"You have an appointment: {a['title']} at {a['time']}.")
        if bills:
            parts.append(f"You have {len(bills)} bill{'s' if len(bills)!=1 else ''} due.")
        if not meds and not appts and not bills:
            parts.append("You have no urgent tasks today. Enjoy your day!")

        message = " ".join(parts)
        services.speak(message)

        popup = ctk.CTkToplevel(self)
        popup.title("Start My Day")
        popup.geometry("480x260")
        popup.grab_set()
        ctk.CTkLabel(popup, text="☀️ Your Day", font=theme.font_heading(20)).pack(pady=(20, 10))
        ctk.CTkLabel(popup, text=message, font=theme.font_body(15), wraplength=420,
                     justify="left").pack(padx=24, pady=10)
        PillButton(popup, "Got it", command=popup.destroy, width=140).pack(pady=16)
