import customtkinter as ctk

import theme
import database
import services
from widgets import SectionTitle


class EmergencyPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.user_id = app.current_user_id
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="🚨 Emergency", font=theme.font_title(30),
                     text_color=theme.DANGER).pack(pady=(theme.PAD, 4))
        ctk.CTkLabel(self, text="Press any button below. Help will be contacted immediately.",
                     font=theme.font_body(16), text_color=theme.TEXT_MUTED).pack(pady=(0, 20))

        contacts = database.query(
            "SELECT name, phone FROM family WHERE user_id=? AND is_emergency_contact=1",
            (self.user_id,))
        buttons = []
        for c in contacts:
            buttons.append((f"👤 Call {c['name']}", c["phone"] or "No number saved", theme.PRIMARY))
        buttons += [
            ("🚑 Call Ambulance", "999", theme.DANGER),
            ("👮 Call Police", "999", theme.TEXT_DARK),
            ("🏥 Call Doctor", "Dr. Rahman", theme.SUCCESS),
            ("📍 Share My Location", "Sends location to family", theme.WARNING),
        ]

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(expand=True, fill="both", padx=theme.PAD, pady=theme.PAD)
        cols = 2
        for i in range(cols):
            grid.grid_columnconfigure(i, weight=1)
        for i in range((len(buttons) + 1) // cols):
            grid.grid_rowconfigure(i, weight=1)

        for idx, (label, sub, color) in enumerate(buttons):
            row, col = divmod(idx, cols)
            btn = ctk.CTkButton(grid, text=f"{label}\n{sub}", font=theme.font_button(19),
                                 fg_color=color, hover_color=theme.PRIMARY_DARK, text_color="white",
                                 corner_radius=24, height=theme.BIG_BUTTON_HEIGHT + 20,
                                 command=lambda l=label: self._trigger(l))
            btn.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")

    def _trigger(self, label):
        services.speak(f"{label}. Please stay calm, help is on the way.")
        services.notify("Emergency Alert", f"{label} triggered from Memory Bridge.")

        popup = ctk.CTkToplevel(self)
        popup.title("Emergency")
        popup.geometry("380x200")
        popup.grab_set()
        ctk.CTkLabel(popup, text="✅ Alert Sent", font=theme.font_heading(20),
                     text_color=theme.SUCCESS).pack(pady=(30, 10))
        ctk.CTkLabel(popup, text=label, font=theme.font_body(15), text_color=theme.TEXT_MUTED).pack()
        ctk.CTkButton(popup, text="Close", command=popup.destroy, fg_color=theme.PRIMARY,
                     height=44, corner_radius=12).pack(pady=24)
