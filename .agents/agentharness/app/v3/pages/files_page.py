"""Files page mixin."""
import tkinter as tk
import urllib.parse
from tkinter import ttk
from pages.constants import *


class FilesPageMixin:
    def show_files(self):
        self._set_active_nav("Files")
        self._clear_content()
        self._section_header(self.content, "📁 Files & Documents",
                             "Upload files, embed for RAG search, and run semantic queries.")

        search_row = tk.Frame(self.content, bg=BG_CANVAS)
        search_row.pack(fill="x", padx=20, pady=(0, 10))
        self._file_search_var = tk.StringVar()
        se = self._entry(search_row, self._file_search_var)
        se.pack(side="left", fill="x", expand=True, padx=(0, 8))
        se.insert(0, "Semantic search across embedded files…")
        se.bind("<FocusIn>", lambda e: se.delete(0, "end") if se.get().startswith("Semantic") else None)
        # UX: Enter key triggers search
        se.bind("<Return>", lambda _e: self._search_files())
        self._button(search_row, "🔍 Search", self._search_files).pack(side="left", padx=(0, 8))
        self._button(search_row, "📤 Upload File", self._upload_file, accent=True).pack(side="left")

        card = self._card(self.content, "Uploaded Files")
        card.pack(fill="both", expand=True, padx=20, pady=(0, 8))
        cols = ("name", "type", "size", "status", "uploaded")
        self.files_tree = ttk.Treeview(card, columns=cols, show="headings", selectmode="browse")
        for col, txt, w in [("name", "Name", 200), ("type", "Type", 80), ("size", "Size", 80),
                            ("status", "Status", 100), ("uploaded", "Uploaded", 130)]:
            self.files_tree.heading(col, text=txt)
            self.files_tree.column(col, width=w, anchor="w")
        sb = ttk.Scrollbar(card, orient="vertical", command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=sb.set)
        self.files_tree.pack(side="left", fill="both", expand=True, padx=14, pady=(0, 10))
        sb.pack(side="right", fill="y", pady=(0, 10))

        btn_row = tk.Frame(card, bg=BG_PANEL)
        btn_row.pack(fill="x", padx=14, pady=(0, 10))
        self._button(btn_row, "🔄 Refresh", self._refresh_files).pack(side="left", padx=4)
        self._button(btn_row, "⚙ Embed for RAG", self._embed_selected_file).pack(side="left", padx=4)
        self._button(btn_row, "🗑 Delete", self._delete_selected_file).pack(side="left", padx=4)

        res_card = self._card(self.content, "Search Results")
        res_card.pack(fill="x", padx=20, pady=(0, 20))
        self.file_search_text = self._text_widget(res_card, height=8)
        self.file_search_text.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self.file_search_text.configure(state="disabled")
        self._refresh_files()

    def _refresh_files(self):
        if not hasattr(self, "files_tree"):
            return
        self.files_tree.delete(*self.files_tree.get_children())
        try:
            data = self.hub._get("/api/files") or []
            files = data if isinstance(data, list) else data.get("files", [])
            for f in files:
                size_kb = f"{int(f.get('size', 0)) // 1024}KB"
                self.files_tree.insert("", "end", iid=str(f.get("id", "")),
                                       values=(f.get("original_filename", f.get("filename", "")),
                                               f.get("file_type", ""), size_kb,
                                               f.get("processing_status", ""), str(f.get("created_at", ""))[:16]))
        except Exception as e:
            self._toast(f"Files load error: {e}", ERROR)

    def _upload_file(self):
        from tkinter import filedialog
        import os, threading as _t

        path = filedialog.askopenfilename(
            title="Select file to upload",
            filetypes=[("All files", "*.*"), ("PDFs", "*.pdf"), ("Docs", "*.docx"),
                       ("Spreadsheets", "*.xlsx *.csv"), ("Images", "*.png *.jpg *.jpeg")]
        )
        if not path:
            return
        self._toast("Uploading…", ACCENT)

        def _run():
            try:
                import requests

                token = getattr(self.hub, "token", None)
                headers = {"Authorization": f"Bearer {token}"} if token else {}
                with open(path, "rb") as fh:
                    resp = requests.post(f"{self.hub.base_url}/api/files/upload",
                                         files={"file": (os.path.basename(path), fh)},
                                         headers=headers, timeout=60)
                if resp.status_code in (200, 201):
                    self._ui_queue.put(("toast", "File uploaded!", SUCCESS))
                    self._ui_queue.put(("call", self._refresh_files))
                else:
                    self._ui_queue.put(("toast", f"Upload failed: {resp.status_code}", ERROR))
            except Exception as e:
                self._ui_queue.put(("toast", f"Upload error: {e}", ERROR))

        _t.Thread(target=_run, daemon=True).start()

    def _embed_selected_file(self):
        if not hasattr(self, "files_tree"):
            return
        sel = self.files_tree.selection()
        if not sel:
            self._toast("Select a file first.", WARNING)
            return
        file_id = sel[0]
        import threading as _t

        self._toast("Embedding…", ACCENT)

        def _run():
            try:
                self.hub.post_json(f"/api/files/{file_id}/embed", {})
                self._ui_queue.put(("toast", "Embedding complete!", SUCCESS))
                self._ui_queue.put(("call", self._refresh_files))
            except Exception as e:
                self._ui_queue.put(("toast", f"Embed error: {e}", ERROR))

        _t.Thread(target=_run, daemon=True).start()

    def _delete_selected_file(self):
        if not hasattr(self, "files_tree"):
            return
        sel = self.files_tree.selection()
        if not sel:
            self._toast("Select a file first.", WARNING)
            return
        file_id = sel[0]
        try:
            self.hub.delete(f"/api/files/{file_id}")
            self.files_tree.delete(file_id)
            self._toast("File deleted.", SUCCESS)
        except Exception as e:
            self._toast(f"Delete error: {e}", ERROR)

    def _search_files(self):
        q = self._file_search_var.get().strip()
        if not q or q.startswith("Semantic"):
            return
        import threading as _t

        self._toast("Searching…", ACCENT)

        def _run():
            try:
                # Bug fix: URL-encode query string
                results = self.hub._get(f"/api/files/_search?q={urllib.parse.quote(q)}&limit=8") or {}
                rows = results.get("results", []) if isinstance(results, dict) else []
                lines = []
                for r in rows:
                    lines.append(f"[{r.get('filename', '')}] (score {float(r.get('score', 0) or 0):.3f})")
                    lines.append(f"  {str(r.get('text', ''))[:200]}")
                    lines.append("")
                text = "\n".join(lines) if lines else "No results found."
                self._ui_queue.put(("set_text", self.file_search_text, text))
                self._ui_queue.put(("toast", f"{len(lines) // 3} result(s) found.", SUCCESS))
            except Exception as e:
                self._ui_queue.put(("toast", f"Search error: {e}", ERROR))

        _t.Thread(target=_run, daemon=True).start()
