from __future__ import annotations

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
from typing import Dict, List

from . import storage


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Chamada - Atendimento/Presenças")
        self.geometry("760x520")

        self.data = storage.load()

        self.class_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Pronto")

        self._build_ui()
        self._refresh_classes()

    # UI
    def _build_ui(self) -> None:
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top, text="Turma:").pack(side=tk.LEFT)
        self.class_combo = ttk.Combobox(top, textvariable=self.class_var, state="readonly", width=40)
        self.class_combo.pack(side=tk.LEFT, padx=8)
        self.class_combo.bind("<<ComboboxSelected>>", lambda e: self._on_class_change())

        ttk.Button(top, text="Nova turma", command=self._add_class).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Renomear", command=self._rename_class).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Excluir", command=self._delete_class).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Exportar CSV", command=self._export_csv).pack(side=tk.RIGHT)

        body = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Students panel
        left = ttk.Labelframe(body, text="Alunos")
        body.add(left, weight=1)

        self.student_list = tk.Listbox(left)
        self.student_list.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6, pady=6)

        btns = ttk.Frame(left)
        btns.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=(0, 6))
        ttk.Button(btns, text="Adicionar", command=self._add_student).pack(side=tk.LEFT)
        ttk.Button(btns, text="Remover", command=self._remove_student).pack(side=tk.LEFT, padx=6)

        # Attendance panel
        right = ttk.Labelframe(body, text="Chamada de hoje")
        body.add(right, weight=2)

        self.attendance_frame = ttk.Frame(right)
        self.attendance_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        controls = ttk.Frame(right)
        controls.pack(fill=tk.X, padx=6, pady=(0, 6))
        ttk.Button(controls, text="Todos presentes", command=lambda: self._set_all(True)).pack(side=tk.LEFT)
        ttk.Button(controls, text="Todos ausentes", command=lambda: self._set_all(False)).pack(side=tk.LEFT, padx=6)
        ttk.Button(controls, text="Salvar chamada", command=self._save_attendance).pack(side=tk.RIGHT)

        status = ttk.Label(self, textvariable=self.status_var, anchor="w")
        status.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=6)

    # Data helpers
    def _refresh_classes(self) -> None:
        classes = storage.list_classes(self.data)
        names = [c["name"] for c in classes]
        self.class_combo["values"] = names
        # Keep selection if possible
        cur_id = self._current_class_id()
        if cur_id:
            # find current by id
            for idx, c in enumerate(classes):
                if c["id"] == cur_id:
                    self.class_combo.current(idx)
                    break
        elif classes:
            self.class_combo.current(0)
        self._on_class_change()

    def _current_class(self) -> Dict | None:
        classes = storage.list_classes(self.data)
        if not classes:
            return None
        idx = self.class_combo.current()
        if idx is None or idx < 0 or idx >= len(classes):
            return None
        return classes[idx]

    def _current_class_id(self) -> str | None:
        c = self._current_class()
        return c["id"] if c else None

    # Actions: classes
    def _add_class(self) -> None:
        name = simpledialog.askstring("Nova turma", "Nome da turma:", parent=self)
        if not name:
            return
        storage.add_class(self.data, name)
        storage.save(self.data)
        self._refresh_classes()
        self.status_var.set("Turma criada")

    def _rename_class(self) -> None:
        c = self._current_class()
        if not c:
            messagebox.showinfo("Turma", "Crie uma turma primeiro.")
            return
        name = simpledialog.askstring("Renomear turma", "Novo nome:", initialvalue=c["name"], parent=self)
        if not name:
            return
        storage.rename_class(self.data, c["id"], name)
        storage.save(self.data)
        self._refresh_classes()
        self.status_var.set("Turma renomeada")

    def _delete_class(self) -> None:
        c = self._current_class()
        if not c:
            messagebox.showinfo("Turma", "Nada para excluir.")
            return
        if not messagebox.askyesno("Excluir turma", f"Excluir '{c['name']}' e suas chamadas?"):
            return
        storage.delete_class(self.data, c["id"])
        storage.save(self.data)
        self._refresh_classes()
        self._refresh_students_and_attendance()
        self.status_var.set("Turma excluída")

    # Actions: students
    def _add_student(self) -> None:
        c = self._current_class()
        if not c:
            messagebox.showinfo("Alunos", "Crie uma turma primeiro.")
            return
        name = simpledialog.askstring("Novo aluno", "Nome do aluno:", parent=self)
        if not name:
            return
        storage.add_student(self.data, c["id"], name)
        storage.save(self.data)
        self._refresh_students_and_attendance()
        self.status_var.set("Aluno adicionado")

    def _remove_student(self) -> None:
        c = self._current_class()
        if not c:
            return
        sel = self.student_list.curselection()
        if not sel:
            return
        idx = sel[0]
        students = c.get("students", [])
        st = students[idx]
        if not messagebox.askyesno("Remover aluno", f"Remover '{st['name']}'?"):
            return
        storage.remove_student(self.data, c["id"], st["id"])
        storage.save(self.data)
        self._refresh_students_and_attendance()
        self.status_var.set("Aluno removido")

    # Actions: attendance
    def _set_all(self, present: bool) -> None:
        for sid, var in self._presence_vars.items():
            var.set(1 if present else 0)

    def _save_attendance(self) -> None:
        c = self._current_class()
        if not c:
            messagebox.showinfo("Chamada", "Crie uma turma primeiro.")
            return
        presence = {sid: bool(var.get()) for sid, var in self._presence_vars.items()}
        storage.save_attendance(self.data, c["id"], presence)
        storage.save(self.data)
        self.status_var.set("Chamada salva")

    # Event handlers
    def _on_class_change(self) -> None:
        self._refresh_students_and_attendance()

    def _refresh_students_and_attendance(self) -> None:
        # students list
        self.student_list.delete(0, tk.END)
        c = self._current_class()
        if not c:
            self._render_attendance([])
            return
        for s in c.get("students", []):
            self.student_list.insert(tk.END, s["name"])
        self._render_attendance(c.get("students", []))

    def _render_attendance(self, students: List[Dict]) -> None:
        for w in self.attendance_frame.winfo_children():
            w.destroy()
        self._presence_vars: Dict[str, tk.IntVar] = {}
        # Pre-fill from today's session
        c = self._current_class()
        entries = {}
        if c:
            session = storage.get_today_session(self.data, c["id"])
            entries = {e["student_id"]: bool(e.get("present")) for e in session.get("entries", [])}
        # header
        hdr = ttk.Frame(self.attendance_frame)
        hdr.pack(fill=tk.X)
        ttk.Label(hdr, text="Presente", width=10).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Label(hdr, text="Aluno").pack(side=tk.LEFT)
        ttk.Separator(self.attendance_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=4)
        # items
        for s in students:
            row = ttk.Frame(self.attendance_frame)
            row.pack(fill=tk.X, pady=2)
            var = tk.IntVar(value=1 if entries.get(s["id"], False) else 0)
            cb = ttk.Checkbutton(row, variable=var)
            cb.pack(side=tk.LEFT, padx=(0, 6))
            ttk.Label(row, text=s["name"], anchor="w").pack(side=tk.LEFT)
            self._presence_vars[s["id"]] = var

    # Export
    def _export_csv(self) -> None:
        c = self._current_class()
        if not c:
            messagebox.showinfo("Exportar", "Crie uma turma primeiro.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
            initialfile=f"{c['name']}.csv",
        )
        if not path:
            return
        try:
            from pathlib import Path

            storage.export_class_csv(self.data, c["id"], Path(path))
            self.status_var.set("CSV exportado")
        except Exception as e:
            messagebox.showerror("Erro ao exportar", str(e))


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()

