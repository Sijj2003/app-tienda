# module_devolucion.py (MÓDULO DE DEVOLUCIÓN - Lógica Inversa a Ventas)

import customtkinter as ctk
from tkinter import messagebox, simpledialog, ttk 
import sqlite3
import datetime
import json
import re

# Importamos las utilidades
from utils import setup_db, DB_NAME, verify_password 

# --- CLASE: VENTANA MODAL DE AUTENTICACIÓN (DISEÑO SOBRIO) ---
# Reutilizamos la clase del módulo de ventas para consistencia.
class DevolucionAdminAuthWindow(ctk.CTkToplevel):
    """Ventana modal de autenticación de administrador para autorizar una devolución."""
    def __init__(self, master, success_callback):
        super().__init__(master)
        self.title("🔑 Autorización de Devolución")
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
                     text="Se requiere autenticación para DEVOLUCIÓN", 
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="#34495E").grid(row=1, column=0, padx=20, pady=(20, 10))
        
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
                      text="Autorizar", 
                      font=ctk.CTkFont(size=16, weight="bold"),
                      width=120,
                      height=35,
                      command=self.check_password,
                      fg_color="#34495E",
                      hover_color="#5D6D7E").grid(row=3, column=0, pady=(0, 20)) 

        self.password_entry.bind('<Return>', lambda event=None: self.check_password())

    def check_password(self):
        password = self.password_entry.get().strip()
        if verify_password(password):
            self.destroy()
            self.success_callback() 
        else:
            messagebox.showerror("Error de Contraseña", "Contraseña incorrecta. Inténtelo de nuevo.", parent=self)
            self.password_entry.delete(0, ctk.END)
            self.password_entry.focus_set()


# ===================================================================
# --- CLASE PRINCIPAL: DevolucionModule ---
# ===================================================================

