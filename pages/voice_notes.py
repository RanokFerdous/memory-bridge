import customtkinter as ctk
from datetime import datetime

import theme
import database
import services
from widgets import Card, SectionTitle, PillButton, confirm_dialog


class VoiceNotesPage(ctk.CTkScrollableFrame):
    """
    Voice Notes page.

    Note: true speech-to-text needs an extra library (e.g. SpeechRecognition
    + a microphone backend) which was not in the requested package list.
    To keep the project runnable out-of-the-box with only the packages you
    asked for, this page provides a big "Speak / Type Your Note" button that
    captures the note as text and then SPEAKS it back and saves it as a
    reminder using pyttsx3 - so the voice *output* side is fully functional.
    If you later add SpeechRecognition + PyAudio, you can swap the text
    entry below for a real microphone capture with minimal changes.
    """

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.user_id = app.current_user_id
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=theme.PAD, pady=(theme.PAD, 10))
        SectionTitle(header, "🎙️  Voice Notes").pack(side="left")

        record_card = Card(self)
        record_card.pack(fill="x", padx=theme.PAD, pady=10)
        inner = ctk.CTkFrame(record_card, fg_color="transparent")
        inner.pack(padx=24, pady=24, fill="x")

        ctk.CTkLabel(inner, text="Press the button, then say or type what you want to remember.",
                     font=theme.font_body(15), text_color=theme.TEXT_MUTED).pack(anchor="w", pady=(0, 12))

        self.note_entry = ctk.CTkEntry(inner, placeholder_text="e.g. Buy rice tomorrow",
                                        height=48, corner_radius=14, font=theme.font_body(15))
        self.note_entry.pack(fill="x", pady=(0, 14))
        self.note_entry.bind("<Return>", lambda e: self._save_note())

        big_btn = ctk.CTkButton(inner, text="🎙️  Save Voice Note", height=theme.BIG_BUTTON_HEIGHT,
                                 corner_radius=20, font=theme.font_button(20), fg_color=theme.PRIMARY,
                                 hover_color=theme.PRIMARY_DARK, command=self._save_note)
        big_btn.pack(fill="x")

        list_card = Card(self)
        list_card.pack(fill="both", expand=True, padx=theme.PAD, pady=(0, theme.PAD))
        SectionTitle(list_card, "📝  Saved Notes").pack(anchor="w", padx=20, pady=(18, 10))
        self.list_body = ctk.CTkFrame(list_card, fg_color="transparent")
        self.list_body.pack(fill="both", expand=True, padx=20, pady=(0, 18))
        self._refresh()

    def _save_note(self):
        text = self.note_entry.get().strip()
        if not text:
            return
        now = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        database.execute("INSERT INTO voice_notes (user_id, text, created_at) VALUES (?,?,?)",
                         (self.user_id, text, now))
        services.speak(f"Saved reminder: {text}")
        services.notify("Voice Note Saved", text)
        self.note_entry.delete(0, "end")
        self._refresh()

    def _refresh(self):
        for w in self.list_body.winfo_children():
            w.destroy()

        notes = database.query("SELECT * FROM voice_notes WHERE user_id=? ORDER BY id DESC",
                               (self.user_id,))
        if not notes:
            ctk.CTkLabel(self.list_body, text="No voice notes yet.", text_color=theme.TEXT_MUTED).pack(pady=10)
            return

        for n in notes:
            row = ctk.CTkFrame(self.list_body, fg_color=theme.BACKGROUND, corner_radius=12)
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text=n["text"], font=theme.font_body(15), anchor="w",
                         wraplength=560).pack(anchor="w", padx=16, pady=(12, 0))
            ctk.CTkLabel(row, text=n["created_at"], font=theme.font_small(12),
                         text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w", padx=16, pady=(2, 10))

            btn_row = ctk.CTkFrame(row, fg_color="transparent")
            btn_row.place(relx=1.0, rely=0.5, anchor="e", x=-16)
            ctk.CTkButton(btn_row, text="🔊", width=36, height=32, fg_color=theme.CARD,
                         hover_color=theme.CARD_HOVER,
                         command=lambda t=n["text"]: services.speak(t)).pack(side="left", padx=3)
            ctk.CTkButton(btn_row, text="🗑️", width=36, height=32, fg_color=theme.CARD,
                         text_color=theme.DANGER, hover_color=theme.CARD_HOVER,
                         command=lambda nid=n["id"]: self._delete(nid)).pack(side="left", padx=3)

    def _delete(self, note_id):
        uid = self.user_id
        def do():
            database.execute("DELETE FROM voice_notes WHERE id=? AND user_id=?", (note_id, uid))
            self._refresh()
        confirm_dialog(self, "Delete Note?", "Are you sure you want to delete this voice note?", do)
