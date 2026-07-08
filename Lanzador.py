import os
import sys
import json
import subprocess
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import webbrowser
import customtkinter as ctk
from PIL import Image

# Configuración del entorno CustomTkinter
ctk.set_appearance_mode("dark")

CONFIG_FILE = "launcher_config.json"

def obtener_ruta_recurso(ruta_relativa):
    """ Obtiene la ruta del recurso, compatible con el empaquetado de PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, ruta_relativa)
    return os.path.join(os.path.abspath("."), ruta_relativa)

class ViZoRLauncherFinal(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ViZoRRetrogames - PCSX2x6 Ultimate Launcher")
        self.geometry("850x760")
        self.resizable(False, False)
        
        # Paleta de Colores Oficial
        self.BG_COLOR = "#10141D"
        self.FRAME_BG = "#161B26"
        self.ACCENT_YELLOW = "#FFB300"
        self.TEXT_LIGHT = "#E2E8F0"
        
        self.configure(fg_color=self.BG_COLOR)

        self.config = {
            "pcsx2_path": "",
            "games_dir": "",
            "memcards_dir": "",
            "last_rom_path": "",
            "last_mcard_path": ""
        }
        self.cargar_config_global()
        
        # =====================================================================
        # CABECERA CON AMBOS LOGOS LADO A LADO (CENTRADOS)
        # =====================================================================
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(15, 5), fill="x")
        
        # Contenedor centralizado para empaquetar de forma limpia horizontalmente
        self.logos_wrapper = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.logos_wrapper.pack(anchor="center")
        
        # Logo del Canal (Izquierda)
        self.logo_label = ctk.CTkLabel(self.logos_wrapper, text="")
        self.logo_label.pack(side="left", padx=15)
        
        # Logo del Emulador [LogoEmu.png] (Derecha)
        self.logo_emu_label = ctk.CTkLabel(self.logos_wrapper, text="")
        self.logo_emu_label.pack(side="left", padx=15)
        
        self.cargar_logos_cabecera()

        # Enlace YouTube Industrial
        self.yt_link = ctk.CTkLabel(
            self.header_frame, 
            text="Visita mi Canal de YouTube", 
            font=("Impact", 14, "underline"), 
            text_color=self.ACCENT_YELLOW, 
            cursor="hand2"
        )
        self.yt_link.pack(pady=(8, 0))
        self.yt_link.bind("<Button-1>", lambda e: webbrowser.open("https://www.youtube.com/@ViZoRRetrogames"))

        # =====================================================================
        # SECCIÓN 1: CONFIGURACIÓN DE PARÁMETROS GLOBALES
        # =====================================================================
        self.param_frame = ctk.CTkFrame(self, fg_color=self.FRAME_BG, border_color=self.ACCENT_YELLOW, border_width=2, corner_radius=6)
        self.param_frame.pack(pady=10, padx=25, fill="x")
        
        ctk.CTkLabel(
            self.param_frame, 
            text=" 🛠️ PCSX2x6 SYSTEM ARCHITECTURE / GLOBAL SETTINGS ", 
            font=("Impact", 13), 
            text_color=self.ACCENT_YELLOW
        ).grid(row=0, column=0, columnspan=3, pady=(10, 12), padx=15, sticky="w")

        self.crear_fila_ruta(self.param_frame, "Ruta pcsx2-qt.exe:", "pcsx2_path", self.buscar_emulador, 1)
        self.crear_fila_ruta(self.param_frame, "Carpeta destino Juegos:", "games_dir", self.buscar_dir_juegos, 2)
        self.crear_fila_ruta(self.param_frame, "Carpeta memcards PCSX2:", "memcards_dir", self.buscar_dir_mcards, 3)

        # =====================================================================
        # SECCIÓN 2: SELECTORES Y CONFIGURACIÓN ARCADE
        # =====================================================================
        self.main_frame = ctk.CTkFrame(self, fg_color=self.FRAME_BG, border_width=1, border_color="#2D3748", corner_radius=6)
        self.main_frame.pack(pady=10, padx=25, fill="both", expand=True)

        # Contenedor de Selección de Juego y Miniatura
        self.selector_layout = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.selector_layout.pack(fill="x", padx=20, pady=(12, 5))

        self.controles_juego_frame = ctk.CTkFrame(self.selector_layout, fg_color="transparent")
        self.controles_juego_frame.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(self.controles_juego_frame, text="1. SYSTEM246 / SYSTEM256 GAME ID SELECTOR:", font=("Impact", 12), text_color=self.TEXT_LIGHT).pack(anchor="w", pady=(0, 2))
        
        lista_juegos = self.listar_juegos_proverb()
        if not lista_juegos:
            lista_juegos = ["Seleccionar ID..."]
        
        self.combo_game_id = ctk.CTkComboBox(
            self.controles_juego_frame, 
            values=lista_juegos, 
            width=250, 
            fg_color="#0D1117",
            border_color="#4A5568",
            button_color=self.ACCENT_YELLOW,
            button_hover_color="#D99B00",
            text_color=self.TEXT_LIGHT,
            command=self.actualizar_info_juego
        )
        self.combo_game_id.pack(anchor="w", pady=5)
        self.combo_game_id.set(lista_juegos[0])
        
        self.lbl_game_title = ctk.CTkLabel(self.controles_juego_frame, text="Título: No seleccionado", font=("Arial", 12, "bold", "italic"), text_color="#A0AEC0")
        self.lbl_game_title.pack(anchor="w", pady=2)

        # Miniatura del juego seleccionado (Derecha)
        self.preview_frame = ctk.CTkFrame(self.selector_layout, width=140, height=105, fg_color="#0D1117", border_color="#2D3748", border_width=1)
        self.preview_frame.pack(side="right", padx=(10, 0))
        self.preview_frame.pack_propagate(False)

        self.lbl_miniature = ctk.CTkLabel(self.preview_frame, text="Imagen no\ndisponible", font=("Arial", 11, "italic"), text_color="#718096")
        self.lbl_miniature.pack(expand=True, fill="both")

        # Entrada de Archivo Origen del Juego (ROM)
        ctk.CTkLabel(self.main_frame, text="2. SOURCE ROM IMAGE (.CHD / .ISO / .BIN):", font=("Impact", 12), text_color=self.TEXT_LIGHT).pack(anchor="w", padx=20, pady=(10, 2))
        self.rom_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.rom_frame.pack(fill="x", padx=20, pady=5)
        self.entry_rom = ctk.CTkEntry(self.rom_frame, fg_color="#0D1117", border_color="#4A5568", text_color=self.TEXT_LIGHT, placeholder_text="Ruta del archivo original...")
        self.entry_rom.pack(side="left", fill="x", expand=True, padx=(0, 10))
        if self.config["last_rom_path"]: self.entry_rom.insert(0, self.config["last_rom_path"])
        self.btn_rom = ctk.CTkButton(self.rom_frame, text="🗁", width=45, fg_color="#2D3748", hover_color="#4A5568", text_color=self.TEXT_LIGHT, font=("Arial", 14), command=self.buscar_rom)
        self.btn_rom.pack(side="right")

        # Entrada de Fichero de la Memory Card (Dongle)
        ctk.CTkLabel(self.main_frame, text="3. SECURITY DONGLE FILE (.BIN):", font=("Impact", 12), text_color=self.TEXT_LIGHT).pack(anchor="w", padx=20, pady=(10, 2))
        self.mcard_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.mcard_frame.pack(fill="x", padx=20, pady=5)
        self.entry_mcard = ctk.CTkEntry(self.mcard_frame, fg_color="#0D1117", border_color="#4A5568", text_color=self.TEXT_LIGHT, placeholder_text="Selecciona tarjeta .bin...")
        self.entry_mcard.pack(side="left", fill="x", expand=True, padx=(0, 10))
        if self.config["last_mcard_path"]: self.entry_mcard.insert(0, self.config["last_mcard_path"])
        self.btn_mcard = ctk.CTkButton(self.mcard_frame, text="🗁", width=45, fg_color="#2D3748", hover_color="#4A5568", text_color=self.TEXT_LIGHT, font=("Arial", 14), command=self.buscar_mcard)
        self.btn_mcard.pack(side="right")

        # BOTÓN ACCIÓN ARCADE LAUNCHER
        self.btn_launch = ctk.CTkButton(
            self, 
            text="⚡ INITIALIZE CABINET & LAUNCH ARCADE SYSTEM ⚡", 
            font=("Impact", 16), 
            height=54, 
            fg_color=self.ACCENT_YELLOW, 
            text_color="#10141D",
            hover_color="#FFFFFF", 
            corner_radius=4,
            command=self.ejecutar_lanzamiento_oficial
        )
        self.btn_launch.pack(pady=(15, 20), padx=25, fill="x")

        self.game_real_title = ""
        self.actualizar_info_juego()

    def crear_fila_ruta(self, master, label_text, config_key, command_func, row):
        ctk.CTkLabel(master, text=label_text, font=("Arial", 11, "bold"), text_color=self.TEXT_LIGHT).grid(row=row, column=0, sticky="w", padx=15, pady=6)
        entry = ctk.CTkEntry(master, width=480, fg_color="#0D1117", border_color="#4A5568", text_color=self.TEXT_LIGHT)
        entry.grid(row=row, column=1, padx=10, pady=6, sticky="ew")
        if self.config[config_key]:
            entry.insert(0, self.config[config_key])
        btn = ctk.CTkButton(master, text="Browse", width=85, fg_color="#2D3748", text_color=self.TEXT_LIGHT, hover_color="#4A5568", font=("Arial", 11, "bold"), command=command_func)
        btn.grid(row=row, column=2, padx=15, pady=6)
        setattr(self, f"entry_{config_key}", entry)

    def cargar_config_global(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.config.update(json.load(f))
            except: pass

    def guardar_config_global(self):
        for key in ["pcsx2_path", "games_dir", "memcards_dir"]:
            entry_widget = getattr(self, f"entry_{key}", None)
            if entry_widget:
                self.config[key] = entry_widget.get()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)

    def cargar_logos_cabecera(self):
        # Carga del Logo 1 (logo.png)
        path_logo = obtener_ruta_recurso("logo.png")
        if os.path.exists(path_logo):
            img = Image.open(path_logo).convert("RGBA")
            self.logo_image = ctk.CTkImage(light_image=img, dark_image=img, size=(125, 125))
            self.logo_label.configure(image=self.logo_image, text="")

        # Carga del Logo 2 (LogoEmu.png) en la misma raíz
        path_emu = obtener_ruta_recurso("LogoEmu.png")
        if os.path.exists(path_emu):
            img_emu = Image.open(path_emu).convert("RGBA")
            self.logo_emu_image = ctk.CTkImage(light_image=img_emu, dark_image=img_emu, size=(125, 125))
            self.logo_emu_label.configure(image=self.logo_emu_image, text="")

    def listar_juegos_proverb(self):
        base = os.path.join(".", "proverb", "bin")
        if os.path.exists(base):
            return [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]
        return []

    def actualizar_info_juego(self, *args):
        game_id = self.combo_game_id.get()
        if not game_id or game_id == "Seleccionar ID...":
            return
            
        p = os.path.join(".", "proverb", "bin", game_id, "title.txt")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                lineas = f.readlines()
                titulo_encontrado = game_id
                for linea in lineas:
                    if "Title:" in linea:
                        titulo_encontrado = linea.replace("Title:", "").strip()
                        break
                self.game_real_title = titulo_encontrado
                self.lbl_game_title.configure(text=f"Juego Identificado: {self.game_real_title}")
        else:
            self.game_real_title = game_id
            self.lbl_game_title.configure(text="Título: No seleccionado")

        img_game_path = os.path.join(".", "proverb", "bin", game_id, f"{game_id}.png")
        if os.path.exists(img_game_path):
            try:
                img_mini = Image.open(img_game_path).convert("RGBA")
                self.game_mini_image = ctk.CTkImage(light_image=img_mini, dark_image=img_mini, size=(140, 105))
                self.lbl_miniature.configure(image=self.game_mini_image, text="")
            except:
                self.lbl_miniature.configure(image="", text="Error al cargar\nimagen")
        else:
            self.lbl_miniature.configure(image="", text="Imagen no\ndisponible")

    def buscar_emulador(self):
        p = filedialog.askopenfilename(filetypes=[("Emu", "pcsx2-qt.exe")])
        if p: self.actualizar_campo("pcsx2_path", p)

    def buscar_dir_juegos(self):
        p = filedialog.askdirectory()
        if p: self.actualizar_campo("games_dir", p)

    def buscar_dir_mcards(self):
        p = filedialog.askdirectory()
        if p: self.actualizar_campo("memcards_dir", p)

    def buscar_rom(self):
        p = filedialog.askopenfilename(filetypes=[("Juegos", "*.chd *.iso *.bin")])
        if p:
            self.entry_rom.delete(0, tk.END)
            self.entry_rom.insert(0, os.path.abspath(p))
            self.config["last_rom_path"] = os.path.abspath(p)
            self.guardar_config_global()

    def buscar_mcard(self):
        p = filedialog.askopenfilename(filetypes=[("Memory Card", "*.bin")])
        if p:
            self.entry_mcard.delete(0, tk.END)
            self.entry_mcard.insert(0, os.path.abspath(p))
            self.config["last_mcard_path"] = os.path.abspath(p)
            self.guardar_config_global()

    def actualizar_campo(self, key, value):
        entry = getattr(self, f"entry_{key}")
        entry.delete(0, tk.END)
        entry.insert(0, os.path.abspath(value))
        self.guardar_config_global()

    def ejecutar_lanzamiento_oficial(self):
        self.guardar_config_global()

        emu = self.config["pcsx2_path"]
        target_games_base = self.config["games_dir"]
        target_mcard_dir = self.config["memcards_dir"]
        
        game_id = self.combo_game_id.get()
        source_rom = self.entry_rom.get()
        source_mcard = self.entry_mcard.get()

        if not all([emu, target_games_base, target_mcard_dir, game_id, source_rom, source_mcard]) or game_id == "Seleccionar ID...":
            messagebox.showerror("Error", "Por favor rellena todos los campos del lanzador.")
            return

        source_proverb_elf = os.path.abspath(os.path.join(".", "proverb", "bin", game_id, "proverb.elf"))
        if not os.path.exists(source_proverb_elf):
            messagebox.showerror("Error", f"Falta el dongle de origen en:\n{source_proverb_elf}")
            return

        folder_name = "".join(c for c in self.game_real_title if c.isalnum() or c in (" ", "_", "-")).strip()
        if not folder_name:
            folder_name = game_id

        try:
            rom_filename = os.path.basename(source_rom)
            mcard_filename_clean = os.path.splitext(os.path.basename(source_mcard))[0]
            mcard_target_name = f"{mcard_filename_clean}.PS2"
            
            game_folder_path = os.path.join(target_games_base, folder_name)
            os.makedirs(game_folder_path, exist_ok=True)

            os.makedirs(target_mcard_dir, exist_ok=True)
            shutil.copy2(source_mcard, os.path.join(target_mcard_dir, mcard_target_name))

            final_rom_path = os.path.join(game_folder_path, rom_filename)
            if os.path.abspath(source_rom) != os.path.abspath(final_rom_path):
                shutil.copy2(source_rom, final_rom_path)
                
            final_proverb_path = os.path.join(game_folder_path, "proverb.elf")
            shutil.copy2(source_proverb_elf, final_proverb_path)

            acgame_path = os.path.join(target_games_base, f"{folder_name}.acgame")
            
            acgame_content = (
                "[game]\n"
                f"name={folder_name}\n"
                f"gameid={game_id}\n"
                "platform=256\n"
                "[data]\n"
                f"subdir={folder_name}\n"
                "elf=proverb.elf\n"
                f"dongle={mcard_target_name}\n"
                f"mediasrc={rom_filename}\n"
                "media=DVD\n"
            )
            
            with open(acgame_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(acgame_content)

            subprocess.Popen([emu, acgame_path], cwd=os.path.dirname(emu))

        except Exception as e:
            messagebox.showerror("Error Crítico", f"Ocurrió un error al procesar la estructura arcade:\n{e}")

if __name__ == "__main__":
    app = ViZoRLauncherFinal()
    app.mainloop()