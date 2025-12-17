# module_avance_efectivo.py (CÓDIGO COMPLETO Y CORREGIDO: Modales Modernos Centrados, Solo Bs.)

import customtkinter as ctk
import datetime
import sqlite3
from utils import setup_db, DB_NAME 
from tkinter import Toplevel # Necesario para asegurar la correcta herencia de Toplevel

# ===================================================================
# --- 1. CLASES: VENTANAS MODALES MODERNAS (CTKTOPLEVEL) ---
# (Se mantienen sin cambios, ya que su UI es moderna)
# ===================================================================

class CustomMessageDialog(ctk.CTkToplevel):
    """Ventana modal moderna para mensajes de información o error (Info/Error)."""
    def __init__(self, master, title, message, dialog_type='info'):
        super().__init__(master)
        self.title(title)
        self.message = message
        self.dialog_type = dialog_type
        
        # Configuración Modal
        self.transient(master) 
        self.grab_set()
        
        # Dimensiones y Centrado de la ventana
        window_width = 450
        window_height = 250
        self.geometry(f"{window_width}x{window_height}")
        self.resizable(False, False)
        
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f'{window_width}x{window_height}+{x}+{y}') # Centrado
        self.after(100, self.lift) # Traer al frente
        
        self.grid_columnconfigure(0, weight=1)
        self.create_widgets()
        self.focus_force() 
        self.wait_window(self)

    def create_widgets(self):
        # Colores e Iconos basados en el tipo de diálogo
        if self.dialog_type == 'info':
            color = "#10B981"  # Verde
            icon = "✅"
        elif self.dialog_type == 'error':
            color = "#EF4444"  # Rojo
            icon = "❌"
        else: # Default
            color = "#FACC15" 
            icon = "ℹ️"
        
        ctk.CTkLabel(self, 
                     text=f"{icon} {self.title()}", 
                     font=ctk.CTkFont(size=24, weight="bold"), 
                     text_color=color).pack(pady=(20, 10))
        
        # Usamos un CTkTextbox para permitir mensajes largos y mantener el estilo CTK
        textbox = ctk.CTkTextbox(self, 
                       height=80, 
                       width=400,
                       font=ctk.CTkFont(size=14),
                       wrap="word")
        textbox.pack(padx=20, pady=10)
        textbox.insert("0.0", self.message)
        textbox.configure(state="disabled") # Para que el usuario solo pueda leer
        
        ctk.CTkButton(self, 
                      text="Aceptar", 
                      font=ctk.CTkFont(size=18, weight="bold"),
                      width=150,
                      command=self.destroy).pack(pady=20)
        
        self.bind('<Return>', lambda event: self.destroy())


class CustomAskYesNoDialog(ctk.CTkToplevel):
    """Ventana modal moderna para confirmación (Sí/No)."""
    def __init__(self, master, title, message):
        super().__init__(master)
        self.title(title)
        self.message = message
        self.result = False
        
        # Configuración Modal
        self.transient(master) 
        self.grab_set()
        
        # Dimensiones y Centrado de la ventana
        window_width = 450
        window_height = 250
        self.geometry(f"{window_width}x{window_height}")
        self.resizable(False, False)

        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f'{window_width}x{window_height}+{x}+{y}') # Centrado
        self.after(100, self.lift)

        self.grid_columnconfigure(0, weight=1)
        self.create_widgets()
        self.focus_force()
        self.wait_window(self) 

    def create_widgets(self):
        ctk.CTkLabel(self, 
                     text=f"❓ {self.title()}", 
                     font=ctk.CTkFont(size=24, weight="bold"), 
                     text_color="#FACC15").pack(pady=(20, 10))
        
        textbox = ctk.CTkTextbox(self, 
                       height=60, 
                       width=400,
                       font=ctk.CTkFont(size=14),
                       wrap="word")
        textbox.pack(padx=20, pady=10)
        textbox.insert("0.0", self.message)
        textbox.configure(state="disabled")

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20, padx=20, fill='x')
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkButton(button_frame, 
                      text="No", 
                      font=ctk.CTkFont(size=18, weight="bold"),
                      fg_color="#EF4444", 
                      hover_color="#DC2626",
                      command=self.no_action).grid(row=0, column=0, padx=10, sticky="ew")

        ctk.CTkButton(button_frame, 
                      text="Sí", 
                      font=ctk.CTkFont(size=18, weight="bold"),
                      fg_color="#10B981", 
                      hover_color="#059669",
                      command=self.yes_action).grid(row=0, column=1, padx=10, sticky="ew")

    def yes_action(self):
        self.result = True
        self.destroy()

    def no_action(self):
        self.result = False
        self.destroy()

    @staticmethod
    def show(master, title, message):
        """Método estático para mostrar el diálogo y obtener el resultado."""
        dialog = CustomAskYesNoDialog(master, title, message)
        return dialog.result

