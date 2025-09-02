import customtkinter as ctk
from frames.numeros_frame import NumerosFrame
from frames.mensagens_frame import MensagensFrame
from frames.log_frame import LogFrame
from frames.controls_frame import ControlsFrame
from backend import WhatsAppBot
import threading
import shutil
import os
import csv

PROFILE_DIR = "firefox_profile"

class AppGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Disparador de Mensagens WhatsApp")
        self.geometry("900x600")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")

        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        # --- Bot ---
        self.bot_thread = None
        self.stop_event = None
        self.bot = None

        # --- Frames ---
        self.numeros_frame = NumerosFrame(self, self.log_message)
        self.numeros_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.mensagens_frame = MensagensFrame(self, self.log_message)
        self.mensagens_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.log_frame = LogFrame(self)
        self.log_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        self.controls_frame = ControlsFrame(
            self,
            start_callback=self.start_bot,
            stop_callback=self.stop_bot,
            forget_callback=self.forget_session,
            resume_callback=self.load_resume_file
        )
        self.controls_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        # Grid weights
        self.grid_rowconfigure(0, weight=2)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    # --- Log ---
    def log_message(self, msg: str):
        self.log_frame.log(msg)

    # --- Bot callbacks ---
    def bot_finished(self, running: bool):
        self.log_message("ℹ️ Bot finalizado.")
        self.bot_thread = None
        self.stop_event = None
        self.bot = None

    def update_progress(self, enviados: int, total: int):
        self.log_message(f"Progresso: {enviados} de {total} enviados.")

    # --- Start / Stop bot ---
    def start_bot(self):
        numeros = self.numeros_frame.get_numeros()
        mensagens = self.mensagens_frame.get_mensagens()
        if not numeros or not mensagens:
            self.log_message("⚠️ Insira números e mensagens antes de iniciar.")
            return

        self.stop_event = threading.Event()

        def handle_callback(_):
            pass  # integração futura com janela

        self.bot = WhatsAppBot(
            numeros=numeros,
            mensagens=mensagens,
            log_callback=self.log_message,
            status_callback=self.bot_finished,
            progress_callback=self.update_progress,
            handle_callback=handle_callback,
            stop_event=self.stop_event,
            profile_path=PROFILE_DIR
        )

        self.bot_thread = threading.Thread(target=self.bot.run, daemon=True)
        self.bot_thread.start()
        self.log_message("🚀 Bot iniciado.")

    def stop_bot(self):
        if self.stop_event:
            self.stop_event.set()
            self.log_message("🛑 Sinal enviado para parar o bot.")

    # --- Esquecer sessão ---
    def forget_session(self):
        if os.path.exists(PROFILE_DIR):
            try:
                shutil.rmtree(PROFILE_DIR)
                self.log_message("ℹ️ Sessão esquecida. Será necessário escanear o QR Code novamente.")
            except Exception as e:
                self.log_message(f"❌ Não foi possível apagar '{PROFILE_DIR}': {e}")
        else:
            self.log_message("ℹ️ Nenhuma sessão salva.")

    # --- Continuar pendentes ---
    def load_resume_file(self):
        if not os.path.exists("faltantes.csv"):
            self.log_message("⚠️ Nenhum arquivo 'faltantes.csv' encontrado.")
            return
        with open("faltantes.csv", "r", encoding="utf-8") as f:
            faltantes = [row[0] for row in csv.reader(f) if row]
        if not faltantes:
            self.log_message("⚠️ Arquivo de pendentes vazio.")
            return
        self.numeros_frame.set_numeros(faltantes)
        self.log_message(f"ℹ️ Carregados {len(faltantes)} números pendentes.")
