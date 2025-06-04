import os
import sys
import json
import subprocess
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

CONFIG_PATH = os.path.expanduser("~/.android_health_checker_gui.json")

# Define all possible steps: (Display Name, CLI Flags, use_gradlew, gradle_task)
ALL_STEPS = [
    ("Scan XML",      ['--html-resources', 'xml_report.html'], False, None),
    ("Scan Resources",['--scan'],                          False, None),
    ("Generate Stubs",['--stubs'],                         False, None),
    ("Check Syntax",  ['--check-syntax'],                  False, None),
    ("Run Lint",      ['--lint'],                          True,  'lintDebug'),
    ("Build APK",     ['--assemble'],                      True,  'assembleDebug'),
    ("HTML Report",   ['--html-report', 'issues.html'],    False, None),
]

class HealthCheckGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Android Health Checker UI")
        self._load_config()
        self._build_ui()

    def _load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH) as f:
                    cfg = json.load(f)
            except:
                cfg = {}
        else:
            cfg = {}
        self.last_project = cfg.get("project_dir", "")
        self.last_report = cfg.get("report_file", "issues.html")
        # load saved step order or default to ALL_STEPS
        saved = cfg.get("steps_order", [s[0] for s in ALL_STEPS])
        self.steps_order = [name for name in saved if name in {s[0] for s in ALL_STEPS}]
        # ensure any missing get appended
        for s in ALL_STEPS:
            if s[0] not in self.steps_order:
                self.steps_order.append(s[0])

    def _save_config(self):
        cfg = {
            "project_dir": self.project_var.get(),
            "report_file": self.report_path_var.get(),
            "steps_order": list(self.steps_order)
        }
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)

    def _build_ui(self):
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill='both', expand=True)

        # Project dir + report path
        top = ttk.Frame(frm)
        top.pack(fill='x', pady=5)
        ttk.Label(top, text="Project Directory:").grid(row=0, column=0, sticky='w')
        self.project_var = tk.StringVar(value=self.last_project)
        ttk.Entry(top, textvariable=self.project_var, width=50).grid(row=0, column=1, sticky='we')
        ttk.Button(top, text="Browse…", command=self._browse).grid(row=0, column=2)

        ttk.Label(top, text="HTML Report File:").grid(row=1, column=0, sticky='w')
        self.report_path_var = tk.StringVar(value=self.last_report)
        ttk.Entry(top, textvariable=self.report_path_var, width=20).grid(row=1, column=1, sticky='w')

        top.columnconfigure(1, weight=1)

        # Steps list + controls
        mid = ttk.Frame(frm)
        mid.pack(fill='both', expand=True)

        list_frame = ttk.Labelframe(mid, text="Steps (in order)", padding=5)
        list_frame.pack(side='left', fill='both', expand=True, padx=(0,5))
        self.steps_box = tk.Listbox(list_frame, height=10)
        self.steps_box.pack(side='left', fill='both', expand=True)
        for name in self.steps_order:
            self.steps_box.insert('end', name)
        scrollbar = ttk.Scrollbar(list_frame, command=self.steps_box.yview)
        scrollbar.pack(side='right', fill='y')
        self.steps_box.config(yscrollcommand=scrollbar.set)

        ctrl = ttk.Frame(mid)
        ctrl.pack(side='left', fill='y')
        ttk.Button(ctrl, text="Up ▲",    command=self._move_up).pack(fill='x', pady=2)
        ttk.Button(ctrl, text="Down ▼",  command=self._move_down).pack(fill='x', pady=2)
        ttk.Button(ctrl, text="Remove ➖",command=self._remove_step).pack(fill='x', pady=2)
        # Add dropdown
        ttk.Label(ctrl, text="Add Step:").pack(pady=(10,0))
        self.add_var = tk.StringVar()
        self.add_menu = ttk.Combobox(ctrl, textvariable=self.add_var, state='readonly')
        self._refresh_add_menu()
        self.add_menu.pack(fill='x', pady=2)
        ttk.Button(ctrl, text="Add ➕", command=self._add_step).pack(fill='x', pady=2)

        # Action buttons
        bottom = ttk.Frame(frm)
        bottom.pack(fill='x', pady=5)
        self.start_btn = ttk.Button(bottom, text="Start", command=self._start)
        self.start_btn.pack(side='left', padx=5)
        self.view_btn = ttk.Button(bottom, text="View Report", command=self._on_view, state='disabled')
        self.view_btn.pack(side='left', padx=5)
        self.baseline_btn = ttk.Button(bottom, text="Create Lint Baseline", command=self._on_baseline, state='disabled')
        self.baseline_btn.pack(side='left', padx=5)

        # Console output
        self.output = tk.Text(frm, wrap='none', height=15, state='disabled')
        self.output.pack(fill='both', expand=True)
        self.output.tag_configure('success', foreground='green')
        self.output.tag_configure('error', foreground='red')
        self.output.tag_configure('info', foreground='blue')

        # auto-disable lint if no gradlew
        self._update_lint_availability()

    def _browse(self):
        d = filedialog.askdirectory(title="Select Android Project Directory")
        if d:
            self.project_var.set(d)
            self._update_lint_availability()

    def _update_lint_availability(self):
        p = self.project_var.get().strip()
        gradlew = os.path.join(p, "gradlew.bat" if os.name=='nt' else "gradlew")
        # disable Run Lint entry if missing
        names = list(self.steps_box.get(0,'end'))
        if not os.path.isfile(gradlew):
            if "Run Lint" in names:
                idx = names.index("Run Lint")
                self.steps_box.delete(idx)
                self.steps_order.remove("Run Lint")
                messagebox.showwarning("Lint Disabled", "No Gradle wrapper found; 'Run Lint' removed.")
        else:
            # ensure it's possible to add back via dropdown
            pass
        self._refresh_add_menu()

    def _refresh_add_menu(self):
        present = set(self.steps_box.get(0,'end'))
        choices = [s[0] for s in ALL_STEPS if s[0] not in present]
        self.add_menu['values'] = choices
        self.add_var.set(choices[0] if choices else "")

    def _move_up(self):
        sel = self.steps_box.curselection()
        if not sel: return
        i = sel[0]
        if i==0: return
        txt = self.steps_box.get(i)
        self.steps_box.delete(i)
        self.steps_box.insert(i-1, txt)
        self.steps_box.selection_set(i-1)
        self.steps_order = list(self.steps_box.get(0,'end'))
        self._save_config()

    def _move_down(self):
        sel = self.steps_box.curselection()
        if not sel: return
        i = sel[0]
        if i==self.steps_box.size()-1: return
        txt = self.steps_box.get(i)
        self.steps_box.delete(i)
        self.steps_box.insert(i+1, txt)
        self.steps_box.selection_set(i+1)
        self.steps_order = list(self.steps_box.get(0,'end'))
        self._save_config()

    def _remove_step(self):
        sel = self.steps_box.curselection()
        if not sel: return
        i = sel[0]
        self.steps_box.delete(i)
        self.steps_order = list(self.steps_box.get(0,'end'))
        self._refresh_add_menu()
        self._save_config()

    def _add_step(self):
        name = self.add_var.get()
        if not name: return
        self.steps_box.insert('end', name)
        self.steps_order = list(self.steps_box.get(0,'end'))
        self._refresh_add_menu()
        self._save_config()

    def _append_output(self, text, tag=None):
        self.output.configure(state='normal')
        self.output.insert('end', text, tag or 'info')
        self.output.see('end')
        self.output.configure(state='disabled')

    def _start(self):
        # disable UI
        for w in (self.start_btn, self.view_btn, self.baseline_btn):
            w.state(['disabled'])
        self.output.configure(state='normal')
        self.output.delete('1.0','end')
        self.output.configure(state='disabled')

        project_dir = self.project_var.get().strip()
        # build the step queue
        names = self.steps_box.get(0,'end')
        queue = [step for step in ALL_STEPS if step[0] in names]
        # preserve order
        queue.sort(key=lambda x: names.index(x[0]))

        threading.Thread(target=self._run_queue, args=(project_dir, queue), daemon=True).start()

    def _run_queue(self, project_dir, queue):
        results = []
        for name, flags, use_gradlew, task in queue:
            self._append_output(f"\n=== {name} ===\n", 'info')
            if use_gradlew:
                gradlew = "gradlew.bat" if os.name=='nt' else "./gradlew"
                cmd = [os.path.join(project_dir, gradlew), task]
                proc = subprocess.Popen(cmd, cwd=project_dir,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            else:
                cmd = [sys.executable,
                       os.path.join(os.path.dirname(__file__), "android_health_check.py"),
                       "--project-dir", project_dir] + flags
                proc = subprocess.Popen(cmd, cwd=project_dir,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            # stream output
            out_buf = ""
            for line in proc.stdout:
                out_buf += line
                tag = 'error' if 'FAILURE' in line or 'Error' in line else 'success'
                self._append_output(line, tag)
            ret = proc.wait()
            ok = (ret == 0)
            results.append((name, ok, out_buf))

            # if lint failed, enable baseline button
            if name == "Run Lint" and not ok and "baseline = file" in out_buf:
                self.baseline_btn.state(['!disabled'])

        # summary
        self._append_output("\n=== Summary ===\n", 'info')
        for name, ok, _ in results:
            mark = '✅' if ok else '❌'
            self._append_output(f"  {name}: {mark}\n", 'info')
        # enable view if report step succeeded
        if any(n=="HTML Report" and ok for n, ok, _ in results):
            self.view_btn.state(['!disabled'])

        self.start_btn.state(['!disabled'])
        self._save_config()

    def _on_baseline(self):
        proj = self.project_var.get().strip()
        gradlew = "gradlew.bat" if os.name=='nt' else "./gradlew"
        cmd = [os.path.join(proj, gradlew), "updateLintBaseline"]
        self._append_output("\n=== Creating Lint Baseline ===\n", 'info')
        proc = subprocess.Popen(cmd, cwd=proj,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            self._append_output(line, 'info')
        ret = proc.wait()
        if ret == 0:
            self._append_output("✅ Baseline created successfully.\n", 'success')
            self.baseline_btn.state(['disabled'])
        else:
            self._append_output(f"❌ Baseline failed (exit {ret}).\n", 'error')

    def _on_view(self):
        path = os.path.join(self.project_var.get().strip(), self.report_path_var.get())
        if os.path.isfile(path):
            webbrowser.open(path)
        else:
            messagebox.showerror("Not Found", f"Report not found:\n{path}")


if __name__ == "__main__":
    HealthCheckGUI().mainloop()
