import customtkinter as ctk
from tkinter import filedialog
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

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "family_photos")
os.makedirs(ASSETS_DIR, exist_ok=True)


class FamilyPage(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.user_id = app.current_user_id
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=theme.PAD, pady=(theme.PAD, 10))
        SectionTitle(header, "👨‍👩‍👧  Family Memory Book").pack(side="left")
        PillButton(header, "+ Add Family Member", command=self._open_add_form, width=210).pack(side="right")

        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=theme.PAD)
        self._refresh()

    def _refresh(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()

        people = database.query("SELECT * FROM family WHERE user_id=? ORDER BY name", (self.user_id,))
        if not people:
            ctk.CTkLabel(self.grid_frame, text="No family members added yet.",
                         text_color=theme.TEXT_MUTED).pack(pady=30)
            return

        cols = 3
        for i in range(cols):
            self.grid_frame.grid_columnconfigure(i, weight=1)

        for idx, p in enumerate(people):
            row, col = divmod(idx, cols)
            card = Card(self.grid_frame)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            photo_box = ctk.CTkFrame(card, width=90, height=90, corner_radius=45, fg_color=theme.PRIMARY)
            photo_box.pack(pady=(20, 10))
            photo_box.pack_propagate(False)

            img = self._load_photo(p["photo_path"])
            if img:
                ctk.CTkLabel(photo_box, image=img, text="").place(relx=0.5, rely=0.5, anchor="center")
            else:
                initials = "".join([w[0] for w in p["name"].split()][:2]).upper()
                ctk.CTkLabel(photo_box, text=initials, font=theme.font_heading(24),
                             text_color="white").place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkLabel(card, text=p["name"], font=theme.font_heading(17)).pack()
            ctk.CTkLabel(card, text=p["relationship"] or "", font=theme.font_body(13),
                         text_color=theme.TEXT_MUTED).pack()
            ctk.CTkLabel(card, text=f"🎂 {p['birthday'] or '—'}", font=theme.font_small(12),
                         text_color=theme.TEXT_MUTED).pack(pady=(2, 0))
            ctk.CTkLabel(card, text=f"📞 {p['phone'] or '—'}", font=theme.font_small(12),
                         text_color=theme.TEXT_MUTED).pack(pady=(0, 10))

            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(pady=(0, 8))
            PillButton(btn_row, "📞 Call", height=36, width=90,
                       command=lambda pp=p: self._call(pp)).grid(row=0, column=0, padx=4)
            PillButton(btn_row, "🎥 Video", height=36, width=90, color=theme.SUCCESS,
                       command=lambda pp=p: self._call(pp, video=True)).grid(row=0, column=1, padx=4)

            small_row = ctk.CTkFrame(card, fg_color="transparent")
            small_row.pack(pady=(0, 16))
            ctk.CTkButton(small_row, text="✏️ Edit", width=80, height=30, fg_color=theme.BACKGROUND,
                         text_color=theme.TEXT_DARK, hover_color=theme.CARD_HOVER,
                         command=lambda pp=p: self._open_edit_form(pp)).grid(row=0, column=0, padx=4)
            ctk.CTkButton(small_row, text="🗑️ Delete", width=80, height=30, fg_color=theme.BACKGROUND,
                         text_color=theme.DANGER, hover_color=theme.CARD_HOVER,
                         command=lambda pid=p["id"]: self._delete(pid)).grid(row=0, column=1, padx=4)

    def _load_photo(self, path):
        if not path or not PIL_AVAILABLE or not os.path.exists(path):
            return None
        try:
            image = Image.open(path)
            return ctk.CTkImage(light_image=image, dark_image=image, size=(90, 90))
        except Exception:
            return None

    def _call(self, person, video=False):
        kind = "Video call" if video else "Call"
        services.speak(f"{kind} to {person['name']}, your {person['relationship']}.")
        popup = ctk.CTkToplevel(self)
        popup.title(kind)
        popup.geometry("360x200")
        popup.grab_set()
        ctk.CTkLabel(popup, text=f"📞 {kind}ing {person['name']}...", font=theme.font_heading(18)).pack(pady=30)
        ctk.CTkLabel(popup, text=person["phone"] or "No phone number saved",
                     font=theme.font_body(15), text_color=theme.TEXT_MUTED).pack()
        PillButton(popup, "End", command=popup.destroy, width=140, color=theme.DANGER).pack(pady=20)

    def _delete(self, person_id):
        uid = self.user_id
        def do():
            database.execute("DELETE FROM family WHERE id=? AND user_id=?", (person_id, uid))
            self._refresh()
            self.app.refresh_right_panel()
        confirm_dialog(self, "Remove Family Member?", "Are you sure you want to remove this profile?", do)

    def _open_add_form(self):
        self._open_form(None)

    def _open_edit_form(self, person):
        self._open_form(person)

    def _open_form(self, person):
        popup = ctk.CTkToplevel(self)
        popup.title("Edit Family Member" if person else "Add Family Member")
        popup.geometry("460x640")
        popup.grab_set()

        ctk.CTkLabel(popup, text="Edit Family Member" if person else "Add Family Member",
                     font=theme.font_heading(19)).pack(pady=(20, 14))

        form = ctk.CTkFrame(popup, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24)

        fields = {}
        specs = [("name", "Full Name"), ("relationship", "Relationship (e.g. Daughter)"),
                 ("phone", "Phone Number"), ("birthday", "Birthday (e.g. 15 August)")]
        for key, label in specs:
            ctk.CTkLabel(form, text=label, anchor="w", text_color=theme.TEXT_MUTED).pack(anchor="w", pady=(8, 2))
            entry = ctk.CTkEntry(form, height=40)
            entry.pack(fill="x")
            if person and person[key]:
                entry.insert(0, str(person[key]))
            fields[key] = entry

        emergency_var = ctk.BooleanVar(value=bool(person["is_emergency_contact"]) if person else False)
        ctk.CTkCheckBox(form, text="Set as Emergency Contact", variable=emergency_var,
                         font=theme.font_body(14)).pack(anchor="w", pady=(14, 4))

        photo_path_holder = {"path": person["photo_path"] if person else None}

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

        PillButton(form, "📷 Choose Photo", command=choose_photo, height=40).pack(fill="x", pady=(10, 4))

        def save():
            name = fields["name"].get().strip()
            if not name:
                return
            values = (name, fields["relationship"].get().strip(), fields["phone"].get().strip(),
                      fields["birthday"].get().strip(), photo_path_holder["path"],
                      1 if emergency_var.get() else 0)
            if person:
                database.execute("""UPDATE family SET name=?, relationship=?, phone=?, birthday=?,
                    photo_path=?, is_emergency_contact=? WHERE id=? AND user_id=?""",
                    values + (person["id"], self.user_id))
            else:
                database.execute("""INSERT INTO family
                    (user_id, name, relationship, phone, birthday, photo_path, is_emergency_contact)
                    VALUES (?,?,?,?,?,?,?)""", (self.user_id,) + values)
            popup.destroy()
            self._refresh()
            self.app.refresh_right_panel()

        PillButton(popup, "Save", command=save, width=200).pack(pady=18)
