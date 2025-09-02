import customtkinter as ctk
from tkinter import filedialog
import csv
import os

class NumerosFrame(ctk.CTkFrame):
    def __init__(self, parent, log_callback):
        super().__init__(parent)
        self.log_callback = log_callback

        # --- Label ---
        self.label = ctk.CTkLabel(self, text="Números", font=("Arial", 14, "bold"))
        self.label.pack(pady=(0,5))

        # --- Textbox ---
        self.textbox = ctk.CTkTextbox(self, height=120)
        self.textbox.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Botão carregar arquivo ---
        self.btn_load = ctk.CTkButton(self, text="Carregar Arquivo", command=self._carregar)
        self.btn_load.pack(fill="x", padx=5, pady=(0,5))

    # --- Carregar CSV ou TXT ---
    def _carregar(self):
        filepath = filedialog.askopenfilename(
            title="Selecionar arquivo de números",
            filetypes=[("CSV files","*.csv"),("Text files","*.txt")]
        )
        if not filepath:
            return

        numeros = []
        if filepath.lower().endswith(".csv"):
            with open(filepath, "r", encoding="utf-8") as f:
                numeros = [row[0].strip() for row in csv.reader(f) if row]
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                numeros = [line.strip() for line in f if line.strip()]

        self.set_numeros(numeros)
        self.log_callback(f"Arquivo '{os.path.basename(filepath)}' carregado.")

    # --- Obter números ---
    def get_numeros(self):
        content = self.textbox.get("0.0", "end").strip()
        return [line for line in content.splitlines() if line.strip()]

    # --- Definir números (para botão Continuar) ---
    def set_numeros(self, numeros):
        self.textbox.delete("0.0", "end")
        self.textbox.insert("0.0", "\n".join(numeros))
