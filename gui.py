import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from transcriber import AudioTranscriber, CANDIDATE_LANGUAGES
from file_manager import (
    scan_audio_files,
    generate_short_title,
    get_unique_filepath,
    save_transcript_to_txt,
    apply_file_renames
)


class ModernTranscriberApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("מתמלל ומשנה שמות קובצי שמע - Windows")
        self.root.geometry("1020x680")
        self.root.minsize(850, 550)

        self.transcriber = AudioTranscriber()
        self.files_to_process = []
        self.preview_data = []
        self.is_processing = False

        self._apply_theme()
        self._build_ui()

    def _apply_theme(self):
        self.root.configure(bg="#F4F6F9")
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure(".", font=("Segoe UI", 10), background="#F4F6F9")
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#1E293B", background="#F4F6F9")
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 9), foreground="#64748B", background="#F4F6F9")
        
        self.style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), background="#2563EB", foreground="#FFFFFF")
        self.style.map("Primary.TButton", background=[("active", "#1D4ED8"), ("disabled", "#94A3B8")])

        self.style.configure("Success.TButton", font=("Segoe UI", 10, "bold"), background="#16A34A", foreground="#FFFFFF")
        self.style.map("Success.TButton", background=[("active", "#15803D"), ("disabled", "#94A3B8")])

        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#E2E8F0", foreground="#1E293B")
        self.style.configure("Treeview", font=("Segoe UI", 9), rowheight=26, background="#FFFFFF", fieldbackground="#FFFFFF")

    def _build_ui(self):
        # Top title frame
        header_frame = tk.Frame(self.root, bg="#F4F6F9", padx=15, pady=10)
        header_frame.pack(fill=tk.X)
        
        lbl_title = ttk.Label(header_frame, text="מתמלל ומעדכן שמות הקלטות אוטומטי", style="Header.TLabel")
        lbl_title.pack(anchor="e")
        lbl_sub = ttk.Label(header_frame, text="תמלול באמצעות Google Speech Recognition, זיהוי שפה אוטומטי ושינוי שמות בטוח", style="SubHeader.TLabel")
        lbl_sub.pack(anchor="e")

        # Configuration frame
        config_frame = ttk.LabelFrame(self.root, text=" הגדרות וסריקה ", padding=12)
        config_frame.pack(fill=tk.X, padx=15, pady=5)

        # Folder selection row
        folder_row = tk.Frame(config_frame, bg="#F4F6F9")
        folder_row.pack(fill=tk.X, pady=4)
        
        self.btn_browse = ttk.Button(folder_row, text="בחר תיקייה...", command=self.choose_folder)
        self.btn_browse.pack(side=tk.LEFT, padx=5)

        self.txt_folder = ttk.Entry(folder_row, font=("Segoe UI", 9))
        self.txt_folder.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

        # Options row
        opts_row = tk.Frame(config_frame, bg="#F4F6F9")
        opts_row.pack(fill=tk.X, pady=6)

        # Save txt checkbox
        self.var_save_txt = tk.BooleanVar(value=True)
        chk_txt = ttk.Checkbutton(opts_row, text="שמור קובץ TXT של התמלול המלא", variable=self.var_save_txt)
        chk_txt.pack(side=tk.RIGHT, padx=10)

        # Skip processed checkbox
        self.var_skip_processed = tk.BooleanVar(value=False)
        chk_skip = ttk.Checkbutton(opts_row, text="דלג על קבצים שכבר טופלו", variable=self.var_skip_processed)
        chk_skip.pack(side=tk.RIGHT, padx=10)

        # Word count spinner
        lbl_words = ttk.Label(opts_row, text="מספר מילים בשם הקובץ:")
        lbl_words.pack(side=tk.RIGHT, padx=(15, 2))
        self.spn_words = ttk.Spinbox(opts_row, from_=1, to=20, width=5)
        self.spn_words.set(6)
        self.spn_words.pack(side=tk.RIGHT, padx=5)

        # Language dropdown
        lbl_lang = ttk.Label(opts_row, text="שפת שמע:")
        lbl_lang.pack(side=tk.RIGHT, padx=(15, 2))
        self.cbo_lang = ttk.Combobox(opts_row, state="readonly", width=18)
        lang_values = ["auto: זיהוי אוטומטי"] + [f"{code}: {name}" for code, name in CANDIDATE_LANGUAGES]
        self.cbo_lang['values'] = lang_values
        self.cbo_lang.current(0)
        self.cbo_lang.pack(side=tk.RIGHT, padx=5)

        # Main Table (Treeview)
        table_frame = tk.Frame(self.root, bg="#F4F6F9", padx=15, pady=5)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("status", "new_name", "orig_name", "idx")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("idx", text="#")
        self.tree.heading("orig_name", text="שם קובץ מקורי")
        self.tree.heading("new_name", text="שם מוצע (תצוגה מקדימה)")
        self.tree.heading("status", text="סטטוס / שגיאה")

        self.tree.column("idx", width=45, anchor="center")
        self.tree.column("orig_name", width=260, anchor="e")
        self.tree.column("new_name", width=330, anchor="e")
        self.tree.column("status", width=250, anchor="e")

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.tree.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Progress and status footer
        footer_frame = tk.Frame(self.root, bg="#F4F6F9", padx=15, pady=8)
        footer_frame.pack(fill=tk.X)

        self.lbl_progress = ttk.Label(footer_frame, text="מוכן לפעולה. בחר תיקייה כדי להתחיל.")
        self.lbl_progress.pack(anchor="e", pady=2)

        self.progress_bar = ttk.Progressbar(footer_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=4)

        # Actions buttons
        actions_frame = tk.Frame(self.root, bg="#F4F6F9", padx=15, pady=10)
        actions_frame.pack(fill=tk.X)

        self.btn_apply = ttk.Button(
            actions_frame, 
            text="3. אשר ובצע שינוי שמות בפועל", 
            style="Success.TButton", 
            state=tk.DISABLED,
            command=self.apply_renames
        )
        self.btn_apply.pack(side=tk.LEFT, padx=5)

        self.btn_start = ttk.Button(
            actions_frame, 
            text="2. התחל תמלול ויצירת תצוגה מקדימה", 
            style="Primary.TButton", 
            state=tk.DISABLED,
            command=self.start_transcription_thread
        )
        self.btn_start.pack(side=tk.LEFT, padx=5)

    def choose_folder(self):
        selected_dir = filedialog.askdirectory(title="בחר תיקיית קובצי שמע")
        if not selected_dir:
            return
            
        self.txt_folder.delete(0, tk.END)
        self.txt_folder.insert(0, selected_dir)
        self.refresh_file_list()

    def refresh_file_list(self):
        folder_path = self.txt_folder.get().strip()
        if not folder_path or not os.path.isdir(folder_path):
            return

        self.files_to_process = scan_audio_files(
            folder_path, skip_processed=self.var_skip_processed.get()
        )
        
        self.tree.delete(*self.tree.get_children())
        self.preview_data = []

        for idx, file_path in enumerate(self.files_to_process, start=1):
            filename = os.path.basename(file_path)
            self.tree.insert("", tk.END, iid=str(idx-1), values=("ממתין לתמלול", "-", filename, idx))

        count = len(self.files_to_process)
        if count > 0:
            self.lbl_progress.config(text=f"נמצאו {count} קובצי שמע מתאימים.")
            self.btn_start.config(state=tk.NORMAL)
            self.btn_apply.config(state=tk.DISABLED)
        else:
            self.lbl_progress.config(text="לא נמצאו קובצי שמע מתאימים בתיקייה זו.")
            self.btn_start.config(state=tk.DISABLED)
            self.btn_apply.config(state=tk.DISABLED)

    def start_transcription_thread(self):
        if self.is_processing:
            return
        self.is_processing = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_browse.config(state=tk.DISABLED)
        self.btn_apply.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=self._process_all_files, daemon=True)
        thread.start()

    def _process_all_files(self):
        total = len(self.files_to_process)
        self.preview_data = []
        
        try:
            word_count = int(self.spn_words.get())
        except ValueError:
            word_count = 6

        raw_lang = self.cbo_lang.get()
        selected_lang_code = raw_lang.split(":")[0].strip()

        for idx, original_path in enumerate(self.files_to_process):
            file_name = os.path.basename(original_path)
            dir_name = os.path.dirname(original_path)
            _, ext = os.path.splitext(original_path)
            
            self._update_ui_progress(idx, total, f"מעבד קובץ {idx+1} מתוך {total}: {file_name}")
            self._update_tree_item(idx, status="מתמלל...", new_name="-")

            def chunk_callback(msg):
                self._update_ui_progress(idx, total, f"[{idx+1}/{total}] {file_name} - {msg}")

            try:
                transcript = self.transcriber.transcribe_audio_file(
                    original_path, 
                    language_code=selected_lang_code,
                    progress_callback=chunk_callback
                )

                if not transcript:
                    status_text = "שגיאה: לא זוהה דיבור"
                    self._update_tree_item(idx, status=status_text, new_name="[ללא שינוי]")
                    self.preview_data.append({
                        "original_path": original_path,
                        "target_path": original_path,
                        "status": status_text
                    })
                    continue

                # Save transcript TXT if requested
                if self.var_save_txt.get():
                    save_transcript_to_txt(original_path, transcript)

                # Generate new title
                short_title = generate_short_title(transcript, word_count=word_count)
                new_filepath = get_unique_filepath(dir_name, short_title, ext)
                new_filename = os.path.basename(new_filepath)

                self._update_tree_item(idx, status="מוכן לשינוי", new_name=new_filename)
                self.preview_data.append({
                    "original_path": original_path,
                    "target_path": new_filepath,
                    "status": "מוכן לשינוי"
                })

            except Exception as ex:
                err_msg = f"שגיאה: {str(ex)}"
                self._update_tree_item(idx, status=err_msg, new_name="[דולג]")
                self.preview_data.append({
                    "original_path": original_path,
                    "target_path": original_path,
                    "status": err_msg
                })

        self._update_ui_progress(total, total, "שלב התמלול הסתיים! אנא בדוק את התצוגה המקדימה ולחץ לאישור.")
        self.root.after(0, self._on_transcription_finished)

    def _on_transcription_finished(self):
        self.is_processing = False
        self.btn_browse.config(state=tk.NORMAL)
        self.btn_start.config(state=tk.NORMAL)
        
        valid_items = [p for p in self.preview_data if p.get("status") == "מוכן לשינוי"]
        if valid_items:
            self.btn_apply.config(state=tk.NORMAL)
            messagebox.showinfo("תצוגה מקדימה מוכנה", f"התמלול הושלם בהצלחה עבור {len(valid_items)} קבצים.\nבאפשרותך לצפות בשמות המוצעים ולאשר את השינוי.")
        else:
            messagebox.showwarning("התמלול הסתיים", "לא נוצרו שמות חדשים (יתכן שהקבצים ריקים או שחלה שגיאה).")

    def apply_renames(self):
        if not self.preview_data:
            return
            
        confirm = messagebox.askyesno(
            "אישור שינוי שמות",
            "האם אתה בטוח שברצונך לשנות את שמות הקבצים לפי התצוגה המקדימה?"
        )
        if not confirm:
            return

        results = apply_file_renames(self.preview_data)
        for idx, res in enumerate(results):
            self._update_tree_item(idx, status=res.get("final_status", ""))

        self.btn_apply.config(state=tk.DISABLED)
        self.lbl_progress.config(text="פעולת שינוי השמות הושלמה בהצלחה!")
        messagebox.showinfo("סיום", "כל שמות הקבצים עודכנו בהצלחה במערכת הקבצים!")

    def _update_ui_progress(self, current: int, total: int, text: str):
        def _sync():
            self.lbl_progress.config(text=text)
            if total > 0:
                pct = (current / total) * 100
                self.progress_bar['value'] = pct
        self.root.after(0, _sync)

    def _update_tree_item(self, idx: int, status: str = None, new_name: str = None):
        def _sync():
            item_id = str(idx)
            if self.tree.exists(item_id):
                current_values = list(self.tree.item(item_id, "values"))
                if status is not None:
                    current_values[0] = status
                if new_name is not None:
                    current_values[1] = new_name
                self.tree.item(item_id, values=current_values)
        self.root.after(0, _sync)
