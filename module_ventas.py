# module_ventas_minimalista.py (Mejora Gráfica Minimalista y Accesible)

import customtkinter as ctk
from tkinter import messagebox, simpledialog, ttk 
import sqlite3
import datetime
import json
import re

# Importamos las utilidades, incluyendo verify_password (Lógica Intacta)
from utils import setup_db, DB_NAME, verify_password 

# --- FUNCIÓN AUXILIAR: OBTENER TASA BCV (Lógica Intacta) ---
def get_latest_bcv_rate(conn):
    """Obtiene la tasa BCV más reciente registrada en la base de datos TasasBCV."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT tasa FROM TasasBCV ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Error al obtener la última tasa BCV: {e}")
        return None

# ===================================================================
# --- CLASE: VENTANA MODAL DE AUTENTICACIÓN (DISEÑO SOBRIO) ---
# ===================================================================

class VentasAdminAuthWindow(ctk.CTkToplevel):
    """Ventana modal de autenticación de administrador para acciones dentro del módulo de Ventas (Diseño Sobrio)."""
    def __init__(self, master, success_callback):
        super().__init__(master)
        self.title("🔑 Autorización de Administrador")
        self.success_callback = success_callback 
        
        self.transient(master) 
        self.grab_set() 
        
        window_width = 400 
        window_height = 280
        self.geometry(f"{window_width}x{window_height}")
        self.resizable(False, False)
        
        # Centrado en pantalla
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')

        self.create_widgets()
        self.focus_force() 
        self.after(1, self.password_entry.focus_set) 

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 4), weight=1) 
        
        # Título Sobrio
        ctk.CTkLabel(self, 
                     text="Se requiere autenticación", 
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#34495E").grid(row=1, column=0, padx=20, pady=(20, 10)) # Dark Grayish-Blue
        
        # Campo de Contraseña
        self.password_entry = ctk.CTkEntry(self, 
                                           placeholder_text="Contraseña de Administrador",
                                           width=280, 
                                           height=35, 
                                           font=ctk.CTkFont(size=16), 
                                           show="*")
        self.password_entry.grid(row=2, column=0, padx=20, pady=(10, 20))
        
        # Botón de Acceso
        ctk.CTkButton(self, 
                      text="Acceder", 
                      font=ctk.CTkFont(size=16, weight="bold"),
                      width=120,
                      height=35,
                      command=self.check_password,
                      fg_color="#34495E", # Sobrio
                      hover_color="#5D6D7E").grid(row=3, column=0, pady=(0, 20)) 

        self.password_entry.bind('<Return>', lambda event=None: self.check_password())

    # Lógica check_password se mantiene
    def check_password(self):
        # Lógica original...
        password = self.password_entry.get().strip()
        if verify_password(password):
            self.destroy()
            self.success_callback() 
        else:
            messagebox.showerror("Error de Contraseña", "Contraseña incorrecta. Inténtelo de nuevo.", parent=self)
            self.password_entry.delete(0, ctk.END)
            self.password_entry.focus_set()

# ===================================================================
# --- CLASE PRINCIPAL: VentasModule (DISEÑO MINIMALISTA Y ACCESIBLE) ---
# ===================================================================

class VentasModule(ctk.CTkFrame): 
    """Módulo principal de la Caja Registradora/Punto de Venta."""
    def __init__(self, parent, controller):
        super().__init__(parent) 
        self.controller = controller
        
        self.conn = setup_db()
        self.cart = {}
        self.transaction_id_counter = 0 
        self.final_total = 0.0 
        
        self.create_widgets()
        self.update_totals() 
        self.focus_barcode_entry()

    # MÉTODOS DE LÓGICA (se mantienen SIN CAMBIOS)
    def _get_bcv_rate(self) -> float:
        # Lógica original...
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT tasa FROM TasasBCV ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            if result:
                return result[0]
            return 1.0 
        except sqlite3.Error as e:
            print(f"Error DB al obtener tasa BCV: {e}")
            return 1.0

    def create_widgets(self):
        # ----------------------------------------------------------------------
        # --- Cabecera del Módulo y Frame Principal (Minimalista) ---
        # ----------------------------------------------------------------------
        ctk.CTkLabel(self, 
                     text="🛒 Punto de Venta", 
                     font=ctk.CTkFont(size=30, weight="bold"),
                     text_color="#34495E").pack(pady=(20, 5)) # Título sobrio

        main_frame = ctk.CTkFrame(self, fg_color="transparent") # Fondo transparente para minimalismo
        main_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        main_frame.grid_columnconfigure(0, weight=3) # Carrito más grande
        main_frame.grid_columnconfigure(1, weight=1) 
        main_frame.grid_rowconfigure(0, weight=1)
        
        # ----------------------------------------------------------------------
        # --- Panel de Carrito (Izquierda) ---
        # ----------------------------------------------------------------------
        cart_panel = ctk.CTkFrame(main_frame, fg_color="transparent")
        cart_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        cart_panel.grid_rowconfigure(1, weight=1) # El treeview ocupa todo el espacio
        cart_panel.grid_columnconfigure(0, weight=1)
        
        # 1. Entrada de Código de Barras (Minimalista)
        input_frame = ctk.CTkFrame(cart_panel, fg_color="#ECF0F1", corner_radius=8) # Fondo gris claro
        input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 10))
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.barcode_entry = ctk.CTkEntry(input_frame, 
                                          width=350, 
                                          height=50, 
                                          font=ctk.CTkFont(size=22), # Fuente más grande
                                          placeholder_text="Escanear Producto (ENTER)...")
        self.barcode_entry.grid(row=0, column=0, padx=15, pady=10, sticky="ew")
        self.barcode_entry.bind('<Return>', self.add_product_to_cart_by_event)
        
        ctk.CTkButton(input_frame, 
                      text="Añadir", 
                      width=100, 
                      height=50, 
                      font=ctk.CTkFont(size=18, weight="bold"),
                      fg_color="#16A085", # Verde Teal Sobrio
                      hover_color="#138D75",
                      command=self.add_product_to_cart).grid(row=0, column=1, padx=15, pady=10)
        

        # 2. Treeview del Carrito (ACCESIBLE: Fuente y Altura Grandes)
        self.style = ttk.Style(self)
        self.style.theme_use("default") 
        
        # Aumentar drásticamente el tamaño de la fuente y la altura de la fila
        FONT_SIZE_ACCESSIBLE = 18 
        ROW_HEIGHT_ACCESSIBLE = 40 
        
        self.style.configure("Cart.Treeview.Heading", font=('Helvetica', FONT_SIZE_ACCESSIBLE, 'bold'), background="#34495E", foreground="white") # Encabezados oscuros
        self.style.configure("Cart.Treeview", font=('Helvetica', FONT_SIZE_ACCESSIBLE), rowheight=ROW_HEIGHT_ACCESSIBLE) 
        self.style.map('Cart.Treeview', background=[('selected', '#7F8C8D')]) # Gris sobrio de selección
        
        cart_tree_container = ctk.CTkFrame(cart_panel)
        cart_tree_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 10))
        
        self.cart_tree = ttk.Treeview(cart_tree_container, 
                                      columns=("ID_Producto", "Nombre", "Precio_U", "Cantidad", "Subtotal"), 
                                      show='headings', 
                                      style="Cart.Treeview")
        
        # Ajustar ancho de columna para mejor lectura
        self.cart_tree.column("ID_Producto", width=50, anchor='center', stretch=False)
        self.cart_tree.column("Nombre", width=400, anchor='w', stretch=True)
        self.cart_tree.column("Precio_U", width=120, anchor='e', stretch=False)
        self.cart_tree.column("Cantidad", width=100, anchor='center', stretch=False)
        self.cart_tree.column("Subtotal", width=150, anchor='e', stretch=False)

        self.cart_tree.heading("ID_Producto", text="ID DB")
        self.cart_tree.heading("Nombre", text="PRODUCTO")
        self.cart_tree.heading("Precio_U", text="PRECIO U. ($)")
        self.cart_tree.heading("Cantidad", text="CANT.")
        self.cart_tree.heading("Subtotal", text="SUBTOTAL ($)")
        
        vsb = ttk.Scrollbar(cart_tree_container, orient="vertical", command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=vsb.set)
        
        self.cart_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")


        # ----------------------------------------------------------------------
        # --- Panel de Controles y Totales (Derecha) (Minimalista) ---
        # ----------------------------------------------------------------------
        control_panel = ctk.CTkFrame(main_frame, fg_color="transparent")
        control_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        control_panel.grid_columnconfigure(0, weight=1)

        # 1. Totales y Pago (Visualmente jerarquizados y sobrios)
        totals_frame = ctk.CTkFrame(control_panel, fg_color="#F8F9F9", corner_radius=10) # Fondo casi blanco
        totals_frame.pack(fill='x', padx=5, pady=(5, 15))
        
        # SUBTOTAL USD
        ctk.CTkLabel(totals_frame, 
                     text="SUBTOTAL:", 
                     font=ctk.CTkFont(size=18),
                     text_color="#7F8C8D").pack(pady=(10, 2), anchor='w', padx=10)
        self.subtotal_label = ctk.CTkLabel(totals_frame, 
                                           text="$0.00", 
                                           font=ctk.CTkFont(size=24, weight="bold"), 
                                           text_color="#7F8C8D") # Gris de bajo énfasis
        self.subtotal_label.pack(pady=(0, 10), anchor='e', padx=10) 
        
        # TOTAL FINAL USD (El más grande e importante, color azul sobrio)
        ctk.CTkLabel(totals_frame, 
                     text="TOTAL USD:", 
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(10, 5), anchor='w', padx=10)
        self.final_total_label = ctk.CTkLabel(totals_frame, 
                                              text="$0.00", 
                                              font=ctk.CTkFont(size=48, weight="bold"), 
                                              text_color="#3498DB") # Azul sobrio
        self.final_total_label.pack(pady=(0, 15), anchor='e', padx=10) 
        
        # TOTAL EN BOLÍVARES (Color de atención, no alarmante)
        ctk.CTkLabel(totals_frame, 
                     text="TOTAL BS. (BCV):", 
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(5, 5), anchor='w', padx=10)
        self.total_bs_label = ctk.CTkLabel(totals_frame, 
                                           text="Bs. 0.00", 
                                           font=ctk.CTkFont(size=30, weight="bold"), 
                                           text_color="#8B0000") # Rojo oscuro (Maroon)
        self.total_bs_label.pack(pady=(0, 10), anchor='e', padx=10)
        
        
        # Método de Pago
        self.payment_methods = ["Efectivo", "Divisa", "Punto de Venta", "Biopago", "Pago Móvil"]
        self.payment_method_var = ctk.StringVar(value=self.payment_methods[0]) 
        
        ctk.CTkLabel(control_panel, 
                     text="Método de Pago:", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(fill='x', padx=5, pady=(10, 5))
        self.payment_combobox = ctk.CTkComboBox(control_panel, 
                                                values=self.payment_methods, 
                                                variable=self.payment_method_var, 
                                                height=35, 
                                                font=ctk.CTkFont(size=16)) 
        self.payment_combobox.pack(fill='x', padx=5, pady=(0, 15))

        # 2. Botones de Control (Sobrios y grandes)
        btn_font = ctk.CTkFont(size=20, weight="bold")
        
        ctk.CTkButton(control_panel, 
                      text="✅ FINALIZAR VENTA", 
                      font=ctk.CTkFont(size=24, weight="bold"), 
                      height=70, 
                      command=self.finalize_sale, 
                      fg_color="#16A085", # Verde Teal Sobrio
                      hover_color="#138D75").pack(fill='x', padx=5, pady=(10, 10))
        
        ctk.CTkButton(control_panel, 
                      text="❌ Remover Producto", 
                      font=btn_font, 
                      height=45, 
                      command=self.remove_item_from_cart, 
                      fg_color="#9B59B6", # Púrpura sobrio
                      hover_color="#8E44AD").pack(fill='x', padx=5, pady=(5, 5))
        
        ctk.CTkButton(control_panel, 
                      text="🚫 Cancelar Compra", 
                      font=btn_font, 
                      height=45, 
                      command=self.cancel_sale_confirm, 
                      fg_color="#D35400", # Naranja oscuro
                      hover_color="#BA4A00").pack(fill='x', padx=5, pady=(5, 5)) 
        
        ctk.CTkButton(control_panel, 
                      text="🏠 Volver al Menú", 
                      font=ctk.CTkFont(size=16, weight="bold"), 
                      height=30, 
                      command=self.exit_sale_to_caja_menu, 
                      fg_color="#95A5A6", # Gris Ligeramente más claro
                      hover_color="#7F8C8D").pack(fill='x', padx=5, pady=(15, 10))


    # --- Resto de los métodos (Lógica Intacta) ---

    def update_totals(self):
        """Calcula y actualiza los totales de la venta en USD y Bs."""
        # Lógica original...
        subtotal_usd = sum(item['precio'] * item['cantidad'] for item in self.cart.values())
        self.final_total = subtotal_usd 
        
        tasa_bcv = self._get_bcv_rate()
        total_bs = self.final_total * tasa_bcv
        
        self.subtotal_label.configure(text=f"${subtotal_usd:.2f}")
        self.final_total_label.configure(text=f"${self.final_total:.2f}")
        
        try:
            # Formato de Bolívares: separador de miles con punto, decimal con coma (ej: 1.234.567,89)
            formatted_bs_str = "{:,.2f}".format(total_bs)
            formatted_bs = formatted_bs_str.replace(",", "_TEMP_").replace(".", ",").replace("_TEMP_", ".")
            self.total_bs_label.configure(text=f"Bs. {formatted_bs}", text_color="#8B0000")
        except:
             self.total_bs_label.configure(text=f"Bs. {total_bs:.2f}", text_color="#8B0000")

        if tasa_bcv == 1.0:
            self.total_bs_label.configure(text="Bs. N/A (Tasa no disponible)", text_color="#F39C12") # Mantener color de advertencia para no disponible

    def clear_cart(self):
        # Lógica original...
        self.cart = {}
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        self.update_totals()
        self.payment_method_var.set(self.payment_methods[0])

    def add_product_to_cart_by_event(self, event):
        # Lógica original...
        self.add_product_to_cart()

    def add_product_to_cart(self):
        # Lógica original (Chequeo de stock, adición, actualización de display)...
        barcode = self.barcode_entry.get().strip()
        self.barcode_entry.delete(0, ctk.END) 
        
        if not barcode:
            self.focus_barcode_entry()
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, nombre, precio_venta, stock FROM Productos WHERE codigo_barras = ?", 
                (barcode,)
            )
            data = cursor.fetchone()

            if not data:
                messagebox.showerror("Producto No Encontrado", f"Producto con código '{barcode}' no existe en el inventario.")
                self.focus_barcode_entry()
                return
            
            product_id, name, price, stock_actual = data
            
            current_cart_quantity = self.cart.get(product_id, {}).get('cantidad', 0)
            
            if current_cart_quantity >= stock_actual:
                 messagebox.showwarning("Stock Agotado", f"El producto '{name}' solo tiene {stock_actual} unidades en inventario (límite alcanzado en el carrito).")
                 return
                 
            if product_id in self.cart:
                self.cart[product_id]['cantidad'] += 1
            else:
                self.cart[product_id] = {'nombre': name, 'precio': price, 'cantidad': 1, 'id_db': product_id}
                
            self.update_cart_display()
            self.update_totals() 

        except sqlite3.Error as e:
            messagebox.showerror("Error DB", f"Error al buscar producto en la base de datos: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado al añadir producto: {e}")
            
        self.focus_barcode_entry()

    def update_cart_display(self):
        # Lógica original...
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        for id_db, item in self.cart.items():
            subtotal = item['precio'] * item['cantidad']
            self.cart_tree.insert('', 'end', 
                                  iid=id_db, 
                                  values=(item['id_db'], item['nombre'], f"{item['precio']:.2f}", item['cantidad'], f"{subtotal:.2f}"),
                                  tags=(id_db,))


    def remove_item_from_cart(self):
        # Lógica original (Autenticación y remoción)...
        selected_item = self.cart_tree.focus()
        if not selected_item:
            messagebox.showwarning("Selección Requerida", "Debe seleccionar un producto del carrito para eliminar.")
            return

        def remove_authenticated():
            # Lógica original de remoción...
            try:
                item_id = int(self.cart_tree.item(selected_item, 'values')[0]) 
                if item_id in self.cart:
                    nombre_producto = self.cart[item_id]['nombre']
                    if messagebox.askyesno("Confirmar", f"¿Desea eliminar TODAS las unidades de '{nombre_producto}' del carrito?"):
                        del self.cart[item_id]
                        self.update_cart_display()
                        self.update_totals() 
                        messagebox.showinfo("Producto Eliminado", f"Producto '{nombre_producto}' eliminado del carrito.")
                    else:
                        messagebox.showinfo("Cancelado", "Operación de eliminación cancelada.")
                else:
                    messagebox.showerror("Error Interno", "ID de producto no encontrado en el carrito interno.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al procesar la eliminación: {e}")
            finally:
                self.focus_barcode_entry()

        VentasAdminAuthWindow(self.master.master, remove_authenticated)


    def finalize_sale(self):
        # Lógica original (Actualización de stock, registro en DB)...
        if not self.cart:
            messagebox.showwarning("Venta Vacía", "El carrito está vacío. Agregue productos para finalizar.")
            return

        metodo_pago = self.payment_method_var.get()
        
        if not messagebox.askyesno("Confirmar Pago", f"¿El cliente ya realizó el pago por un total de ${self.final_total:.2f}?"):
            return 

        try:
            cursor = self.conn.cursor()
            sale_details = []
            
            # --- LÓGICA DE CHEQUEO DE STOCK Y CÁLCULO (INTACTA) ---
            for item_id, item_data in self.cart.items():
                cantidad_vendida = item_data['cantidad']
                
                cursor.execute("SELECT nombre, stock, stock_bultos, unidades_por_bulto FROM Productos WHERE id = ?", (item_id,))
                result = cursor.fetchone()
                
                if not result: raise Exception(f"Producto ID {item_id} no encontrado en DB.")
                nombre, stock_actual, stock_bultos_actual, unidades_por_bulto = result
                
                if stock_actual < cantidad_vendida:
                    messagebox.showerror("Error de Stock", f"El producto '{nombre}' solo tiene {stock_actual} unidades en inventario. Venta CANCELADA.")
                    self.conn.rollback() 
                    return

                # --- LÓGICA DE ACTUALIZACIÓN DE INVENTARIO (UNIDAD Y BULTO) ---
                nuevo_stock = stock_actual - cantidad_vendida
                
                if unidades_por_bulto and unidades_por_bulto > 0:
                    reduccion_bulto = cantidad_vendida / unidades_por_bulto
                    nuevo_stock_bulto = stock_bultos_actual - reduccion_bulto
                    cursor.execute(
                        "UPDATE Productos SET stock = ?, stock_bultos = ? WHERE id = ?", 
                        (nuevo_stock, nuevo_stock_bulto, item_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE Productos SET stock = ? WHERE id = ?", 
                        (nuevo_stock, item_id)
                    )
                # ------------------------------------------------------------------
                
                sale_details.append({
                    'id': item_id, 'nombre': nombre, 'cantidad': cantidad_vendida,
                    'precio_u': item_data['precio'], 'subtotal': item_data['precio'] * item_data['cantidad']
                })
            # --------------------------------------------------------------------
            
            total_venta = self.final_total
            estado = "Completada" 
            detalle_json = json.dumps(sale_details) 
            tasa_bcv = self._get_bcv_rate()
            monto_total_bs = total_venta * tasa_bcv
            now = datetime.datetime.now()
            fecha_str = now.strftime("%Y-%m-%d")
            hora_str = now.strftime("%H:%M:%S")

            cursor.execute("""
                INSERT INTO Ventas (
                    fecha, hora, total_venta, monto_total_bs, tasa_bcv, detalle, metodo_pago, estado
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (fecha_str, hora_str, total_venta, monto_total_bs, tasa_bcv, detalle_json, metodo_pago, estado))
            
            self.conn.commit()
            
            messagebox.showinfo("Venta Exitosa", f"Venta de ${total_venta:.2f} finalizada con {metodo_pago}.")
            self.clear_cart()
            
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Error DB", f"No se pudo registrar la venta. Error: {e}")


    def cancel_sale_confirm(self):
        # Lógica original...
        if not self.cart:
            messagebox.showwarning("Venta Vacía", "El carrito ya está vacío.")
            return

        confirm = messagebox.askyesno(
            "Confirmar Cancelación", 
            f"¿Está seguro que desea **CANCELAR** la compra actual de ${self.final_total:.2f}?\n"
            "Esta acción registrará la compra como Cancelada para auditoría."
        )

        if confirm:
            self._register_cancelled_sale()

    def _register_cancelled_sale(self):
        # Lógica original...
        metodo_pago = self.payment_method_var.get()
        try:
            cursor = self.conn.cursor()
            sale_details = []
            for item_id, item_data in self.cart.items():
                sale_details.append({
                    'id': item_id, 'nombre': item_data['nombre'], 'cantidad': item_data['cantidad'], 
                    'precio_u': item_data['precio'], 'subtotal': item_data['precio'] * item_data['cantidad']
                })
            total_cancelado = self.final_total
            estado = "Cancelada" 
            detalle_json = json.dumps(sale_details) 
            tasa_bcv = self._get_bcv_rate()
            monto_total_bs = total_cancelado * tasa_bcv
            now = datetime.datetime.now()
            fecha_str = now.strftime("%Y-%m-%d")
            hora_str = now.strftime("%H:%M:%S")
            cursor.execute("""
                INSERT INTO Ventas (
                    fecha, hora, total_venta, monto_total_bs, tasa_bcv, detalle, metodo_pago, estado
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (fecha_str, hora_str, total_cancelado, monto_total_bs, tasa_bcv, detalle_json, metodo_pago, estado))
            
            self.conn.commit()
            messagebox.showinfo("Compra Cancelada", "La compra ha sido cancelada y registrada.")
            self.clear_cart()
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Error DB", f"No se pudo registrar la cancelación. Error: {e}")
            
    def focus_barcode_entry(self):
        # Lógica original...
        self.after(1, self.barcode_entry.focus_set)

    def exit_sale_to_caja_menu(self):
        # Lógica original...
        if self.cart:
            messagebox.showwarning(
                "Venta Activa", 
                "No puede salir del módulo con una venta pendiente.\n\n"
                "Debe **FINALIZAR VENTA** o **CANCELAR COMPRA** primero."
            )
            return
        self.controller.show_frame("CajaMenu") 

    def is_sale_active(self):
        # Lógica original...
        return bool(self.cart)

    def handle_app_close_event(self):
        # Lógica original...
        if not self.cart:
            return True 
        confirm = messagebox.askyesno(
            "⚠️ VENTA PENDIENTE - CIERRE DE APP ⚠️", 
            f"Hay una venta activa. Si cierra la aplicación ahora, se generará un reporte de **'Cierre Forzado de App'** para auditoría y la venta NO se registrará.\n\n"
            f"Total Pendiente: ${self.final_total:.2f}\n\n"
            "¿Desea cerrar la aplicación de todas formas y registrar el evento como **Cierre Forzado**?",
            parent=self.master.master 
        )
        if confirm:
            self.register_forced_closure_report()
            return True 
        else:
            return False 

    def register_forced_closure_report(self):
        # Lógica original...
        metodo_pago = self.payment_method_var.get()
        try:
            cursor = self.conn.cursor()
            sale_details = []
            for item_id, item_data in self.cart.items():
                sale_details.append({
                    'id': item_id, 'nombre': item_data['nombre'], 'cantidad': item_data['cantidad'], 
                    'precio_u': item_data['precio'], 'subtotal': item_data['precio'] * item_data['cantidad']
                })
            total_transaccion = self.final_total
            estado = "Cierre Forzado de App" 
            detalle_json = json.dumps(sale_details) 
            tasa_bcv = self._get_bcv_rate()
            monto_total_bs = total_transaccion * tasa_bcv
            now = datetime.datetime.now()
            fecha_str = now.strftime("%Y-%m-%d")
            hora_str = now.strftime("%H:%M:%S")

            cursor.execute("""
                INSERT INTO Ventas (
                    fecha, hora, total_venta, monto_total_bs, tasa_bcv, detalle, metodo_pago, estado
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (fecha_str, hora_str, total_transaccion, monto_total_bs, tasa_bcv, detalle_json, metodo_pago, estado))
            
            self.conn.commit()
            self.clear_cart() 
        except Exception as e:
            self.conn.rollback() 
            print(f"Error al registrar el reporte de cierre forzado: {e}")
            
    def synchronize_inventory_counts(self):
        # Lógica original...
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, stock, stock_bultos, unidades_por_bulto FROM Productos WHERE unidades_por_bulto > 0")
            products_to_check = cursor.fetchall()
            count_updates = 0
            for product_id, current_stock, current_stock_bultos, units_per_bulto in products_to_check:
                theoretical_stock = round(current_stock_bultos * units_per_bulto)
                if abs(current_stock - theoretical_stock) > 0.001: 
                    cursor.execute("UPDATE Productos SET stock = ? WHERE id = ?", (theoretical_stock, product_id))
                    count_updates += 1
            self.conn.commit()
            if count_updates > 0:
                print(f"Sincronización de inventario completada. {count_updates} productos ajustados.")
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Error DB al sincronizar inventario: {e}")
        except Exception as e:
            print(f"Error inesperado al sincronizar inventario: {e}")