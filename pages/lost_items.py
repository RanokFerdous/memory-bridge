import customtkinter as ctk
from tkinter import filedialog
from datetime import date
import os
import shutil

import theme
import database
import services
from widgets import Card, SectionTitle, PillButton, confirm_dialog

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "item_photos")
os.makedirs(ASSETS_DIR, exist_ok=True)


class LostItemsPage(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.user_id = app.current_user_id
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=theme.PAD, pady=(theme.PAD, 10))
        SectionTitle(header, "🔎  Where Did I Keep It?").pack(side="left")
        PillButton(header, "+ Save Item Location", command=self._open_form, width=210).pack(side="right")

        self.search_var = ctk.StringVar()
        search = ctk.CTkEntry(self, textvariable=self.search_var,
                               placeholder_text="Search: passport, keys, glasses...",
                               height=44, corner_radius=12)
        search.pack(fill="x", padx=theme.PAD, pady=(0, 10))
        self.search_var.trace_add("write", lambda *a: self._refresh())

        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=theme.PAD)
        self._refresh()

    def _refresh(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()

        term = f"%{self.search_var.get()}%"
        items = database.query(
            "SELECT * FROM lost_items WHERE user_id=? AND name LIKE ? ORDER BY date_saved DESC",
            (self.user_id, term))

        if not items:
            ctk.CTkLabel(self.grid_frame, text="Nothing saved yet. Add an item's location above.",
                         text_color=theme.TEXT_MUTED).pack(pady=30)
            return

        cols = 3
        for i in range(cols):
            self.grid_frame.grid_columnconfigure(i, weight=1)

        for idx, item in enumerate(items):
            row, col = divmod(idx, cols)
            card = Card(self.grid_frame)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            photo_box = ctk.CTkFrame(card, width=200, height=120, corner_radius=12, fg_color=theme.BACKGROUND)
            photo_box.pack(padx=16, pady=(16, 10), fill="x")
            photo_box.pack_propagate(False)
            img = self._load_photo(item["photo_path"])
            if img:
                ctk.CTkLabel(photo_box, image=img, text="").place(relx=0.5, rely=0.5, anchor="center")
            else:
                ctk.CTkLabel(photo_box, text="📷", font=theme.font_title(36),
                             text_color=theme.TEXT_MUTED).place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkLabel(card, text=item["name"], font=theme.font_heading(17)).pack(padx=16, anchor="w")
            ctk.CTkLabel(card, text=f"📍 {item['location'] or 'Unknown'}", font=theme.font_body(13),
                         text_color=theme.TEXT_MUTED, anchor="w", wraplength=220).pack(padx=16, anchor="w")
            ctk.CTkLabel(card, text=f"Saved on {item['date_saved']}", font=theme.font_small(12),
                         text_color=theme.TEXT_MUTED, anchor="w").pack(padx=16, pady=(2, 10), anchor="w")

            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(pady=(0, 16))
            PillButton(btn_row, "🔊 Remind Me", height=34, width=110,
                       command=lambda it=item: self._speak_location(it)).grid(row=0, column=0, padx=4)
            ctk.CTkButton(btn_row, text="🗑️", width=40, height=34, fg_color=theme.BACKGROUND,
                         text_color=theme.DANGER, hover_color=theme.CARD_HOVER,
                         command=lambda iid=item["id"]: self._delete(iid)).grid(row=0, column=1, padx=4)

    def _load_photo(self, path):
        if not path or not PIL_AVAILABLE or not os.path.exists(path):
            return None
        try:
            image = Image.open(path)
            return ctk.CTkImage(light_image=image, dark_image=image, size=(180, 100))
        except Exception:
            return None

    def _speak_location(self, item):
        services.speak(f"Your {item['name']} is at: {item['location']}")

    def _delete(self, item_id):
        uid = self.user_id
        def do():
            database.execute("DELETE FROM lost_items WHERE id=? AND user_id=?", (item_id, uid))
            self._refresh()
        confirm_dialog(self, "Remove Item?", "Are you sure you want to remove this saved location?", do)

    def _open_form(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Save Item Location")
        popup.geometry("440x460")
        popup.grab_set()

        ctk.CTkLabel(popup, text="Save Where You Kept It", font=theme.font_heading(18)).pack(pady=(20, 14))

        form = ctk.CTkFrame(popup, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24)

        ctk.CTkLabel(form, text="Item Name (e.g. Passport)", text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w", pady=(6, 2))
        name_entry = ctk.CTkEntry(form, height=40)
        name_entry.pack(fill="x")

        ctk.CTkLabel(form, text="Location (e.g. Blue drawer)", text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w", pady=(14, 2))
        location_entry = ctk.CTkEntry(form, height=40)
        location_entry.pack(fill="x")

        photo_path_holder = {"path": None}

        def choose_photo():
            path = filedialog.askopenfilename(title="Choose Photo",
                                               filetypes=[("Images", "*.jpg *.jpeg *.png")])
            if path:
                dest = os.path.join(ASSETS_DIR, os.path.basename(path))
                try:
                    shutil.copy(path, dest)
                    photo_path_holder["path"] = dest
                except Exception:
                    pass

        PillButton(form, "📷 Add Photo (optional)", command=choose_photo, height=40).pack(fill="x", pady=(16, 4))

        def save():
            if not name_entry.get().strip():
                return
            database.execute(
                "INSERT INTO lost_items (user_id, name, location, photo_path, date_saved) VALUES (?,?,?,?,?)",
                (self.user_id, name_entry.get().strip(), location_entry.get().strip(),
                 photo_path_holder["path"], date.today().isoformat()))
            popup.destroy()
            self._refresh()

        PillButton(popup, "Save", command=save, width=200).pack(pady=18)
