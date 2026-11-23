import os
import sys
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# Set up Django environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

try:
    import django
    django.setup()
    from tracker.models import Record, OperationalMetric, local_owner
except Exception as e:
    messagebox.showerror("Initialization Error", f"Failed to initialize Django environment:\n{e}")
    sys.exit(1)


class DailyTrackerPopup(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Daily Progress & Performance Tracker - Trainer Input")
        self.geometry("640x760")
        self.minsize(550, 600)
        
        # Center the window on screen
        self.update_idletasks()
        width = 640
        height = 760
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2) - 30
        self.geometry(f"{width}x{height}+{x}+{max(10, y)}")

        # Bring window to front
        self.attributes('-topmost', True)
        self.after(500, lambda: self.attributes('-topmost', False))

        self.setup_ui()

    def setup_ui(self):
        # Configure style
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TLabel', font=('Segoe UI', 9))
        style.configure('Header.TLabel', font=('Segoe UI', 14, 'bold'), foreground='#1e3a8a')
        style.configure('Subheader.TLabel', font=('Segoe UI', 9), foreground='#475569')
        style.configure('Section.TLabelframe.Label', font=('Segoe UI', 10, 'bold'), foreground='#1e293b')
        style.configure('Primary.TButton', font=('Segoe UI', 10, 'bold'), background='#2563eb', foreground='#ffffff')
        style.map('Primary.TButton', background=[('active', '#1d4ed8')])

        # Header Frame
        header_frame = tk.Frame(self, bg='#f1f5f9', padx=16, pady=12)
        header_frame.pack(fill='x')

        ttk.Label(header_frame, text="Daily Trainer Update", style='Header.TLabel', background='#f1f5f9').pack(anchor='w')
        ttk.Label(
            header_frame,
            text="Record your sessions, completed work, evaluations, and metrics directly into the tracker.",
            style='Subheader.TLabel',
            background='#f1f5f9'
        ).pack(anchor='w', pady=(2, 0))

        # Main Scrollable Area
        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding=(16, 12, 16, 12))

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)

        # Mouse wheel support
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.bind_all("<MouseWheel>", on_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(xscrollcommand=None, yscrollcommand=scrollbar.set)

        # Date Row
        date_frame = ttk.Frame(scrollable_frame)
        date_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(date_frame, text="Date (YYYY-MM-DD):", font=('Segoe UI', 9, 'bold')).pack(side='left', padx=(0, 8))
        self.date_var = tk.StringVar(value=datetime.date.today().isoformat())
        self.date_entry = ttk.Entry(date_frame, textvariable=self.date_var, width=15)
        self.date_entry.pack(side='left')

        # -------------------------------------------------------------------------
        # Section 1: Sessions & Batches Conducted
        # -------------------------------------------------------------------------
        sec1 = ttk.LabelFrame(scrollable_frame, text=" 🎓 1. Sessions / Batches Conducted ", style='Section.TLabelframe', padding=10)
        sec1.pack(fill='x', pady=6)

        ttk.Label(sec1, text="Batch Name & Timing (e.g., Batch Python 10:00 - 12:00):").pack(anchor='w')
        self.batch_title_var = tk.StringVar()
        ttk.Entry(sec1, textvariable=self.batch_title_var).pack(fill='x', pady=(2, 6))

        batch_sub = ttk.Frame(sec1)
        batch_sub.pack(fill='x')
        ttk.Label(batch_sub, text="Duration (Hours):").pack(side='left', padx=(0, 6))
        self.batch_hours_var = tk.StringVar()
        ttk.Entry(batch_sub, textvariable=self.batch_hours_var, width=10).pack(side='left')

        ttk.Label(sec1, text="Topics Covered & Tasks / Homework Assigned:").pack(anchor='w', pady=(6, 2))
        self.batch_notes_text = tk.Text(sec1, height=3, font=('Segoe UI', 9), wrap='word')
        self.batch_notes_text.pack(fill='x', pady=(0, 2))

        # -------------------------------------------------------------------------
        # Section 2: Tasks & Work Completed
        # -------------------------------------------------------------------------
        sec2 = ttk.LabelFrame(scrollable_frame, text=" 📌 2. Tasks & Work Completed ", style='Section.TLabelframe', padding=10)
        sec2.pack(fill='x', pady=6)

        ttk.Label(sec2, text="Task Summary / Title:").pack(anchor='w')
        self.task_title_var = tk.StringVar()
        ttk.Entry(sec2, textvariable=self.task_title_var).pack(fill='x', pady=(2, 6))

        task_sub = ttk.Frame(sec2)
        task_sub.pack(fill='x')
        ttk.Label(task_sub, text="Hours Spent:").pack(side='left', padx=(0, 6))
        self.task_hours_var = tk.StringVar()
        ttk.Entry(task_sub, textvariable=self.task_hours_var, width=10).pack(side='left')

        ttk.Label(sec2, text="Details / Progress Notes:").pack(anchor='w', pady=(6, 2))
        self.task_notes_text = tk.Text(sec2, height=3, font=('Segoe UI', 9), wrap='word')
        self.task_notes_text.pack(fill='x', pady=(0, 2))

        # -------------------------------------------------------------------------
        # Section 3: Evaluations & Mock Interviews
        # -------------------------------------------------------------------------
        sec3 = ttk.LabelFrame(scrollable_frame, text=" 📊 3. Project Evaluations & Mock Interviews ", style='Section.TLabelframe', padding=10)
        sec3.pack(fill='x', pady=6)

        counts_frame = ttk.Frame(sec3)
        counts_frame.pack(fill='x', pady=(0, 6))

        ttk.Label(counts_frame, text="Project Evals Conducted:").grid(row=0, column=0, sticky='w', padx=(0, 6), pady=2)
        self.proj_eval_count_var = tk.IntVar(value=0)
        ttk.Spinbox(counts_frame, from_=0, to=100, textvariable=self.proj_eval_count_var, width=8).grid(row=0, column=1, sticky='w', padx=(0, 20), pady=2)

        ttk.Label(counts_frame, text="Mock Interviews Conducted:").grid(row=0, column=2, sticky='w', padx=(0, 6), pady=2)
        self.mock_int_count_var = tk.IntVar(value=0)
        ttk.Spinbox(counts_frame, from_=0, to=100, textvariable=self.mock_int_count_var, width=8).grid(row=0, column=3, sticky='w', pady=2)

        ttk.Label(sec3, text="Evaluation / Mock Interview Highlights & Student Feedback:").pack(anchor='w', pady=(4, 2))
        self.eval_notes_text = tk.Text(sec3, height=3, font=('Segoe UI', 9), wrap='word')
        self.eval_notes_text.pack(fill='x', pady=(0, 2))

        # -------------------------------------------------------------------------
        # Section 4: Operational Metric Changes
        # -------------------------------------------------------------------------
        sec4 = ttk.LabelFrame(scrollable_frame, text=" 📈 4. Operational Metric Changes ", style='Section.TLabelframe', padding=10)
        sec4.pack(fill='x', pady=6)

        ops_grid = ttk.Frame(sec4)
        ops_grid.pack(fill='x', pady=(0, 6))

        ttk.Label(ops_grid, text="Support / Admission Enquiries:").grid(row=0, column=0, sticky='w', padx=(0, 6), pady=2)
        self.support_count_var = tk.IntVar(value=0)
        ttk.Spinbox(ops_grid, from_=0, to=100, textvariable=self.support_count_var, width=8).grid(row=0, column=1, sticky='w', padx=(0, 20), pady=2)

        ttk.Label(ops_grid, text="Syllabus Updates:").grid(row=0, column=2, sticky='w', padx=(0, 6), pady=2)
        self.syllabus_count_var = tk.IntVar(value=0)
        ttk.Spinbox(ops_grid, from_=0, to=100, textvariable=self.syllabus_count_var, width=8).grid(row=0, column=3, sticky='w', pady=2)

        ttk.Label(ops_grid, text="Placements Supported:").grid(row=1, column=0, sticky='w', padx=(0, 6), pady=4)
        self.placement_count_var = tk.IntVar(value=0)
        ttk.Spinbox(ops_grid, from_=0, to=100, textvariable=self.placement_count_var, width=8).grid(row=1, column=1, sticky='w', padx=(0, 20), pady=4)

        ttk.Label(sec4, text="Operational Highlights / Metric Notes:").pack(anchor='w', pady=(4, 2))
        self.ops_notes_var = tk.StringVar()
        ttk.Entry(sec4, textvariable=self.ops_notes_var).pack(fill='x', pady=(0, 2))

        # -------------------------------------------------------------------------
        # Action Buttons
        # -------------------------------------------------------------------------
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(fill='x', pady=16)

        submit_btn = ttk.Button(btn_frame, text="💾 Save & Record to Tracker", style='Primary.TButton', command=self.save_data)
        submit_btn.pack(side='right', padx=(8, 0))

        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.destroy)
        cancel_btn.pack(side='right')

    def parse_hours(self, val_str):
        if not val_str or not val_str.strip():
            return None
        try:
            return round(float(val_str.strip()), 2)
        except ValueError:
            return None

    def save_data(self):
        # Validate date
        date_str = self.date_var.get().strip()
        try:
            record_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            messagebox.showerror("Validation Error", f"Invalid date format '{date_str}'. Please use YYYY-MM-DD.")
            return

        added_records = []
        owner = local_owner()
        metric = OperationalMetric.get_for(owner)
        metric_updated = False

        # 1. Batch / Session
        batch_title = self.batch_title_var.get().strip()
        batch_notes = self.batch_notes_text.get("1.0", tk.END).strip()
        batch_hours = self.parse_hours(self.batch_hours_var.get())
        if batch_title:
            rec = Record.objects.create(
                user=owner,
                date=record_date,
                category='Batch',
                title=batch_title,
                notes=batch_notes,
                hours=batch_hours
            )
            added_records.append(f"🎓 Batch: {rec.title}")

        # 2. Task
        task_title = self.task_title_var.get().strip()
        task_notes = self.task_notes_text.get("1.0", tk.END).strip()
        task_hours = self.parse_hours(self.task_hours_var.get())
        if task_title:
            rec = Record.objects.create(
                user=owner,
                date=record_date,
                category='Task',
                title=task_title,
                notes=task_notes,
                hours=task_hours
            )
            added_records.append(f"📌 Task: {rec.title}")

        # 3. Project Evaluations & Mock Interviews
        proj_evals = self.proj_eval_count_var.get()
        mock_ints = self.mock_int_count_var.get()
        eval_notes = self.eval_notes_text.get("1.0", tk.END).strip()

        if proj_evals > 0 or (eval_notes and "eval" in eval_notes.lower()):
            title = f"Conducted {proj_evals} Project Evaluation(s)" if proj_evals > 0 else "Project Evaluation Activity"
            rec = Record.objects.create(
                user=owner,
                date=record_date,
                category='ProjectEval',
                title=title,
                notes=eval_notes,
                hours=None
            )
            if proj_evals > 0:
                metric.project_evaluations += proj_evals
                metric_updated = True
            added_records.append(f"📊 Project Evals: {proj_evals}")

        if mock_ints > 0 or (eval_notes and "mock" in eval_notes.lower()):
            title = f"Conducted {mock_ints} Mock Interview(s)" if mock_ints > 0 else "Mock Interview Session"
            rec = Record.objects.create(
                user=owner,
                date=record_date,
                category='MockInterview',
                title=title,
                notes=eval_notes,
                hours=None
            )
            if mock_ints > 0:
                metric.mock_interviews += mock_ints
                metric_updated = True
            added_records.append(f"🎙️ Mock Interviews: {mock_ints}")

        # 4. Operational Metrics
        support_cnt = self.support_count_var.get()
        if support_cnt > 0:
            metric.support_enquiries += support_cnt
            metric_updated = True
            added_records.append(f"💼 Support Enquiries: +{support_cnt}")

        syllabus_cnt = self.syllabus_count_var.get()
        if syllabus_cnt > 0:
            metric.syllabus_updates += syllabus_cnt
            metric_updated = True
            added_records.append(f"📚 Syllabus Updates: +{syllabus_cnt}")

        placement_cnt = self.placement_count_var.get()
        if placement_cnt > 0:
            metric.placements_supported += placement_cnt
            metric_updated = True
            added_records.append(f"🎯 Placements Supported: +{placement_cnt}")

        ops_notes = self.ops_notes_var.get().strip()
        if ops_notes:
            metric.notes = (metric.notes + "\n" + ops_notes).strip() if metric.notes else ops_notes
            metric_updated = True

        if metric_updated:
            metric.save()

        if not added_records and not metric_updated:
            messagebox.showwarning("No Data Entered", "Please fill in at least one field before saving.")
            return

        summary = "\n".join(added_records)
        messagebox.showinfo(
            "Success",
            f"Successfully saved to Daily Tracker database!\n\nRecorded Items:\n{summary}"
        )
        self.destroy()


if __name__ == '__main__':
    app = DailyTrackerPopup()
    app.mainloop()
