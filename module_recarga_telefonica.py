# module_recarga_telefonica.py (NUEVO ARCHIVO COMPLETO)

import customtkinter as ctk
import datetime
import sqlite3
from tkinter import Toplevel # Necesario para asegurar la correcta herencia de Toplevel
# Asumimos que utils.py está en el mismo directorio.
from utils import setup_db, DB_NAME 

# ===================================================================
# --- 1. CLASES: VENTANAS MODALES MODERNAS (CTKTOPLEVEL) ---
# (Copiadas del código original para autonomía)
# ===================================================================

class CustomMessageDialog(ctk.CTkToplevel):
    """Ventana modal moderna para mensajes de información o error (Info/Error)."""
    # ... (El código de CustomMessageDialog se mantiene igual)
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
        if self.dialog_type == 'info':
            color = "#10B981"
            icon = "✅"
        elif self.dialog_type == 'error':
            color = "#EF4444"
            icon = "❌"
        else:
            color = "#FACC15" 
            icon = "ℹ️"
        
        ctk.CTkLabel(self, 
                     text=f"{icon} {self.title()}", 
                     font=ctk.CTkFont(size=24, weight="bold"), 
                     text_color=color).pack(pady=(20, 10))
        
        textbox = ctk.CTkTextbox(self, 
                       height=80, 
                       width=400,
                       font=ctk.CTkFont(size=14),
                       wrap="word")
        textbox.pack(padx=20, pady=10)
        textbox.insert("0.0", self.message)
        textbox.configure(state="disabled")
        
        ctk.CTkButton(self, 
                      text="Aceptar", 
                      font=ctk.CTkFont(size=18, weight="bold"),
                      width=150,
                      command=self.destroy).pack(pady=20)
        
        self.bind('<Return>', lambda event: self.destroy())


class CustomAskYesNoDialog(ctk.CTkToplevel):
    """Ventana modal moderna para confirmación (Sí/No)."""
    # ... (El código de CustomAskYesNoDialog se mantiene igual)
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
# --- 2. CLASE DEL MÓDULO: RecargaTelefonicaModule ---
# ===================================================================

