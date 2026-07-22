import customtkinter as ctk
import shutil
from tkinter import filedialog
import os

import theme
import database
from widgets import Card, SectionTitle, PillButton


class SettingsPage(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.user_id = app.current_user_id
        self._build()

    def _build(self):
        SectionTitle(self, "⚙️  Settings").pack(anchor="w", padx=theme.PAD, pady=(theme.PAD, 10))

        # Profile
        card = Card(self)
        card.pack(fill="x", padx=theme.PAD, pady=8)
        SectionTitle(card, "👤 Your Name").pack(anchor="w", padx=20, pady=(16, 6))
        name_entry = ctk.CTkEntry(card, height=42)
        name_entry.insert(0, database.get_setting("user_name", "Friend", self.user_id))
        name_entry.pack(fill="x", padx=20, pady=(0, 12))

        def save_name():
            database.set_setting("user_name", name_entry.get().strip() or "Friend", self.user_id)
            self.app.refresh_current_page()
        PillButton(card, "Save Name", command=save_name, height=40, width=160).pack(
            anchor="w", padx=20, pady=(0, 16))

        # Appearance
        card2 = Card(self)
        card2.pack(fill="x", padx=theme.PAD, pady=8)
        SectionTitle(card2, "🎨 Appearance").pack(anchor="w", padx=20, pady=(16, 6))
        mode_row = ctk.CTkFrame(card2, fg_color="transparent")
        mode_row.pack(anchor="w", padx=20, pady=(0, 16))
        ctk.CTkLabel(mode_row, text="Theme:", font=theme.font_body(14)).pack(side="left", padx=(0, 10))
        mode_var = ctk.StringVar(value=database.get_setting("appearance_mode", "Light", self.user_id))

        def change_mode(choice):
            ctk.set_appearance_mode(choice)
            database.set_setting("appearance_mode", choice, self.user_id)

        ctk.CTkOptionMenu(mode_row, values=["Light", "Dark", "System"], variable=mode_var,
                         command=change_mode, height=38).pack(side="left")

        # Font size
        card3 = Card(self)
        card3.pack(fill="x", padx=theme.PAD, pady=8)
        SectionTitle(card3, "🔤 Text Size").pack(anchor="w", padx=20, pady=(16, 6))
        ctk.CTkLabel(card3, text="Larger text is easier to read. Restart the app after changing this.",
                     font=theme.font_small(13), text_color=theme.TEXT_MUTED).pack(anchor="w", padx=20)
        scale_var = ctk.DoubleVar(value=float(database.get_setting("font_scale", 1.0, self.user_id)))

        def change_scale(val):
            database.set_setting("font_scale", round(float(val), 2), self.user_id)

        ctk.CTkSlider(card3, from_=0.8, to=1.5, variable=scale_var, command=change_scale).pack(
            fill="x", padx=20, pady=(8, 16))

        # Voice
        card4 = Card(self)
        card4.pack(fill="x", padx=theme.PAD, pady=8)
        SectionTitle(card4, "🔊 Voice Reminders").pack(anchor="w", padx=20, pady=(16, 6))
        voice_var = ctk.BooleanVar(value=database.get_setting("voice_enabled", "1", self.user_id) == "1")

        def toggle_voice():
            database.set_setting("voice_enabled", "1" if voice_var.get() else "0", self.user_id)

        ctk.CTkSwitch(card4, text="Enable spoken reminders and voice assistant replies",
                     variable=voice_var, command=toggle_voice, font=theme.font_body(14)).pack(
            anchor="w", padx=20, pady=(0, 16))

        # Water target
        card5 = Card(self)
        card5.pack(fill="x", padx=theme.PAD, pady=8)
        SectionTitle(card5, "💧 Daily Water Goal").pack(anchor="w", padx=20, pady=(16, 6))
        water_row = ctk.CTkFrame(card5, fg_color="transparent")
        water_row.pack(anchor="w", padx=20, pady=(0, 16))
        water_entry = ctk.CTkEntry(water_row, width=80, height=38)
        water_entry.insert(0, database.get_setting("water_target", "8", self.user_id))
        water_entry.pack(side="left", padx=(0, 10))

        def save_water():
            try:
                target = int(water_entry.get())
                database.set_setting("water_target", target, self.user_id)
                self.app.refresh_right_panel()
            except ValueError:
                pass
        PillButton(water_row, "Save", command=save_water, height=38, width=100).pack(side="left")

        # Backup / Restore
        card6 = Card(self)
        card6.pack(fill="x", padx=theme.PAD, pady=8)
        SectionTitle(card6, "💾 Backup & Restore").pack(anchor="w", padx=20, pady=(16, 6))
        btn_row = ctk.CTkFrame(card6, fg_color="transparent")
        btn_row.pack(anchor="w", padx=20, pady=(0, 16))
        PillButton(btn_row, "Backup Data", command=self._backup, height=40, width=160).pack(side="left", padx=(0, 10))
        PillButton(btn_row, "Restore Data", command=self._restore, height=40, width=160,
                   color=theme.WARNING).pack(side="left")

    def _backup(self):
        dest = filedialog.asksaveasfilename(defaultextension=".db",
                                             filetypes=[("Database", "*.db")],
                                             initialfile="memory_bridge_backup.db")
        if dest:
            try:
                shutil.copy(database.DB_PATH, dest)
            except Exception as e:
                print(f"Backup failed: {e}")

    def _restore(self):
        src = filedialog.askopenfilename(filetypes=[("Database", "*.db")])
        if src and os.path.exists(src):
            try:
                shutil.copy(src, database.DB_PATH)
                self.app.refresh_current_page()
            except Exception as e:
                print(f"Restore failed: {e}")
