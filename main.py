import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os

DATA_FILE = "tasks.json"

class TaskMaster:
    def __init__(self, root):
        self.root = root
        self.root.title("TaskMaster - Менеджер задач")
        self.root.geometry("700x500")

        self.tasks = []
        self.next_id = 1

        self.load_tasks()
        self.create_widgets()
        self.refresh_treeview()

    # ---------- Интерфейс ----------
    def create_widgets(self):
        # Верхняя панель: ввод новой задачи
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)

        self.task_entry = ttk.Entry(top_frame, width=50)
        self.task_entry.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        self.task_entry.bind("<Return>", lambda e: self.add_task())

        add_btn = ttk.Button(top_frame, text="Добавить", command=self.add_task)
        add_btn.pack(side=tk.LEFT)

        # Средняя панель: таблица задач
        mid_frame = ttk.Frame(self.root, padding="10")
        mid_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "text", "status")
        self.tree = ttk.Treeview(mid_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("id", text="ID")
        self.tree.heading("text", text="Задача")
        self.tree.heading("status", text="Статус")
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("text", width=400, anchor=tk.W)
        self.tree.column("status", width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(mid_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self.on_double_click)

        # Нижняя панель: кнопки управления
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill=tk.X)

        ttk.Button(bottom_frame, text="Удалить", command=self.delete_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Редактировать", command=self.edit_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Выполнено/Активно", command=self.toggle_done).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Очистить выполненные", command=self.clear_completed).pack(side=tk.LEFT, padx=5)

        ttk.Label(bottom_frame, text="Фильтр:").pack(side=tk.LEFT, padx=(20, 5))
        self.filter_var = tk.StringVar(value="Все")
        filter_combo = ttk.Combobox(
            bottom_frame,
            textvariable=self.filter_var,
            values=["Все", "Активные", "Выполненные"],
            state="readonly",
            width=15
        )
        filter_combo.pack(side=tk.LEFT)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_treeview())

        # Статус-бар
        self.status_label = ttk.Label(self.root, text="", relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

    # ---------- Работа с данными ----------
    def load_tasks(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.tasks = data.get("tasks", [])
                    self.next_id = data.get("next_id", 1)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить задачи: {e}")
                self.tasks = []
                self.next_id = 1
        else:
            self.tasks = []
            self.next_id = 1

    def save_tasks(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump({"tasks": self.tasks, "next_id": self.next_id}, f,
                          ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить задачи: {e}")

    def refresh_treeview(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        filter_val = self.filter_var.get()
        for task in self.tasks:
            if filter_val == "Активные" and task["done"]:
                continue
            if filter_val == "Выполненные" and not task["done"]:
                continue
            status = "✓ Выполнено" if task["done"] else "В работе"
            self.tree.insert("", tk.END, iid=task["id"],
                             values=(task["id"], task["text"], status))

        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t["done"])
        self.status_label.config(
            text=f"Всего задач: {total} | Выполнено: {done} | Активных: {total - done}"
        )

    # ---------- Действия ----------
    def add_task(self):
        text = self.task_entry.get().strip()
        if not text:
            messagebox.showwarning("Предупреждение", "Введите текст задачи.")
            return
        task = {"id": self.next_id, "text": text, "done": False}
        self.tasks.append(task)
        self.next_id += 1
        self.task_entry.delete(0, tk.END)
        self.save_tasks()
        self.refresh_treeview()

    def delete_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите задачу для удаления.")
            return
        task_id = int(selected[0])
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        self.save_tasks()
        self.refresh_treeview()

    def edit_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите задачу для редактирования.")
            return
        task_id = int(selected[0])
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if task:
            new_text = simpledialog.askstring(
                "Редактирование", "Измените текст задачи:", initialvalue=task["text"]
            )
            if new_text and new_text.strip():
                task["text"] = new_text.strip()
                self.save_tasks()
                self.refresh_treeview()

    def toggle_done(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите задачу.")
            return
        task_id = int(selected[0])
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if task:
            task["done"] = not task["done"]
            self.save_tasks()
            self.refresh_treeview()

    def clear_completed(self):
        if not any(t["done"] for t in self.tasks):
            messagebox.showinfo("Информация", "Нет выполненных задач.")
            return
        if messagebox.askyesno("Подтверждение", "Удалить все выполненные задачи?"):
            self.tasks = [t for t in self.tasks if not t["done"]]
            self.save_tasks()
            self.refresh_treeview()

    def on_double_click(self, event):
        self.toggle_done()


if __name__ == "__main__":
    root = tk.Tk()
    app = TaskMaster(root)
    root.mainloop()