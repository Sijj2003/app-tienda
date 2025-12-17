import customtkinter as ctk
import sqlite3
import datetime
import requests
from bs4 import BeautifulSoup
from tkinter import ttk, messagebox 
from utils import setup_db, DB_NAME 
import urllib3 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) 

# URL Oficial del BCV
BCV_RATE_URL = "https://www.bcv.org.ve/" 

# --- ESTILOS DE FUENTE Y COLORES ---
FONT_SIZE_ACCESSIBLE = 18 
ROW_HEIGHT_ACCESSIBLE = 40 
DARK_BLUE_SOBRIO = "#34495E"
TEAL_SOBRIO = "#16A085"
GRAY_LIGHT = "#ECF0F1"

class BCVRateModule(ctk.CTkFrame):
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller # Controlador MainApplication
        self.conn = setup_db()
        self.current_automatic_rate = None
        
        self.button_font = ctk.CTkFont(size=18, weight="bold")
        
        self.create_widgets()
        self.load_historical_rates()

    def create_widgets(self):
        # ----------------------------------------------------------------------
        # --- Configuración General del Layout ---
        # ----------------------------------------------------------------------
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1) # El historial de tasas ocupa el espacio restante

        # ----------------------------------------------------------------------
        # --- Cabecera del Módulo (Minimalista) ---
        # ----------------------------------------------------------------------
        ctk.CTkLabel(self, 
                     text="💲 GESTIÓN DE TASA BCV", 
                     font=ctk.CTkFont(size=30, weight="bold"),
                     text_color=DARK_BLUE_SOBRIO).grid(row=0, column=0, pady=(20, 5), padx=20, sticky="n")

        # ----------------------------------------------------------------------
        # --- 1. Panel de Tasa Automática (Minimalista) ---
        # ----------------------------------------------------------------------
        auto_panel = ctk.CTkFrame(self, fg_color=GRAY_LIGHT, corner_radius=10) # Fondo gris claro
        auto_panel.grid(row=1, column=0, padx=30, pady=15, sticky="ew")
        auto_panel.grid_columnconfigure(0, weight=1)
        auto_panel.grid_columnconfigure(1, weight=1)
        
        # Título de Tasa Oficial
        ctk.CTkLabel(auto_panel, 
                     text="Tasa BCV Oficial (Bs./$):", 
                     font=ctk.CTkFont(size=FONT_SIZE_ACCESSIBLE, weight="bold"),
                     text_color=DARK_BLUE_SOBRIO).grid(row=0, column=0, padx=15, pady=10, sticky="w")

        # Etiqueta de la Tasa
        self.auto_rate_label = ctk.CTkLabel(auto_panel, 
                                             text="Presione 'Cargar Oficial'...", 
                                             font=ctk.CTkFont(size=FONT_SIZE_ACCESSIBLE + 4, weight="bold"), # Más grande
                                             text_color="#F39C12") # Color de advertencia inicial
        self.auto_rate_label.grid(row=0, column=1, padx=15, pady=10, sticky="e")

        # Botón para Cargar y Guardar Tasa Oficial
        ctk.CTkButton(auto_panel, 
                      text="🌐 CARGAR y GUARDAR TASA OFICIAL BCV", 
                      command=self.fetch_and_save_automatic_rate,
                      font=ctk.CTkFont(size=20, weight="bold"),
                      height=50,
                      fg_color=DARK_BLUE_SOBRIO, # Azul sobrio principal
                      hover_color="#5D6D7E").grid(row=1, column=0, columnspan=2, pady=(15, 20), padx=15, sticky="ew")

        # ----------------------------------------------------------------------
        # --- 2. Panel de Ingreso Manual ---
        # ----------------------------------------------------------------------
        
        # Separador visual
        ctk.CTkLabel(self, text="— O INGRESE TASA MANUALMENTE —", 
                     font=ctk.CTkFont(size=16),
                     text_color="#7F8C8D").grid(row=2, column=0, pady=10) # Gris sobrio

        manual_panel = ctk.CTkFrame(self, fg_color="transparent")
        manual_panel.grid(row=3, column=0, padx=30, pady=10, sticky="ew")
        manual_panel.grid_columnconfigure(0, weight=1)
        manual_panel.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(manual_panel, 
                     text="Tasa de Cambio Manual (Bs./$):", 
                     font=ctk.CTkFont(size=FONT_SIZE_ACCESSIBLE, weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.rate_entry = ctk.CTkEntry(manual_panel, 
                                       width=250, 
                                       height=40, # Altura consistente
                                       font=ctk.CTkFont(size=FONT_SIZE_ACCESSIBLE))
        self.rate_entry.grid(row=0, column=1, padx=10, pady=10, sticky="e")
        
        ctk.CTkButton(manual_panel, 
                      text="💾 GUARDAR TASA MANUAL", 
                      command=self.save_manual_rate, 
                      font=ctk.CTkFont(size=20, weight="bold"),
                      height=50,
                      fg_color=TEAL_SOBRIO, # Verde Teal Sobrio (Acción de guardar)
                      hover_color="#138D75").grid(row=1, column=0, columnspan=2, pady=(10, 20), padx=10, sticky="ew")

        # ----------------------------------------------------------------------
        # --- 3. Panel de Historial de Tasas (Accesible) ---
        # ----------------------------------------------------------------------
        history_panel = ctk.CTkFrame(self, fg_color="transparent")
        history_panel.grid(row=4, column=0, padx=30, pady=(10, 20), sticky="nsew")
        history_panel.grid_columnconfigure(0, weight=1)
        history_panel.grid_rowconfigure(1, weight=1) # Treeview ocupa el espacio
        
        ctk.CTkLabel(history_panel, 
                     text="Historial de Tasas Registradas (Últimas 20)", 
                     font=ctk.CTkFont(size=FONT_SIZE_ACCESSIBLE, weight="bold"),
                     text_color=DARK_BLUE_SOBRIO).grid(row=0, column=0, pady=(10, 5), sticky="w")
        
        # Configuración del estilo Treeview (Duplicado del estilo accesible de VentasModule)
        self.style = ttk.Style(history_panel)
        self.style.theme_use("clam") 
        
        self.style.configure("BCV.Treeview.Heading", 
                            font=('Helvetica', FONT_SIZE_ACCESSIBLE, 'bold'), 
                            background=DARK_BLUE_SOBRIO, 
                            foreground="white") # Encabezados oscuros
        self.style.configure("BCV.Treeview", 
                            font=('Helvetica', FONT_SIZE_ACCESSIBLE - 2), # Fuente ligeramente menor que en Ventas
                            rowheight=ROW_HEIGHT_ACCESSIBLE - 5,
                            background="#ECF0F1", 
                            foreground="#2C3E50") # Gris claro, Texto oscuro
        self.style.map('BCV.Treeview', background=[('selected', '#7F8C8D')]) # Gris sobrio de selección
        
        self.rate_tree = ttk.Treeview(history_panel, columns=("Fecha", "Tasa"), show='headings', style="BCV.Treeview")
        
        self.rate_tree.heading("Fecha", text="FECHA y HORA")
        self.rate_tree.heading("Tasa", text="TASA (Bs./$)")
        
        self.rate_tree.column("Fecha", width=250, anchor="w", stretch=True)
        self.rate_tree.column("Tasa", width=150, anchor="center", stretch=False)
        
        vsb = ttk.Scrollbar(history_panel, orient="vertical", command=self.rate_tree.yview)
        self.rate_tree.configure(yscrollcommand=vsb.set)
        
        self.rate_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        vsb.grid(row=1, column=1, sticky='ns', pady=(0, 10))
        
        self.rate_entry.focus_set()


    # ===================================================================
    # --- API PÚBLICA (ESTÁTICA) Y CONSULTA DE DB (ACTUALIZADA) ---
    # ===================================================================
    
    # *** TODO EL CÓDIGO RESTANTE ABAJO PERMANECE SIN CAMBIOS DE LÓGICA ***

    @staticmethod
    def get_current_rate_api():
        """[API Pública] Obtiene la tasa de cambio actual del BCV desde la web."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(BCV_RATE_URL, headers=headers, timeout=10, verify=False)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            rate_container = soup.find('div', id='dolar') 

            if rate_container:
                rate_tag = rate_container.find('strong')

                if rate_tag:
                    rate_text = rate_tag.text.strip().replace(',', '.')
                    tasa = float(rate_text)
                    return tasa
                return None
            return None

        except requests.exceptions.RequestException as e:
            print(f"BCV API ERROR: No se pudo conectar/obtener la tasa. {e}")
            return None
        except ValueError:
            print("BCV API ERROR: El valor extraído no es un número válido.")
            return None

    # ⭐ FUNCIÓN CLAVE: Ahora es pública para que main_app la pueda consultar
    def get_latest_rate_from_db(self):
        """[API Pública] Obtiene la última tasa registrada en la base de datos."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT tasa FROM TasasBCV ORDER BY id DESC LIMIT 1") 
            latest_rate = cursor.fetchone()
            if latest_rate:
                return latest_rate[0]
            return None
        except Exception as e:
            print(f"Error al obtener la última tasa de la DB: {e}")
            return None
            
    # Función para uso interno del módulo (comparación)
    def _get_latest_db_rate(self):
        return self.get_latest_rate_from_db()


    # ===================================================================
    # --- MÉTODOS PARA ACTUALIZACIÓN PROGRAMADA Y UI (MODIFICADO) ---
    # ===================================================================

    def _update_ui_display(self, tasa):
        """Actualiza solo el label de la UI con la tasa obtenida."""
        self.current_automatic_rate = tasa
        # Color verde sobrio para éxito
        self.auto_rate_label.configure(text=f"Bs. {tasa:,.4f}", text_color=TEAL_SOBRIO) 

    def _handle_api_error_ui(self):
        """Maneja el estado de error en la UI."""
        # Color rojo oscuro para error
        self.auto_rate_label.configure(text="Error al obtener tasa.", text_color="#D35400")
    
    def check_and_update_rate_scheduled(self, new_tasa: float):
        """
        Llamado por el scheduler. Compara la nueva tasa con la última guardada.
        Si hay un cambio, actualiza la UI y guarda la tasa (genera reporte).
        """
        
        latest_db_rate = self._get_latest_db_rate()
        
        should_save = True
        
        if latest_db_rate is not None:
            # Comparamos si la diferencia absoluta es menor a una tolerancia pequeña (para floats)
            if abs(new_tasa - latest_db_rate) < 0.000001:
                should_save = False
            else:
                should_save = True
        
        # Siempre actualizamos el display dentro del módulo con el valor raspado
        self._update_ui_display(new_tasa)
        
        # Guarda solo si hubo un cambio (genera reporte de actualización)
        if should_save:
            print(f"BCV Auto Update: Tasa cambiada de {latest_db_rate} a {new_tasa}. Guardando nuevo registro.")
            # La función _save_rate_to_db ahora notifica al controlador para que actualice el sidebar
            self._save_rate_to_db(new_tasa, "Web (BCV Auto)", silent=True)
        else:
            print(f"BCV Auto Update: Tasa sin cambio ({new_tasa}). No se generó nuevo registro (reporte).")

    # ===================================================================
    # --- FUNCIONES DE BOTÓN (SE MANTIENEN IGUAL) ---
    # ===================================================================
    
    def fetch_automatic_rate(self):
        """
        [Botón] Obtiene la tasa usando la API y actualiza la UI, mostrando modal si hay error.
        """
        self.auto_rate_label.configure(text="Cargando...", text_color="#F39C12")
        self.update_idletasks()
        
        tasa = self.get_current_rate_api() # Llama al @staticmethod

        if tasa is not None:
            self._update_ui_display(tasa)
            return tasa
        else:
            self._handle_api_error_ui()
            messagebox.showerror("Error BCV", "Fallo al obtener la tasa oficial. Revise la conexión o el HTML del BCV.")
            return None
        
    def fetch_and_save_automatic_rate(self):
        """[Botón] Obtiene la tasa de la web usando la API y la guarda en la base de datos."""
        tasa = self.fetch_automatic_rate()
        if tasa is not None:
            self._save_rate_to_db(tasa, "Web (BCV Manual)", silent=False) 

    # ===================================================================
    # --- FUNCIONES DE BASE DE DATOS (LÓGICA INTACTA) ---
    # ===================================================================
    
    def _save_rate_to_db(self, tasa: float, source: str, silent=False):
        """Guarda la tasa de cambio en la base de datos y notifica al controlador."""
        try:
            fecha_registro = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO TasasBCV (tasa, fecha_registro)
                VALUES (?, ?)
            """, (tasa, fecha_registro))
            
            self.conn.commit()
            
            # ⭐ NOTIFICACIÓN AL CONTROLADOR (LÓGICA INTACTA)
            if self.controller and hasattr(self.controller, 'refresh_bcv_rate_from_db'):
                self.controller.refresh_bcv_rate_from_db()

            if not silent: 
                messagebox.showinfo("Éxito", f"Tasa de cambio guardada ({source}): 1$ = Bs. {tasa:,.4f}")
            
            self.load_historical_rates()
            
        except Exception as e:
            self.conn.rollback()
            if silent:
                print(f"ERROR DB [Auto Update]: Error al guardar la tasa: {e}")
            else:
                messagebox.showerror("Error DB", f"Error al guardar la tasa: {e}")
                
    def save_manual_rate(self):
        """Procesa y guarda la tasa ingresada manualmente."""
        tasa_str = self.rate_entry.get().strip().replace(',', '.')
        
        if not tasa_str:
            messagebox.showerror("Error", "Debe ingresar una tasa de cambio.")
            return

        try:
            tasa = float(tasa_str)
            if tasa <= 0:
                messagebox.showerror("Error", "La tasa debe ser un valor positivo.")
                return
            
            # La llamada a _save_rate_to_db manejará la notificación al controlador
            self._save_rate_to_db(tasa, "Manual", silent=False)
            self.rate_entry.delete(0, ctk.END)
            
        except ValueError:
            messagebox.showerror("Error", "Formato de tasa inválido. Use solo números.")

    def load_historical_rates(self):
        """Carga y muestra las últimas 20 tasas registradas."""
        for item in self.rate_tree.get_children():
            self.rate_tree.delete(item)
            
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT tasa, fecha_registro FROM TasasBCV ORDER BY id DESC LIMIT 20") 
            rates = cursor.fetchall()
            
            for tasa, fecha_registro in rates:
                self.rate_tree.insert('', 'end', values=(fecha_registro, f"Bs. {tasa:,.4f}"))
                
        except Exception as e:
            print(f"Error al cargar el historial de tasas: {e}")
            messagebox.showerror("Error DB", "Error al cargar el historial de tasas.")

    def reset_focus(self):
        self.rate_entry.focus_set()