# ===================================================================
# --- 2. CLASE PRINCIPAL: AvanceEfectivoModule ---
# ===================================================================

class AvanceEfectivoModule(ctk.CTkFrame):
    
    TASA_COMISION = 0.20  # 20% de comisión

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.conn = setup_db()
        
        self.create_widgets()

    def create_widgets(self):
        # Configuración del Grid principal para ser completamente responsive
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1) # Fila 1 (Operación) toma todo el espacio vertical

        # --- Cabecera (Mejora Gráfica) ---
        ctk.CTkLabel(self, text="💵 AVANCE DE EFECTIVO", 
                     font=ctk.CTkFont(size=34, weight="bold")).grid(row=0, column=0, pady=30, sticky="n")

        # --- Frame Principal de Operación (Mejora Gráfica) ---
        operation_frame = ctk.CTkFrame(self, fg_color="#292F38", corner_radius=15) # Fondo oscuro/Bordes redondeados
        operation_frame.grid(row=1, column=0, padx=60, pady=20, sticky="nsew") # Mayor padding y sticky="nsew"
        operation_frame.grid_columnconfigure((0, 1), weight=1)
        
        # --- ENTRADA DE MONTO (Mejora Gráfica) ---
        ctk.CTkLabel(operation_frame, text="Monto de Efectivo a Entregar (Bs.)", 
                     font=ctk.CTkFont(size=24, weight="bold"), text_color="#B0BEC5").grid(row=0, column=0, columnspan=2, pady=(30, 5), sticky="w", padx=30)
        
        self.monto_entregar_entry = ctk.CTkEntry(operation_frame,
                                                 placeholder_text="Ej: 1.000,00",
                                                 font=ctk.CTkFont(size=28), # Fuente más grande
                                                 height=60, # Más alto
                                                 corner_radius=10)
        self.monto_entregar_entry.grid(row=1, column=0, columnspan=2, padx=30, pady=(0, 30), sticky="ew")
        
        # 1. Bind para calcular
        self.monto_entregar_entry.bind('<KeyRelease>', self.calculate_total)
        
        # --- RESULTADOS DEL CÁLCULO (Mejora Gráfica) ---
        ctk.CTkLabel(operation_frame, text="COMISIÓN (20%):", 
                     font=ctk.CTkFont(size=22), text_color="#B0BEC5").grid(row=2, column=0, sticky="w", padx=30, pady=(15, 5))
        self.comision_label = ctk.CTkLabel(operation_frame, text="Bs. 0.00", text_color="#FACC15", 
                                            font=ctk.CTkFont(size=30, weight="bold"))
        self.comision_label.grid(row=2, column=1, sticky="e", padx=30, pady=(15, 5))

        ctk.CTkLabel(operation_frame, text="MONTO TOTAL A PAGAR:", 
                     font=ctk.CTkFont(size=28, weight="bold"), text_color="#B0BEC5").grid(row=3, column=0, sticky="w", padx=30, pady=(20, 10))
        self.total_label = ctk.CTkLabel(operation_frame, text="Bs. 0.00", text_color="#10B981", 
                                        font=ctk.CTkFont(size=44, weight="bold")) # Fuente del total muy grande
        self.total_label.grid(row=3, column=1, sticky="e", padx=30, pady=(20, 10))
        
        # --- MÉTODO DE PAGO (Mejora Gráfica) ---
        ctk.CTkLabel(operation_frame, text="Método de Pago:", 
                     font=ctk.CTkFont(size=22), text_color="#B0BEC5").grid(row=4, column=0, sticky="w", padx=30, pady=(20, 5))
        
        self.metodo_pago_var = ctk.StringVar(value="Punto de Venta")
        metodos = ["Punto de Venta", "Pago Móvil", "BioPago"]
        self.metodo_pago_option = ctk.CTkOptionMenu(operation_frame, 
                                                    values=metodos, 
                                                    variable=self.metodo_pago_var, 
                                                    font=ctk.CTkFont(size=20),
                                                    height=40)
        self.metodo_pago_option.grid(row=5, column=0, columnspan=2, padx=30, pady=(0, 40), sticky="ew")


        # --- 3. Botones de Acción (Mejora Gráfica) ---
        button_frame = ctk.CTkFrame(operation_frame, fg_color="transparent")
        button_frame.grid(row=6, column=0, columnspan=2, pady=30, padx=30, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(operation_frame, text="✅ REALIZAR AVANCE", command=self.concretar_avance, 
                      fg_color="#10B981", hover_color="#059669", font=ctk.CTkFont(size=22, weight="bold"), 
                      height=60).grid(row=6, column=0, columnspan=2, pady=(40, 30), padx=30, sticky="ew")

    # --- MÉTODOS DE LÓGICA (Inalterados) ---
    def reset_focus(self):
        """Forzar foco al campo de entrada al cambiar de módulo."""
        self.after(100, self.monto_entregar_entry.focus_set) 


    def calculate_total(self, event=None):
        try:
            # Aseguramos el uso del punto como separador decimal
            monto_entregado = float(self.monto_entregar_entry.get().replace(',', '.')) 
        except ValueError:
            self.comision_label.configure(text="Bs. 0.00")
            self.total_label.configure(text="Bs. 0.00")
            return

        comision = monto_entregado * self.TASA_COMISION
        monto_total = monto_entregado + comision

        # Formato con separador de miles (,) y dos decimales
        self.comision_label.configure(text=f"Bs. {comision:,.2f}") 
        self.total_label.configure(text=f"Bs. {monto_total:,.2f}")
        
    def _get_transaction_data(self):
        # El master de los modales es el controlador principal (MainApplication)
        modal_master = self.controller 
        
        try:
            monto_entregado = float(self.monto_entregar_entry.get().replace(',', '.'))
            if monto_entregado <= 0:
                # ⭐ MODAL MODERNIZADO
                CustomMessageDialog(modal_master, "Error", "El monto a entregar debe ser positivo.", 'error')
                return None, None, None, None
        except ValueError:
            # ⭐ MODAL MODERNIZADO
            CustomMessageDialog(modal_master, "Error", "Ingrese un monto válido a entregar.", 'error')
            return None, None, None, None

        comision = monto_entregado * self.TASA_COMISION
        monto_total = monto_entregado + comision
        metodo_pago = self.metodo_pago_var.get()
        
        return monto_entregado, comision, monto_total, metodo_pago

    def _register_advance(self, estado):
        monto_entregado, comision, monto_total, metodo_pago = self._get_transaction_data()
        
        if monto_entregado is None:
            return

        fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        modal_master = self.controller 

        # --- Confirmación (MODAL MODERNIZADO) ---
        if estado == 'Concretado':
            confirm_msg = (f"Entregado: Bs. {monto_entregado:,.2f}\n"
                           f"Comisión: Bs. {comision:,.2f}\n"
                           f"Total a Pagar: Bs. {monto_total:,.2f}\n"
                           f"Método: {metodo_pago}\n\n"
                           f"¿Desea **CONCRETAR** el avance y generar el reporte?")
            if not CustomAskYesNoDialog.show(modal_master, "Confirmar Avance", confirm_msg): 
                return
        else: # Cancelado
            confirm_msg = (f"Entregado: Bs. {monto_entregado:,.2f}\n"
                           f"Comisión: Bs. {comision:,.2f}\n"
                           f"Total a Pagar: Bs. {monto_total:,.2f}\n\n"
                           f"¿Desea **CANCELAR** la transacción y generar el reporte?")
            if not CustomAskYesNoDialog.show(modal_master, "Confirmar Cancelación", confirm_msg):
                return

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO AvancesEfectivo (monto_entregado, comision, monto_total, metodo_pago, fecha_hora, estado)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (monto_entregado, comision, monto_total, metodo_pago, fecha_hora, estado))
            self.conn.commit()

            # --- Generar Reporte de Confirmación ---
            reporte_resumido = (
                f"ESTADO: {estado}\n"
                f"Total Entregado: Bs. {monto_entregado:,.2f}\n"
                f"Total a Pagar: Bs. {monto_total:,.2f}\n"
                f"Método: {metodo_pago if estado == 'Concretado' else 'N/A'}"
            )
            
            # ⭐ MODAL DE INFORMACIÓN MODERNIZADO Y RESUMIDO
            CustomMessageDialog(modal_master, 
                                "✅ Reporte Generado", 
                                f"La transacción ha sido registrada con éxito como '{estado}'.\n\nDetalles:\n{reporte_resumido}", 
                                'info')
            self._reset_fields()

        except Exception as e:
            # ⭐ MODAL DE ERROR MODERNIZADO
            self.conn.rollback()
            CustomMessageDialog(modal_master, "Error DB", f"Error al registrar el avance: {e}", 'error')

    def concretar_avance(self):
        self._register_advance('Concretado')

    def cancelar_avance(self):
        self._register_advance('Cancelado')

    def _reset_fields(self):
        self.monto_entregar_entry.delete(0, ctk.END)
        self.comision_label.configure(text="Bs. 0.00")
        self.total_label.configure(text="Bs. 0.00")
        self.reset_focus()