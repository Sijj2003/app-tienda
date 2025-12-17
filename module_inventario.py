# module_inventario.py (CÓDIGO MODIFICADO Y SIN REFERENCIAS A PROVEEDOR)

import customtkinter as ctk
from tkinter import messagebox, Toplevel, simpledialog, ttk 
import sqlite3
import datetime
import re 

from utils import setup_db, verify_password, DB_NAME 

# ===================================================================
# --- NUEVA CLASE: VENTANA MODAL DE AUTENTICACIÓN (InventoryAdminAuthWindow) ---
# ===================================================================

class InventoryAdminAuthWindow(ctk.CTkToplevel):
    """Ventana modal de autenticación de administrador para acciones dentro del inventario."""
    def __init__(self, master, success_callback):
        super().__init__(master)
        self.title("🔑 Autorización de Administrador")
        self.success_callback = success_callback 
        
        self.transient(master) 
        self.grab_set() 
        
        # Dimensiones y centrado de la ventana (550x350)
        window_width = 550
        window_height = 350
        self.geometry(f"{window_width}x{window_height}")
        self.resizable(False, False)
        
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')

        self.create_widgets()
        self.focus_force() 
        self.after(1, self.password_entry.focus_set) # Foco instantáneo

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(self, 
                     text="Se requiere autenticación de administrador", 
                     font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, pady=(40, 0), sticky="s")

        ctk.CTkLabel(self, 
                     text="Ingrese la contraseña:", 
                     font=ctk.CTkFont(size=20)).grid(row=1, column=0, pady=(10, 5), sticky="s")
        
        self.password_entry = ctk.CTkEntry(self, 
                                          width=300, 
                                          height=45, 
                                          show="*", 
                                          font=ctk.CTkFont(size=20))
        self.password_entry.grid(row=2, column=0, pady=(0, 10), sticky="n")

        ctk.CTkButton(self, 
                      text="Acceder (Enter)", 
                      font=ctk.CTkFont(size=22, weight="bold"),
                      width=200, 
                      height=50,
                      command=self.check_password).grid(row=3, column=0, pady=(10, 30), sticky="n")

        self.password_entry.bind('<Return>', lambda event=None: self.check_password())

    def check_password(self):
        password = self.password_entry.get().strip()
        
        if verify_password(password):
            self.destroy()
            self.success_callback() # Ejecuta el siguiente paso (abrir la búsqueda de código, por ejemplo)
        else:
            messagebox.showerror("Error de Contraseña", "Contraseña incorrecta. Inténtelo de nuevo.", parent=self)
            self.password_entry.delete(0, ctk.END)
            self.password_entry.focus_set()


# ===================================================================
# --- 1. VENTANA MODAL PARA AÑADIR PRODUCTO (ProductFormWindow) ---
# ===================================================================