class DevolucionModule(ctk.CTkFrame): 
    """Módulo para el registro de devoluciones (operación inversa a Ventas)."""
    def __init__(self, parent, controller):
        super().__init__(parent) 
        self.controller = controller
        
        self.conn = setup_db()
        self.return_cart = {} # Carrito de productos a devolver
        self.final_return_total = 0.0 
        
        self.create_widgets()
        self.update_totals() 
        self.focus_barcode_entry()

    # MÉTODOS DE UTILIDAD
    def _get_bcv_rate(self) -> float:
        """Obtiene la última tasa BCV registrada, usando la misma lógica que Ventas."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT tasa FROM TasasBCV ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            return result[0] if result else 1.0 
        except sqlite3.Error as e:
            print(f"Error DB al obtener tasa BCV: {e}")
            return 1.0

    def focus_barcode_entry(self):
        """Establece el foco en la entrada de código de barras."""
        self.after(1, self.barcode_entry.focus_set)
        
    def exit_sale_to_caja_menu(self):
        """Maneja la salida del módulo."""
        if self.return_cart:
            messagebox.showwarning(
                "Devolución Pendiente", 
                "No puede salir del módulo con una devolución pendiente.\n\n"
                "Debe **CONCRETAR DEVOLUCIÓN** o **CANCELAR DEVOLUCIÓN** primero."
            )
            return
        self.controller.show_frame("CajaMenu") 

    def update_totals(self):
        """Calcula y actualiza el total a devolver en USD y Bs."""
        subtotal_usd = sum(item['precio'] * item['cantidad'] for item in self.return_cart.values())
        self.final_return_total = subtotal_usd 
        
        tasa_bcv = self._get_bcv_rate()
        total_bs_to_return = self.final_return_total * tasa_bcv
        
        # Actualización de Labels
        self.subtotal_label.configure(text=f"${subtotal_usd:.2f}")
        self.final_total_label.configure(text=f"${self.final_return_total:.2f}")
        
        try:
            # Formato de Bolívares
            formatted_bs_str = "{:,.2f}".format(total_bs_to_return)
            formatted_bs = formatted_bs_str.replace(",", "_TEMP_").replace(".", ",").replace("_TEMP_", ".")
            self.total_bs_label.configure(text=f"Bs. {formatted_bs}", text_color="#D35400") # Naranja oscuro
        except:
             self.total_bs_label.configure(text=f"Bs. {total_bs_to_return:.2f}", text_color="#D35400")

        if tasa_bcv == 1.0:
            self.total_bs_label.configure(text="Bs. N/A (Tasa no disponible)", text_color="#F39C12")


    def create_widgets(self):
        # ----------------------------------------------------------------------
        # --- Cabecera del Módulo y Frame Principal ---
        # ----------------------------------------------------------------------
        ctk.CTkLabel(self, 
                     text="↩️ Devolución Rápida", 
                     font=ctk.CTkFont(size=30, weight="bold"),
                     text_color="#D35400").pack(pady=(20, 5)) # Título en color de advertencia/devolución

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        main_frame.grid_columnconfigure(0, weight=3) 
        main_frame.grid_columnconfigure(1, weight=1) 
        main_frame.grid_rowconfigure(0, weight=1)
        
        # ----------------------------------------------------------------------
        # --- Panel de Carrito de Devolución (Izquierda) ---
        # ----------------------------------------------------------------------
        cart_panel = ctk.CTkFrame(main_frame, fg_color="transparent")
        cart_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        cart_panel.grid_rowconfigure(1, weight=1) 
        cart_panel.grid_columnconfigure(0, weight=1)
        
        # 1. Entrada de Código de Barras
        input_frame = ctk.CTkFrame(cart_panel, fg_color="#FADBD8", corner_radius=8) # Fondo rojizo claro
        input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 10))
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.barcode_entry = ctk.CTkEntry(input_frame, 
                                          width=350, 
                                          height=50, 
                                          font=ctk.CTkFont(size=22),
                                          placeholder_text="Escanear Producto a Devolver (ENTER)...")
        self.barcode_entry.grid(row=0, column=0, padx=15, pady=10, sticky="ew")
        self.barcode_entry.bind('<Return>', self.add_product_to_return_cart_by_event)
        
        ctk.CTkButton(input_frame, 
                      text="Añadir", 
                      width=100, 
                      height=50, 
                      font=ctk.CTkFont(size=18, weight="bold"),
                      fg_color="#E74C3C", # Rojo Sobrio
                      hover_color="#C0392B",
                      command=self.add_product_to_return_cart).grid(row=0, column=1, padx=15, pady=10)
        
        # 2. Treeview del Carrito de Devolución
        self.style = ttk.Style(self)
        self.style.theme_use("default") 
        
        FONT_SIZE_ACCESSIBLE = 18 
        ROW_HEIGHT_ACCESSIBLE = 40 
        
        self.style.configure("Return.Treeview.Heading", font=('Helvetica', FONT_SIZE_ACCESSIBLE, 'bold'), background="#E74C3C", foreground="white") # Encabezados Rojos
        self.style.configure("Return.Treeview", font=('Helvetica', FONT_SIZE_ACCESSIBLE), rowheight=ROW_HEIGHT_ACCESSIBLE) 
        self.style.map('Return.Treeview', background=[('selected', '#ECF0F1')]) # Gris muy claro de selección
        
        cart_tree_container = ctk.CTkFrame(cart_panel)
        cart_tree_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 10))
        
        self.return_tree = ttk.Treeview(cart_tree_container, 
                                      columns=("ID_Producto", "Nombre", "Precio_U", "Cantidad", "Subtotal"), 
                                      show='headings', 
                                      style="Return.Treeview")
        
        self.return_tree.column("ID_Producto", width=50, anchor='center', stretch=False)
        self.return_tree.column("Nombre", width=400, anchor='w', stretch=True)
        self.return_tree.column("Precio_U", width=120, anchor='e', stretch=False)
        self.return_tree.column("Cantidad", width=100, anchor='center', stretch=False)
        self.return_tree.column("Subtotal", width=150, anchor='e', stretch=False)

        self.return_tree.heading("ID_Producto", text="ID DB")
        self.return_tree.heading("Nombre", text="PRODUCTO DEVUELTO")
        self.return_tree.heading("Precio_U", text="PRECIO U. ($)")
        self.return_tree.heading("Cantidad", text="CANT.")
        self.return_tree.heading("Subtotal", text="SUBTOTAL ($)")
        
        vsb = ttk.Scrollbar(cart_tree_container, orient="vertical", command=self.return_tree.yview)
        self.return_tree.configure(yscrollcommand=vsb.set)
        
        self.return_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")


        # ----------------------------------------------------------------------
        # --- Panel de Controles y Totales (Derecha) ---
        # ----------------------------------------------------------------------
        control_panel = ctk.CTkFrame(main_frame, fg_color="transparent")
        control_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        control_panel.grid_columnconfigure(0, weight=1)

        # 1. Totales y Pago
        totals_frame = ctk.CTkFrame(control_panel, fg_color="#F8F9F9", corner_radius=10)
        totals_frame.pack(fill='x', padx=5, pady=(5, 15))
        
        # SUBTOTAL USD
        ctk.CTkLabel(totals_frame, 
                     text="SUBTOTAL DEVUELTO:", 
                     font=ctk.CTkFont(size=18),
                     text_color="#7F8C8D").pack(pady=(10, 2), anchor='w', padx=10)
        self.subtotal_label = ctk.CTkLabel(totals_frame, 
                                           text="$0.00", 
                                           font=ctk.CTkFont(size=24, weight="bold"), 
                                           text_color="#7F8C8D")
        self.subtotal_label.pack(pady=(0, 10), anchor='e', padx=10) 
        
        # TOTAL FINAL USD (Total a Reembolsar)
        ctk.CTkLabel(totals_frame, 
                     text="TOTAL USD A REEMBOLSAR:", 
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#E74C3C").pack(pady=(10, 5), anchor='w', padx=10) # Rojo
        self.final_total_label = ctk.CTkLabel(totals_frame, 
                                              text="$0.00", 
                                              font=ctk.CTkFont(size=48, weight="bold"), 
                                              text_color="#E74C3C") 
        self.final_total_label.pack(pady=(0, 15), anchor='e', padx=10) 
        
        # TOTAL EN BOLÍVARES (Total a Reembolsar)
        ctk.CTkLabel(totals_frame, 
                     text="TOTAL BS. A REEMBOLSAR (BCV):", 
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(5, 5), anchor='w', padx=10)
        self.total_bs_label = ctk.CTkLabel(totals_frame, 
                                           text="Bs. 0.00", 
                                           font=ctk.CTkFont(size=30, weight="bold"), 
                                           text_color="#D35400") # Naranja oscuro
        self.total_bs_label.pack(pady=(0, 10), anchor='e', padx=10)
        
        
        # Método de Devolución
        self.return_methods = ["Efectivo", "Divisa", "Punto de Venta", "Biopago", "Pago Móvil"]
        self.return_method_var = ctk.StringVar(value=self.return_methods[0]) 
        
        ctk.CTkLabel(control_panel, 
                     text="Método de Reembolso:", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(fill='x', padx=5, pady=(10, 5))
        self.return_combobox = ctk.CTkComboBox(control_panel, 
                                                values=self.return_methods, 
                                                variable=self.return_method_var, 
                                                height=35, 
                                                font=ctk.CTkFont(size=16)) 
        self.return_combobox.pack(fill='x', padx=5, pady=(0, 15))

        # 2. Botones de Control
        btn_font = ctk.CTkFont(size=20, weight="bold")
        
        ctk.CTkButton(control_panel, 
                      text="✅ CONCRETAR DEVOLUCIÓN", 
                      font=ctk.CTkFont(size=24, weight="bold"), 
                      height=70, 
                      command=self.confirm_return, 
                      fg_color="#E74C3C", # Rojo de Devolución
                      hover_color="#C0392B").pack(fill='x', padx=5, pady=(10, 10))
        
        ctk.CTkButton(control_panel, 
                      text="🗑️ Remover Producto de Devolución", 
                      font=btn_font, 
                      height=45, 
                      command=self.remove_item_from_return_cart, 
                      fg_color="#9B59B6", 
                      hover_color="#8E44AD").pack(fill='x', padx=5, pady=(5, 5))
        
        ctk.CTkButton(control_panel, 
                      text="🚫 Cancelar Devolución", 
                      font=btn_font, 
                      height=45, 
                      command=self.cancel_return_confirm, 
                      fg_color="#34495E", 
                      hover_color="#5D6D7E").pack(fill='x', padx=5, pady=(5, 5)) 
        
        ctk.CTkButton(control_panel, 
                      text="🏠 Volver al Menú", 
                      font=ctk.CTkFont(size=16, weight="bold"), 
                      height=30, 
                      command=self.exit_sale_to_caja_menu, 
                      fg_color="#95A5A6",
                      hover_color="#7F8C8D").pack(fill='x', padx=5, pady=(15, 10))


    # --- Lógica de Carrito Inversa ---
    
    def clear_return_cart(self):
        """Limpia el carrito de devolución y actualiza totales."""
        self.return_cart = {}
        for item in self.return_tree.get_children():
            self.return_tree.delete(item)
        self.update_totals()
        self.return_method_var.set(self.return_methods[0])
        self.focus_barcode_entry()

    def add_product_to_return_cart_by_event(self, event):
        """Manejador de evento de tecla ENTER."""
        self.add_product_to_return_cart()

    def add_product_to_return_cart(self):
        """Busca el producto por código de barras y lo agrega al carrito de devolución."""
        barcode = self.barcode_entry.get().strip()
        self.barcode_entry.delete(0, ctk.END) 
        
        if not barcode:
            self.focus_barcode_entry()
            return

        try:
            cursor = self.conn.cursor()
            # Solo necesitamos ID, nombre y precio de venta
            cursor.execute(
                "SELECT id, nombre, precio_venta FROM Productos WHERE codigo_barras = ?", 
                (barcode,)
            )
            data = cursor.fetchone()

            if not data:
                messagebox.showerror("Producto No Encontrado", f"Producto con código '{barcode}' no existe en el inventario.")
                self.focus_barcode_entry()
                return
            
            product_id, name, price = data
            
            # Siempre agregamos 1 unidad por escaneo. Si quiere más, debe escanear más veces
            if product_id in self.return_cart:
                self.return_cart[product_id]['cantidad'] += 1
            else:
                self.return_cart[product_id] = {'nombre': name, 'precio': price, 'cantidad': 1, 'id_db': product_id}
                
            self.update_return_display()
            self.update_totals() 

        except sqlite3.Error as e:
            messagebox.showerror("Error DB", f"Error al buscar producto en la base de datos: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado al añadir producto: {e}")
            
        self.focus_barcode_entry()

    def update_return_display(self):
        """Actualiza la visualización del Treeview con el carrito de devolución."""
        for item in self.return_tree.get_children():
            self.return_tree.delete(item)
        
        for id_db, item in self.return_cart.items():
            subtotal = item['precio'] * item['cantidad']
            self.return_tree.insert('', 'end', 
                                  iid=id_db, 
                                  values=(item['id_db'], item['nombre'], f"{item['precio']:.2f}", item['cantidad'], f"{subtotal:.2f}"),
                                  tags=(id_db,))


    def remove_item_from_return_cart(self):
        """Remueve un producto seleccionado del carrito (Requiere autenticación)."""
        selected_item = self.return_tree.focus()
        if not selected_item:
            messagebox.showwarning("Selección Requerida", "Debe seleccionar un producto de la devolución para remover.")
            return

        def remove_authenticated():
            try:
                # El valor [0] es el 'ID_Producto'
                item_id = int(self.return_tree.item(selected_item, 'values')[0]) 
                if item_id in self.return_cart:
                    nombre_producto = self.return_cart[item_id]['nombre']
                    if messagebox.askyesno("Confirmar", f"¿Desea eliminar TODAS las unidades de '{nombre_producto}' de la lista de devolución?"):
                        del self.return_cart[item_id]
                        self.update_return_display()
                        self.update_totals() 
                        messagebox.showinfo("Producto Removido", f"Producto '{nombre_producto}' removido de la devolución.")
                    else:
                        messagebox.showinfo("Cancelado", "Operación de remoción cancelada.")
                else:
                    messagebox.showerror("Error Interno", "ID de producto no encontrado en el carrito interno.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al procesar la remoción: {e}")
            finally:
                self.focus_barcode_entry()

        DevolucionAdminAuthWindow(self.master.master, remove_authenticated)
        
        
    # --- Lógica de Concretar Devolución ---

    def confirm_return(self):
        """Confirma la devolución, actualiza el inventario y registra la transacción."""
        if not self.return_cart:
            messagebox.showwarning("Devolución Vacía", "El carrito de devolución está vacío. Agregue productos para concretar.")
            return

        metodo_reembolso = self.return_method_var.get()
        
        confirm_msg = (
            f"¿Confirma la devolución de ${self.final_return_total:.2f}?\n"
            f"Se debe reembolsar **{self.final_total_label.cget('text')} USD** ({self.total_bs_label.cget('text')}) "
            f"mediante el método: **{metodo_reembolso}**."
        )
        if not messagebox.askyesno("Confirmar Devolución y Reembolso", confirm_msg):
            return 

        def process_return():
            """Función ejecutada tras la autenticación."""
            try:
                cursor = self.conn.cursor()
                return_details = []
                
                # --- LÓGICA DE SUMA AL INVENTARIO (INVERSA A VENTA) ---
                for item_id, item_data in self.return_cart.items():
                    cantidad_devuelta = item_data['cantidad']
                    
                    cursor.execute("SELECT nombre, stock, stock_bultos, unidades_por_bulto FROM Productos WHERE id = ?", (item_id,))
                    result = cursor.fetchone()
                    
                    if not result: raise Exception(f"Producto ID {item_id} no encontrado en DB.")
                    nombre, stock_actual, stock_bultos_actual, unidades_por_bulto = result
                    
                    # Aumentar stock de unidades
                    nuevo_stock = stock_actual + cantidad_devuelta
                    
                    # Aumentar stock de bultos (si aplica)
                    if unidades_por_bulto and unidades_por_bulto > 0:
                        aumento_bulto = cantidad_devuelta / unidades_por_bulto
                        nuevo_stock_bulto = stock_bultos_actual + aumento_bulto
                        cursor.execute(
                            "UPDATE Productos SET stock = ?, stock_bultos = ? WHERE id = ?", 
                            (nuevo_stock, nuevo_stock_bulto, item_id)
                        )
                    else:
                        cursor.execute(
                            "UPDATE Productos SET stock = ? WHERE id = ?", 
                            (nuevo_stock, item_id)
                        )
                    
                    return_details.append({
                        'id': item_id, 'nombre': nombre, 'cantidad': cantidad_devuelta,
                        'precio_u': item_data['precio'], 'subtotal': item_data['precio'] * item_data['cantidad']
                    })
                # ------------------------------------------------------------------
                
                total_devolucion = self.final_return_total
                estado = "Devolucion" # Nuevo estado para el registro
                detalle_json = json.dumps(return_details) 
                tasa_bcv = self._get_bcv_rate()
                monto_total_bs = total_devolucion * tasa_bcv
                now = datetime.datetime.now()
                fecha_str = now.strftime("%Y-%m-%d")
                hora_str = now.strftime("%H:%M:%S")

                # Registrar la transacción como "Devolucion"
                cursor.execute("""
                    INSERT INTO Ventas (
                        fecha, hora, total_venta, monto_total_bs, tasa_bcv, detalle, metodo_pago, estado
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (fecha_str, hora_str, total_devolucion, monto_total_bs, tasa_bcv, detalle_json, metodo_reembolso, estado))
                
                self.conn.commit()
                
                messagebox.showinfo("Devolución Exitosa", f"Devolución de ${total_devolucion:.2f} concretada. Inventario actualizado. Reembolso: {metodo_reembolso}.")
                self.clear_return_cart()
                
            except Exception as e:
                self.conn.rollback()
                messagebox.showerror("Error DB", f"No se pudo registrar la devolución. Error: {e}")

        # La devolución debe ser autorizada por un administrador
        DevolucionAdminAuthWindow(self.master.master, process_return)


    def cancel_return_confirm(self):
        """Confirma la cancelación de la devolución actual."""
        if not self.return_cart:
            messagebox.showwarning("Devolución Vacía", "El carrito de devolución ya está vacío.")
            return

        confirm = messagebox.askyesno(
            "Confirmar Cancelación", 
            f"¿Está seguro que desea **CANCELAR** la devolución actual de ${self.final_return_total:.2f}?\n"
        )

        if confirm:
            self.clear_return_cart()
            messagebox.showinfo("Cancelado", "Devolución cancelada y carrito vaciado.")