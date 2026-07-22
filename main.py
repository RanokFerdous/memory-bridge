"""
Memory Bridge - Your Digital Memory Companion
A desktop HCI project for elderly users with mild memory loss.

Run with:  python main.py
Requires:  Python 3.12+, see requirements.txt
"""

import customtkinter as ctk
from datetime import datetime
import threading
import time

import theme
import database
import services
from widgets import PillButton

from pages.dashboard import DashboardPage
from pages.medicines import MedicinesPage
from pages.schedule import SchedulePage
from pages.calendar_view import CalendarPage
from pages.family import FamilyPage
from pages.health import HealthPage
from pages.lost_items import LostItemsPage
from pages.voice_notes import VoiceNotesPage
from pages.emergency import EmergencyPage
from pages.settings_page import SettingsPage
from pages.login_page import LoginWindow

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

NAV_ITEMS = [
    ("Dashboard",        "🏠", DashboardPage),
    ("Medicines",        "💊", MedicinesPage),
    ("Today's Schedule", "📋", SchedulePage),
    ("Calendar",         "📅", CalendarPage),
    ("Family",           "👨‍👩‍👧", FamilyPage),
    ("Health",           "❤️", HealthPage),
    ("Lost Items",       "🔎", LostItemsPage),
    ("Voice Notes",      "🎙️", VoiceNotesPage),
    ("Emergency",        "🚨", EmergencyPage),
    ("Settings",         "⚙️", SettingsPage),
]


