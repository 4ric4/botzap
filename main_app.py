# main_app.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import csv
import threading
import os
import shutil
from backend import WhatsAppBot
from queue import Queue
import platform
import sys

# Redireciona stdout/stderr em .exe
if getattr(sys, 'frozen', False):
    log_dir = os.path.dirname(sys.executable)
    sys.stdout = open(os.path.join(log_dir, 'stdout.log'), 'w', encoding='utf-8')
    sys.stderr = open(os.path.join(log_dir, 'stderr.log'), 'w', encoding='utf-8')

IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    try:
        import win32gui
        import win32con
    except ImportError:
        IS_WINDOWS = False
        print("AVISO: pywin32 não encontrado. Integração de janela não funcionará.")

PROFILE_DIR = "firefox_profile"

class AppGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Disparador de Mensagens WhatsApp")
        self.state('zoomed')

        self.log_queue = Queue()
        self.progress_queue = Queue()
        self.window_handle_queue = Queue()
        self.is_running = False
        self.stop_event = None
        self.bot_thread = None
        self.browser_hwnd = None

        self._create_widgets()
        self.after(100, self._process_queues)
        self.after(200, self._update_resume_button_state)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_rowconfigure(0, weight=5)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        self.browser_frame = ttk.LabelFrame(main_frame, text="Navegador", padding="10")
        self.browser_frame.grid(row=0, column=0, sticky="nsew", pady=(0,10))
        self.browser_frame.bind("<Configure>", self._on_browser_frame_resize)
        self.browser_placeholder = ttk.Label(self.browser_frame, text="Aguardando início...", style="TLabel")
        self.browser_placeholder.pack(expand=True)

        controls_container = ttk.Frame(main_frame)
        controls_container.grid(row=1, column=0, sticky="nsew")
        controls_container.grid_columnconfigure(0, weight=3)
        controls_container.grid_columnconfigure(1, weight=1)
        controls_container.grid_columnconfigure(2, weight=3)
        controls_container.grid_rowconfigure(0, weight=1)

        # Números
        data_frame = ttk.Frame(controls_container)
        data_frame.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        numeros_frame = ttk.LabelFrame(data_frame, text="1. Números", padding="5")
        numeros_frame.grid(row=0, column=0, sticky="nsew", padx=(0,5))
        numeros_frame.grid_rowconfigure(1, weight=1)
        numeros_frame.grid_columnconfigure(0, weight=1)
        self.numeros_text = tk.Text(numeros_frame, height=5)
        self.numeros_text.grid(row=1, column=0, sticky="nsew", pady=(5,0))
        numeros_buttons_frame = ttk.Frame(numeros_frame)
        numeros_buttons_frame.grid(row=0, column=0, sticky="ew")
        self.btn_load_numeros = ttk.Button(numeros_buttons_frame, text="Carregar", command=self._carregar_numeros)
        self.btn_load_numeros.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,2))
        self.resume_button = ttk.Button(numeros_buttons_frame, text="Continuar", command=self._load_resume_file, state="disabled")
        self.resume_button.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Mensagens
        mensagens_frame = ttk.LabelFrame(data_frame, text="2. Mensagens", padding="5")
        mensagens_frame.grid(row=0, column=1, sticky="nsew")
        mensagens_frame.grid_rowconfigure(1, weight=1)
        mensagens_frame.grid_columnconfigure(0, weight=1)
        self.mensagens_text = tk.Text(mensagens_frame, height=5)
        self.mensagens_text.grid(row=1, column=0, sticky="nsew", pady=(5,0))
        self.mensagens_text.insert(tk.END, "Olá, tudo bem?")
        self.btn_load_mensagens = ttk.Button(mensagens_frame, text="Carregar Mensagens", command=self._carregar_mensagens)
        self.btn_load_mensagens.grid(row=0, column=0, sticky="ew")

        # Botões e progresso
        actions_frame = ttk.Frame(controls_container)
        actions_frame.grid(row=0, column=1, sticky="ns", padx=(0,10))
        self.progress_label = ttk.Label(actions_frame, text="Aguardando início...", anchor="center")
        self.progress_label.pack(fill=tk.X, pady=(5,5))
        self.start_button = ttk.Button(actions_frame, text="🚀 INICIAR ENVIOS", command=self._toggle_bot_state)
        self.start_button.pack(expand=True, fill=tk.BOTH, ipady=10)
        session_frame = ttk.Frame(actions_frame)
        session_frame.pack(fill=tk.X, pady=(5,0))
        self.remember_session_var = tk.BooleanVar(value=True)
        self.remember_session_check = ttk.Checkbutton(session_frame, text="Manter sessão", variable=self.remember_session_var)
        self.remember_session_check.pack(side=tk.LEFT)
        self.forget_button = ttk.Button(session_frame, text="Esquecer Login", command=self._forget_session)
        self.forget_button.pack(side=tk.RIGHT)

        # Log
        log_frame = ttk.LabelFrame(controls_container, text="Log de Atividade", padding="5")
        log_frame.grid(row=0, column=2, sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1); log_frame.grid_columnconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(log_frame, state='disabled', wrap=tk.WORD, bg="#2b2b2b", fg="#d3d3d3", height=7)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # --- Funções auxiliares ---
    def _forget_session(self):
        if os.path.isdir(PROFILE_DIR):
            try: shutil.rmtree(PROFILE_DIR); self.log_message("Sessão esquecida, será necessário escanear o QR Code novamente.")
            except Exception as e: messagebox.showerror("Erro", f"Não foi possível apagar '{PROFILE_DIR}': {e}")
        else: self.log_message("Nenhuma sessão salva.")

    def _on_browser_frame_resize(self, event):
        if IS_WINDOWS and self.browser_hwnd:
            win32gui.SetWindowPos(self.browser_hwnd, None, 0,0, event.width, event.height, win32con.SWP_NOZORDER)

    def _embed_browser_window(self, browser_hwnd):
        if IS_WINDOWS and browser_hwnd:
            self.browser_placeholder.pack_forget()
            self.browser_hwnd = browser_hwnd
            container_hwnd = self.browser_frame.winfo_id()
            self.update_idletasks()
            win32gui.SetParent(browser_hwnd, container_hwnd)
            style = win32gui.GetWindowLong(browser_hwnd, win32con.GWL_STYLE)
            style &= ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME | win32con.WS_SYSMENU)
            win32gui.SetWindowLong(browser_hwnd, win32con.GWL_STYLE, style)
            win32gui.SetWindowPos(browser_hwnd, None, 0,0,self.browser_frame.winfo_width(), self.browser_frame.winfo_height(), win32con.SWP_NOZORDER|win32con.SWP_FRAMECHANGED)

    def _on_closing(self):
        if self.is_running: messagebox.showwarning("Processo em Andamento", "Pare o envio antes de fechar a aplicação.")
        else: self.destroy()

    def _update_resume_button_state(self):
        if os.path.exists("faltantes.csv"):
            with open("faltantes.csv",'r',encoding='utf-8') as f:
                if f.readline().strip(): self.resume_button.config(state="normal"); return
        self.resume_button.config(state="disabled")

    def _load_resume_file(self):
        if not os.path.exists("faltantes.csv"): self.log_message("Nenhum arquivo 'faltantes.csv'"); return
        with open("faltantes.csv",'r',encoding='utf-8') as f:
            faltantes = [row[0] for row in csv.reader(f) if row]
        if not faltantes: self.log_message("Arquivo vazio."); return
        self.numeros_text.delete('1.0', tk.END); self.numeros_text.insert('1.0', '\n'.join(faltantes))
        self.log_message(f"Carregados {len(faltantes)} números pendentes.")

    def _carregar_arquivo(self, text_widget, title):
        filepath = filedialog.askopenfilename(title=title, filetypes=[("CSV files","*.csv"),("Text files","*.txt")])
        if not filepath: return
        content_list = []
        if filepath.lower().endswith('.csv'):
            with open(filepath,'r',encoding='utf-8',newline='') as f:
                content_list.extend(row[0].strip() for row in csv.reader(f) if row)
        else:
            with open(filepath,'r',encoding='utf-8') as f: content_list.extend(line.strip() for line in f if line.strip())
        text_widget.delete('1.0', tk.END); text_widget.insert('1.0', '\n'.join(content_list))
        self.log_message(f"Arquivo '{os.path.basename(filepath)}' carregado.")

    def _carregar_numeros(self): self._carregar_arquivo(self.numeros_text, "Selecionar arquivo de números")
    def _carregar_mensagens(self): self._carregar_arquivo(self.mensagens_text, "Selecionar arquivo de mensagens")
    def log_message(self,msg): self.log_queue.put(msg)
    def update_progress(self,sent,total): self.progress_queue.put((sent,total))
    def update_browser_handle(self,handle): self.window_handle_queue.put(handle)

    def _process_queues(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get_nowait(); self.log_text.config(state='normal'); self.log_text.insert(tk.END,msg+'\n'); self.log_text.config(state='disabled'); self.log_text.see(tk.END)
        while not self.progress_queue.empty():
            sent,total = self.progress_queue.get_nowait(); self.progress_label.config(text=f"Progresso: {sent} de {total} enviados.")
        while not self.window_handle_queue.empty():
            handle = self.window_handle_queue.get_nowait(); self._embed_browser_window(handle)
        self.after(100,self._process_queues)

    def _get_data_from_text(self,text_widget):
        content = text_widget.get('1.0', tk.END).strip(); return [line.strip() for line in content.split('\n') if line.strip()]

    def _set_running_state(self,is_running):
        self.is_running = is_running
        self.start_button.config(text="🚫 PARAR ENVIOS" if is_running else "🚀 INICIAR ENVIOS", state='normal')
        widget_state = "disabled" if is_running else "normal"
        for widget in [self.numeros_text,self.mensagens_text,self.btn_load_numeros,self.btn_load_mensagens,self.remember_session_check,self.forget_button]:
            widget.config(state=widget_state)
        if not is_running: 
            self.after(100,self._update_resume_button_state); self.browser_hwnd = None; self.browser_placeholder.pack(expand=True)
        else: self.resume_button.config(state="disabled")

    def _toggle_bot_state(self):
        if self.is_running: self._parar_bot()
        else: self._iniciar_bot()

    def _iniciar_bot(self):
        numeros = self._get_data_from_text(self.numeros_text)
        mensagens = self._get_data_from_text(self.mensagens_text)
        if not numeros or not mensagens: messagebox.showwarning("Faltam Dados","Insira pelo menos um número e uma mensagem."); return
        profile_path = PROFILE_DIR if self.remember_session_var.get() else None
        self._set_running_state(True)
        self.log_message("="*50); self.log_message("Iniciando o bot..."); self.update_progress(0,len(numeros))
        self.stop_event = threading.Event()
        bot = WhatsAppBot(numeros,mensagens,self.log_message,self._set_running_state,self.update_progress,self.update_browser_handle,self.stop_event,profile_path)
        self.bot_thread = threading.Thread(target=bot.run,daemon=True); self.bot_thread.start()

    def _parar_bot(self):
        if self.bot_thread and self.bot_thread.is_alive() and self.stop_event:
            self.log_message("="*50); self.log_message("🛑 Enviando sinal de interrupção..."); self.log_message("   O processo irá parar e salvar o progresso.")
            self.stop_event.set(); self.start_button.config(text="Aguardando Interrupção...", state='disabled')

if __name__ == "__main__":
    if not IS_WINDOWS: messagebox.showinfo("Funcionalidade Limitada","Integração da janela só disponível no Windows.")
    app = AppGUI(); app.mainloop()
