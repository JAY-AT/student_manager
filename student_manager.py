"""
╔══════════════════════════════════════════════════════════╗
║       STUDENT MANAGEMENT SYSTEM — Python + XAMPP         ║
║  Requires: pip install mysql-connector-python            ║
║  Make sure XAMPP MySQL is running before launching!      ║
╚══════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# ── Database Configuration ─────────────────────────────────
DB_HOST     = "localhost"
DB_USER     = "root"
DB_PASSWORD = ""          # Default XAMPP = empty password
DB_NAME     = "student_management"

# ── Color Palette ──────────────────────────────────────────
C = {
    "bg":       "#0d0f14",
    "surface":  "#161920",
    "surface2": "#1e2230",
    "border":   "#2a2f42",
    "accent":   "#5b6ef8",
    "accent2":  "#f85b8a",
    "green":    "#5bf8a8",
    "text":     "#e8eaf6",
    "muted":    "#7a82a8",
    "danger":   "#f85b6e",
    "warn":     "#f8c45b",
    "white":    "#ffffff",
}

# ══════════════════════════════════════════════════════════
#  DATABASE LAYER
# ══════════════════════════════════════════════════════════
class Database:
    def __init__(self):
        self.conn = None
        self.connected = False
        self.connect()

    def connect(self):
        """
        Step 1: Connect WITHOUT specifying database (so we can CREATE it if missing)
        Step 2: Create DB + table
        Step 3: Reconnect WITH the database selected
        """
        try:
            # Step 1 — connect to MySQL server only (no db yet)
            tmp = mysql.connector.connect(
                host=DB_HOST, user=DB_USER, password=DB_PASSWORD
            )
            cursor = tmp.cursor()

            # Step 2 — create database & table
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
            cursor.execute(f"USE `{DB_NAME}`")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id           INT AUTO_INCREMENT PRIMARY KEY,
                    student_id   VARCHAR(20)  NOT NULL UNIQUE,
                    full_name    VARCHAR(100) NOT NULL,
                    email        VARCHAR(100),
                    phone_number VARCHAR(20),
                    gender       VARCHAR(10),
                    course       VARCHAR(100),
                    year_level   INT DEFAULT 1,
                    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Add columns if table already exists (for existing users upgrading)
            for col_sql in [
                "ALTER TABLE students ADD COLUMN phone_number VARCHAR(20) AFTER email",
                "ALTER TABLE students ADD COLUMN gender VARCHAR(10) AFTER phone_number",
            ]:
                try:
                    cursor.execute(col_sql)
                except:
                    pass  # Column already exists, skip
            tmp.commit()
            cursor.close()
            tmp.close()

            # Step 3 — reconnect with database selected
            self.conn = mysql.connector.connect(
                host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
            )
            self.connected = self.conn.is_connected()

        except Error as e:
            self.connected = False
            messagebox.showerror(
                "❌ MySQL Connection Failed",
                f"Hindi makaconnect sa MySQL!\n\n"
                f"Siguraduhing:\n"
                f"  • Bukas ang XAMPP Control Panel\n"
                f"  • Naka-START ang MySQL (green na)\n"
                f"  • Port 3306 hindi blocked\n\n"
                f"Error details:\n{e}"
            )

    def is_ok(self):
        """Check if connection is alive, reconnect if dropped."""
        try:
            if self.conn and self.conn.is_connected():
                return True
            self.connect()
            return self.connected
        except:
            return False

    def insert(self, student_id, full_name, email, phone_number, gender, course, year_level):
        if not self.is_ok():
            return False, "No database connection. Check XAMPP MySQL."
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO students (student_id, full_name, email, phone_number, gender, course, year_level) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (student_id, full_name, email, phone_number, gender, course, year_level)
            )
            self.conn.commit()
            inserted_id = cursor.lastrowid
            cursor.close()
            return True, f"Student saved to database! (ID #{inserted_id})"
        except Error as e:
            if e.errno == 1062:
                return False, f"Student ID '{student_id}' already exists."
            return False, f"DB Error: {str(e)}"

    def update(self, record_id, student_id, full_name, email, phone_number, gender, course, year_level):
        if not self.is_ok():
            return False, "No database connection. Check XAMPP MySQL."
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE students SET student_id=%s, full_name=%s, email=%s, "
                "phone_number=%s, gender=%s, course=%s, year_level=%s WHERE id=%s",
                (student_id, full_name, email, phone_number, gender, course, year_level, record_id)
            )
            self.conn.commit()
            cursor.close()
            return True, f"Student updated successfully!"
        except Error as e:
            if e.errno == 1062:
                return False, f"Student ID '{student_id}' already exists."
            return False, f"DB Error: {str(e)}"

    def delete(self, record_id):
        if not self.is_ok():
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM students WHERE id = %s", (record_id,))
            self.conn.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
        except Error as e:
            messagebox.showerror("Delete Error", str(e))
            return False

    def fetch_all(self, search=""):
        if not self.is_ok():
            return []
        try:
            cursor = self.conn.cursor()
            if search:
                q = f"%{search}%"
                cursor.execute(
                    "SELECT id, student_id, full_name, email, phone_number, gender, course, year_level, created_at "
                    "FROM students WHERE full_name LIKE %s OR student_id LIKE %s OR course LIKE %s "
                    "ORDER BY id DESC",
                    (q, q, q)
                )
            else:
                cursor.execute(
                    "SELECT id, student_id, full_name, email, phone_number, gender, course, year_level, created_at "
                    "FROM students ORDER BY id DESC"
                )
            rows = cursor.fetchall()
            cursor.close()
            return rows
        except Error as e:
            messagebox.showerror("Fetch Error", str(e))
            return []

    def count(self):
        if not self.is_ok():
            return (0, 0, 0)
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*), COUNT(DISTINCT course), COUNT(DISTINCT year_level) FROM students")
            row = cursor.fetchone()
            cursor.close()
            return row if row else (0, 0, 0)
        except:
            return (0, 0, 0)


# ══════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════
class StudentApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.db = Database()

        self.title("StudentDB — Management System")
        self.geometry("1280x750")
        self.minsize(1000, 650)
        self.configure(bg=C["bg"])
        self.resizable(True, True)

        # Try to set a nice icon
        try:
            self.iconbitmap(default="")
        except:
            pass

        self._setup_styles()
        self._build_ui()
        self.refresh_table()

    # ── Styles ─────────────────────────────────────────────
    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # Treeview
        style.configure("Custom.Treeview",
            background=C["surface"],
            foreground=C["text"],
            fieldbackground=C["surface"],
            rowheight=38,
            font=("Courier New", 10),
            borderwidth=0,
        )
        style.configure("Custom.Treeview.Heading",
            background=C["surface2"],
            foreground=C["muted"],
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            borderwidth=0,
        )
        style.map("Custom.Treeview",
            background=[("selected", C["accent"])],
            foreground=[("selected", C["white"])],
        )
        style.map("Custom.Treeview.Heading",
            background=[("active", C["border"])],
        )

        # Scrollbar
        style.configure("Dark.Vertical.TScrollbar",
            background=C["surface2"],
            troughcolor=C["surface"],
            borderwidth=0,
            arrowcolor=C["muted"],
        )

    # ── UI Construction ────────────────────────────────────
    def _build_ui(self):
        # ─ Header
        header = tk.Frame(self, bg=C["surface"], height=60)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        tk.Label(header, text="Student", fg=C["text"], bg=C["surface"],
                 font=("Segoe UI", 18, "bold")).pack(side="left", padx=(20, 0), pady=10)
        tk.Label(header, text="DB", fg=C["accent"], bg=C["surface"],
                 font=("Segoe UI", 18, "bold")).pack(side="left", pady=10)
        tk.Label(header, text="Management System", fg=C["muted"], bg=C["surface"],
                 font=("Segoe UI", 11)).pack(side="left", padx=(10, 0), pady=14)

        self.count_label = tk.Label(header, text="", fg=C["white"], bg=C["accent"],
                                     font=("Courier New", 10, "bold"), padx=12, pady=4)
        self.count_label.pack(side="right", padx=(8, 20), pady=14)

        reconnect_btn = tk.Button(header, text="🔄 Reconnect", bg=C["surface2"],
                                   fg=C["muted"], relief="flat", font=("Segoe UI", 8),
                                   cursor="hand2", activebackground=C["border"],
                                   activeforeground=C["text"], command=self._reconnect_db)
        reconnect_btn.pack(side="right", pady=14, ipadx=6, ipady=3)

        self.db_status_label = tk.Label(header, text="", bg=C["surface"],
                                         font=("Segoe UI", 9, "bold"), padx=8)
        self.db_status_label.pack(side="right", pady=14)
        self._update_db_status()

        # ─ Separator
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")

        # ─ Stats Bar
        self.stats_frame = tk.Frame(self, bg=C["bg"], pady=10)
        self.stats_frame.pack(fill="x", padx=20)
        self._build_stats()

        # ─ Main Body (Left form + Right table)
        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self._build_form(body)
        self._build_table(body)

    def _build_stats(self):
        for w in self.stats_frame.winfo_children():
            w.destroy()
        total, courses, years = self.db.count()
        stats = [
            ("Total Students", total, C["accent"]),
            ("Courses",        courses, C["green"]),
            ("Year Levels",    years,  C["warn"]),
        ]
        for label, val, color in stats:
            card = tk.Frame(self.stats_frame, bg=C["surface"], padx=20, pady=10,
                            highlightbackground=C["border"], highlightthickness=1)
            card.pack(side="left", padx=(0, 12))
            tk.Label(card, text=str(val), fg=color, bg=C["surface"],
                     font=("Segoe UI", 22, "bold")).pack(anchor="w")
            tk.Label(card, text=label, fg=C["muted"], bg=C["surface"],
                     font=("Segoe UI", 8)).pack(anchor="w")

    # ── Left Panel: Add Form ───────────────────────────────
    def _build_form(self, parent):
        panel = tk.Frame(parent, bg=C["surface"], width=320,
                         highlightbackground=C["border"], highlightthickness=1)
        panel.pack(side="left", fill="y", padx=(0, 15), pady=(10, 0))
        panel.pack_propagate(False)

        # Title
        hdr = tk.Frame(panel, bg=C["surface2"], pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="➕  Add New Student", fg=C["text"], bg=C["surface2"],
                 font=("Segoe UI", 11, "bold"), padx=16).pack(anchor="w")

        # Form fields
        form = tk.Frame(panel, bg=C["surface"], padx=18, pady=10)
        form.pack(fill="both", expand=True)

        self.fields = {}
        field_defs = [
            ("student_id",  "Student ID *",    "e.g. STU-2024-001"),
            ("full_name",   "Full Name *",      "e.g. Maria Santos"),
            ("email",       "Email Address",    "student@email.com"),
            ("phone_number","Phone Number",     "e.g. 09171234567"),
            ("course",      "Course",           "e.g. Computer Science"),
        ]

        for key, label, placeholder in field_defs:
            tk.Label(form, text=label, fg=C["muted"], bg=C["surface"],
                     font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(8, 2))
            entry = tk.Entry(form, bg=C["surface2"], fg=C["text"], insertbackground=C["text"],
                             relief="flat", font=("Courier New", 10), bd=0,
                             highlightbackground=C["border"], highlightthickness=1,
                             highlightcolor=C["accent"])
            entry.pack(fill="x", ipady=7)
            entry.insert(0, placeholder)
            entry.config(fg=C["muted"])
            entry.bind("<FocusIn>",  lambda e, en=entry, ph=placeholder: self._on_focus_in(e, en, ph))
            entry.bind("<FocusOut>", lambda e, en=entry, ph=placeholder: self._on_focus_out(e, en, ph))
            self.fields[key] = entry

        # Gender dropdown
        tk.Label(form, text="Gender", fg=C["muted"], bg=C["surface"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(8, 2))
        self.gender_var = tk.StringVar(value="Male")
        gender_menu = tk.OptionMenu(form, self.gender_var, "Male", "Female", "Other", "Prefer not to say")
        gender_menu.config(bg=C["surface2"], fg=C["text"], activebackground=C["accent"],
                           activeforeground=C["white"], relief="flat", font=("Segoe UI", 10),
                           highlightthickness=0, bd=0, cursor="hand2")
        gender_menu["menu"].config(bg=C["surface2"], fg=C["text"], activebackground=C["accent"],
                                    activeforeground=C["white"])
        gender_menu.pack(fill="x", ipady=4)

        # Year Level dropdown
        tk.Label(form, text="Year Level", fg=C["muted"], bg=C["surface"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(8, 2))
        self.year_var = tk.StringVar(value="1st Year")
        year_menu = tk.OptionMenu(form, self.year_var,
                                  "1st Year", "2nd Year", "3rd Year", "4th Year")
        year_menu.config(bg=C["surface2"], fg=C["text"], activebackground=C["accent"],
                         activeforeground=C["white"], relief="flat", font=("Segoe UI", 10),
                         highlightthickness=0, bd=0, cursor="hand2")
        year_menu["menu"].config(bg=C["surface2"], fg=C["text"], activebackground=C["accent"],
                                  activeforeground=C["white"])
        year_menu.pack(fill="x", ipady=4)

        # Buttons
        btn_frame = tk.Frame(form, bg=C["surface"])
        btn_frame.pack(fill="x", pady=(20, 0))

        add_btn = tk.Button(btn_frame, text="➕  Add Student", bg=C["accent"], fg=C["white"],
                            relief="flat", font=("Segoe UI", 10, "bold"), cursor="hand2",
                            activebackground="#4a5ce8", activeforeground=C["white"],
                            command=self.add_student)
        add_btn.pack(fill="x", ipady=8)

        clear_btn = tk.Button(btn_frame, text="↺  Clear Fields", bg=C["surface2"], fg=C["muted"],
                              relief="flat", font=("Segoe UI", 9), cursor="hand2",
                              activebackground=C["border"], activeforeground=C["text"],
                              command=self.clear_fields)
        clear_btn.pack(fill="x", ipady=5, pady=(8, 0))

        # Status message
        self.status_var = tk.StringVar()
        self.status_label = tk.Label(form, textvariable=self.status_var, bg=C["surface"],
                                      font=("Segoe UI", 9), wraplength=260, justify="left")
        self.status_label.pack(fill="x", pady=(12, 0))

    def _on_focus_in(self, event, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, "end")
            entry.config(fg=C["text"])

    def _on_focus_out(self, event, entry, placeholder):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg=C["muted"])

    # ── Right Panel: Table ─────────────────────────────────
    def _build_table(self, parent):
        panel = tk.Frame(parent, bg=C["surface"],
                         highlightbackground=C["border"], highlightthickness=1)
        panel.pack(side="left", fill="both", expand=True, pady=(10, 0))

        # Table header row
        top = tk.Frame(panel, bg=C["surface2"], pady=10, padx=15)
        top.pack(fill="x")

        tk.Label(top, text="📋  Student Records", fg=C["text"], bg=C["surface2"],
                 font=("Segoe UI", 11, "bold")).pack(side="left")

        # Search
        search_frame = tk.Frame(top, bg=C["surface2"])
        search_frame.pack(side="right")

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *_: self.refresh_table())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                 bg=C["surface"], fg=C["text"], insertbackground=C["text"],
                                 relief="flat", font=("Courier New", 10), width=22,
                                 highlightbackground=C["border"], highlightthickness=1,
                                 highlightcolor=C["accent"])
        search_entry.pack(side="left", ipady=5, padx=(0, 6))

        tk.Label(search_frame, text="🔍", fg=C["muted"], bg=C["surface2"],
                 font=("Segoe UI", 12)).pack(side="left")

        tk.Frame(panel, bg=C["border"], height=1).pack(fill="x")

        # Treeview
        cols = ("student_id", "full_name", "gender", "phone", "email", "course", "year", "added")
        self.tree = ttk.Treeview(panel, columns=cols, show="headings",
                                  style="Custom.Treeview", selectmode="browse")

        col_cfg = {
            "student_id": ("Student ID",   110, "center"),
            "full_name":  ("Full Name",     150, "w"),
            "gender":     ("Gender",         80, "center"),
            "phone":      ("Phone",         120, "center"),
            "email":      ("Email",         150, "w"),
            "course":     ("Course",        130, "w"),
            "year":       ("Year",           55, "center"),
            "added":      ("Date Added",    105, "center"),
        }
        for col, (heading, width, anchor) in col_cfg.items():
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor=anchor, minwidth=50)

        # Alternating row tags
        self.tree.tag_configure("odd",  background=C["surface"])
        self.tree.tag_configure("even", background="#191c28")

        # Scrollbar
        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=self.tree.yview,
                                   style="Dark.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Delete button row
        bottom = tk.Frame(panel, bg=C["surface2"], pady=10, padx=15)
        bottom.pack(fill="x", side="bottom")

        self.result_label = tk.Label(bottom, text="", fg=C["muted"], bg=C["surface2"],
                                      font=("Courier New", 9))
        self.result_label.pack(side="left")

        del_btn = tk.Button(bottom, text="🗑️  Delete Selected", bg=C["surface"],
                             fg=C["danger"], relief="flat", font=("Segoe UI", 9, "bold"),
                             cursor="hand2", activebackground=C["danger"],
                             activeforeground=C["white"], bd=0,
                             highlightbackground=C["danger"], highlightthickness=1,
                             command=self.delete_student)
        del_btn.pack(side="right", ipadx=10, ipady=5)

        edit_btn = tk.Button(bottom, text="✏️  Edit Selected", bg=C["surface"],
                              fg=C["warn"], relief="flat", font=("Segoe UI", 9, "bold"),
                              cursor="hand2", activebackground=C["warn"],
                              activeforeground=C["bg"], bd=0,
                              highlightbackground=C["warn"], highlightthickness=1,
                              command=self.edit_student)
        edit_btn.pack(side="right", ipadx=10, ipady=5, padx=(0, 10))

        # Double-click to edit
        self.tree.bind("<Double-1>", lambda e: self.edit_student())

    # ── DB Status Helpers ──────────────────────────────────
    def _update_db_status(self):
        if self.db.connected and self.db.is_ok():
            self.db_status_label.config(
                text="● MySQL Connected",
                fg=C["green"]
            )
        else:
            self.db_status_label.config(
                text="● MySQL Disconnected",
                fg=C["danger"]
            )

    def _reconnect_db(self):
        self.db.connect()
        self._update_db_status()
        if self.db.connected:
            self.refresh_table()
            messagebox.showinfo("Connected!", "✅ Successfully connected to MySQL!\n\nDatabase: student_management")
        else:
            messagebox.showerror("Failed", "❌ Still cannot connect.\n\nMake sure MySQL is running in XAMPP.")

    # ── Actions ────────────────────────────────────────────
    def add_student(self):
        placeholders = {
            "student_id":   "e.g. STU-2024-001",
            "full_name":    "e.g. Maria Santos",
            "email":        "student@email.com",
            "phone_number": "e.g. 09171234567",
            "course":       "e.g. Computer Science",
        }
        vals = {}
        for key, entry in self.fields.items():
            val = entry.get().strip()
            if val == placeholders[key]:
                val = ""
            vals[key] = val

        if not vals["student_id"] or not vals["full_name"]:
            self._set_status("⚠️ Student ID and Full Name are required.", C["warn"])
            return

        year_map = {"1st Year": 1, "2nd Year": 2, "3rd Year": 3, "4th Year": 4}
        year   = year_map.get(self.year_var.get(), 1)
        gender = self.gender_var.get()

        ok, msg = self.db.insert(vals["student_id"], vals["full_name"],
                                  vals["email"], vals["phone_number"],
                                  gender, vals["course"], year)
        if ok:
            self._set_status(f"✅ {msg}", C["green"])
            self.clear_fields()
            self.refresh_table()
            self._update_db_status()
        else:
            self._set_status(f"❌ {msg}", C["danger"])

    def edit_student(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Walang Napili", "I-click muna ang isang row para i-edit.")
            return

        item      = self.tree.item(selected[0])
        record_id = item["tags"][0]
        vals      = item["values"]
        # vals: (student_id, full_name, gender, phone, email, course, year_str, date)

        current = {
            "record_id":    record_id,
            "student_id":   vals[0],
            "full_name":    vals[1],
            "gender":       vals[2] if vals[2] != "—" else "Male",
            "phone_number": vals[3] if vals[3] != "—" else "",
            "email":        vals[4] if vals[4] != "—" else "",
            "course":       vals[5] if vals[5] != "—" else "",
            "year_level":   vals[6],
        }

        EditDialog(self, self.db, current, on_save=self._on_edit_saved)

    def _on_edit_saved(self, msg):
        self.refresh_table()
        self._set_status(f"✅ {msg}", C["green"])

    def delete_student(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please click a row to select a student first.")
            return

        item = self.tree.item(selected[0])
        name = item["values"][1]
        record_id = item["tags"][0]  # stored as first tag

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete:\n\n  {name}\n\nThis cannot be undone.",
            icon="warning"
        )
        if confirm:
            if self.db.delete(record_id):
                self.refresh_table()
                self._set_status(f"🗑️ '{name}' deleted.", C["muted"])

    def clear_fields(self):
        placeholders = {
            "student_id":   "e.g. STU-2024-001",
            "full_name":    "e.g. Maria Santos",
            "email":        "student@email.com",
            "phone_number": "e.g. 09171234567",
            "course":       "e.g. Computer Science",
        }
        for key, entry in self.fields.items():
            entry.delete(0, "end")
            entry.insert(0, placeholders[key])
            entry.config(fg=C["muted"])
        self.year_var.set("1st Year")
        self.gender_var.set("Male")

    def refresh_table(self):
        # Clear
        for item in self.tree.get_children():
            self.tree.delete(item)

        search = self.search_var.get().strip() if hasattr(self, "search_var") else ""
        rows = self.db.fetch_all(search)

        for i, row in enumerate(rows):
            db_id, sid, name, email, phone, gender, course, year, created = row
            date_str  = created.strftime("%b %d, %Y") if created else ""
            year_str  = f"{year}{'st' if year==1 else 'nd' if year==2 else 'rd' if year==3 else 'th'}"
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end",
                values=(sid, name, gender or "—", phone or "—",
                        email or "—", course or "—", year_str, date_str),
                tags=(str(db_id), tag)
            )

        count = len(rows)
        total, _, _ = self.db.count()
        self.count_label.config(text=f"  {total} Records  ")
        self.result_label.config(
            text=f"Showing {count} of {total} students" if search else f"{count} students total"
        )
        self._build_stats()

    def _set_status(self, msg, color):
        self.status_var.set(msg)
        self.status_label.config(fg=color)
        self.after(4000, lambda: self.status_var.set(""))


# ══════════════════════════════════════════════════════════
#  EDIT DIALOG — Popup window para mag-edit ng student info
# ══════════════════════════════════════════════════════════
class EditDialog(tk.Toplevel):
    def __init__(self, parent, db, current, on_save):
        super().__init__(parent)
        self.db        = db
        self.current   = current
        self.on_save   = on_save

        self.title("✏️  Edit Student")
        self.geometry("460x740")
        self.minsize(460, 740)
        self.resizable(False, False)
        self.configure(bg=C["bg"])
        self.grab_set()
        self.focus_set()

        # Center the popup sa screen
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  // 2) - 230
        py = parent.winfo_y() + (parent.winfo_height() // 2) - 370
        self.geometry(f"+{px}+{py}")

        self._build()

    def _build(self):
        # ── Header ──
        hdr = tk.Frame(self, bg=C["surface2"], pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="✏️  Edit Student Information", fg=C["text"],
                 bg=C["surface2"], font=("Segoe UI", 12, "bold"), padx=20).pack(anchor="w")
        tk.Label(hdr, text=f"ID: {self.current['student_id']}", fg=C["muted"],
                 bg=C["surface2"], font=("Courier New", 9), padx=20).pack(anchor="w")

        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")

        # ── Buttons FIXED at bottom (pack before form so they don't get pushed off) ──
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", side="bottom")
        btn_row = tk.Frame(self, bg=C["surface2"], pady=14, padx=20)
        btn_row.pack(fill="x", side="bottom")

        save_btn = tk.Button(btn_row, text="💾  Save Changes", bg=C["accent"], fg=C["white"],
                              relief="flat", font=("Segoe UI", 11, "bold"), cursor="hand2",
                              activebackground="#4a5ce8", activeforeground=C["white"],
                              command=self._save)
        save_btn.pack(side="left", ipadx=18, ipady=9)

        cancel_btn = tk.Button(btn_row, text="✕  Cancel", bg=C["surface"], fg=C["muted"],
                                relief="flat", font=("Segoe UI", 10), cursor="hand2",
                                activebackground=C["border"], activeforeground=C["text"],
                                command=self.destroy)
        cancel_btn.pack(side="right", ipadx=18, ipady=9)

        # ── Scrollable Form area ──
        form = tk.Frame(self, bg=C["bg"], padx=24, pady=12)
        form.pack(fill="both", expand=True)

        self.edit_fields = {}
        field_defs = [
            ("student_id",   "Student ID *",   self.current["student_id"]),
            ("full_name",    "Full Name *",     self.current["full_name"]),
            ("email",        "Email Address",   self.current["email"]),
            ("phone_number", "Phone Number",    self.current["phone_number"]),
            ("course",       "Course",          self.current["course"]),
        ]

        for key, label, value in field_defs:
            tk.Label(form, text=label, fg=C["muted"], bg=C["bg"],
                     font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(8, 2))
            entry = tk.Entry(form, bg=C["surface"], fg=C["text"],
                             insertbackground=C["text"], relief="flat",
                             font=("Courier New", 10), bd=0,
                             highlightbackground=C["border"], highlightthickness=1,
                             highlightcolor=C["accent"])
            entry.pack(fill="x", ipady=8)
            entry.insert(0, value)
            self.edit_fields[key] = entry

        # Gender
        tk.Label(form, text="Gender", fg=C["muted"], bg=C["bg"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(8, 2))
        self.edit_gender = tk.StringVar(value=self.current["gender"])
        g_menu = tk.OptionMenu(form, self.edit_gender, "Male", "Female", "Other", "Prefer not to say")
        g_menu.config(bg=C["surface"], fg=C["text"], activebackground=C["accent"],
                      activeforeground=C["white"], relief="flat", font=("Segoe UI", 10),
                      highlightthickness=0, bd=0, cursor="hand2")
        g_menu["menu"].config(bg=C["surface"], fg=C["text"],
                               activebackground=C["accent"], activeforeground=C["white"])
        g_menu.pack(fill="x", ipady=4)

        # Year Level
        tk.Label(form, text="Year Level", fg=C["muted"], bg=C["bg"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(8, 2))
        year_map_r = {"1st": "1st Year", "2nd": "2nd Year", "3rd": "3rd Year", "4th": "4th Year"}
        cur_year   = year_map_r.get(self.current["year_level"][:3], "1st Year")
        self.edit_year = tk.StringVar(value=cur_year)
        y_menu = tk.OptionMenu(form, self.edit_year, "1st Year", "2nd Year", "3rd Year", "4th Year")
        y_menu.config(bg=C["surface"], fg=C["text"], activebackground=C["accent"],
                      activeforeground=C["white"], relief="flat", font=("Segoe UI", 10),
                      highlightthickness=0, bd=0, cursor="hand2")
        y_menu["menu"].config(bg=C["surface"], fg=C["text"],
                               activebackground=C["accent"], activeforeground=C["white"])
        y_menu.pack(fill="x", ipady=4)

        # Status label
        self.edit_status = tk.Label(form, text="", fg=C["warn"], bg=C["bg"],
                                     font=("Segoe UI", 9), wraplength=380)
        self.edit_status.pack(pady=(10, 0))

    def _save(self):
        vals = {k: e.get().strip() for k, e in self.edit_fields.items()}

        if not vals["student_id"] or not vals["full_name"]:
            self.edit_status.config(text="⚠️ Student ID at Full Name ay required!", fg=C["warn"])
            return

        year_map = {"1st Year": 1, "2nd Year": 2, "3rd Year": 3, "4th Year": 4}
        year   = year_map.get(self.edit_year.get(), 1)
        gender = self.edit_gender.get()

        ok, msg = self.db.update(
            self.current["record_id"],
            vals["student_id"], vals["full_name"],
            vals["email"], vals["phone_number"],
            gender, vals["course"], year
        )

        if ok:
            self.destroy()
            self.on_save(msg)
        else:
            self.edit_status.config(text=f"❌ {msg}", fg=C["danger"])


# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = StudentApp()
    app.mainloop()