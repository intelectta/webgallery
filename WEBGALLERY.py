# ============================================================
# WEBGALLERY v1.0  –  Interactive HTML generator for media files
# ============================================================
# Author: INTELECTTA / ChatGPT GPT-5
# Python 3.10+ | Dependencies: tkinter, mutagen
# ------------------------------------------------------------
# Features:
# - Select multiple mp3/mp4 files
# - Choose which metadata fields and buttons to include
# - Generates a single self-contained HTML file with JS player
# - Saves last-used folder in config.json
# - Simple login/session (local)
# ============================================================

import os, json, time, hashlib, webbrowser
from tkinter import *
from tkinter import filedialog, messagebox, ttk
from mutagen import File as MFile

CONFIG_PATH = "config.json"
OUTPUT_DIR = "output"
USERS_FILE = "users.json"

# ------------- Helper Functions ------------------

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            return json.load(open(CONFIG_PATH, "r", encoding="utf-8"))
        except:
            return {}
    return {}

def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def hash_pw(pw:str)->str:
    return hashlib.sha256(pw.encode()).hexdigest()

def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------- HTML + JS template ----------------

def make_html(media_files, fields, actions):
    html_top = """<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1.0'>
<title>WebGallery</title>
<style>
body {font-family:Arial, sans-serif; background:#101010; color:#eee; margin:0; padding:20px;}
h1 {text-align:center; color:#0ff;}
.item {border:1px solid #333; padding:10px; margin:10px; border-radius:8px; background:#181818;}
button {margin:5px; padding:6px 10px; border:none; border-radius:4px; background:#333; color:#fff; cursor:pointer;}
button:hover {background:#0ff; color:#000;}
audio, video {width:100%; max-width:480px; margin-top:5px;}
</style>
</head><body>
<h1>🎧 WebGallery</h1>
<div id='gallery'>
"""
    html_items = ""
    for f in media_files:
        base = os.path.basename(f)
        ext = os.path.splitext(base)[1].lower()
        try:
            mf = MFile(f)
            dur = mf.info.length if mf and hasattr(mf.info, "length") else 0
        except Exception:
            dur = 0
        html_items += f"<div class='item'><h3>{base}</h3>"
        if "duration" in fields and dur:
            html_items += f"<p>Duration: {dur:.1f} sec</p>"
        if "path" in fields:
            html_items += f"<p>Path: {f}</p>"
        if ext in [".mp4", ".webm"]:
            html_items += f"<video controls src='{f}'></video>"
        else:
            html_items += f"<audio controls src='{f}'></audio>"
        for act in actions:
            if act == "Play":
                html_items += f"<button onclick='playMedia(\"{f}\")'>▶ Play</button>"
            elif act == "Pause":
                html_items += f"<button onclick='pauseMedia()'>⏸ Pause</button>"
            elif act == "Download":
                html_items += f"<button onclick='downloadFile(\"{f}\")'>⬇ Download</button>"
            elif act == "Like":
                html_items += f"<button onclick='like(this)'>❤️ Like</button>"
        html_items += "</div>\n"

    html_bottom = """</div>
<script>
let current = null;
function playMedia(src){
  if(current){current.pause();}
  current = new Audio(src);
  current.play();
}
function pauseMedia(){ if(current){ current.pause(); }}
function downloadFile(src){
  const a = document.createElement('a');
  a.href = src; a.download = src.split('/').pop(); a.click();
}
function like(btn){
  btn.textContent = '💖 Liked!';
  btn.disabled = true;
}
</script>
</body></html>
"""
    return html_top + html_items + html_bottom

# ------------- GUI Classes -----------------------

