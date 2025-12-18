import tkinter as tk
from tkinter import messagebox
import random
import string
import math

# --- Алфавиты ---
LATIN_LOWER = string.ascii_lowercase
LATIN_UPPER = string.ascii_uppercase
DIGITS = string.digits

# Русские буквы
RUS_LOWER = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
RUS_UPPER = RUS_LOWER.upper()


class PasswordGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор паролей")

        self.create_widgets()

    def create_widgets(self):
        # --- Длина пароля ---
        tk.Label(self.root, text="Длина пароля (1–64):").grid(row=0, column=0, sticky="w")
        self.length_entry = tk.Entry(self.root, width=10)
        self.length_entry.insert(0, "8")
        self.length_entry.grid(row=0, column=1, sticky="w")

        # --- Флажки ---
        self.var_latin = tk.BooleanVar(value=True)
        self.var_russian = tk.BooleanVar(value=False)
        self.var_digits = tk.BooleanVar(value=True)
        self.var_case = tk.BooleanVar(value=True)
        self.var_special = tk.BooleanVar(value=False)

        tk.Checkbutton(self.root, text="Строчные латинские буквы", variable=self.var_latin,
                       command=self.update_all).grid(row=1, column=0, columnspan=2, sticky="w")

        tk.Checkbutton(self.root, text="Строчные русские буквы", variable=self.var_russian,
                       command=self.update_all).grid(row=2, column=0, columnspan=2, sticky="w")

        tk.Checkbutton(self.root, text="Цифры", variable=self.var_digits,
                       command=self.update_all).grid(row=3, column=0, columnspan=2, sticky="w")

        tk.Checkbutton(self.root, text="Учитывать регистр", variable=self.var_case,
                       command=self.update_all).grid(row=4, column=0, columnspan=2, sticky="w")

        tk.Checkbutton(self.root, text="Использовать спецсимволы",
                       variable=self.var_special, command=self.update_all).grid(
            row=5, column=0, columnspan=2, sticky="w"
        )

        # --- Спецсимволы ---
        tk.Label(self.root, text="Спецсимволы:").grid(row=6, column=0, sticky="w")
        self.special_entry = tk.Entry(self.root, width=30)
        self.special_entry.grid(row=6, column=1, sticky="w")
        self.special_entry.bind("<KeyRelease>", lambda e: self.update_all())

        # --- Итоговый алфавит ---
        tk.Label(self.root, text="Итоговый алфавит:").grid(row=7, column=0, sticky="nw")
        self.alphabet_text = tk.Text(self.root, height=3, width=40, state="disabled")
        self.alphabet_text.grid(row=7, column=1, sticky="w")

        # --- Количество паролей ---
        tk.Label(self.root, text="Количество возможных паролей:").grid(row=8, column=0, sticky="w")
        self.count_label = tk.Label(self.root, text="0")
        self.count_label.grid(row=8, column=1, sticky="w")

        # --- Сгенерированный пароль ---
        tk.Label(self.root, text="Сгенерированный пароль:").grid(row=9, column=0, sticky="w")
        self.password_entry = tk.Entry(self.root, width=30)
        self.password_entry.grid(row=9, column=1, sticky="w")

        # --- Кнопка ---
        tk.Button(self.root, text="Обновить пароль", command=self.generate_password)\
            .grid(row=10, column=0, columnspan=2, pady=10)

        self.update_all()

    def build_alphabet(self):
        alphabet = ""

        if self.var_latin.get():
            alphabet += LATIN_LOWER
            if self.var_case.get():
                alphabet += LATIN_UPPER

        if self.var_russian.get():
            alphabet += RUS_LOWER
            if self.var_case.get():
                alphabet += RUS_UPPER

        if self.var_digits.get():
            alphabet += DIGITS

        if self.var_special.get():
            specials = self.special_entry.get()
            forbidden = set(LATIN_LOWER + LATIN_UPPER + RUS_LOWER + RUS_UPPER + DIGITS)
            for ch in specials:
                if ch in forbidden:
                    messagebox.showerror(
                        "Ошибка",
                        f"Спецсимвол '{ch}' уже относится к выбранным алфавитам"
                    )
                    return None
            alphabet += specials

        return "".join(sorted(set(alphabet)))

    def update_all(self):
        try:
            length = int(self.length_entry.get())
            if not (1 <= length <= 64):
                raise ValueError
        except ValueError:
            self.count_label.config(text="Ошибка")
            return

        alphabet = self.build_alphabet()
        if not alphabet:
            self.show_alphabet("")
            self.count_label.config(text="0")
            return

        self.show_alphabet(alphabet)

        count = pow(len(alphabet), length)
        self.count_label.config(text=str(count))

        self.generate_password()

    def show_alphabet(self, alphabet):
        self.alphabet_text.config(state="normal")
        self.alphabet_text.delete("1.0", tk.END)
        self.alphabet_text.insert(tk.END, alphabet)
        self.alphabet_text.config(state="disabled")

    def generate_password(self):
        alphabet = self.build_alphabet()
        if not alphabet:
            self.password_entry.delete(0, tk.END)
            return

        try:
            length = int(self.length_entry.get())
        except ValueError:
            return

        password = "".join(random.choice(alphabet) for _ in range(length))
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, password)


if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordGeneratorApp(root)
    root.mainloop()
