import customtkinter as ctk

class LogFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.textbox = ctk.CTkTextbox(self, height=10)
        self.textbox.pack(fill="both", expand=True)
        self.textbox.configure(state="disabled")

    def log(self, msg: str):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", msg + "\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")