class LoginWindow(Toplevel):
    def __init__(self, master, callback):
        super().__init__(master)
        self.title("Login - WebGallery")
        self.geometry("300x200")
        self.callback = callback

        Label(self, text="Username:").pack(pady=5)
        self.user = Entry(self); self.user.pack()
        Label(self, text="Password:").pack(pady=5)
        self.pw = Entry(self, show="*"); self.pw.pack()
        Button(self, text="Login", command=self.login).pack(pady=10)
        Button(self, text="Register", command=self.register).pack()

    def login(self):
        u, p = self.user.get(), self.pw.get()
        if not os.path.exists(USERS_FILE):
            messagebox.showinfo("Info", "No users yet. Register first.")
            return
        users = json.load(open(USERS_FILE))
        if u in users and users[u]==hash_pw(p):
            self.callback(u)
            self.destroy()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def register(self):
        u, p = self.user.get(), self.pw.get()
        if not u or not p: return
        users = {}
        if os.path.exists(USERS_FILE):
            users = json.load(open(USERS_FILE))
        users[u]=hash_pw(p)
        json.dump(users, open(USERS_FILE,"w"))
        messagebox.showinfo("Registered", "User saved! Now login.")

# --------------------------------------------------

class WebGalleryApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("WEBGALLERY v1.0")
        self.geometry("720x600")
        ensure_dirs()
        self.config_data = load_config()
        self.username = None
        self.files = []

        self.login_window = LoginWindow(self, self.start_session)

    def start_session(self, username):
        self.username = username
        self.build_main_ui()

    def build_main_ui(self):
        Label(self, text=f"Logged in as: {self.username}", fg="cyan").pack(anchor='w', padx=10)
        frame = Frame(self); frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # --- left side ---
        left = Frame(frame); left.pack(side=LEFT, fill=Y)
        Button(left, text="Select Files", command=self.select_files).pack(pady=5)
        self.listbox = Listbox(left, width=50, height=25, selectmode=EXTENDED)
        self.listbox.pack(padx=5, pady=5, fill=Y)

        # --- right side ---
        right = Frame(frame); right.pack(side=LEFT, fill=BOTH, expand=True)

        Label(right, text="Select FIELDS:").pack(anchor='w')
        self.field_vars = {f: BooleanVar() for f in ["duration", "path"]}
        for f,v in self.field_vars.items():
            Checkbutton(right, text=f, var=v).pack(anchor='w')

        Label(right, text="Select ACTION BUTTONS:").pack(anchor='w', pady=(10,0))
        acts = ["Play","Pause","Download","Like"]
        self.action_vars = {a:BooleanVar() for a in acts}
        for a,v in self.action_vars.items():
            Checkbutton(right, text=a, var=v).pack(anchor='w')

        Button(right, text="Generate HTML", bg="#0ff", fg="#000",
               command=self.generate).pack(pady=20, fill=X)
        Button(right, text="Open Output Folder", command=self.open_output).pack(pady=5, fill=X)

        self.status = Label(self, text="", fg="yellow")
        self.status.pack(fill=X)

        if "last_dir" in self.config_data:
            self.status.config(text=f"Last folder: {self.config_data['last_dir']}")

    def select_files(self):
        lastdir = self.config_data.get("last_dir",".")
        f = filedialog.askopenfilenames(initialdir=lastdir,
                                        title="Select media files",
                                        filetypes=[("Media","*.mp3 *.mp4 *.wav *.webm")])
        if f:
            self.files = list(f)
            self.listbox.delete(0,END)
            for i in self.files: self.listbox.insert(END,i)
            self.config_data["last_dir"] = os.path.dirname(self.files[0])
            save_config(self.config_data)

    def generate(self):
        if not self.files:
            messagebox.showerror("Error","Select media files first.")
            return
        fields = [k for k,v in self.field_vars.items() if v.get()]
        acts = [k for k,v in self.action_vars.items() if v.get()]
        html = make_html(self.files, fields, acts)
        ts = int(time.time())
        outpath = os.path.join(OUTPUT_DIR, f"gallery_{ts}.html")
        with open(outpath,"w",encoding="utf-8") as f:
            f.write(html)
        self.status.config(text=f"Saved: {outpath}")
        webbrowser.open(outpath)

    def open_output(self):
        os.startfile(os.path.abspath(OUTPUT_DIR))

# --------------------------------------------------

if __name__ == "__main__":
    app = WebGalleryApp()
    app.mainloop()
