import subprocess
import os
import platform
import sys

# --- Configurações ---
APP_NAME = "DisparadorWhatsApp"
ENTRY_POINT = "main_app.py"
ICON_PATH = "icon.ico"
INSTALLER_SCRIPT = "installer_script.iss"

DEPENDENCIES = ['pyinstaller', 'camoufox', 'playwright', 'pygetwindow', 'pywin32']

# --- Lógica do Script ---

def install_dependencies():
    """Verifica e instala as dependências necessárias."""
    print("="*60 + "\n Verificando e instalando dependências...\n" + "="*60)
    try:
        for package in DEPENDENCIES:
            print(f"\n--- Verificando {package} ---")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"✅ {package} está pronto.")
        
        print("\n--- Verificando navegador Firefox para o Playwright ---")
        subprocess.check_call([sys.executable, '-m', 'playwright', 'install', 'firefox'])
        print("✅ Navegador Firefox para Playwright está pronto.")
        
        print("\n" + "*"*60 + "\n ✅ Todas as dependências estão instaladas com sucesso!\n" + "*"*60)
        return True
    except Exception as e:
        print(f"\n❌ ERRO ao instalar dependências: {e}")
        return False

def create_executable():
    """Usa o PyInstaller para criar o executável."""
    print("\n" + "="*50 + f"\n Iniciando a construção do '{APP_NAME}.exe'...\n" + "="*50)
    
    # Comando robusto usando os 'hooks' oficiais do Playwright
    command = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--onefile',
        '--windowed',
        f'--name={APP_NAME}',
        '--collect-data', 'playwright',  # Inclui o navegador e todos os dados necessários
        '--collect-data', 'camoufox',
        '--collect-data', 'browserforge',
        '--collect-data', 'language_tags'
    ]

    if os.path.exists(ICON_PATH):
        command.append(f'--icon={ICON_PATH}')
    else:
        print(f"AVISO: Ícone '{ICON_PATH}' não encontrado.")

    command.append(ENTRY_POINT)
    print(f"\nComando: {' '.join(command)}\n")
    
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
        for line in iter(process.stdout.readline, ''):
            print(line.strip())
        process.wait()
        
        if process.returncode == 0:
            print("\n" + "*"*50 + f"\n ✅ SUCESSO! O executável foi criado em 'dist'.\n" + "*"*50)
            return True
        else:
            print("\n" + "!"*50 + "\n ❌ ERRO DURANTE A CONSTRUÇÃO DO .EXE!\n" + "!"*50)
            return False
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")
        return False

def find_inno_setup_compiler():
    """Tenta encontrar o compilador do Inno Setup."""
    for path in [r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe", r"C:\Program Files\Inno Setup 6\ISCC.exe"]:
        if os.path.exists(path): return path
    return None

def create_installer():
    """Cria um instalador .exe usando o Inno Setup."""
    print("\n" + "="*50 + "\n Iniciando a criação do instalador 'setup.exe'...\n" + "="*50)
    compiler_path = find_inno_setup_compiler()
    if not compiler_path:
        print("\nAVISO: Compilador do Inno Setup não encontrado.")
        print("   Para criar um instalador, instale o Inno Setup a partir de: https://jrsoftware.org/isinfo.php")
        return

    if not os.path.exists(INSTALLER_SCRIPT):
        print(f"\nERRO: O ficheiro de script '{INSTALLER_SCRIPT}' não foi encontrado.")
        return

    try:
        subprocess.run([compiler_path, INSTALLER_SCRIPT], check=True)
        print("\n" + "*"*50 + f"\n ✅ SUCESSO! O instalador foi criado em 'installers'.\n" + "*"*50)
    except Exception as e:
        print(f"\n❌ ERRO DURANTE A CRIAÇÃO DO INSTALADOR: {e}")

if __name__ == "__main__":
    print("Este script irá preparar o ambiente, empacotar a aplicação e criar um instalador.")
    input("Pressione ENTER para começar...")
    
    if install_dependencies():
        if create_executable():
            create_installer()
    else:
        print("\nA construção não pode continuar devido a erros na instalação das dependências.")

