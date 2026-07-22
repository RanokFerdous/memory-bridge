"""
pages/login_page.py
Beautiful login / register screen shown before the main app.
Supports multi-user with email + password authentication.
"""

import customtkinter as ctk
import theme
import database
from widgets import PillButton


class LoginWindow(ctk.CTkToplevel):
    """
    Shown as a modal before the main MemoryBridgeApp.
    On successful login/register, calls on_success(user_id, user_name).
    """

    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success
        self._mode = "login"   # "login" or "register"

        self.title("Memory Bridge — Sign In")
        self.geometry("520x640")
        self.resizable(False, False)
        self.configure(fg_color=theme.BACKGROUND)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 520) // 2
        y = (self.winfo_screenheight() - 640) // 2
        self.geometry(f"520x640+{x}+{y}")

        self._build()

    def _on_close(self):
        # Close whole app if login window is closed
        self.master.destroy()

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        # ── Header banner ────────────────────────────────────────────────
        banner = ctk.CTkFrame(self, fg_color=theme.PRIMARY, corner_radius=0, height=160)
        banner.pack(fill="x")
        banner.pack_propagate(False)

        ctk.CTkLabel(banner, text="🧠", font=ctk.CTkFont(size=52)).pack(pady=(22, 4))
        ctk.CTkLabel(banner, text="Memory Bridge",
                     font=ctk.CTkFont(family=theme.FONT_FAMILY, size=26, weight="bold"),
                     text_color="white").pack()
        ctk.CTkLabel(banner, text="Your Digital Memory Companion",
                     font=ctk.CTkFont(family=theme.FONT_FAMILY, size=13),
                     text_color="#d0e8ff").pack(pady=(2, 0))

        # ── Form card ────────────────────────────────────────────────────
        card = ctk.CTkFrame(self, fg_color=theme.CARD, corner_radius=20,
                            border_width=1, border_color=theme.BORDER)
        card.pack(fill="both", expand=True, padx=36, pady=28)

        title_text = "Welcome Back 👋" if self._mode == "login" else "Create Account 🎉"
        ctk.CTkLabel(card, text=title_text,
                     font=ctk.CTkFont(family=theme.FONT_FAMILY, size=22, weight="bold"),
                     text_color=theme.TEXT_DARK).pack(pady=(24, 6))
        sub_text = "Sign in to your account" if self._mode == "login" else "Fill in details to get started"
        ctk.CTkLabel(card, text=sub_text,
                     font=ctk.CTkFont(family=theme.FONT_FAMILY, size=13),
                     text_color=theme.TEXT_MUTED).pack(pady=(0, 20))

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=28)

        # Name field — only for register
        self._name_frame = ctk.CTkFrame(form, fg_color="transparent")
        if self._mode == "register":
            self._name_frame.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(self._name_frame, text="Full Name",
                         font=ctk.CTkFont(family=theme.FONT_FAMILY, size=13),
                         text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w", pady=(0, 4))
            self._name_entry = ctk.CTkEntry(self._name_frame, height=46, corner_radius=12,
                                             placeholder_text="e.g. Ranok Ahmed",
                                             font=ctk.CTkFont(family=theme.FONT_FAMILY, size=14))
            self._name_entry.pack(fill="x")

        # Email
        ctk.CTkLabel(form, text="Email Address",
                     font=ctk.CTkFont(family=theme.FONT_FAMILY, size=13),
                     text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w", pady=(0, 4))
        self._email_entry = ctk.CTkEntry(form, height=46, corner_radius=12,
                                          placeholder_text="you@example.com",
                                          font=ctk.CTkFont(family=theme.FONT_FAMILY, size=14))
        self._email_entry.pack(fill="x", pady=(0, 12))

        # Password
        ctk.CTkLabel(form, text="Password",
                     font=ctk.CTkFont(family=theme.FONT_FAMILY, size=13),
                     text_color=theme.TEXT_MUTED, anchor="w").pack(anchor="w", pady=(0, 4))
        pw_row = ctk.CTkFrame(form, fg_color="transparent")
        pw_row.pack(fill="x", pady=(0, 4))
        self._pw_entry = ctk.CTkEntry(pw_row, height=46, corner_radius=12, show="•",
                                       placeholder_text="Your password",
                                       font=ctk.CTkFont(family=theme.FONT_FAMILY, size=14))
        self._pw_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._show_pw = False
        self._eye_btn = ctk.CTkButton(pw_row, text="👁", width=46, height=46, corner_radius=12,
                                       fg_color=theme.BACKGROUND, text_color=theme.TEXT_MUTED,
                                       hover_color=theme.CARD_HOVER, command=self._toggle_pw)
        self._eye_btn.pack(side="right")

        # Error label
        self._err_label = ctk.CTkLabel(form, text="", text_color=theme.DANGER,
                                        font=ctk.CTkFont(family=theme.FONT_FAMILY, size=12),
                                        wraplength=380, anchor="w")
        self._err_label.pack(anchor="w", pady=(4, 0))

        # Main action button
        btn_text = "Sign In  →" if self._mode == "login" else "Create Account  →"
        PillButton(card, btn_text, command=self._submit,
                   height=50, width=300).pack(pady=(18, 10))

        # Toggle mode
        toggle_text = "Don't have an account?  Register →" if self._mode == "login" \
                      else "Already have an account?  Sign In →"
        ctk.CTkButton(card, text=toggle_text,
                      fg_color="transparent", hover_color=theme.CARD_HOVER,
                      text_color=theme.PRIMARY,
                      font=ctk.CTkFont(family=theme.FONT_FAMILY, size=13),
                      command=self._toggle_mode).pack(pady=(0, 8))

        # Demo hint
        if self._mode == "login":
            ctk.CTkLabel(card, text="💡 Register a new account to get started with demo data",
                         font=ctk.CTkFont(family=theme.FONT_FAMILY, size=11),
                         text_color=theme.TEXT_MUTED).pack(pady=(0, 16))

        # Bind Enter key
        self._email_entry.bind("<Return>", lambda e: self._submit())
        self._pw_entry.bind("<Return>", lambda e: self._submit())

    def _toggle_pw(self):
        self._show_pw = not self._show_pw
        self._pw_entry.configure(show="" if self._show_pw else "•")
        self._eye_btn.configure(text="🙈" if self._show_pw else "👁")

    def _toggle_mode(self):
        self._mode = "register" if self._mode == "login" else "login"
        self._build()

    def _set_error(self, msg):
        self._err_label.configure(text=f"⚠  {msg}")

    def _submit(self):
        self._err_label.configure(text="")

        email = self._email_entry.get().strip()
        password = self._pw_entry.get().strip()

        if not email or not password:
            self._set_error("Please fill in all fields.")
            return
        if "@" not in email:
            self._set_error("Please enter a valid email address.")
            return
        if len(password) < 4:
            self._set_error("Password must be at least 4 characters.")
            return

        if self._mode == "register":
            name = self._name_entry.get().strip() if hasattr(self, "_name_entry") else ""
            if not name:
                self._set_error("Please enter your full name.")
                return
            ok, result = database.register_user(name, email, password)
            if not ok:
                self._set_error(result)
                return
            user_id = result
            # Update user_name setting to the registered name
            database.set_setting("user_name", name, user_id)
            self.grab_release()
            self.destroy()
            self.on_success(user_id, name)
        else:
            user = database.verify_user(email, password)
            if not user:
                self._set_error("Incorrect email or password.")
                return
            name = database.get_setting("user_name", user["name"], user["id"])
            self.grab_release()
            self.destroy()
            self.on_success(user["id"], name)
