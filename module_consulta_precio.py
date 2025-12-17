# module_consulta_precio.py (CÓDIGO CON MEJORA GRÁFICA Y RESPONSIVIDAD - FUENTES AJUSTADAS)

import customtkinter as ctk
from tkinter import messagebox
import sqlite3
from utils import setup_db, DB_NAME 

class ConsultaPrecioModule(ctk.CTkFrame):
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.conn = setup_db()
        self.create_widgets()
        self.focus_barcode_entry() 

    # =====================================================================================
    # ⭐ MÉTODO: OBTENER TASA BCV (Lógica inalterada)
    # =====================================================================================
    def _get_bcv_rate(self) -> float:
        """Obtiene la última tasa BCV registrada en la base de datos."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT tasa FROM TasasBCV ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            return result[0] if result else 1.0 
        except sqlite3.Error as e:
            print(f"Error DB al obtener tasa BCV: {e}")
            return 1.0

    def create_widgets(self):
        # Configuración del Grid principal para ser completamente responsive
        self.grid_columnconfigure(0, weight=1)
        # Fila 0 (Título) y Fila 2 (Input) tienen altura fija (weight=0)
        self.grid_rowconfigure((0, 2), weight=0) 
        # Fila 1 (Resultados) toma todo el espacio vertical restante (weight=1)
        self.grid_rowconfigure(1, weight=1) 

        # --- Cabecera y Resultados ---
        ctk.CTkLabel(self, 
                     text="💰 CONSULTOR DE PRECIOS", 
                     font=ctk.CTkFont(size=34, weight="bold")).grid(row=0, column=0, pady=(30, 10), sticky="n") # Fuente ajustada: 34
        
        result_frame = ctk.CTkFrame(self, fg_color="#292F38", corner_radius=15) 
        result_frame.grid(row=1, column=0, sticky="nsew", padx=60, pady=20) 
        
        # Configuración del Grid interno de Resultados (para responsividad vertical)
        result_frame.grid_columnconfigure(0, weight=1)
        # Filas de Títulos (peso 0) y Filas de Datos (peso 1)
        result_frame.grid_rowconfigure((0, 2, 4), weight=0) 
        result_frame.grid_rowconfigure((1, 3, 5), weight=1) 

        # -----------------------------------------------------------
        # 1. Nombre del Producto
        # -----------------------------------------------------------
        ctk.CTkLabel(result_frame, text="PRODUCTO:", 
                     font=ctk.CTkFont(size=28, weight="bold"), # Fuente ajustada: 28
                     text_color="#B0BEC5").grid(row=0, column=0, pady=(25, 5), sticky="s")
        self.nombre_label = ctk.CTkLabel(result_frame, 
                                        text="ESPERANDO CÓDIGO...", 
                                        font=ctk.CTkFont(size=50, weight="bold"), # Fuente ajustada: 50
                                        text_color="#FFFFFF", wraplength=800)
        self.nombre_label.grid(row=1, column=0, padx=20, pady=10, sticky="nsew") 

        # -----------------------------------------------------------
        # 2. Precio en USD
        # -----------------------------------------------------------
        ctk.CTkLabel(result_frame, text="PRECIO DE VENTA (USD):", 
                     font=ctk.CTkFont(size=28, weight="bold"), # Fuente ajustada: 28
                     text_color="#B0BEC5").grid(row=2, column=0, pady=(25, 5), sticky="s")
        self.precio_label = ctk.CTkLabel(result_frame, 
                                         text="$0.00", 
                                         font=ctk.CTkFont(size=90, weight="bold"), # Fuente ajustada: 90
                                         text_color="#10B981") 
        self.precio_label.grid(row=3, column=0, padx=20, pady=(10, 20), sticky="nsew") 

        # -----------------------------------------------------------
        # 3. Precio en BOLÍVARES
        # -----------------------------------------------------------
        ctk.CTkLabel(result_frame, text="PRECIO DE VENTA (BS):", 
                     font=ctk.CTkFont(size=28, weight="bold"), # Fuente ajustada: 28
                     text_color="#B0BEC5").grid(row=4, column=0, pady=(25, 5), sticky="s")
        self.precio_bs_label = ctk.CTkLabel(result_frame, 
                                         text="Bs. 0.00", 
                                         font=ctk.CTkFont(size=70, weight="bold"), # Fuente ajustada: 70
                                         text_color="#F87171") 
        self.precio_bs_label.grid(row=5, column=0, padx=20, pady=(10, 25), sticky="nsew") 


        # --- Entrada de Código (Responsividad horizontal) ---
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.grid(row=2, column=0, sticky="ew", padx=60, pady=(10, 30))
        input_frame.grid_columnconfigure(0, weight=1)

        self.barcode_entry = ctk.CTkEntry(input_frame, 
                                          placeholder_text="🔍 ESCANEAR/INGRESAR CÓDIGO DE BARRAS (ENTER)",
                                          height=55, 
                                          font=ctk.CTkFont(size=22), # Fuente ajustada: 22
                                          corner_radius=10)
        self.barcode_entry.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.barcode_entry.bind('<Return>', self.search_price_by_event)
        
    
    # --- MÉTODOS DE LÓGICA (Inalterados) ---
    def focus_barcode_entry(self):
        """Establece el foco en la entrada de código de barras."""
        self.after(0, self.barcode_entry.focus_set)
        
    def reset_display(self, message="ESPERANDO CÓDIGO..."):
        self.nombre_label.configure(text=message, text_color="#FFFFFF")
        self.precio_label.configure(text="$0.00", text_color="#10B981")
        self.precio_bs_label.configure(text="Bs. 0.00", text_color="#F87171") 
        self.focus_barcode_entry()
        
    def search_price_by_event(self, event):
        self.search_and_clear()

    def search_and_clear(self):
        barcode = self.barcode_entry.get().strip()
        
        if not barcode:
            self.reset_display("Ingrese un código de barras")
            return
        
        self.barcode_entry.delete(0, ctk.END)
        self.focus_barcode_entry()

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT nombre, precio_venta FROM Productos WHERE codigo_barras = ?", (barcode,))
            data = cursor.fetchone()

            if data:
                nombre, precio_venta = data
                
                tasa_bcv = self._get_bcv_rate()
                precio_bs = precio_venta * tasa_bcv
                
                formatted_bs = "N/A"
                try:
                    formatted_bs_str = "{:,.2f}".format(precio_bs)
                    formatted_bs = formatted_bs_str.replace(",", "_TEMP_").replace(".", ",").replace("_TEMP_", ".")
                except:
                    formatted_bs = f"{precio_bs:.2f}"
                
                self.nombre_label.configure(text=nombre, text_color="#FFFFFF")
                self.precio_label.configure(text=f"${precio_venta:.2f}", text_color="#10B981")
                self.precio_bs_label.configure(text=f"Bs. {formatted_bs}", text_color="#F87171")
                
                if tasa_bcv == 1.0:
                    self.precio_bs_label.configure(text="Bs. N/A (Tasa no disponible)", text_color="#FFD700")

            else:
                self.nombre_label.configure(text=f"¡PRODUCTO NO ENCONTRADO! ({barcode})", text_color="#EF4444") 
                self.precio_label.configure(text="N/D", text_color="#EF4444")
                self.precio_bs_label.configure(text="N/D", text_color="#EF4444") 
                
        except Exception as e:
            messagebox.showerror("Error DB", f"Error de búsqueda: {e}")
            self.reset_display("ERROR DE BASE DE DATOS")