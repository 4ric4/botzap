import customtkinter as ctk
from tkinter import filedialog
import os

class MensagensFrame(ctk.CTkFrame):
    def __init__(self, parent, log_callback):
        super().__init__(parent)
        self.log_callback = log_callback

        self.label = ctk.CTkLabel(self, text="Mensagens", font=("Arial", 14, "bold"))
        self.label.pack(pady=(0,5))

        self.textbox = ctk.CTkTextbox(self, height=120)
        self.textbox.pack(fill="both", expand=True, padx=5, pady=5)

        self.btn_load = ctk.CTkButton(self, text="Carregar Arquivo", command=self._carregar)
        self.btn_load.pack(fill="x", padx=5, pady=(0,5))

    def _carregar(self):
        filepath = filedialog.askopenfilename(title="Selecionar arquivo de mensagens",
                                              filetypes=[("Text files","*.txt")])
        if not filepath:
            return
        with open(filepath, "r", encoding="utf-8") as f:
            mensagens = [line.strip() for line in f if line.strip()]

        self.textbox.delete("0.0", "end")
        self.textbox.insert("0.0", "\n".join(mensagens))
        self.log_callback(f"Arquivo '{os.path.basename(filepath)}' carregado.")

    def get_mensagens(self):
        content = self.textbox.get("0.0", "end").strip()
        return [line for line in content.splitlines() if line.strip()]
