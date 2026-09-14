import sys
import base64
import os
import shutil
import string
import secrets
import sqlite3
import hashlib
import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken
from PIL import Image

# إعداد المظهر العام
ctk.set_appearance_mode("System")

# ألوان مستوحاة من شعار Egyxos
BRAND_COLOR = "#234060"
BRAND_HOVER = "#172A40"
ACCENT_COLOR = "#335C8A"

# نص التحقق المستخدم للتأكد من صحة كلمة المرور الرئيسية
VERIFIER_TEXT = "EGYXOS_VAULT_OK"

# مدة الاحتفاظ بالقيمة المنسوخة قبل مسحها تلقائيًا (بالثواني)
CLIPBOARD_CLEAR_SECONDS = 20

# أيقونة ولون مميزان لكل فئة من فئات الحسابات
CATEGORY_STYLES = {
    "Social Media": ("💬", "#7C4DFF"),
    "Work": ("💼", "#3F51B5"),
    "Banking": ("🏦", "#2E7D32"),
    "Web Hosting": ("🌐", "#F57C00"),
    "Others": ("🗂️", "#607D8B"),
}
DEFAULT_CATEGORY_STYLE = ("📁", BRAND_COLOR)


class EgyxosManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Egyxos - Enterprise Password Manager")
        self.root.geometry("850x550")
        self.root.resizable(False, False)

        # تعيين أيقونة التطبيق
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
            icon_path = os.path.join(base_path, "egyxos_icon.ico")
            self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Error loading icon: {e}")

        self.db_file = self.get_vault_path()
        self.key = None
        self.conn = None
        self.cursor = None
        self.show_manual_password = False

        # تحميل الشعار
        self.logo_image = None
        self.small_logo = None
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
            logo_path = os.path.join(base_path, "logo.png")

            img_data = Image.open(logo_path)
            self.logo_image = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(220, 110))
            self.small_logo = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(60, 30))
        except Exception as e:
            print(f"Error loading logo: {e}")

        self.init_db()
        self.create_auth_screen()

        # التأكد من إغلاق قاعدة البيانات بشكل صحيح عند إغلاق التطبيق
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def get_vault_path(self):
        """يحدد مكانًا ثابتًا لملف الخزنة بعيدًا عن مجلد التشغيل الحالي،
        حتى لا يضيع الملف عند تشغيل التطبيق من اختصار أو مجلد مختلف."""
        if os.name == 'nt':
            base = os.getenv('APPDATA', os.path.expanduser('~'))
        else:
            base = os.path.join(os.path.expanduser('~'), '.config')

        app_dir = os.path.join(base, 'Egyxos')
        os.makedirs(app_dir, exist_ok=True)
        new_path = os.path.join(app_dir, 'egyxos_vault.db')

        # ترحيل تلقائي لخزنة قديمة كانت محفوظة بجانب البرنامج التنفيذي
        if not os.path.exists(new_path):
            if getattr(sys, 'frozen', False):
                exe_dir = os.path.dirname(sys.executable)
            else:
                exe_dir = os.path.abspath(".")
            old_path = os.path.join(exe_dir, 'egyxos_vault.db')
            if os.path.exists(old_path):
                try:
                    shutil.copy2(old_path, new_path)
                except Exception as e:
                    print(f"Could not migrate old vault: {e}")

        return new_path

    def on_close(self):
        if self.conn:
            self.conn.close()
        self.root.destroy()

    def init_db(self):
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS metadata (
                               id INTEGER PRIMARY KEY,
                               salt TEXT,
                               verifier TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS vault (
                               id INTEGER PRIMARY KEY,
                               service TEXT,
                               username TEXT,
                               password TEXT,
                               category TEXT)''')
        self.conn.commit()

        # ترقية قواعد بيانات قديمة لا تحتوي على عمود verifier
        try:
            self.cursor.execute("ALTER TABLE metadata ADD COLUMN verifier TEXT")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # العمود موجود بالفعل

    def _generate_key(self, master_password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
        )
        return base64.urlsafe_b64encode(kdf.derive(master_password.encode()))

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def toggle_appearance_mode(self):
        current = ctk.get_appearance_mode()  # "Light" or "Dark"
        new_mode = "Dark" if current == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)
        if hasattr(self, 'theme_toggle_btn') and self.theme_toggle_btn.winfo_exists():
            self.theme_toggle_btn.configure(text="☀️  Light Mode" if new_mode == "Dark" else "🌙  Dark Mode")

    def make_theme_toggle(self, master):
        current = ctk.get_appearance_mode()
        btn = ctk.CTkButton(master, text="☀️  Light Mode" if current == "Dark" else "🌙  Dark Mode",
                             width=160, fg_color="transparent", border_width=1, border_color=BRAND_COLOR,
                             text_color=BRAND_COLOR, hover_color="#e0e0e0", command=self.toggle_appearance_mode)
        self.theme_toggle_btn = btn
        return btn

    def create_auth_screen(self):
        self.clear_window()
        self.key = None  # التأكد من محو المفتاح من الذاكرة عند العودة لشاشة الدخول

        # زر تبديل المظهر أعلى يمين النافذة
        self.make_theme_toggle(self.root).place(relx=0.97, rely=0.04, anchor="ne")

        self.cursor.execute("SELECT salt FROM metadata WHERE id=1")
        result = self.cursor.fetchone()
        is_new_vault = result is None

        frame_height = 480 if is_new_vault else 420
        frame = ctk.CTkFrame(master=self.root, width=380, height=frame_height, corner_radius=15)
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # عرض الشعار بدون تكرار النصوص
        if self.logo_image:
            logo_label = ctk.CTkLabel(master=frame, text="", image=self.logo_image)
            logo_label.pack(pady=(35, 15))

        self.master_entry = ctk.CTkEntry(master=frame, width=280, placeholder_text="Master Password",
                                          show="*", border_color=BRAND_COLOR)
        self.master_entry.pack(pady=(20, 10) if is_new_vault else 20)

        self.confirm_entry = None
        if is_new_vault:
            self.confirm_entry = ctk.CTkEntry(master=frame, width=280, placeholder_text="Confirm Master Password",
                                               show="*", border_color=BRAND_COLOR)
            self.confirm_entry.pack(pady=10)

            btn = ctk.CTkButton(master=frame, text="Create New Vault", width=280, command=self.init_vault,
                                 fg_color=BRAND_COLOR, hover_color=BRAND_HOVER, font=("Arial", 14, "bold"))
        else:
            btn = ctk.CTkButton(master=frame, text="Unlock Vault", width=280, command=self.unlock_vault,
                                 fg_color=BRAND_COLOR, hover_color=BRAND_HOVER, font=("Arial", 14, "bold"))
        btn.pack(pady=(10, 30))

        # الضغط على Enter يقوم بنفس عملية الزر
        self.master_entry.bind("<Return>", lambda e: btn.invoke())
        if self.confirm_entry:
            self.confirm_entry.bind("<Return>", lambda e: btn.invoke())
        self.master_entry.focus()

    def init_vault(self):
        mp = self.master_entry.get()
        confirm = self.confirm_entry.get() if self.confirm_entry else mp

        if not mp:
            messagebox.showerror("Error", "Master password cannot be empty!")
            return
        if len(mp) < 8:
            messagebox.showerror("Error", "Master password must be at least 8 characters.")
            return
        if mp != confirm:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        salt = os.urandom(16)
        self.key = self._generate_key(mp, salt)

        # تشفير نص التحقق لاستخدامه لاحقًا في التأكد من صحة كلمة المرور
        f_cipher = Fernet(self.key)
        verifier_enc = f_cipher.encrypt(VERIFIER_TEXT.encode()).decode('utf-8')

        salt_b64 = base64.b64encode(salt).decode('utf-8')
        self.cursor.execute("INSERT INTO metadata (id, salt, verifier) VALUES (1, ?, ?)",
                             (salt_b64, verifier_enc))
        self.conn.commit()
        self.create_main_screen()

    def unlock_vault(self):
        mp = self.master_entry.get()
        if not mp:
            return

        self.cursor.execute("SELECT salt, verifier FROM metadata WHERE id=1")
        row = self.cursor.fetchone()
        salt_b64, verifier_enc = row[0], row[1]
        salt = base64.b64decode(salt_b64)

        self.key = self._generate_key(mp, salt)

        # التحقق الفعلي من كلمة المرور عبر فك تشفير نص التحقق
        if not verifier_enc:
            # قاعدة بيانات قديمة بدون verifier - ننشئه الآن لهذه المرة فقط
            messagebox.showwarning("Notice", "Vault upgraded to the new security check.")
            f_cipher = Fernet(self.key)
            verifier_enc = f_cipher.encrypt(VERIFIER_TEXT.encode()).decode('utf-8')
            self.cursor.execute("UPDATE metadata SET verifier=? WHERE id=1", (verifier_enc,))
            self.conn.commit()
            self.create_main_screen()
            return

        try:
            f_cipher = Fernet(self.key)
            decrypted = f_cipher.decrypt(verifier_enc.encode()).decode('utf-8')
            if decrypted != VERIFIER_TEXT:
                raise InvalidToken()
        except Exception:
            messagebox.showerror("Error", "Invalid Master Password!")
            return

        self.create_main_screen()

    def lock_vault(self):
        self.key = None
        self.create_auth_screen()

    def create_main_screen(self):
        self.clear_window()
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self.root, width=320, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")

        if self.small_logo:
            sidebar_logo = ctk.CTkLabel(sidebar, text="", image=self.small_logo)
            sidebar_logo.pack(pady=(20, 10))
        else:
            ctk.CTkLabel(sidebar, text="EGYXOS", font=("Arial Black", 20), text_color=BRAND_COLOR).pack(pady=20)

        self.service_entry = ctk.CTkEntry(sidebar, placeholder_text="Service Name", width=250, border_color=BRAND_COLOR)
        self.service_entry.pack(pady=5)

        self.user_entry = ctk.CTkEntry(sidebar, placeholder_text="Username / Email", width=250, border_color=BRAND_COLOR)
        self.user_entry.pack(pady=5)

        pass_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        pass_row.pack(pady=5)

        self.pass_entry = ctk.CTkEntry(pass_row, placeholder_text="Password", width=210, show="*",
                                        border_color=BRAND_COLOR)
        self.pass_entry.pack(side="left")
        self.pass_entry.bind("<KeyRelease>", self.check_password_strength)

        self.toggle_pass_btn = ctk.CTkButton(pass_row, text="👁", width=32, fg_color="transparent",
                                              border_width=1, border_color=BRAND_COLOR, text_color=BRAND_COLOR,
                                              hover_color="#e0e0e0", command=self.toggle_manual_password)
        self.toggle_pass_btn.pack(side="left", padx=(5, 0))

        self.strength_bar = ctk.CTkProgressBar(sidebar, width=250, height=8, progress_color=BRAND_COLOR)
        self.strength_bar.set(0)
        self.strength_bar.pack(pady=(5, 2))

        self.strength_label = ctk.CTkLabel(sidebar, text="", font=("Arial", 11, "bold"))
        self.strength_label.pack(pady=(0, 5))

        self.category_combo = ctk.CTkComboBox(sidebar, values=["Social Media", "Work", "Banking", "Web Hosting", "Others"],
                                              width=250, border_color=BRAND_COLOR, button_color=BRAND_COLOR, button_hover_color=BRAND_HOVER)
        self.category_combo.pack(pady=10)

        ctk.CTkButton(sidebar, text="Generate Secure", width=250, fg_color="transparent", border_width=2,
                      text_color=BRAND_COLOR, border_color=BRAND_COLOR, hover_color="#e0e0e0", command=self.generate_pass).pack(pady=5)

        ctk.CTkButton(sidebar, text="Save Entry", width=250, fg_color=BRAND_COLOR, hover_color=BRAND_HOVER,
                      font=("Arial", 14, "bold"), command=self.save_password).pack(pady=15)

        bottom_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom_row.pack(side="bottom", pady=20)

        self.make_theme_toggle(bottom_row).pack(pady=5)

        ctk.CTkButton(bottom_row, text="Change Master Password", width=250, fg_color="transparent",
                      border_width=1, border_color=BRAND_COLOR, text_color=BRAND_COLOR, hover_color="#e0e0e0",
                      command=self.open_change_master_password).pack(pady=5)

        ctk.CTkButton(bottom_row, text="🔒 Lock Vault", width=250, fg_color="#dc3545", hover_color="#c82333",
                      command=self.lock_vault).pack(pady=5)

        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        search_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search services...", width=300, border_color=BRAND_COLOR)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_services(self.search_entry.get()))

        self.services_scroll = ctk.CTkScrollableFrame(main_frame)
        self.services_scroll.pack(fill="both", expand=True)

        self.load_services()

    def toggle_manual_password(self):
        self.show_manual_password = not self.show_manual_password
        self.pass_entry.configure(show="" if self.show_manual_password else "*")
        self.toggle_pass_btn.configure(text="🙈" if self.show_manual_password else "👁")

    def check_password_strength(self, event=None):
        pwd = self.pass_entry.get()
        score = 0
        if len(pwd) >= 8: score += 0.2
        if len(pwd) >= 12: score += 0.2
        if any(c.islower() for c in pwd) and any(c.isupper() for c in pwd): score += 0.2
        if any(c.isdigit() for c in pwd): score += 0.2
        if any(c in string.punctuation for c in pwd): score += 0.2

        self.strength_bar.set(score)

        if not pwd:
            self.strength_label.configure(text="")
        elif score < 0.4:
            self.strength_bar.configure(progress_color="#dc3545")
            self.strength_label.configure(text="Weak", text_color="#dc3545")
        elif score < 0.8:
            self.strength_bar.configure(progress_color="#ffc107")
            self.strength_label.configure(text="Medium", text_color="#b98900")
        else:
            self.strength_bar.configure(progress_color="#28a745")
            self.strength_label.configure(text="Strong", text_color="#28a745")

    def generate_pass(self):
        alphabet = string.ascii_letters + string.digits + string.punctuation
        while True:
            password = ''.join(secrets.choice(alphabet) for _ in range(16))
            if (any(c.islower() for c in password) and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password) and any(c in string.punctuation for c in password)):
                break

        self.pass_entry.delete(0, tk.END)
        self.pass_entry.insert(0, password)
        self.show_manual_password = True
        self.pass_entry.configure(show="")
        self.toggle_pass_btn.configure(text="🙈")
        self.check_password_strength()

    def save_password(self):
        service = self.service_entry.get().strip()
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        category = self.category_combo.get()

        if not service or not username or not password:
            messagebox.showerror("Error", "Service, username and password are required.")
            return

        f_cipher = Fernet(self.key)
        enc_user = f_cipher.encrypt(username.encode()).decode('utf-8')
        enc_pass = f_cipher.encrypt(password.encode()).decode('utf-8')

        self.cursor.execute("INSERT INTO vault (service, username, password, category) VALUES (?, ?, ?, ?)",
                            (service, enc_user, enc_pass, category))
        self.conn.commit()

        self.service_entry.delete(0, tk.END)
        self.user_entry.delete(0, tk.END)
        self.pass_entry.delete(0, tk.END)
        self.show_manual_password = False
        self.pass_entry.configure(show="*")
        self.toggle_pass_btn.configure(text="👁")
        self.strength_bar.set(0)
        self.strength_label.configure(text="")
        self.load_services()

    def load_services(self, search_query=""):
        for widget in self.services_scroll.winfo_children():
            widget.destroy()

        if search_query:
            self.cursor.execute("SELECT id, service, category FROM vault WHERE service LIKE ?", ('%'+search_query+'%',))
        else:
            self.cursor.execute("SELECT id, service, category FROM vault")

        rows = self.cursor.fetchall()

        if not rows:
            empty_frame = ctk.CTkFrame(self.services_scroll, fg_color="transparent")
            empty_frame.pack(expand=True, pady=60)
            ctk.CTkLabel(empty_frame, text="🔐", font=("Arial", 40)).pack(pady=(0, 10))
            if search_query:
                msg = f"No entries match \"{search_query}\"."
            else:
                msg = "Your vault is empty.\nAdd your first password from the panel on the left."
            ctk.CTkLabel(empty_frame, text=msg, font=("Arial", 14), text_color=("gray30", "gray70"),
                         justify="center").pack()
            return

        for row in rows:
            record_id, service, category = row
            icon, color = CATEGORY_STYLES.get(category, DEFAULT_CATEGORY_STYLE)
            btn_text = f"{icon}  {service}      {category}"

            btn = ctk.CTkButton(self.services_scroll, text=btn_text, anchor="w",
                                fg_color="transparent", border_width=2, border_color=color,
                                hover_color=ACCENT_COLOR, text_color=("gray10", "gray90"),
                                command=lambda rid=record_id, s=service: self.show_details(rid, s))
            btn.pack(fill="x", pady=5, padx=5)

    def check_pwned_api(self, password):
        # تشغيل الاستعلام في خيط منفصل حتى لا يتجمد التطبيق أثناء انتظار الشبكة
        threading.Thread(target=self._check_pwned_worker, args=(password,), daemon=True).start()

    def _check_pwned_worker(self, password):
        import requests  # استيراد مؤجل لتسريع بدء تشغيل التطبيق

        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix, suffix = sha1_hash[:5], sha1_hash[5:]
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        headers = {"User-Agent": "Egyxos-Password-Manager"}

        for attempt in range(2):  # محاولة واحدة إضافية في حال انتهاء المهلة
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()

                pairs = (line.split(':') for line in response.text.splitlines())
                for h, count in pairs:
                    if h == suffix:
                        self.root.after(0, lambda: messagebox.showwarning(
                            "Security Alert",
                            f"This password has been leaked {count} times in data breaches! Change it immediately."))
                        return
                self.root.after(0, lambda: messagebox.showinfo(
                    "Safe", "This password has not been found in known data breaches."))
                return

            except requests.exceptions.SSLError as e:
                self.root.after(0, lambda e=e: messagebox.showerror(
                    "SSL Error",
                    "Could not verify HIBP's security certificate.\n\n"
                    "This usually happens in a packaged .exe when the certificate bundle "
                    "wasn't included in the build. Rebuild with:\n"
                    "--collect-data certifi\n\n"
                    f"Details: {e}"))
                return
            except requests.exceptions.Timeout:
                if attempt == 0:
                    continue  # حاول مرة أخرى قبل الاستسلام
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", "Connection to HIBP timed out twice. Check your internet connection or firewall."))
                return
            except requests.exceptions.ConnectionError as e:
                self.root.after(0, lambda e=e: messagebox.showerror(
                    "Error",
                    "Could not reach the HIBP API. This is usually a network, proxy, or firewall/antivirus block.\n\n"
                    f"Details: {e}"))
                return
            except Exception as e:
                self.root.after(0, lambda e=e: messagebox.showerror("Error", f"Could not connect to HIBP API.\n\nDetails: {e}"))
                return

    def copy_to_clipboard(self, text, label="Value"):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        messagebox.showinfo("Copied", f"{label} copied to clipboard.\nIt will be cleared automatically in {CLIPBOARD_CLEAR_SECONDS} seconds.")
        self.root.after(CLIPBOARD_CLEAR_SECONDS * 1000, lambda: self._clear_clipboard_if_unchanged(text))

    def _clear_clipboard_if_unchanged(self, text):
        try:
            current = self.root.clipboard_get()
        except tk.TclError:
            current = None
        if current == text:
            self.root.clipboard_clear()

    def delete_entry(self, record_id, win):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this entry? This cannot be undone."):
            self.cursor.execute("DELETE FROM vault WHERE id=?", (record_id,))
            self.conn.commit()
            win.destroy()
            self.load_services()

    def show_details(self, record_id, service):
        self.cursor.execute("SELECT username, password, category FROM vault WHERE id=?", (record_id,))
        enc_user, enc_pass, category = self.cursor.fetchone()

        f_cipher = Fernet(self.key)
        try:
            username = f_cipher.decrypt(enc_user.encode()).decode('utf-8')
            password = f_cipher.decrypt(enc_pass.encode()).decode('utf-8')

            icon, color = CATEGORY_STYLES.get(category, DEFAULT_CATEGORY_STYLE)

            win = ctk.CTkToplevel(self.root)
            win.title(service)
            win.geometry("400x460")
            win.grab_set()

            ctk.CTkLabel(win, text=f"{icon}  {service}", font=("Arial Black", 20), text_color=color).pack(pady=(20, 2))
            ctk.CTkLabel(win, text=category, font=("Arial", 12), text_color=("gray40", "gray60")).pack(pady=(0, 10))

            user_row = ctk.CTkFrame(win, fg_color="transparent")
            user_row.pack(pady=5)
            ctk.CTkLabel(user_row, text=f"User: {username}", font=("Arial", 14)).pack(side="left", padx=(0, 10))
            ctk.CTkButton(user_row, text="Copy", width=60, fg_color=BRAND_COLOR, hover_color=BRAND_HOVER,
                          command=lambda: self.copy_to_clipboard(username, "Username")).pack(side="left")

            p_entry = ctk.CTkEntry(win, width=220, justify="center", border_color=BRAND_COLOR)
            p_entry.insert(0, password)
            p_entry.configure(state="readonly")
            p_entry.pack(pady=10)

            ctk.CTkButton(win, text="Copy Password", fg_color=BRAND_COLOR, hover_color=BRAND_HOVER,
                          command=lambda: self.copy_to_clipboard(password, "Password")).pack(pady=5)

            ctk.CTkButton(win, text="Check if Pwned", fg_color="#dc3545", hover_color="#c82333",
                          command=lambda: self.check_pwned_api(password)).pack(pady=10)

            ctk.CTkButton(win, text="Edit Entry", fg_color=ACCENT_COLOR, hover_color=BRAND_HOVER,
                          command=lambda: self.edit_entry(record_id, service, username, password, category, win)).pack(pady=5)

            ctk.CTkButton(win, text="Delete Entry", fg_color="#dc3545", hover_color="#c82333",
                          command=lambda: self.delete_entry(record_id, win)).pack(pady=5)

            ctk.CTkButton(win, text="Close", fg_color=BRAND_COLOR, hover_color=BRAND_HOVER,
                          command=win.destroy).pack(pady=10)
        except Exception:
            messagebox.showerror("Error", "Decryption failed!")

    def edit_entry(self, record_id, service, username, password, category, parent_win):
        parent_win.destroy()

        win = ctk.CTkToplevel(self.root)
        win.title(f"Edit - {service}")
        win.geometry("380x420")
        win.grab_set()

        ctk.CTkLabel(win, text=f"Edit {service}", font=("Arial Black", 18), text_color=BRAND_COLOR).pack(pady=15)

        service_entry = ctk.CTkEntry(win, width=250, border_color=BRAND_COLOR)
        service_entry.insert(0, service)
        service_entry.pack(pady=5)

        user_entry = ctk.CTkEntry(win, width=250, border_color=BRAND_COLOR)
        user_entry.insert(0, username)
        user_entry.pack(pady=5)

        pass_entry = ctk.CTkEntry(win, width=250, border_color=BRAND_COLOR)
        pass_entry.insert(0, password)
        pass_entry.pack(pady=5)

        category_combo = ctk.CTkComboBox(win, values=["Social Media", "Work", "Banking", "Web Hosting", "Others"],
                                          width=250, border_color=BRAND_COLOR, button_color=BRAND_COLOR,
                                          button_hover_color=BRAND_HOVER)
        category_combo.set(category)
        category_combo.pack(pady=10)

        def save_changes():
            new_service = service_entry.get().strip()
            new_user = user_entry.get().strip()
            new_pass = pass_entry.get().strip()
            new_category = category_combo.get()

            if not new_service or not new_user or not new_pass:
                messagebox.showerror("Error", "All fields are required.")
                return

            f_cipher = Fernet(self.key)
            enc_user = f_cipher.encrypt(new_user.encode()).decode('utf-8')
            enc_pass = f_cipher.encrypt(new_pass.encode()).decode('utf-8')

            self.cursor.execute(
                "UPDATE vault SET service=?, username=?, password=?, category=? WHERE id=?",
                (new_service, enc_user, enc_pass, new_category, record_id)
            )
            self.conn.commit()
            win.destroy()
            self.load_services()

        ctk.CTkButton(win, text="Save Changes", fg_color=BRAND_COLOR, hover_color=BRAND_HOVER,
                      font=("Arial", 14, "bold"), command=save_changes).pack(pady=20)
        ctk.CTkButton(win, text="Cancel", fg_color="transparent", border_width=1, border_color=BRAND_COLOR,
                      text_color=BRAND_COLOR, hover_color="#e0e0e0", command=win.destroy).pack(pady=5)

    def open_change_master_password(self):
        win = ctk.CTkToplevel(self.root)
        win.title("Change Master Password")
        win.geometry("380x340")
        win.grab_set()

        ctk.CTkLabel(win, text="Change Master Password", font=("Arial Black", 16), text_color=BRAND_COLOR).pack(pady=15)

        current_entry = ctk.CTkEntry(win, width=250, placeholder_text="Current Master Password", show="*",
                                      border_color=BRAND_COLOR)
        current_entry.pack(pady=8)

        new_entry = ctk.CTkEntry(win, width=250, placeholder_text="New Master Password", show="*",
                                  border_color=BRAND_COLOR)
        new_entry.pack(pady=8)

        confirm_entry = ctk.CTkEntry(win, width=250, placeholder_text="Confirm New Password", show="*",
                                      border_color=BRAND_COLOR)
        confirm_entry.pack(pady=8)

        def apply_change():
            current_mp = current_entry.get()
            new_mp = new_entry.get()
            confirm_mp = confirm_entry.get()

            if not current_mp or not new_mp:
                messagebox.showerror("Error", "All fields are required.")
                return
            if len(new_mp) < 8:
                messagebox.showerror("Error", "New master password must be at least 8 characters.")
                return
            if new_mp != confirm_mp:
                messagebox.showerror("Error", "New passwords do not match.")
                return

            # التحقق من كلمة المرور الحالية أولًا
            self.cursor.execute("SELECT salt, verifier FROM metadata WHERE id=1")
            salt_b64, verifier_enc = self.cursor.fetchone()
            salt = base64.b64decode(salt_b64)
            current_key = self._generate_key(current_mp, salt)

            try:
                current_cipher = Fernet(current_key)
                decrypted = current_cipher.decrypt(verifier_enc.encode()).decode('utf-8')
                if decrypted != VERIFIER_TEXT:
                    raise InvalidToken()
            except Exception:
                messagebox.showerror("Error", "Current master password is incorrect.")
                return

            # فك تشفير كل الإدخالات بالمفتاح القديم
            self.cursor.execute("SELECT id, username, password FROM vault")
            entries = self.cursor.fetchall()

            decrypted_entries = []
            try:
                for entry_id, enc_user, enc_pass in entries:
                    user_plain = current_cipher.decrypt(enc_user.encode()).decode('utf-8')
                    pass_plain = current_cipher.decrypt(enc_pass.encode()).decode('utf-8')
                    decrypted_entries.append((entry_id, user_plain, pass_plain))
            except Exception:
                messagebox.showerror("Error", "Failed to decrypt existing entries. Password not changed.")
                return

            # توليد ملح ومفتاح جديدين وإعادة تشفير كل شيء
            new_salt = os.urandom(16)
            new_key = self._generate_key(new_mp, new_salt)
            new_cipher = Fernet(new_key)

            for entry_id, user_plain, pass_plain in decrypted_entries:
                new_enc_user = new_cipher.encrypt(user_plain.encode()).decode('utf-8')
                new_enc_pass = new_cipher.encrypt(pass_plain.encode()).decode('utf-8')
                self.cursor.execute("UPDATE vault SET username=?, password=? WHERE id=?",
                                     (new_enc_user, new_enc_pass, entry_id))

            new_verifier = new_cipher.encrypt(VERIFIER_TEXT.encode()).decode('utf-8')
            new_salt_b64 = base64.b64encode(new_salt).decode('utf-8')
            self.cursor.execute("UPDATE metadata SET salt=?, verifier=? WHERE id=1",
                                 (new_salt_b64, new_verifier))
            self.conn.commit()

            self.key = new_key
            win.destroy()
            messagebox.showinfo("Success", "Master password changed successfully.")

        ctk.CTkButton(win, text="Change Password", fg_color=BRAND_COLOR, hover_color=BRAND_HOVER,
                      font=("Arial", 14, "bold"), command=apply_change).pack(pady=20)
        ctk.CTkButton(win, text="Cancel", fg_color="transparent", border_width=1, border_color=BRAND_COLOR,
                      text_color=BRAND_COLOR, hover_color="#e0e0e0", command=win.destroy).pack(pady=5)


if __name__ == "__main__":
    app_root = ctk.CTk()
    app = EgyxosManager(app_root)
    app_root.mainloop()