class ProductFormWindow(ctk.CTkToplevel):
    def __init__(self, master, conn, load_callback):
        super().__init__(master)
        self.title("➕ Añadir Nuevo Producto")
        self.conn = conn
        self.load_callback = load_callback
        
        self.transient(master)
        self.grab_set() 
        self.geometry("600x650") 
        self.resizable(False, False)

        self.update_idletasks()
        window_width = 600
        window_height = 650
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')

        self.font_size_label = 24
        self.font_size_entry = 20
        self.font_size_button = 24
        
        self.codigo_barras = None 
        self.create_widgets()
        self.show_step1_barcode() 
        self.focus_force() 

    def create_widgets(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.entries = {}
        
    def _clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_step1_barcode(self):
        self._clear_main_frame()
        
        ctk.CTkLabel(self.main_frame, 
                     text="Paso 1: Ingrese Código de Barras", 
                     font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(50, 20))
        
        ctk.CTkLabel(self.main_frame, 
                     text="Código de Barras:", 
                     font=ctk.CTkFont(size=self.font_size_label)).pack(pady=5, padx=20, anchor="w")
        
        self.barcode_entry = ctk.CTkEntry(self.main_frame, 
                                          width=450, 
                                          height=40, 
                                          font=ctk.CTkFont(size=self.font_size_entry))
        self.barcode_entry.pack(pady=(0, 20))
        
        ctk.CTkButton(self.main_frame, 
                      text="Continuar (Enter)", 
                      font=ctk.CTkFont(size=self.font_size_button), 
                      width=200, height=50,
                      command=self.process_barcode).pack(pady=20)
        
        self.barcode_entry.bind('<Return>', lambda event=None: self.process_barcode())
        self.after(100, self.barcode_entry.focus_set)
        
    def process_barcode(self):
        code = self.barcode_entry.get().strip()
        if not code:
            messagebox.showerror("Error", "El Código de Barras no puede estar vacío.", parent=self)
            return
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM Productos WHERE codigo_barras = ?", (code,))
            if cursor.fetchone():
                messagebox.showerror("Error", f"El código de barras '{code}' ya está registrado.", parent=self)
                return
        except Exception as e:
            messagebox.showerror("Error DB", f"Error de verificación: {e}", parent=self)
            return

        self.codigo_barras = code
        self.show_step2_form()

    def show_step2_form(self):
        self._clear_main_frame()
        
        form_frame = ctk.CTkScrollableFrame(self.main_frame, 
                                            label_text=f"Paso 2: Detalles del Producto | Cód: {self.codigo_barras}", 
                                            label_font=ctk.CTkFont(size=self.font_size_label, weight="bold"))
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        fields = [
            ("Nombre del Producto:", "nombre"),
            ("Bultos/Cajas en Stock:", "stock_bultos"),
            ("Unidades por Bulto:", "unidades_por_bulto"),
            ("Precio de Bulto (USD):", "precio_bulto"),
            ("Porcentaje de Ganancia (%):", "porcentaje_ganancia"),
            # CAMBIO: Eliminado el campo Proveedor
            ("Descripción (Opcional):", "descripcion"),
        ]

        for i, (label_text, key) in enumerate(fields):
            ctk.CTkLabel(form_frame, text=label_text, font=ctk.CTkFont(size=self.font_size_label)).pack(pady=(15, 5), padx=20, anchor="w")
            entry = ctk.CTkEntry(form_frame, width=500, height=40, font=ctk.CTkFont(size=self.font_size_entry))
            entry.pack(pady=(0, 10), padx=20)
            self.entries[key] = entry
        
        ctk.CTkLabel(form_frame, text="Precio de Venta por Unidad (Automático):", font=ctk.CTkFont(size=self.font_size_label)).pack(pady=(15, 5), padx=20, anchor="w")
        self.precio_venta_label = ctk.CTkLabel(form_frame, text="$0.00", font=ctk.CTkFont(size=30, weight="bold"), text_color="green")
        self.precio_venta_label.pack(pady=(0, 20), padx=20)
            
        ctk.CTkButton(self.main_frame, text="✅ Guardar Producto (Enter)", 
                      font=ctk.CTkFont(size=self.font_size_button, weight="bold"), 
                      width=250, height=50,
                      command=self.save_product).pack(pady=(10, 20))
        
        self.bind_all('<Return>', lambda event=None: self.save_product() if self.entries.get('nombre') else None)
        
        self._monitor_entries()
        self.entries['nombre'].focus_set()

    def _monitor_entries(self):
        for key in ['unidades_por_bulto', 'precio_bulto', 'porcentaje_ganancia']:
            self.entries[key].bind('<KeyRelease>', lambda event=None: self.calculate_price())
        self.calculate_price() 

    def calculate_price(self):
        try:
            unidades = float(self.entries['unidades_por_bulto'].get().replace(',', '.') or 0)
            precio_bulto = float(self.entries['precio_bulto'].get().replace(',', '.') or 0)
            # La ganancia_pct es el porcentaje (ej. 20.0), no el factor (ej. 0.20)
            ganancia_pct = float(self.entries['porcentaje_ganancia'].get().replace(',', '.') or 0)
        except ValueError:
            self.precio_venta_label.configure(text="$[ERROR]")
            return

        if unidades > 0 and precio_bulto >= 0:
            precio_unidad_compra = precio_bulto / unidades
            
            # --- FÓRMULA DE MARGEN DE VENTA ACTUALIZADA ---
            if ganancia_pct >= 100:
                # Evitar división por cero o negativo
                self.precio_venta_label.configure(text="$[ERROR: Margen >= 100%]")
                self.calculated_price = 0.0
                self.calculated_cost = precio_unidad_compra
                return

            # Paso 1: Obtener el factor de margen de venta (1 - Margen_Ganancia/100)
            margen_venta_factor = (100 - ganancia_pct) / 100.0
            
            # Paso 2: Calcular el precio de venta (Costo_Unitario / Factor)
            precio_venta_unidad = precio_unidad_compra / margen_venta_factor
            # -----------------------------------------------
            
            self.precio_venta_label.configure(text=f"${precio_venta_unidad:.2f}")
            self.calculated_price = precio_venta_unidad
            self.calculated_cost = precio_unidad_compra
        else:
            self.precio_venta_label.configure(text="$0.00")
            self.calculated_price = 0.0
            self.calculated_cost = 0.0

    def _validate_input(self, data):
        required = ["nombre", "stock_bultos", "unidades_por_bulto", "precio_bulto", "porcentaje_ganancia"]
        for key in required:
            if not data.get(key) or str(data[key]).strip() == "": # Uso .get(key) porque 'proveedor' ya no está en data
                messagebox.showerror("Error de Validación", f"El campo '{key.replace('_', ' ').title()}' es obligatorio.", parent=self)
                return False

        numeric_fields = ["stock_bultos", "unidades_por_bulto", "precio_bulto", "porcentaje_ganancia"]
        for key in numeric_fields:
            value = str(data[key]).replace(',', '.')
            if not re.match(r"^\d*\.?\d*$", value):
                messagebox.showerror("Error de Validación", f"El campo '{key.replace('_', ' ').title()}' debe ser un número válido.", parent=self)
                return False
            
            data[key] = float(value)
            if key in ["stock_bultos", "unidades_por_bulto"] and data[key] <= 0:
                 messagebox.showerror("Error de Validación", f"El campo '{key.replace('_', ' ').title()}' debe ser mayor que cero.", parent=self)
                 return False
            if key in ["porcentaje_ganancia"] and data[key] < 0:
                 messagebox.showerror("Error de Validación", f"El campo '{key.replace('_', ' ').title()}' no puede ser negativo.", parent=self)
                 return False

        return True

    def save_product(self):
        data = {k: v.get().strip() for k, v in self.entries.items()}
        
        if not self._validate_input(data):
            return
        
        stock_unidades_total = int(data['stock_bultos'] * data['unidades_por_bulto'])
        self.calculate_price() 
        
        precio_venta = self.calculated_price
        precio_compra = self.calculated_cost
        
        if precio_venta <= 0:
            messagebox.showerror("Error de Cálculo", "El precio de venta calculado es cero o negativo. Revise las unidades y el precio del bulto.", parent=self)
            return

        try:
            cursor = self.conn.cursor()
            fecha = datetime.date.today().strftime("%Y-%m-%d")
            
            # CAMBIO: Eliminada la columna "proveedor" del INSERT
            cursor.execute("""
                INSERT INTO Productos (codigo_barras, nombre, descripcion, precio_compra, precio_venta, stock, fecha_registro, stock_bultos, unidades_por_bulto, precio_bulto, porcentaje_ganancia)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.codigo_barras, 
                  data['nombre'], 
                  data.get('descripcion', ''), 
                  precio_compra, 
                  precio_venta, 
                  stock_unidades_total, 
                  fecha,
                  data['stock_bultos'],
                  data['unidades_por_bulto'],
                  data['precio_bulto'],
                  data['porcentaje_ganancia']))
                
            self.conn.commit()
            messagebox.showinfo("Éxito", f"Producto '{data['nombre']}' añadido correctamente.\nPrecio Venta por Unidad: ${precio_venta:.2f}")
            
            self.load_callback() 
            self.destroy()

        except sqlite3.IntegrityError:
            messagebox.showerror("Error DB", "El código de barras ya existe (esto no debería ocurrir).")
        except Exception as e:
            messagebox.showerror("Error DB", f"Error al guardar datos: {e}")


# ===================================================================
# --- 2. VENTANA MODAL DE BÚSQUEDA GENÉRICA (BarcodeSearchWindow) ---
# ===================================================================

class BarcodeSearchWindow(ctk.CTkToplevel):
    """Ventana modal para buscar un producto por código de barras y ejecutar un callback."""
    def __init__(self, master, conn, success_callback):
        super().__init__(master)
        self.title("🔍 Buscar Producto por Código de Barras")
        self.conn = conn
        self.success_callback = success_callback 
        
        self.transient(master)
        self.grab_set() 
        self.geometry("450x250") 
        self.resizable(False, False)

        self.update_idletasks()
        window_width = 450
        window_height = 250
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')
        self.grid_columnconfigure(0, weight=1)
        self.focus_force() 

        ctk.CTkLabel(self, 
                     text="Escanee o Ingrese Código de Barras", 
                     font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=20)
        
        self.barcode_entry = ctk.CTkEntry(self, 
                                          width=350, 
                                          height=40, 
                                          font=ctk.CTkFont(size=18))
        self.barcode_entry.grid(row=1, column=0, padx=20, pady=(0, 20))
        
        ctk.CTkButton(self, 
                      text="Buscar (Enter)", 
                      font=ctk.CTkFont(size=18, weight="bold"),
                      width=150,
                      height=40,
                      command=self.search_product).grid(row=2, column=0, pady=10)
        
        self.barcode_entry.bind('<Return>', lambda event=None: self.search_product())
        
        # --- AJUSTE DE FOCO ---
        self.after(1, self.barcode_entry.focus_set)
        
    def search_product(self):
        barcode = self.barcode_entry.get().strip()
        if not barcode:
            messagebox.showerror("Error", "Debe ingresar un código de barras.", parent=self)
            self.barcode_entry.focus_set() 
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM Productos WHERE codigo_barras = ?", (barcode,))
            result = cursor.fetchone()

            if result:
                product_id = result[0]
                self.success_callback(product_id) 
                self.destroy()
            else:
                messagebox.showerror("No Encontrado", f"No se encontró un producto con el código: {barcode}", parent=self)
                self.barcode_entry.delete(0, ctk.END)
                self.barcode_entry.focus_set()

        except Exception as e:
            messagebox.showerror("Error DB", f"Error de búsqueda: {e}", parent=self)
            self.barcode_entry.focus_set()


# ===================================================================
# --- 3. VENTANA MODAL PARA EDITAR PRODUCTO (ProductEditWindow) ---
# ===================================================================

class ProductEditWindow(ctk.CTkToplevel):
    """Ventana para editar la información de un producto existente."""
    def __init__(self, master, conn, product_id, load_callback):
        super().__init__(master)
        self.title(f"✏️ Editar Producto ID: {product_id}")
        self.conn = conn
        self.product_id = product_id
        self.load_callback = load_callback
        
        self.transient(master)
        self.grab_set() 
        self.geometry("650x750") 
        self.resizable(False, False)

        self.update_idletasks()
        window_width = 650
        window_height = 750
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')

        self.font_size_label = 24
        self.font_size_entry = 20
        self.font_size_button = 24
        
        self.original_stock_bultos = 0.0 
        self.original_codigo_barras = ""
        self.calculated_price = 0.0
        self.calculated_cost = 0.0
        
        if not self._load_product_data():
             self.destroy()
             return

        self.create_widgets()
        self.focus_force() 
        self.after(1, lambda: self.entries['nombre'].focus_set())

    def _load_product_data(self):
        try:
            cursor = self.conn.cursor()
            # CAMBIO: Eliminada la columna "proveedor" de la consulta
            cursor.execute("""
                SELECT 
                    codigo_barras, nombre, descripcion, precio_compra, precio_venta, stock, 
                    stock_bultos, unidades_por_bulto, precio_bulto, porcentaje_ganancia
                FROM Productos WHERE id = ?
            """, (self.product_id,))
            
            data = cursor.fetchone()

            if not data:
                messagebox.showerror("Error", f"No se encontró el producto con ID {self.product_id}.")
                return False
            
            # CAMBIO: Ajustados los índices tras eliminar 'proveedor'
            self.product_data = {
                'codigo_barras': data[0], 
                'nombre': data[1], 
                'descripcion': data[2], 
                'precio_compra': data[3],
                'precio_venta': data[4], 
                'stock': data[5], 
                'stock_bultos': data[6], 
                'unidades_por_bulto': data[7], 
                'precio_bulto': data[8], 
                'porcentaje_ganancia': data[9] 
            }
            self.original_stock_bultos = self.product_data['stock_bultos']
            self.original_codigo_barras = self.product_data['codigo_barras']
            
            return True
            
        except Exception as e:
            messagebox.showerror("Error DB", f"Error al cargar datos del producto: {e}")
            return False

    def create_widgets(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        form_frame = ctk.CTkScrollableFrame(self.main_frame, 
                                            label_text=f"Editando Cód: {self.original_codigo_barras}", 
                                            label_font=ctk.CTkFont(size=self.font_size_label, weight="bold"))
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.entries = {}
        
        fields = [
            ("Código de Barras (No Editable):", "codigo_barras", True),
            ("Nombre del Producto:", "nombre", False),
            ("Bultos/Cajas en Stock (NO EDITABLE, Actual: {self.original_stock_bultos:.2f}):", "stock_bultos", True), 
            ("Unidades por Bulto:", "unidades_por_bulto", False),
            ("Precio de Bulto (USD):", "precio_bulto", False),
            ("Porcentaje de Ganancia (%):", "porcentaje_ganancia", False),
            # CAMBIO: Eliminado el campo Proveedor
            ("Descripción (Opcional):", "descripcion", False),
        ]

        for i, (label_text, key, disabled) in enumerate(fields):
            
            display_label_text = label_text.format(self=self)
            
            ctk.CTkLabel(form_frame, text=display_label_text, font=ctk.CTkFont(size=self.font_size_label)).pack(pady=(15, 5), padx=20, anchor="w")
            
            if key == 'codigo_barras':
                 ctk.CTkLabel(form_frame, text=self.product_data['codigo_barras'], font=ctk.CTkFont(size=self.font_size_entry, weight="bold"), text_color="grey").pack(pady=(0, 10), padx=20, anchor="w")
                 continue

            entry = ctk.CTkEntry(form_frame, width=500, height=40, font=ctk.CTkFont(size=self.font_size_entry))
            entry.pack(pady=(0, 10), padx=20)
            self.entries[key] = entry

            value = self.product_data.get(key, "")
            if isinstance(value, float):
                 if key == 'stock_bultos':
                    entry.insert(0, f"{value:.2f}".replace('.', ','))
                 else:
                    entry.insert(0, f"{value}".replace('.', ','))
            else:
                 entry.insert(0, str(value))
            
            if disabled:
                entry.configure(state='disabled')
                
        ctk.CTkLabel(form_frame, text="Precio de Venta por Unidad (Automático):", font=ctk.CTkFont(size=self.font_size_label)).pack(pady=(15, 5), padx=20, anchor="w")
        self.precio_venta_label = ctk.CTkLabel(form_frame, text="$0.00", font=ctk.CTkFont(size=30, weight="bold"), text_color="green")
        self.precio_venta_label.pack(pady=(0, 20), padx=20)
            
        ctk.CTkButton(self.main_frame, text="💾 Guardar Cambios (Enter)", 
                      font=ctk.CTkFont(size=self.font_size_button, weight="bold"), 
                      width=250, height=50,
                      command=self.save_product_changes).pack(pady=(10, 20))
        
        self.bind('<Return>', lambda event=None: self.save_product_changes())
        self._monitor_entries()

    def _monitor_entries(self):
        for key in ['unidades_por_bulto', 'precio_bulto', 'porcentaje_ganancia']:
            if key in self.entries:
                self.entries[key].bind('<KeyRelease>', lambda event=None: self.calculate_price())
        self.calculate_price() 

    def calculate_price(self):
        try:
            unidades = float(self.entries['unidades_por_bulto'].get().replace(',', '.') or 0)
            precio_bulto = float(self.entries['precio_bulto'].get().replace(',', '.') or 0)
            # La ganancia_pct es el porcentaje (ej. 20.0), no el factor (ej. 0.20)
            ganancia_pct = float(self.entries['porcentaje_ganancia'].get().replace(',', '.') or 0)
        except ValueError:
            self.precio_venta_label.configure(text="$[ERROR]")
            return

        if unidades > 0 and precio_bulto >= 0:
            precio_unidad_compra = precio_bulto / unidades
            
            # --- FÓRMULA DE MARGEN DE VENTA ACTUALIZADA ---
            if ganancia_pct >= 100:
                # Evitar división por cero o negativo
                self.precio_venta_label.configure(text="$[ERROR: Margen >= 100%]")
                self.calculated_price = 0.0
                self.calculated_cost = precio_unidad_compra
                return
                
            # Paso 1: Obtener el factor de margen de venta (1 - Margen_Ganancia/100)
            margen_venta_factor = (100 - ganancia_pct) / 100.0
            
            # Paso 2: Calcular el precio de venta (Costo_Unitario / Factor)
            precio_venta_unidad = precio_unidad_compra / margen_venta_factor
            # -----------------------------------------------
            
            self.precio_venta_label.configure(text=f"${precio_venta_unidad:.2f}")
            self.calculated_price = precio_venta_unidad
            self.calculated_cost = precio_unidad_compra
        else:
            self.precio_venta_label.configure(text="$0.00")
            self.calculated_price = 0.0
            self.calculated_cost = 0.0
    
    def _validate_input(self, data):
        required = ["nombre", "unidades_por_bulto", "precio_bulto", "porcentaje_ganancia"]
        
        for key in required:
            if not data.get(key) or str(data[key]).strip() == "":
                messagebox.showerror("Error de Validación", f"El campo '{key.replace('_', ' ').title()}' es obligatorio.", parent=self)
                return False

        numeric_fields = ["unidades_por_bulto", "precio_bulto", "porcentaje_ganancia"]
        for key in numeric_fields:
            value = str(data[key]).replace(',', '.')
            if not re.match(r"^\d*\.?\d*$", value):
                messagebox.showerror("Error de Validación", f"El campo '{key.replace('_', ' ').title()}' debe ser un número válido.", parent=self)
                return False
            
            data[key] = float(value)
            if key in ["unidades_por_bulto"] and data[key] <= 0:
                 messagebox.showerror("Error de Validación", f"El campo '{key.replace('_', ' ').title()}' debe ser mayor que cero.", parent=self)
                 return False
            if key in ["porcentaje_ganancia"] and data[key] < 0:
                 messagebox.showerror("Error de Validación", f"El campo '{key.replace('_', ' ').title()}' no puede ser negativo.", parent=self)
                 return False

        return True

    def save_product_changes(self):
        data = {k: v.get().strip() for k, v in self.entries.items() if k in self.entries and v.winfo_exists() and v.cget('state') != 'disabled'}
        
        if not self._validate_input(data):
            return
        
        unidades_por_bulto_new = data['unidades_por_bulto']
        stock_unidades_total = int(self.original_stock_bultos * unidades_por_bulto_new)

        self.calculate_price() 
        
        precio_venta = self.calculated_price
        precio_compra = self.calculated_cost
        
        if precio_venta <= 0:
            messagebox.showerror("Error de Cálculo", "El precio de venta calculado es cero o negativo. Revise las unidades y el precio del bulto.", parent=self)
            return

        try:
            cursor = self.conn.cursor()
            
            # CAMBIO: Eliminada la columna "proveedor" del UPDATE
            cursor.execute("""
                UPDATE Productos SET
                    nombre = ?, descripcion = ?, precio_compra = ?, precio_venta = ?, stock = ?, 
                    unidades_por_bulto = ?, precio_bulto = ?, porcentaje_ganancia = ?
                WHERE id = ?
            """, (
                  data['nombre'], 
                  data.get('descripcion', ''), 
                  precio_compra, 
                  precio_venta, 
                  stock_unidades_total, 
                  data['unidades_por_bulto'],
                  data['precio_bulto'], 
                  data['porcentaje_ganancia'], 
                  self.product_id))
                
            self.conn.commit()
            messagebox.showinfo("Éxito", f"Producto '{data['nombre']}' (ID: {self.product_id}) actualizado correctamente.\nNuevo Stock Total: {stock_unidades_total} unidades.")
            
            self.load_callback() 
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error DB", f"Error al actualizar datos: {e}")


# ===================================================================
# --- 4. VENTANA MODAL PARA ADICIÓN DE STOCK (StockAddWindow) ---
# ===================================================================

class StockAddWindow(ctk.CTkToplevel):
    """Ventana para añadir bultos al stock de un producto existente."""
    def __init__(self, master, conn, product_id, load_callback):
        super().__init__(master)
        self.conn = conn
        self.product_id = product_id
        self.load_callback = load_callback
        
        self.transient(master)
        self.grab_set() 
        self.geometry("550x450")
        self.resizable(False, False)

        self.update_idletasks()
        window_width = 550
        window_height = 450
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        self.font_size_label = 20
        self.font_size_entry = 18
        self.font_size_button = 22

        if not self._load_product_data():
             self.destroy()
             return
             
        self.title(f"📦 Añadir Stock | Cód: {self.product_data['codigo_barras']}")
        self.create_widgets()
        self.focus_force() 
        self.after(1, self.new_bulks_entry.focus_set)

    def _load_product_data(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    codigo_barras, nombre, stock, stock_bultos, unidades_por_bulto
                FROM Productos WHERE id = ?
            """, (self.product_id,))
            
            data = cursor.fetchone()

            if not data:
                messagebox.showerror("Error", f"No se encontró el producto con ID {self.product_id}.")
                return False
            
            self.product_data = {
                'codigo_barras': data[0], 
                'nombre': data[1], 
                'stock_unidades': data[2],
                'stock_bultos': data[3],
                'unidades_por_bulto': data[4]
            }
            return True
            
        except Exception as e:
            messagebox.showerror("Error DB", f"Error al cargar datos del producto: {e}")
            return False

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Info del Producto
        ctk.CTkLabel(main_frame, text="Producto:", font=ctk.CTkFont(size=self.font_size_label, weight="bold")).pack(pady=(10, 0), padx=20, anchor="w")
        ctk.CTkLabel(main_frame, text=self.product_data['nombre'], font=ctk.CTkFont(size=24, weight="bold"), text_color="blue").pack(pady=(0, 10), padx=20, anchor="w")
        
        ctk.CTkLabel(main_frame, 
                     text=f"Stock Actual (Bultos): {self.product_data['stock_bultos']:.2f}", 
                     font=ctk.CTkFont(size=self.font_size_label)).pack(pady=(5, 5), padx=20, anchor="w")
        
        ctk.CTkLabel(main_frame, 
                     text=f"Unidades por Bulto: {self.product_data['unidades_por_bulto']}", 
                     font=ctk.CTkFont(size=self.font_size_label)).pack(pady=(0, 20), padx=20, anchor="w")

        # Input de Stock
        ctk.CTkLabel(main_frame, 
                     text="Cantidad de Bultos a Añadir:", 
                     font=ctk.CTkFont(size=self.font_size_label, weight="bold")).pack(pady=(20, 5), padx=20, anchor="w")
        
        self.new_bulks_entry = ctk.CTkEntry(main_frame, 
                                            width=350, 
                                            height=40, 
                                            font=ctk.CTkFont(size=self.font_size_entry))
        self.new_bulks_entry.pack(pady=(0, 30))
        
        ctk.CTkButton(main_frame, text="➕ Guardar Nuevo Stock (Enter)", 
                      font=ctk.CTkFont(size=self.font_size_button, weight="bold"), 
                      width=250, height=50, fg_color="green", hover_color="#006400",
                      command=self.add_stock).pack(pady=(10, 20))
        
        self.new_bulks_entry.bind('<Return>', lambda event=None: self.add_stock())

    def add_stock(self):
        new_bulks_str = self.new_bulks_entry.get().strip().replace(',', '.')
        
        try:
            new_bulks = float(new_bulks_str)
        except ValueError:
            messagebox.showerror("Error de Entrada", "La cantidad de bultos a añadir debe ser un número válido.", parent=self)
            self.new_bulks_entry.focus_set()
            return
        
        if new_bulks <= 0:
            messagebox.showerror("Error de Entrada", "La cantidad de bultos a añadir debe ser mayor que cero.", parent=self)
            self.new_bulks_entry.focus_set()
            return

        # Calcular nuevo stock
        current_bultos = self.product_data['stock_bultos']
        unidades_por_bulto = self.product_data['unidades_por_bulto']
        
        new_total_bultos = current_bultos + new_bulks
        # El stock en unidades debe ser entero, por eso int()
        new_total_unidades = int(new_total_bultos * unidades_por_bulto)
        
        if not messagebox.askyesno(
            "Confirmar Adición de Stock",
            f"¿Confirma añadir {new_bulks} bulto(s) a '{self.product_data['nombre']}'?\n\n"
            f"Stock anterior (Bultos): {current_bultos:.2f}\n"
            f"Nuevo Stock Total (Bultos): {new_total_bultos:.2f}\n"
            f"Nuevo Stock Total (Unidades): {new_total_unidades}"
        ):
            self.new_bulks_entry.focus_set()
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE Productos SET
                    stock = ?, 
                    stock_bultos = ?
                WHERE id = ?
            """, (new_total_unidades, new_total_bultos, self.product_id))
                
            self.conn.commit()
            messagebox.showinfo("Éxito", f"Stock de '{self.product_data['nombre']}' actualizado correctamente.\nBultos añadidos: {new_bulks}\nNuevo Stock Total (Bultos): {new_total_bultos:.2f}")
            
            self.load_callback() 
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error DB", f"Error al actualizar stock: {e}")
            self.destroy()


# ===================================================================
# --- 5. VENTANA MODAL PARA ELIMINACIÓN (BarcodeDeleteWindow) ---
# ===================================================================

class BarcodeDeleteWindow(ctk.CTkToplevel):
    """Ventana modal para buscar un producto por código y luego eliminar con autenticación."""
    
    def __init__(self, master, conn, load_callback):
        super().__init__(master)
        self.title("🗑️ Eliminar Producto por Código de Barras")
        self.conn = conn
        self.load_callback = load_callback
        
        self.transient(master)
        self.grab_set() 
        self.geometry("450x250") 
        self.resizable(False, False)

        self.update_idletasks()
        window_width = 450
        window_height = 250
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, 
                     text="Escanee el Código de Barras", 
                     font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=20)
        
        self.barcode_entry = ctk.CTkEntry(self, 
                                          width=350, 
                                          height=40, 
                                          font=ctk.CTkFont(size=18))
        self.barcode_entry.grid(row=1, column=0, padx=20, pady=(0, 20))
        
        ctk.CTkButton(self, 
                      text="Buscar y Eliminar (Enter)", 
                      font=ctk.CTkFont(size=18, weight="bold"),
                      width=150,
                      height=40,
                      command=self.search_product_and_confirm).grid(row=2, column=0, pady=10)
        
        self.barcode_entry.bind('<Return>', lambda event=None: self.search_product_and_confirm())
        
        # --- AJUSTE DE FOCO ---
        self.after(1, self.barcode_entry.focus_set)
        self.focus_force()

    def search_product_and_confirm(self):
        barcode = self.barcode_entry.get().strip()
        if not barcode:
            messagebox.showerror("Error", "Debe ingresar un código de barras.", parent=self)
            self.barcode_entry.focus_set()
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, nombre FROM Productos WHERE codigo_barras = ?", (barcode,))
            result = cursor.fetchone()

            if not result:
                messagebox.showerror("No Encontrado", f"No se encontró un producto con el código: {barcode}", parent=self)
                self.barcode_entry.delete(0, ctk.END)
                self.barcode_entry.focus_set()
                return

            product_id, nombre = result

            # Pregunta de Confirmación
            confirm = messagebox.askyesno(
                "Confirmar Eliminación",
                f"¿Está seguro de que desea **eliminar** el producto '{nombre}' (Cód: {barcode})? Si presiona 'Sí', se le solicitará la clave de administrador."
            )

            if confirm:
                self._open_auth_for_deletion(product_id, nombre)
            else:
                self.destroy()

        except Exception as e:
            messagebox.showerror("Error DB", f"Error de búsqueda o proceso: {e}", parent=self)
            self.destroy() 

    def _open_auth_for_deletion(self, product_id, nombre):
        """Lanza la ventana de autenticación, pasando la función de eliminación como callback."""
        
        # Definimos el callback de éxito
        def delete_action():
            self._execute_deletion(product_id, nombre)
            
        # Lanzamos la ventana de autenticación
        InventoryAdminAuthWindow(self, delete_action)
        
    def _execute_deletion(self, product_id, nombre):
        """Realiza la eliminación si la autenticación fue exitosa."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM Productos WHERE id = ?", (product_id,))
            self.conn.commit()
            messagebox.showinfo("Éxito", f"Producto '{nombre}' eliminado correctamente.")
            self.load_callback() 
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error DB", f"Error al eliminar datos: {e}")
            self.destroy()

