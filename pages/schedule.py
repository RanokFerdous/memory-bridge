"""
pages/schedule.py
Enhanced Schedule Manager:
  - Per-user data isolation (user_id)
  - 5-day tab view: Today + next 4 days
  - "All Upcoming Tasks" timeline for next 5 days
  - Add Task with future date picker
  - Period grouping (Morning / Afternoon / Evening / Night)
"""

import customtkinter as ctk
from datetime import date, timedelta

import theme
import database
from widgets import Card, SectionTitle, PillButton, StatusBadge, confirm_dialog

PERIODS = ["Morning", "Afternoon", "Evening", "Night"]
PERIOD_ICON = {"Morning": "🌅", "Afternoon": "☀️", "Evening": "🌇", "Night": "🌙"}


class SchedulePage(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.user_id = app.current_user_id
        self._active_offset = 0    # 0 = today, 1 = tomorrow, …
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────
    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=theme.PAD, pady=(theme.PAD, 6))
        SectionTitle(header, "📋  Schedule Manager").pack(side="left")
        PillButton(header, "+ Add Task", command=self._open_add_form, width=160).pack(side="right")

        # 5-day tab bar
        tab_bar = ctk.CTkFrame(self, fg_color=theme.CARD, corner_radius=14,
                               border_width=1, border_color=theme.BORDER)
        tab_bar.pack(fill="x", padx=theme.PAD, pady=(0, 12))
        self._tab_btns = {}
        tab_colors = [theme.PRIMARY, theme.SUCCESS, theme.WARNING, "#9b59b6", "#1abc9c"]
        for offset in range(5):
            d = date.today() + timedelta(days=offset)
            if offset == 0:
                day_name = "Today"
            elif offset == 1:
                day_name = "Tomorrow"
            else:
                day_name = d.strftime("%a")
            full_label = f"{day_name}\n{d.strftime('%d %b')}"
            btn = ctk.CTkButton(
                tab_bar, text=full_label,
                font=theme.font_small(11, "bold"),
                height=54, corner_radius=12,
                fg_color=tab_colors[offset] if offset == self._active_offset else "transparent",
                text_color="white" if offset == self._active_offset else theme.TEXT_DARK,
                hover_color=theme.CARD_HOVER if offset != self._active_offset else tab_colors[offset],
                command=lambda o=offset: self._switch_day(o))
            btn.pack(side="left", fill="x", expand=True, padx=5, pady=6)
            self._tab_btns[offset] = btn

        # Per-day schedule body
        self.day_body = ctk.CTkFrame(self, fg_color="transparent")
        self.day_body.pack(fill="both", expand=True, padx=theme.PAD)

        # Upcoming all tasks panel
        upcoming_hdr = ctk.CTkFrame(self, fg_color="transparent")
        upcoming_hdr.pack(fill="x", padx=theme.PAD, pady=(16, 6))
        SectionTitle(upcoming_hdr, "🗓️  All Upcoming Tasks (Next 5 Days)").pack(side="left")
        self.upcoming_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.upcoming_frame.pack(fill="both", expand=True, padx=theme.PAD, pady=(0, 20))

        self._refresh()

    # ── Tab switch ────────────────────────────────────────────────────────
    def _switch_day(self, offset: int):
        self._active_offset = offset
        tab_colors = [theme.PRIMARY, theme.SUCCESS, theme.WARNING, "#9b59b6", "#1abc9c"]
        for o, btn in self._tab_btns.items():
            if o == offset:
                btn.configure(fg_color=tab_colors[o], text_color="white",
                              hover_color=tab_colors[o])
            else:
                btn.configure(fg_color="transparent", text_color=theme.TEXT_DARK,
                              hover_color=theme.CARD_HOVER)
        self._refresh()

    # ── Refresh ───────────────────────────────────────────────────────────
    def _refresh(self):
        # Clear day body
        for w in self.day_body.winfo_children():
            w.destroy()
        for w in self.upcoming_frame.winfo_children():
            w.destroy()

        target_date = (date.today() + timedelta(days=self._active_offset)).isoformat()
        target_dt   = date.today() + timedelta(days=self._active_offset)

        # Day label
        if self._active_offset == 0:
            day_title = f"Today — {target_dt.strftime('%A, %d %B %Y')}"
        elif self._active_offset == 1:
            day_title = f"Tomorrow — {target_dt.strftime('%A, %d %B %Y')}"
        else:
            day_title = target_dt.strftime('%A, %d %B %Y')

        date_header = ctk.CTkLabel(self.day_body, text=f"📅  {day_title}",
                                   font=theme.font_heading(16), text_color=theme.TEXT_DARK,
                                   anchor="w")
        date_header.pack(anchor="w", pady=(0, 10))

        # Period groups
        any_tasks = False
        for period in PERIODS:
            rows = database.query(
                "SELECT * FROM schedule WHERE user_id=? AND date=? AND period=? ORDER BY time",
                (self.user_id, target_date, period))

            card = Card(self.day_body)
            card.pack(fill="x", pady=6)

            period_hdr = ctk.CTkFrame(card, fg_color="transparent")
            period_hdr.pack(fill="x", padx=18, pady=(14, 4))
            ctk.CTkLabel(period_hdr,
                         text=f"{PERIOD_ICON[period]}  {period}",
                         font=theme.font_heading(15),
                         text_color=theme.TEXT_DARK).pack(side="left")
            ctk.CTkLabel(period_hdr,
                         text=f"{len(rows)} task{'s' if len(rows) != 1 else ''}",
                         font=theme.font_small(12),
                         text_color=theme.TEXT_MUTED).pack(side="left", padx=8)

            if not rows:
                ctk.CTkLabel(card, text="Nothing planned.",
                             text_color=theme.TEXT_MUTED,
                             font=theme.font_body(13)).pack(anchor="w", padx=18, pady=(0, 14))
            else:
                any_tasks = True
                for r in rows:
                    self._render_task_row(card, r)
            ctk.CTkFrame(card, fg_color="transparent", height=6).pack()

        if not any_tasks:
            empty = Card(self.day_body)
            empty.pack(fill="x", pady=6)
            ctk.CTkLabel(empty, text="🎉  No tasks scheduled for this day.\nTap '+ Add Task' to plan your day.",
                         font=theme.font_body(15), text_color=theme.TEXT_MUTED,
                         justify="center").pack(pady=30)

        # ── Upcoming 5-day timeline ────────────────────────────────────────
        upcoming = database.get_upcoming_schedule(self.user_id, 5)
        if not upcoming:
            ctk.CTkLabel(self.upcoming_frame, text="No upcoming tasks in the next 5 days.",
                         text_color=theme.TEXT_MUTED).pack(pady=16)
        else:
            # Group by date
            by_date = {}
            for row in upcoming:
                by_date.setdefault(row["date"], []).append(row)

            for d_str, tasks in sorted(by_date.items()):
                d_obj = date.fromisoformat(d_str)
                diff = (d_obj - date.today()).days
                if diff == 0:
                    label = "Today"
                elif diff == 1:
                    label = "Tomorrow"
                else:
                    label = d_obj.strftime("%A")

                grp = ctk.CTkFrame(self.upcoming_frame,
                                   fg_color=theme.CARD, corner_radius=12,
                                   border_width=1, border_color=theme.BORDER)
                grp.pack(fill="x", pady=6)

                grp_hdr = ctk.CTkFrame(grp, fg_color="transparent")
                grp_hdr.pack(fill="x", padx=16, pady=(12, 4))
                ctk.CTkLabel(grp_hdr,
                             text=f"📅 {label} — {d_obj.strftime('%d %B')}",
                             font=theme.font_body(14, "bold"),
                             text_color=theme.PRIMARY).pack(side="left")
                ctk.CTkLabel(grp_hdr,
                             text=f"{len(tasks)} task{'s' if len(tasks) != 1 else ''}",
                             font=theme.font_small(12),
                             text_color=theme.TEXT_MUTED).pack(side="left", padx=8)

                for task in tasks:
                    row_f = ctk.CTkFrame(grp, fg_color="transparent")
                    row_f.pack(fill="x", padx=16, pady=4)

                    # Time chip
                    time_chip = ctk.CTkFrame(row_f, fg_color=theme.BACKGROUND,
                                             corner_radius=8, width=82, height=28)
                    time_chip.pack(side="left", padx=(0, 10))
                    time_chip.pack_propagate(False)
                    ctk.CTkLabel(time_chip, text=task["time"],
                                 font=theme.font_small(11, "bold"),
                                 text_color=theme.PRIMARY).place(relx=0.5, rely=0.5, anchor="center")

                    ctk.CTkLabel(row_f, text=f"{PERIOD_ICON.get(task['period'], '📌')} {task['title']}",
                                 font=theme.font_body(13), anchor="w").pack(side="left", fill="x", expand=True)
                    StatusBadge(row_f, task["status"]).pack(side="right", padx=6)

                ctk.CTkFrame(grp, fg_color="transparent", height=8).pack()

    # ── Task row renderer ─────────────────────────────────────────────────
    def _render_task_row(self, parent, r):
        row_f = ctk.CTkFrame(parent, fg_color="transparent")
        row_f.pack(fill="x", padx=18, pady=5)

        ctk.CTkLabel(row_f, text=r["time"], font=theme.font_body(14, "bold"),
                     width=88, anchor="w").pack(side="left")
        ctk.CTkLabel(row_f, text=r["title"], font=theme.font_body(14),
                     anchor="w").pack(side="left", fill="x", expand=True)
        StatusBadge(row_f, r["status"]).pack(side="right", padx=6)

        if r["status"] == "Pending":
            PillButton(row_f, "✓ Done",
                       command=lambda rid=r["id"]: self._mark(rid, "Completed"),
                       color=theme.SUCCESS, height=30, width=80).pack(side="right", padx=3)
            PillButton(row_f, "✕ Missed",
                       command=lambda rid=r["id"]: self._mark(rid, "Missed"),
                       color=theme.DANGER, height=30, width=80).pack(side="right", padx=3)

        ctk.CTkButton(row_f, text="🗑️", width=32, height=30, fg_color="transparent",
                      text_color=theme.TEXT_MUTED, hover_color=theme.CARD_HOVER,
                      command=lambda rid=r["id"]: self._delete(rid)).pack(side="right", padx=3)

    # ── Actions ───────────────────────────────────────────────────────────
    def _mark(self, task_id, status):
        database.execute("UPDATE schedule SET status=? WHERE id=? AND user_id=?",
                         (status, task_id, self.user_id))
        self._refresh()
        self.app.refresh_right_panel()

    def _delete(self, task_id):
        def do():
            database.execute("DELETE FROM schedule WHERE id=? AND user_id=?",
                             (task_id, self.user_id))
            self._refresh()
        confirm_dialog(self, "Remove Task?", "Are you sure you want to remove this task?", do)

    # ── Add form ──────────────────────────────────────────────────────────
    def _open_add_form(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Add Task")
        popup.geometry("460x500")
        popup.grab_set()

        ctk.CTkLabel(popup, text="➕  Add New Task",
                     font=theme.font_heading(19)).pack(pady=(20, 14))

        form = ctk.CTkFrame(popup, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=28)

        # Task title
        ctk.CTkLabel(form, text="Task Title *", anchor="w",
                     text_color=theme.TEXT_MUTED).pack(anchor="w", pady=(0, 4))
        title_entry = ctk.CTkEntry(form, height=42, corner_radius=10)
        title_entry.pack(fill="x")

        # Date
        ctk.CTkLabel(form, text="Date (YYYY-MM-DD)", anchor="w",
                     text_color=theme.TEXT_MUTED).pack(anchor="w", pady=(14, 4))
        date_frame = ctk.CTkFrame(form, fg_color="transparent")
        date_frame.pack(fill="x")
        date_entry = ctk.CTkEntry(date_frame, height=42, corner_radius=10)
        date_entry.insert(0, (date.today() + timedelta(days=self._active_offset)).isoformat())
        date_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Quick date buttons
        quick_frame = ctk.CTkFrame(form, fg_color="transparent")
        quick_frame.pack(fill="x", pady=(4, 0))
        for label, offset in [("Today", 0), ("+1", 1), ("+2", 2), ("+3", 3), ("+4", 4)]:
            d = date.today() + timedelta(days=offset)
            ctk.CTkButton(quick_frame, text=label, width=52, height=30,
                          fg_color=theme.BACKGROUND, text_color=theme.PRIMARY,
                          hover_color=theme.CARD_HOVER, corner_radius=8,
                          font=theme.font_small(11, "bold"),
                          command=lambda dt=d.isoformat(): (
                              date_entry.delete(0, "end"),
                              date_entry.insert(0, dt)
                          )).pack(side="left", padx=3)

        # Time
        ctk.CTkLabel(form, text="Time (e.g. 09:00 AM)", anchor="w",
                     text_color=theme.TEXT_MUTED).pack(anchor="w", pady=(14, 4))
        time_entry = ctk.CTkEntry(form, height=42, corner_radius=10)
        time_entry.pack(fill="x")

        # Period
        ctk.CTkLabel(form, text="Period of Day", anchor="w",
                     text_color=theme.TEXT_MUTED).pack(anchor="w", pady=(14, 4))
        period_var = ctk.StringVar(value="Morning")
        period_menu = ctk.CTkOptionMenu(form, values=PERIODS, variable=period_var, height=42)
        period_menu.pack(fill="x")

        err_label = ctk.CTkLabel(popup, text="", text_color=theme.DANGER,
                                 font=theme.font_small(12))
        err_label.pack(pady=(6, 0))

        def save():
            title = title_entry.get().strip()
            task_date = date_entry.get().strip()
            if not title:
                err_label.configure(text="⚠  Task title is required.")
                return
            if not task_date:
                err_label.configure(text="⚠  Date is required.")
                return
            database.execute(
                "INSERT INTO schedule (user_id, date, time, title, period, status) VALUES (?,?,?,?,?,?)",
                (self.user_id, task_date,
                 time_entry.get().strip() or "—",
                 title, period_var.get(), "Pending"))
            popup.destroy()
            self._refresh()
            self.app.refresh_right_panel()

        PillButton(popup, "💾  Save Task", command=save, width=220).pack(pady=16)
