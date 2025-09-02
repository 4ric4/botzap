import customtkinter as ctk

class ControlsFrame(ctk.CTkFrame):
    def __init__(self, parent, start_callback, stop_callback, forget_callback=None, resume_callback=None):
        super().__init__(parent)
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.forget_callback = forget_callback
        self.resume_callback = resume_callback

        self.start_btn = ctk.CTkButton(self, text="🚀 INICIAR ENVIOS", command=self.start_callback)
        self.start_btn.grid(row=0, column=0, padx=5, pady=5)

        self.stop_btn = ctk.CTkButton(self, text="🛑 PARAR ENVIOS", command=self.stop_callback)
        self.stop_btn.grid(row=0, column=1, padx=5, pady=5)

        self.forget_btn = ctk.CTkButton(self, text="❌ Esquecer Sessão", command=self.forget_callback or (lambda: None))
        self.forget_btn.grid(row=0, column=2, padx=5, pady=5)

        self.resume_btn = ctk.CTkButton(self, text="🔄 Continuar", command=self.resume_callback or (lambda: None))
        self.resume_btn.grid(row=0, column=3, padx=5, pady=5)

        self.grid_columnconfigure((0,1,2,3), weight=1)