# ===================================================================
# --- 6. MÓDULO PRINCIPAL DE INVENTARIO (InventarioModule) ---
# ===================================================================

class InventarioModule(ctk.CTkFrame): 
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.conn = setup_db()
        
        # Helper para manejar la apariencia en modo oscuro/claro para colores no-CTk
        self.current_mode = ctk.get_appearance_mode() 
        
        self.create_widgets()
        self.load_inventory_list() 

    def create_widgets(self):
        ctk.CTkLabel(self, 
                     text="📦 Módulo de Inventario", 
                     font=ctk.CTkFont(size=40, weight="bold")).pack(pady=25) 

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # ------------------------------------------------------------------------
        # --- CONFIGURACIÓN DE ESTILO DEL TREEVIEW (CON MEJORAS DE ESPACIADO) ---
        # ------------------------------------------------------------------------
        style = ttk.Style(self)
        style.theme_use("default") 
        
        # Estilo de Fila (Datos) - FUENTE LIGERAMENTE REDUCIDA (16) y MENOR ALTO
        style.configure("Inventory.Treeview", 
                        rowheight=35, # REDUCIDO a 35 para MENOS CLUTTER/AGLUTINACIÓN
                        font=('Helvetica', 16), # REDUCIDO a 16 (Aún legible)
                        padding=(5, 5), # AÑADIDO: Padding interno para "aire" alrededor del texto
                        # Colores neutros (la fila alterna se define por tags)
                        background="#FFFFFF" if self.current_mode == "Light" else "#1A1A1A",
                        foreground="#000000" if self.current_mode == "Light" else "#FFFFFF",
                        fieldbackground="#FFFFFF" if self.current_mode == "Light" else "#1A1A1A",
                        borderwidth=0
                       )
        # Estilo de Encabezado - Se mantiene Grande y Negrita (18) para ser legible
        style.configure("Inventory.Treeview.Heading", 
                        font=('Helvetica', 18, 'bold'), 
                        background='#D3D3D3' if self.current_mode == "Light" else '#2C2C2C', 
                        foreground='#000000' if self.current_mode == "Light" else '#FFFFFF', 
                        relief="flat")
        
        style.layout("Inventory.Treeview", [('Inventory.Treeview.treearea', {'sticky': 'nswe'})])
        
        # CAMBIO: Eliminada la columna "Proveedor"
        columns = ("ID", "Código", "Nombre", "Stock", "Venta", "Compra", "Fecha", "Bultos", "UnidadesxBulto")
        self.inventory_tree = ttk.Treeview(main_frame, columns=columns, show='headings', style="Inventory.Treeview") 
        
        # RESPONSIVIDAD: Ajuste de anchos AUMENTADOS PARA LEER MEJOR EL TEXTO
        self.inventory_tree.column("ID", width=60, anchor='center', stretch=False) 
        # CAMBIO: Aumentado el ancho a 220 y Centrado
        self.inventory_tree.column("Código", width=220, anchor='center', stretch=False) 
        # CAMBIO: Centrado (Antes sin especificar)
        self.inventory_tree.column("Nombre", width=450, anchor='center', stretch=True) 
        self.inventory_tree.column("Stock", width=100, anchor='center', stretch=False) 
        # CAMBIO: Centrado (Antes 'e')
        self.inventory_tree.column("Venta", width=130, anchor='center', stretch=False) 
        # CAMBIO: Centrado (Antes 'e')
        self.inventory_tree.column("Compra", width=130, anchor='center', stretch=False) 
        # CAMBIO: Eliminada la configuración de ancho para "Proveedor"
        self.inventory_tree.column("Fecha", width=120, anchor='center', stretch=False) 
        self.inventory_tree.column("Bultos", width=100, anchor='center', stretch=False) 
        self.inventory_tree.column("UnidadesxBulto", width=120, anchor='center', stretch=False) 

        self.inventory_tree.heading("ID", text="ID DB")
        self.inventory_tree.heading("Código", text="Cód. Barras")
        self.inventory_tree.heading("Nombre", text="Nombre Producto")
        self.inventory_tree.heading("Stock", text="Stock (U.)")
        self.inventory_tree.heading("Venta", text="P. Venta (U.)")
        self.inventory_tree.heading("Compra", text="P. Compra (U.)")
        # CAMBIO: Eliminado el encabezado para "Proveedor"
        self.inventory_tree.heading("Fecha", text="F. Registro")
        self.inventory_tree.heading("Bultos", text="Stock (B.)")
        self.inventory_tree.heading("UnidadesxBulto", text="U. x Bulto")

        vsb = ttk.Scrollbar(main_frame, orient="vertical", command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscrollcommand=vsb.set)
        
        self.inventory_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=20)
        
        # BOTONES DE INTERFAZ (Ajustes previos)
        btn_font = ctk.CTkFont(size=22, weight="bold") 
        btn_width = 190 
        btn_height = 55 
        
        # Botones de Módulo de Inventario
        ctk.CTkButton(button_frame, text="➕ Añadir Prod.", font=btn_font, width=btn_width, height=btn_height, command=self.add_product).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="✏️ Editar Prod.", font=btn_font, width=btn_width, height=btn_height, command=self.edit_product).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="🗑️ Eliminar Prod.", font=btn_font, width=btn_width, height=btn_height, command=self.delete_product, fg_color="red", hover_color="#CC0000").pack(side="left", padx=10)
        
        ctk.CTkButton(button_frame, text="➕ Añadir Stock", font=btn_font, width=btn_width, height=btn_height, command=self.add_stock, fg_color="#33A1C9", hover_color="#2A85A4").pack(side="left", padx=10)
        
        ctk.CTkButton(button_frame, 
                      text="Recargar Lista", 
                      font=ctk.CTkFont(size=20), 
                      width=120, 
                      height=50, 
                      command=self.load_inventory_list).pack(side="left", padx=20) 

    def load_inventory_list(self):
        if not self.conn: return
        for item in self.inventory_tree.get_children(): self.inventory_tree.delete(item)
        
        # Colores fijos para el intercaado Azul/Verde (Modo Claro/Oscuro)
        blue_light = '#D9E9F0' 
        blue_dark = '#1A2F3A' 
        green_light = '#E6FAE6'
        green_dark = '#213A21'
        
        current_mode = ctk.get_appearance_mode()
        
        # Configuración de Tags para Alto Contraste y Fuente (16)
        # CAMBIO: Añadido 'bold' a la fuente para todas las filas
        self.inventory_tree.tag_configure('oddrow', 
                                          background=blue_dark if current_mode == "Dark" else blue_light,
                                          foreground='#FFFFFF' if current_mode == "Dark" else '#000000',
                                          font=('Helvetica', 16, 'bold')) 

        # CAMBIO: Añadido 'bold' a la fuente para todas las filas
        self.inventory_tree.tag_configure('evenrow', 
                                          background=green_dark if current_mode == "Dark" else green_light,
                                          foreground='#FFFFFF' if current_mode == "Dark" else '#000000',
                                          font=('Helvetica', 16, 'bold'))

        # Visualización de bajo inventario (Rojo y Negrita - Actualizado a font 16)
        self.inventory_tree.tag_configure('lowstock', foreground='red', font=('Helvetica', 16, 'bold')) 

        try:
            cursor = self.conn.cursor()
            # CAMBIO: Eliminada la columna "proveedor" de la consulta
            cursor.execute("""
                SELECT 
                    id, codigo_barras, nombre, stock, precio_venta, precio_compra, fecha_registro, stock_bultos, unidades_por_bulto 
                FROM Productos 
                ORDER BY nombre
            """)
            
            products = cursor.fetchall()
            
            for i, prod in enumerate(products):
                # 1. Etiqueta para Striping (Filas Alternas)
                tag_row = 'oddrow' if i % 2 != 0 else 'evenrow'
                
                # 2. Etiqueta para Alerta de Bajo Stock (< 10 unidades)
                tag_stock = 'lowstock' if prod[3] < 10 else '' 
                
                # Formato de precios (con separador de miles)
                precio_venta = f"${prod[4]:,.2f}" 
                precio_compra = f"${prod[5]:,.2f}"
                
                # Indices: 0-id, 1-código, 2-nombre, 3-stock, 4-p_venta, 5-p_compra, [6]-fecha, [7]-bultos, [8]-u_x_bulto
                self.inventory_tree.insert('', 'end', 
                                           values=(prod[0], prod[1], prod[2], prod[3], precio_venta, precio_compra, prod[6], f"{prod[7]:,.2f}", prod[8]), 
                                           tags=(prod[0], tag_row, tag_stock) 
                                          )
                                          
        except Exception as e:
            messagebox.showerror("Error DB", f"Error al cargar datos: {e}")

    def add_product(self):
        ProductFormWindow(self.master, self.conn, self.load_inventory_list)

    def _open_edit_window(self, product_id):
        """Función auxiliar que recibe el ID del producto y abre la ventana de edición."""
        ProductEditWindow(self.master, self.conn, product_id, self.load_inventory_list)

    def edit_product(self):
        """Abre la ventana de búsqueda por código de barras para editar el producto."""
        # Se requiere autenticación antes de abrir la búsqueda
        InventoryAdminAuthWindow(self.master, 
                                 lambda: BarcodeSearchWindow(self.master, self.conn, self._open_edit_window))

    def delete_product(self):
        """Inicia la eliminación del producto pidiendo la autenticación."""
        InventoryAdminAuthWindow(self.master, self._open_delete_search)
        
    def _open_delete_search(self):
        """Función auxiliar que se llama tras la autenticación exitosa para abrir la búsqueda de eliminación."""
        BarcodeDeleteWindow(self.master, self.conn, self.load_inventory_list)
        
    def _open_stock_add_window(self, product_id):
        """Función auxiliar que recibe el ID del producto y abre la ventana de adición de stock."""
        StockAddWindow(self.master, self.conn, product_id, self.load_inventory_list)

    def _open_stock_search(self):
        """Función auxiliar que abre la ventana de búsqueda de código de barras para añadir stock."""
        BarcodeSearchWindow(self.master, self.conn, self._open_stock_add_window)

    def add_stock(self):
        """Inicia el proceso de adición de stock pidiendo la autenticación de administrador."""
        InventoryAdminAuthWindow(self.master, self._open_stock_search)