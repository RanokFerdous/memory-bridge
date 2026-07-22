"""
services.py
Wraps pyttsx3 (voice) and plyer (desktop notifications) behind
simple functions, and runs them on background threads so the
CustomTkinter UI never freezes while speaking or notifying.
"""

import threading
import database


def speak(text: str):
    """Speak text out loud using pyttsx3, on a background thread."""
    if database.get_setting("voice_enabled", "1") != "1":
        return

    def _run():
        try:
            import pyttsx3
            engine = pyttsx3.init()
            rate = engine.getProperty("rate")
            engine.setProperty("rate", rate - 20)  # slightly slower, easier to follow
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"[Voice] Could not speak: {e}")

    threading.Thread(target=_run, daemon=True).start()


def notify(title: str, message: str, timeout: int = 8):
    """Show a desktop notification using plyer, on a background thread."""
    def _run():
        try:
            from plyer import notification
            notification.notify(title=title, message=message, timeout=timeout,
                                 app_name="Memory Bridge")
        except Exception as e:
            print(f"[Notify] Could not show notification: {e}")

    threading.Thread(target=_run, daemon=True).start()
