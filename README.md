# 🧠 Memory Bridge — Your Digital Memory Companion

A desktop HCI project built for elderly users with mild memory loss.
Built with **Python + CustomTkinter + SQLite**.

<!--

step 1;
 PS H:\OneDrive\Desktop\3_2 course  document\HCL_PROJECT_LIST\memory bridge copy file here> python.exe -m pip install -r requirements.txt


 step 2:
   PS H:\OneDrive\Desktop\3_2 course  document\HCL_PROJECT_LIST\memory bridge copy file here> python.exe main.py


 -->

---

---

## 🚀 How to Run (from source)

### Step 1 — Open Terminal in the project folder

```powershell
cd "h:\OneDrive\Desktop\3_2 course  document\HCL_PROJECT_LIST\memory bridge copy file here\memory_bridge - Copy"
```

### Step 2 — Activate Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

> **First time only** — if `.venv` doesn't exist yet:
> ```powershell
> python -m venv .venv
> .\.venv\Scripts\Activate.ps1
> pip install -r requirements.txt
> ```

### Step 3 — Run the App

```powershell
python main.py
```

---

## 📦 Build as a Standalone .EXE (share with anyone)

### Option A — One-click batch script (easiest)

1. Make sure your `.venv` is **activated** (see Step 2 above)
2. Install PyInstaller once:
   ```powershell
   pip install pyinstaller
   ```
3. Double-click **`build_exe.bat`** in File Explorer  
   *(or run `.\build_exe.bat` in the terminal)*
4. Wait 1–3 minutes → your app appears at **`dist\MemoryBridge.exe`**

### Option B — Manual command

```powershell
# Activate venv first, then:
pip install pyinstaller
pyinstaller memory_bridge.spec
```

### What you get

```
dist/
└── MemoryBridge.exe   ← share this single file!
```

> ✅ No Python needed on the target PC — just double-click and run  
> ✅ Database is saved next to the `.exe` in `data/memory_bridge.db`

---

## 🌐 Publish for Free (so anyone can download it)

### GitHub Releases (recommended)

1. Create a free account at **github.com**
2. Create a new repository (e.g. `memory-bridge`)
3. Go to **Releases → Create a new release**
4. Upload `dist/MemoryBridge.exe` as an asset
5. Share the release link — anyone can download it!

### Google Drive / OneDrive

1. Upload `dist/MemoryBridge.exe` to your cloud drive
2. Right-click → **Share → Anyone with the link**
3. Copy and share the link

---


## 🔐 Login System

When the app launches, you will see a **Login screen**.

- **First time?** Click **"Register"** to create a new account with your name, email and password.
- **Returning?** Sign in with your email and password.
- Each user has **completely separate** data (medicines, tasks, family, etc.).
- Click the **Logout** button in the top-right header to switch accounts.

### Demo — Quickstart

1. Launch app → click "Register →"
2. Enter: **Name** = `Ranok`, **Email** = `ranok@example.com`, **Password** = `1234`
3. App opens with demo medicines, schedule, and family members pre-loaded
4. Register a second user (e.g. `sara@example.com`) — she will have her own separate data

---

## ✨ New Features

### 1. Multi-User Login

- Secure email + password authentication (SHA-256 hashed passwords)
- Each user's medicines, schedule, family, health records are fully isolated
- Register as many users as needed — all share one database file

### 2. Enhanced Medicine Manager

- **3-day tab view**: Today → Tomorrow → Day After Tomorrow
- Each tab shows medicines scheduled for that day with their exact time
- "Take Now" button logs which day medicine was taken (no double-counting)
- Add medicines with **Start Date / End Date / Frequency** (Daily, Weekly, As Needed)
- Master list shows all medicines with full date range info

### 3. Enhanced Schedule Manager

- **5-day tab bar**: Today, Tomorrow, +2, +3, +4 days
- Add tasks for **any future date** using the quick date buttons (+1, +2, +3…)
- **"All Upcoming Tasks"** panel shows every task across the next 5 days in one timeline
- Mark tasks as Done ✓ or Missed ✕ per day

---

## 📁 Project Structure

```
memory_bridge - Copy/
├── main.py              # App window: login gate, header, sidebar, routing
├── database.py          # SQLite schema + all data access (multi-user)
├── theme.py             # Colors, fonts, sizes
├── widgets.py           # Reusable UI pieces (cards, buttons, badges)
├── services.py          # pyttsx3 voice + plyer notifications
├── requirements.txt
├── pages/
│   ├── login_page.py    # ⭐ NEW: Login / Register screen
│   ├── dashboard.py     # Home: greeting, stats, timeline, quick actions
│   ├── medicines.py     # ⭐ Enhanced: 3-day tab + date-range scheduling
│   ├── schedule.py      # ⭐ Enhanced: 5-day tabs + upcoming timeline
│   ├── calendar_view.py # Calendar with appointments & bills
│   ├── family.py        # Family Memory Book
│   ├── health.py        # Health Dashboard
│   ├── lost_items.py    # "Where Did I Keep It?" finder
│   ├── voice_notes.py   # Voice notes → reminders
│   ├── emergency.py     # One-touch emergency page
│   └── settings_page.py # Theme, font, voice, backup/restore
└── data/               # memory_bridge.db (auto-created)
```

---

## ⚙️ Requirements

| Package       | Version  | Purpose                        |
| ------------- | -------- | ------------------------------ |
| customtkinter | ≥ 5.2.2  | Modern UI framework            |
| Pillow        | ≥ 10.0.0 | Image handling                 |
| pyttsx3       | ≥ 2.90   | Text-to-speech voice reminders |
| plyer         | ≥ 2.1.0  | Desktop notifications          |
| tkcalendar    | ≥ 1.6.1  | Calendar widget                |

---

## 🗄️ Notes

- The SQLite database is stored at `data/memory_bridge.db`
- If you want to start fresh, delete `data/memory_bridge.db` and relaunch
- Voice reminders use `pyttsx3` (works offline) — works best on Windows
- Desktop notifications use `plyer` — may need `notify2` on Linux

---

## 📌 HCI Principles Applied

| Principle               | Where                                       |
| ----------------------- | ------------------------------------------- |
| Recognition over Recall | Photos in Family, icons everywhere          |
| Consistency             | Shared `theme.py` / `widgets.py`            |
| Visibility of Status    | Status badges, right panel                  |
| Error Prevention        | Confirm dialogs before all deletes          |
| Accessibility           | 48px+ buttons, high contrast, voice I/O     |
| User Control            | Per-user data, logout, edit/delete anywhere |