class MemoryBridgeApp(ctk.CTk):
    def __init__(self):
        super().__init__(  )
        database.init_db()

        self.title("Memory Bridge — Your Digital Memory Companion")
        self.geometry("1300x820")
        self.minsize(1100, 700)
        self.configure(fg_color=theme.BACKGROUND)

        # Will be set after login
        self.current_user_id = None
        self.current_user_name = "Friend"

        self.nav_buttons = {}
        self.current_page = None

        # Show login window first
        self._show_login()

    # ──────────────────────────────────────────────────────────────────────
    # LOGIN
    # ──────────────────────────────────────────────────────────────────────
    def _show_login(self):
        """Destroy any existing UI and show login screen."""
        for w in self.winfo_children():
            w.destroy()
        self.nav_buttons = {}
        self.current_page = None

        # Hide main window while login is shown
        self.withdraw()
        login = LoginWindow(self, on_success=self._on_login_success)

    def _on_login_success(self, user_id: int, user_name: str):
        """Called by LoginWindow when credentials are verified."""
        self.current_user_id = user_id
        self.current_user_name = user_name

        # Apply saved appearance mode
        mode = database.get_setting("appearance_mode", "Light", user_id)
        ctk.set_appearance_mode(mode)

        self.deiconify()
        self._build_ui()

    # ──────────────────────────────────────────────────────────────────────
    # MAIN UI BUILD
    # ──────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        """Build the full app UI after successful login."""
        for w in self.winfo_children():
            w.destroy()

        self._build_header()
        self._build_body()
        self.show_page("Dashboard")

        # Background reminder checker
        self._stop_flag = False
        threading.Thread(target=self._reminder_loop, daemon=True).start()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Live clock
        self._tick_clock()

    # ──────────────────────────────────────────────────────────────────────
    # HEADER
    # ──────────────────────────────────────────────────────────────────────
    def _build_header(self):
        header = ctk.CTkFrame(self, height=theme.HEADER_HEIGHT, fg_color=theme.CARD, corner_radius=0)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", padx=24)
        ctk.CTkLabel(left, text="🧠  Memory Bridge", font=theme.font_heading(22),
                     text_color=theme.PRIMARY).pack(side="left")

        mid = ctk.CTkFrame(header, fg_color="transparent")
        mid.pack(side="left", padx=30)
        self.date_label = ctk.CTkLabel(mid, text="", font=theme.font_body(14), text_color=theme.TEXT_MUTED)
        self.date_label.pack(anchor="w")
        self.time_label = ctk.CTkLabel(mid, text="", font=theme.font_heading(16), text_color=theme.TEXT_DARK)
        self.time_label.pack(anchor="w")

        self.search_entry = ctk.CTkEntry(
            header, placeholder_text="🔍  Search medicines, family, reminders...",
            width=320, height=40, corner_radius=20,
            fg_color=theme.BACKGROUND, border_width=0)
        self.search_entry.pack(side="left", padx=20)
        self.search_entry.bind("<Return>", self._on_search)

        # Right side
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", padx=16)

        PillButton(right, "🚨 Emergency", command=lambda: self.show_page("Emergency"),
                   color=theme.DANGER, height=38, width=130).pack(side="right", padx=4)
        PillButton(right, "🎙️ Voice", command=self._voice_assistant,
                   color=theme.PRIMARY, height=38, width=100).pack(side="right", padx=4)

        # User badge + Logout
        user_frame = ctk.CTkFrame(right, fg_color=theme.BACKGROUND, corner_radius=20)
        user_frame.pack(side="right", padx=8)
        ctk.CTkLabel(user_frame,
                     text=f"👤  {self.current_user_name}",
                     font=theme.font_body(13), text_color=theme.TEXT_DARK).pack(
                         side="left", padx=(12, 6), pady=6)
        ctk.CTkButton(user_frame, text="Logout", width=64, height=30,
                      fg_color=theme.DANGER, text_color="white",
                      hover_color="#c0392b", corner_radius=14,
                      font=theme.font_small(12, "bold"),
                      command=self._logout).pack(side="right", padx=(0, 8), pady=6)

    def _tick_clock(self):
        now = datetime.now()
        self.date_label.configure(text=now.strftime("%A, %d %B %Y"))
        self.time_label.configure(text=now.strftime("%I:%M %p"))
        self.after(1000, self._tick_clock)

    def _logout(self):
        self._stop_flag = True
        self.current_user_id = None
        self.current_user_name = "Friend"
        # Destroy body and show login
        for w in self.winfo_children():
            w.destroy()
        self._show_login()

    def _on_search(self, event=None):
        term = self.search_entry.get().strip()
        uid = self.current_user_id
        if not term:
            return
        results = []
        results += [f"💊 {r['name']}" for r in database.query(
            "SELECT name FROM medicines WHERE user_id=? AND name LIKE ?", (uid, f"%{term}%"))]
        results += [f"👨‍👩‍👧 {r['name']}" for r in database.query(
            "SELECT name FROM family WHERE user_id=? AND name LIKE ?", (uid, f"%{term}%"))]
        results += [f"🔎 {r['name']} — {r['location']}" for r in database.query(
            "SELECT name, location FROM lost_items WHERE user_id=? AND name LIKE ?", (uid, f"%{term}%"))]

        popup = ctk.CTkToplevel(self)
        popup.title("Search Results")
        popup.geometry("420x320")
        popup.grab_set()
        ctk.CTkLabel(popup, text=f"Results for '{term}'", font=theme.font_heading(16)).pack(pady=16)
        box = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        if not results:
            ctk.CTkLabel(box, text="No matches found.", text_color=theme.TEXT_MUTED).pack(pady=20)
        for r in results:
            ctk.CTkLabel(box, text=r, font=theme.font_body(14), anchor="w").pack(fill="x", pady=6)

    def _voice_assistant(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Voice Assistant")
        popup.geometry("460x260")
        popup.grab_set()
        ctk.CTkLabel(popup, text="🎙️ Ask Memory Bridge", font=theme.font_heading(18)).pack(pady=(20, 10))
        entry = ctk.CTkEntry(popup, placeholder_text="e.g. Did I take my medicine?", height=44, width=380)
        entry.pack(pady=10)
        answer_label = ctk.CTkLabel(popup, text="", font=theme.font_body(15), wraplength=400,
                                    text_color=theme.TEXT_DARK)
        answer_label.pack(pady=10)

        def ask():
            q = entry.get().lower().strip()
            answer = self._answer_question(q)
            answer_label.configure(text=answer)
            services.speak(answer)

        PillButton(popup, "Ask", command=ask, width=160).pack(pady=6)

    def _answer_question(self, q):
        uid = self.current_user_id
        if "medicine" in q:
            taken = database.query("SELECT name, last_taken FROM medicines WHERE user_id=? AND taken_today=1", (uid,))
            if taken:
                names = ", ".join(r["name"] for r in taken)
                return f"Yes, you already took: {names} today."
            return "You have not taken your medicine yet today."
        if "glass" in q or "keys" in q or "wallet" in q or "where" in q:
            for word in ["glasses", "keys", "wallet", "phone", "passport"]:
                if word in q:
                    row = database.query(
                        "SELECT location FROM lost_items WHERE user_id=? AND name LIKE ?", (uid, f"%{word}%"))
                    if row:
                        return f"Your {word} were last saved at: {row[0]['location']}"
            return "I could not find that item. Try saving it on the Lost Items page."
        if "appointment" in q or "doctor" in q:
            row = database.query(
                "SELECT title, time FROM appointments WHERE user_id=? AND date=date('now') ORDER BY time LIMIT 1",
                (uid,))
            if row:
                return f"Your next appointment today is {row[0]['title']} at {row[0]['time']}."
            return "You have no appointments scheduled for today."
        return "I'm not sure about that yet, but you can check the Dashboard for today's overview."

    # ──────────────────────────────────────────────────────────────────────
    # BODY  (sidebar + center + right panel)
    # ──────────────────────────────────────────────────────────────────────
    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color=theme.BACKGROUND)
        body.pack(side="top", fill="both", expand=True)

        # Sidebar
        self.sidebar = ctk.CTkScrollableFrame(body, width=theme.SIDEBAR_WIDTH,
                                              fg_color=theme.SIDEBAR_BG, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        for name, icon, _cls in NAV_ITEMS:
            btn = ctk.CTkButton(
                self.sidebar, text=f"  {icon}   {name}", anchor="w",
                font=theme.font_body(15), height=48, corner_radius=12,
                fg_color="transparent", text_color=theme.TEXT_DARK,
                hover_color=theme.CARD_HOVER,
                command=lambda n=name: self.show_page(n))
            btn.pack(fill="x", padx=12, pady=4)
            self.nav_buttons[name] = btn

        # Center content area
        self.center_container = ctk.CTkFrame(body, fg_color=theme.BACKGROUND)
        self.center_container.pack(side="left", fill="both", expand=True)

        # Right quick-info panel
        self.right_panel = ctk.CTkScrollableFrame(body, width=theme.RIGHT_PANEL_WIDTH,
                                                   fg_color=theme.CARD, corner_radius=0)
        self.right_panel.pack(side="right", fill="y")
        self._build_right_panel()

    def _build_right_panel(self):
        for w in self.right_panel.winfo_children():
            w.destroy()

        uid = self.current_user_id

        ctk.CTkLabel(self.right_panel, text="Today's Summary", font=theme.font_heading(17),
                     text_color=theme.TEXT_DARK).pack(anchor="w", padx=18, pady=(20, 10))

        # Next medicine
        next_med = database.query(
            "SELECT name, timing FROM medicines WHERE user_id=? AND taken_today=0 ORDER BY timing LIMIT 1",
            (uid,))
        card1 = ctk.CTkFrame(self.right_panel, fg_color=theme.BACKGROUND, corner_radius=12)
        card1.pack(fill="x", padx=18, pady=6)
        ctk.CTkLabel(card1, text="💊 Next Medicine", font=theme.font_small(13, "bold"),
                     text_color=theme.TEXT_MUTED).pack(anchor="w", padx=14, pady=(10, 0))
        text = f"{next_med[0]['name']} at {next_med[0]['timing']}" if next_med else "All medicines taken ✅"
        ctk.CTkLabel(card1, text=text, font=theme.font_body(15), wraplength=240).pack(
            anchor="w", padx=14, pady=(2, 12))

        # Next appointment
        appt = database.query(
            "SELECT title, time FROM appointments WHERE user_id=? AND date=date('now') ORDER BY time LIMIT 1",
            (uid,))
        card2 = ctk.CTkFrame(self.right_panel, fg_color=theme.BACKGROUND, corner_radius=12)
        card2.pack(fill="x", padx=18, pady=6)
        ctk.CTkLabel(card2, text="📅 Next Appointment", font=theme.font_small(13, "bold"),
                     text_color=theme.TEXT_MUTED).pack(anchor="w", padx=14, pady=(10, 0))
        text = f"{appt[0]['title']} at {appt[0]['time']}" if appt else "Nothing scheduled today"
        ctk.CTkLabel(card2, text=text, font=theme.font_body(15), wraplength=240).pack(
            anchor="w", padx=14, pady=(2, 12))

        # Water reminder
        from datetime import date as _date
        today = _date.today().isoformat()
        if database.get_setting("water_date", "", uid) != today:
            database.set_setting("water_date", today, uid)
            database.set_setting("water_count", 0, uid)
        count = int(database.get_setting("water_count", 0, uid))
        target = int(database.get_setting("water_target", 8, uid))

        card3 = ctk.CTkFrame(self.right_panel, fg_color=theme.BACKGROUND, corner_radius=12)
        card3.pack(fill="x", padx=18, pady=6)
        ctk.CTkLabel(card3, text="💧 Water Intake", font=theme.font_small(13, "bold"),
                     text_color=theme.TEXT_MUTED).pack(anchor="w", padx=14, pady=(10, 0))
        ctk.CTkLabel(card3, text=f"{count} / {target} glasses",
                     font=theme.font_body(15)).pack(anchor="w", padx=14, pady=(2, 6))

        def add_water():
            new_count = int(database.get_setting("water_count", 0, uid)) + 1
            database.set_setting("water_count", new_count, uid)
            self._build_right_panel()

        PillButton(card3, "I drank a glass", command=add_water, height=36,
                   color=theme.PRIMARY).pack(padx=14, pady=(0, 12), fill="x")

        # Emergency contact
        contact = database.query(
            "SELECT name, phone FROM family WHERE user_id=? AND is_emergency_contact=1 LIMIT 1", (uid,))
        card4 = ctk.CTkFrame(self.right_panel, fg_color=theme.BACKGROUND, corner_radius=12)
        card4.pack(fill="x", padx=18, pady=6)
        ctk.CTkLabel(card4, text="🚨 Emergency Contact", font=theme.font_small(13, "bold"),
                     text_color=theme.TEXT_MUTED).pack(anchor="w", padx=14, pady=(10, 0))
        text = f"{contact[0]['name']} — {contact[0]['phone']}" if contact else "No contact set"
        ctk.CTkLabel(card4, text=text, font=theme.font_body(15), wraplength=240).pack(
            anchor="w", padx=14, pady=(2, 12))

        # Weather placeholder
        card5 = ctk.CTkFrame(self.right_panel, fg_color=theme.BACKGROUND, corner_radius=12)
        card5.pack(fill="x", padx=18, pady=(6, 20))
        ctk.CTkLabel(card5, text="☀️ Weather", font=theme.font_small(13, "bold"),
                     text_color=theme.TEXT_MUTED).pack(anchor="w", padx=14, pady=(10, 0))
        ctk.CTkLabel(card5, text="Sunny, pleasant today",
                     font=theme.font_body(15)).pack(anchor="w", padx=14, pady=(2, 12))

    # ──────────────────────────────────────────────────────────────────────
    # PAGE ROUTING
    # ──────────────────────────────────────────────────────────────────────
    def show_page(self, name):
        for n, btn in self.nav_buttons.items():
            if n == name:
                btn.configure(fg_color=theme.PRIMARY, text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=theme.TEXT_DARK)

        for w in self.center_container.winfo_children():
            w.destroy()

        cls = dict((n, c) for n, _i, c in NAV_ITEMS)[name]
        page = cls(self.center_container, self)
        page.pack(fill="both", expand=True)
        self.current_page = name
        self.refresh_right_panel()

    def refresh_right_panel(self):
        self._build_right_panel()

    def refresh_current_page(self):
        if self.current_page:
            self.show_page(self.current_page)

    # ──────────────────────────────────────────────────────────────────────
    # BACKGROUND REMINDER LOOP
    # ──────────────────────────────────────────────────────────────────────
    def _reminder_loop(self):
        reminded_ids = set()
        while not self._stop_flag:
            try:
                if self.current_user_id:
                    now_str = datetime.now().strftime("%I:%M %p")
                    rows = database.query(
                        "SELECT id, title FROM schedule WHERE user_id=? AND date=date('now') AND time=? AND status='Pending'",
                        (self.current_user_id, now_str))
                    for r in rows:
                        if r["id"] not in reminded_ids:
                            services.notify("Memory Bridge Reminder", r["title"])
                            services.speak(f"Reminder: {r['title']}")
                            reminded_ids.add(r["id"])
            except Exception as e:
                print(f"[Reminder loop] {e}")
            time.sleep(30)

    def _on_close(self):
        self._stop_flag = True
        self.destroy()


if __name__ == "__main__":
    app = MemoryBridgeApp()
    app.mainloop()