class RecargaTelefonicaModule(ctk.CTkFrame):
    
    TASA_COMISION = 0.15  # 15% de comisión
    PREFIJOS = ["0414", "0424", "0412", "0422", "0416", "0426"]

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        # Se conecta a la DB al iniciar el módulo
        self.conn = setup_db() 
        
        self.create_widgets()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1) 

        # Cabecera
        ctk.CTkLabel(self, text="📞 MÓDULO DE RECARGA TELEFÓNICA", 
                     font=ctk.CTkFont(size=34, weight="bold")).grid(row=0, column=0, pady=30, sticky="n")

        # Frame Principal de Operación
        operation_frame = ctk.CTkFrame(self, fg_color="#292F38", corner_radius=15) 
        operation_frame.grid(row=1, column=0, padx=60, pady=20, sticky="nsew") 
        operation_frame.grid_columnconfigure((0, 1), weight=1)
        
        # --- ENTRADA DE NÚMERO DE TELÉFONO ---
        ctk.CTkLabel(operation_frame, text="Número de Teléfono (Prefijo + Resto)", 
                     font=ctk.CTkFont(size=24, weight="bold"), text_color="#B0BEC5").grid(row=0, column=0, columnspan=2, pady=(30, 5), sticky="w", padx=30)
        
        phone_input_frame = ctk.CTkFrame(operation_frame, fg_color="transparent")
        phone_input_frame.grid(row=1, column=0, columnspan=2, padx=30, pady=(0, 20), sticky="ew")
        phone_input_frame.grid_columnconfigure(0, weight=0) 
        phone_input_frame.grid_columnconfigure(1, weight=1) 
        
        # Input 1: Prefijo (OptionMenu)
        self.prefijo_var = ctk.StringVar(value=self.PREFIJOS[0])
        self.prefijo_option = ctk.CTkOptionMenu(phone_input_frame, 
                                                    values=self.PREFIJOS, 
                                                    variable=self.prefijo_var, 
                                                    font=ctk.CTkFont(size=20),
                                                    height=60)
        self.prefijo_option.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        # Input 2: Resto del Número (Entry)
        self.resto_numero_entry = ctk.CTkEntry(phone_input_frame,
                                                 placeholder_text="Resto del número (7 dígitos)",
                                                 font=ctk.CTkFont(size=28), 
                                                 height=60, 
                                                 corner_radius=10)
        self.resto_numero_entry.grid(row=0, column=1, sticky="ew")
        
        # --- ENTRADA DE MONTO A RECARGAR ---
        ctk.CTkLabel(operation_frame, text="Monto Base de Recarga (Bs.)", 
                     font=ctk.CTkFont(size=24, weight="bold"), text_color="#B0BEC5").grid(row=2, column=0, columnspan=2, pady=(10, 5), sticky="w", padx=30)

        self.monto_recarga_entry = ctk.CTkEntry(operation_frame,
                                                 placeholder_text="Ej: 50.00",
                                                 font=ctk.CTkFont(size=28), 
                                                 height=60, 
                                                 corner_radius=10)
        self.monto_recarga_entry.grid(row=3, column=0, columnspan=2, padx=30, pady=(0, 30), sticky="ew")
        
        self.monto_recarga_entry.bind('<KeyRelease>', self.calculate_total)
        
        # --- RESULTADOS DEL CÁLCULO ---
        ctk.CTkLabel(operation_frame, text="COMISIÓN (15%):", 
                     font=ctk.CTkFont(size=22), text_color="#B0BEC5").grid(row=4, column=0, sticky="w", padx=30, pady=(15, 5))
        self.comision_label = ctk.CTkLabel(operation_frame, text="Bs. 0.00", text_color="#FACC15", 
                                            font=ctk.CTkFont(size=30, weight="bold"))
        self.comision_label.grid(row=4, column=1, sticky="e", padx=30, pady=(15, 5))

        ctk.CTkLabel(operation_frame, text="MONTO TOTAL A COBRAR:", 
                     font=ctk.CTkFont(size=28, weight="bold"), text_color="#B0BEC5").grid(row=5, column=0, sticky="w", padx=30, pady=(20, 10))
        self.total_label = ctk.CTkLabel(operation_frame, text="Bs. 0.00", text_color="#10B981", 
                                        font=ctk.CTkFont(size=44, weight="bold")) 
        self.total_label.grid(row=5, column=1, sticky="e", padx=30, pady=(20, 10))        
        
        # --- Botón de Acción ---
        ctk.CTkButton(operation_frame, text="✅ REALIZAR RECARGA", command=self.realizar_recarga, 
                      fg_color="#10B981", hover_color="#059669", font=ctk.CTkFont(size=22, weight="bold"), 
                      height=60).grid(row=6, column=0, columnspan=2, pady=(40, 30), padx=30, sticky="ew")

    # --- MÉTODOS DE LÓGICA (Idénticos a los definidos en la respuesta anterior) ---
    def reset_focus(self):
        self.after(100, self.monto_recarga_entry.focus_set) 

    def calculate_total(self, event=None):
        try:
            monto_base = float(self.monto_recarga_entry.get().replace(',', '.')) 
        except ValueError:
            self.comision_label.configure(text="Bs. 0.00")
            self.total_label.configure(text="Bs. 0.00")
            return

        comision = monto_base * self.TASA_COMISION
        monto_total = monto_base + comision

        self.comision_label.configure(text=f"Bs. {comision:,.2f}") 
        self.total_label.configure(text=f"Bs. {monto_total:,.2f}")

    def _get_transaction_data(self):
        modal_master = self.controller 
        
        try:
            monto_base = float(self.monto_recarga_entry.get().replace(',', '.'))
            if monto_base <= 0:
                CustomMessageDialog(modal_master, "Error", "El monto de recarga debe ser positivo.", 'error')
                return None, None, None, None, None
        except ValueError:
            CustomMessageDialog(modal_master, "Error", "Ingrese un monto válido de recarga.", 'error')
            return None, None, None, None, None
            
        prefijo = self.prefijo_var.get()
        resto = self.resto_numero_entry.get().strip()
        numero_completo = prefijo + resto

        if not resto.isdigit() or len(resto) != 7:
            CustomMessageDialog(modal_master, "Error", "El resto del número debe ser de 7 dígitos numéricos.", 'error')
            return None, None, None, None, None
        
        comision = monto_base * self.TASA_COMISION
        monto_total = monto_base + comision
        
        return monto_base, comision, monto_total, prefijo, numero_completo

    def _register_recharge(self):
        monto_base, comision, monto_total, prefijo, numero_completo = self._get_transaction_data()
        
        if monto_base is None:
            return

        modal_master = self.controller 
        confirm_msg = (f"Recarga: {numero_completo}\n"
                       f"Monto Base: Bs. {monto_base:,.2f}\n"
                       f"Comisión: Bs. {comision:,.2f}\n"
                       f"Total a Cobrar: Bs. {monto_total:,.2f}\n\n"
                       f"¿El cliente ha realizado el pago correspondiente?")
        
        if not CustomAskYesNoDialog.show(modal_master, "Confirmar Pago", confirm_msg): 
            CustomMessageDialog(modal_master, "Transacción Cancelada", "El pago no fue confirmado. La recarga no se registró.", 'info')
            return

        estado = 'Concretado'
        fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO RecargasTelefonicas (numero, monto_base, comision, monto_total, fecha_hora, estado)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (numero_completo, monto_base, comision, monto_total, fecha_hora, estado))
            self.conn.commit()

            reporte_resumido = (
                f"ESTADO: {estado}\n"
                f"Número: {numero_completo}\n"
                f"Monto Base: Bs. {monto_base:,.2f}\n"
                f"Total a Pagar: Bs. {monto_total:,.2f}"
            )
            
            CustomMessageDialog(modal_master, 
                                "✅ Recarga Exitosa", 
                                f"La recarga ha sido registrada con éxito.\n\nDetalles:\n{reporte_resumido}", 
                                'info')
            self._reset_fields()

        except Exception as e:
            self.conn.rollback()
            CustomMessageDialog(modal_master, "Error DB", f"Error al registrar la recarga: {e}", 'error')
            
    def realizar_recarga(self):
        self._register_recharge()

    def _reset_fields(self):
        self.monto_recarga_entry.delete(0, ctk.END)
        self.resto_numero_entry.delete(0, ctk.END)
        self.comision_label.configure(text="Bs. 0.00")
        self.total_label.configure(text="Bs. 0.00")
        self.reset_focus()


# ===================================================================
# --- 3. CLASE DE LA APLICACIÓN PRINCIPAL (STANDALONE) ---
# ===================================================================

class RecargaTelefonicaApp(ctk.CTk):
    """Aplicación principal que ejecuta el módulo de recarga de forma autónoma."""
    
    def __init__(self):
        super().__init__()
        
        # Configuración de la ventana principal
        self.title("Sistema Modular - Recarga Telefónica")
        self.geometry("1000x750")
        ctk.set_appearance_mode("Dark") 
        ctk.set_default_color_theme("blue")

        # Configurar la grid de la ventana principal
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Inicializar y mostrar el módulo de recarga
        self.recarga_module = RecargaTelefonicaModule(self, self) # self es parent, self es controller
        self.recarga_module.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.recarga_module.reset_focus()


if __name__ == "__main__":
    # Asegura la configuración inicial de la DB
    setup_db(DB_NAME) 
    app = RecargaTelefonicaApp()
    app.mainloop()