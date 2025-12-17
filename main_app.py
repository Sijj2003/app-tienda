# main_app.py (VERSIÓN FINAL)

import customtkinter as ctk
from tkinter import messagebox, Toplevel, simpledialog
import sys 

from utils import verify_password, check_license_key, check_license_file, create_license_file, setup_db 

from module_inventario import InventarioModule
from module_reportes import ReportesModule
from module_ventas import VentasModule
from module_consulta_precio import ConsultaPrecioModule
from module_avance_efectivo import AvanceEfectivoModule
from module_bcv_rate import BCVRateModule 
from module_recarga_telefonica import RecargaTelefonicaModule
from module_devolucion import DevolucionModule
from module_exportacion_reportes import ExportacionReportesModule


# ===================================================================
# --- 1. CLASES DE VENTANAS MODALES Y PÁGINAS ---
# ===================================================================

class LicenseAuthWindow(ctk.CTkToplevel):
    """Ventana modal para solicitar y verificar la clave de licencia."""
    def __init__(self, master, success_callback, failure_callback):
        super().__init__(master)
        self.title("Activación de Licencia")
        self.success_callback = success_callback 
        self.failure_callback = failure_callback
        
        self.transient(master) 
        self.grab_set() 
        
        window_width = 500
        window_height = 350
        self.geometry(f"{window_width}x{window_height}")
        self.resizable(False, False)
        
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 5), weight=1)

        ctk.CTkLabel(self, 
                     text="🔑 Activación del Sistema", 
                     font=ctk.CTkFont(size=24, weight="bold")).grid(row=1, column=0, padx=20, pady=(20, 10))
        
        ctk.CTkLabel(self, 
                     text="Ingrese la clave de licencia para iniciar la aplicación.", 
                     font=ctk.CTkFont(size=14)).grid(row=2, column=0, padx=20, pady=5)

        
        self.license_entry = ctk.CTkEntry(self, 
                                           placeholder_text="Clave de Licencia",
                                           width=400, 
                                           height=40, 
                                           font=ctk.CTkFont(size=16)) 
        self.license_entry.grid(row=3, column=0, padx=20, pady=(10, 20))
        
        ctk.CTkButton(self, 
                      text="Activar y Continuar", 
                      font=ctk.CTkFont(size=18, weight="bold"),
                      width=180,
                      height=45,
                      command=self.verify_license,
                      fg_color="#4CAF50",
                      hover_color="#45A049").grid(row=4, column=0, pady=(0, 20)) 
        
        self.license_entry.bind('<Return>', lambda event=None: self.verify_license())
        self.after(100, self.license_entry.focus_set) 
        
        self.protocol("WM_DELETE_WINDOW", self.on_close_attempt)

    def on_close_attempt(self):
        messagebox.showerror("Acceso Restringido", "Debe ingresar una clave de licencia válida para cerrar esta ventana e iniciar la aplicación.")
        
    def verify_license(self):
        # Lógica de verificación
        # ⭐ NO APLICAMOS .strip() AQUÍ. Confiamos en que check_license_key en utils.py lo haga.
        input_key = self.license_entry.get() 
        
        if check_license_key(input_key):
            create_license_file()
            self.success_callback()
            self.destroy()
        else:
            messagebox.showerror("Licencia Inválida", "Clave de licencia incorrecta. La aplicación se cerrará.", parent=self)
            self.failure_callback() 

# --- El resto de las clases de ventanas (AdminAuthWindow, StartPage, MenuPageBase, etc.) permanece SIN CAMBIOS ---

class AdminAuthWindow(ctk.CTkToplevel):
    def __init__(self, master, callback):
        super().__init__(master)
        self.title("Acceso de Administrador")
        self.callback = callback 
        
        self.transient(master) 
        self.grab_set() 
        
        window_width = 450 
        window_height = 300 
        self.geometry(f"{window_width}x{window_height}")
        self.resizable(False, False)
        
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 4), weight=1)

        ctk.CTkLabel(self, 
                     text="🔐 Acceso Administrativo", 
                     font=ctk.CTkFont(size=24, weight="bold")).grid(row=1, column=0, padx=20, pady=(20, 10))
        
        self.password_entry = ctk.CTkEntry(self, 
                                           placeholder_text="Ingrese Contraseña",
                                           width=300, 
                                           height=40, 
                                           font=ctk.CTkFont(size=18), 
                                           show="*")
        self.password_entry.grid(row=2, column=0, padx=20, pady=(10, 20))
        
        ctk.CTkButton(self, 
                      text="Acceder", 
                      font=ctk.CTkFont(size=18, weight="bold"),
                      width=120,
                      height=40,
                      command=self.authenticate,
                      hover_color="#3B8ED4").grid(row=3, column=0, pady=(0, 20)) 
        
        self.password_entry.bind('<Return>', lambda event=None: self.authenticate())
        self.after(100, self.password_entry.focus_set) 

    def authenticate(self):
        password = self.password_entry.get()
        if verify_password(password):
            self.callback()
            self.destroy()
        else:
            messagebox.showerror("Error de Clave", "Clave incorrecta. Intente de nuevo.", parent=self)
            self.password_entry.delete(0, ctk.END)


class StartPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=0, column=0, padx=50, pady=50, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(content_frame, 
                     text="Bienvenido al Sistema de Gestión de Tienda", 
                     font=ctk.CTkFont(size=36, weight="bold"),
                     text_color="#3B8ED4").pack(pady=(50, 20)) 
        
        ctk.CTkLabel(content_frame, 
                     text="Navegue usando las opciones del menú lateral.", 
                     font=ctk.CTkFont(size=20),
                     text_color="gray").pack(pady=10)
        
        ctk.CTkFrame(content_frame, height=2, fg_color="gray").pack(fill="x", padx=100, pady=30)
        
        ctk.CTkButton(content_frame, 
                      text="🚀 INICIAR VENTA RÁPIDA", 
                      font=ctk.CTkFont(size=24, weight="bold"), 
                      width=450, 
                      height=80,
                      fg_color="#4CAF50", 
                      hover_color="#45A049",
                      command=lambda: controller.show_frame("VentasModule")).pack(pady=(20, 50))


class MenuPageBase(ctk.CTkFrame):
    def __init__(self, parent, controller, title, buttons_data):
        super().__init__(parent)
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self, 
                     text=title, 
                     font=ctk.CTkFont(size=32, weight="bold"),
                     text_color="#3B8ED4").pack(pady=(50, 60))
        
        button_container = ctk.CTkFrame(self, fg_color="transparent")
        button_container.pack(pady=20, padx=20)
        
        button_font = ctk.CTkFont(size=22, weight="bold")
        
        for text, command, fg_color, hover_color in buttons_data:
            ctk.CTkButton(button_container, 
                          text=text, 
                          font=button_font,
                          width=380, 
                          height=70,
                          fg_color=fg_color,
                          hover_color=hover_color,
                          command=command).pack(pady=15)

class AdministracionMenu(MenuPageBase):
    def __init__(self, parent, controller):
        buttons = [
            ("📦 Inventario", lambda: controller.show_frame("InventarioModule"), "#3B8ED4", "#36719F"),
            ("📊 Reportes", lambda: controller.show_frame("ReportesModule"), "#3B8ED4", "#36719F"),
            ("💵 BCV Tasa", lambda: controller.show_frame("BCVRateModule"), "#FFC107", "#FFB300"), 
            ("📄 Exportar Reportes", lambda: controller.show_frame("Exportacion"), "#16A085", "#1ABC9C"),
            ("🔒 Cerrar Sesión Administrador", controller.admin_logout, "#D32F2F", "#B71C1C"),
        ]
        super().__init__(parent, controller, "Menú de Administración", buttons)


class CajaMenu(MenuPageBase):
    def __init__(self, parent, controller):
        buttons = [
            ("🛒 Ventas", lambda: controller.show_frame("VentasModule"), "#4CAF50", "#45A049"), 
            ("↩️ Devolución Rápida", lambda: controller.show_frame("DevolucionModule"), "#E74C3C", "#C0392B"),
            ("🔍 Consulta de Precio", lambda: controller.show_frame("ConsultaPrecioModule"), "#3B8ED4", "#36719F"),
            ("💸 Avance de Efectivo", lambda: controller.show_frame("AvanceEfectivoModule"), "#FF9800", "#FB8C00"), 
            ("📱 Recarga Telefónica", lambda: controller.show_frame("RecargaTelefonicaModule"), "#9C27B0", "#7B1FA2"),
        ]
        super().__init__(parent, controller, "Menú de Caja", buttons)


# ===================================================================
# --- 2. CLASE PRINCIPAL DE LA APLICACIÓN (CONTROLADOR) ---
# ===================================================================

class MainApplication(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        self.title("Inversiones Martinez - Gestión de Tienda")
        self.geometry("1200x800") 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        self.admin_logged_in = False 
        
        self.db_conn = setup_db() 
        if self.db_conn is None:
            messagebox.showerror("Error Crítico", "No se pudo inicializar la base de datos. Cerrando aplicación.")
            self.after(100, self.on_closing)
            return

        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#2C3E50") 
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)
        
        ctk.CTkLabel(self.sidebar_frame, 
                     text="INVERSIONES MARTINEZ", 
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="white").grid(row=0, column=0, padx=20, pady=30)

        sidebar_btn_font = ctk.CTkFont(size=20, weight="bold")
        
        self.btn_administrador = ctk.CTkButton(self.sidebar_frame, 
                                               text="👤 Administración", 
                                               font=sidebar_btn_font,
                                               fg_color="transparent",
                                               hover_color="#34495E",
                                               anchor="w", 
                                               command=self.handle_admin_click) 
        self.btn_administrador.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        self.btn_caja = ctk.CTkButton(self.sidebar_frame, 
                                      text="💵 Caja", 
                                      font=sidebar_btn_font,
                                      fg_color="transparent",
                                      hover_color="#34495E",
                                      anchor="w",
                                      command=lambda: self.show_frame("CajaMenu"))
        self.btn_caja.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        
        self.bcv_display_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="#F39C12", corner_radius=10) 
        self.bcv_display_frame.grid(row=3, column=0, padx=20, pady=30, sticky="ew") 
        
        ctk.CTkLabel(self.bcv_display_frame, 
                     text="TASA BCV OFICIAL:", 
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="black").pack(padx=10, pady=(10, 2))
        
        self.bcv_rate_display = ctk.CTkLabel(self.bcv_display_frame, 
                                             text="Bs. ---", 
                                             font=ctk.CTkFont(size=28, weight="bold"),
                                             text_color="black")
        self.bcv_rate_display.pack(padx=10, pady=(0, 10))


        self.btn_cerrar_app = ctk.CTkButton(self.sidebar_frame, 
                      text="🛑 Cerrar Aplicación", 
                      font=ctk.CTkFont(size=18, weight="bold"),
                      fg_color="#C0392B", 
                      hover_color="#A93226",
                      command=self.on_closing) 
        self.btn_cerrar_app.grid(row=7, column=0, padx=20, pady=20, sticky="s")


        self.main_content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        
        frames_list = {
            "StartPage": StartPage,
            "AdministracionMenu": AdministracionMenu,
            "CajaMenu": CajaMenu,
            "InventarioModule": InventarioModule,
            "ReportesModule": ReportesModule,
            "VentasModule": VentasModule,
            "ConsultaPrecioModule": ConsultaPrecioModule,
            "AvanceEfectivoModule": AvanceEfectivoModule,
            "BCVRateModule": BCVRateModule,
            "RecargaTelefonicaModule": RecargaTelefonicaModule,
            "DevolucionModule": DevolucionModule,
            "Exportacion": ExportacionReportesModule,
        }

        for name, F_class in frames_list.items():
            frame = F_class(self.main_content_frame, self) 
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")
        
        self.load_initial_bcv_rate() 
        self.start_bcv_auto_update() 
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing) 

    def on_closing(self):
        ventas_module = self.frames.get("VentasModule")
        
        if ventas_module and hasattr(ventas_module, 'handle_app_close_event'):
            if ventas_module.handle_app_close_event():
                self.destroy()
            return
        
        self.destroy()

    def show_frame(self, page_name):
        current_frame_name = self.get_current_frame_name()
        
        ventas_module = self.frames.get("VentasModule")
        
        if current_frame_name == "VentasModule" and ventas_module and page_name not in ["VentasModule", "CajaMenu"]:
            if hasattr(ventas_module, 'is_sale_active') and ventas_module.is_sale_active(): 
                messagebox.showwarning(
                    "Venta Pendiente", 
                    "No puede salir del módulo de Ventas con productos en el carrito.\n"
                    "Debe finalizar la venta o **CANCELAR COMPRA** primero."
                )
                self.frames["VentasModule"].tkraise() 
                return 

        if page_name == "VentasModule":
            self.btn_administrador.grid_remove()
            self.btn_caja.grid_remove()
            self.bcv_display_frame.grid_remove() 
            self.btn_cerrar_app.grid_remove() 
        else:
            self.btn_administrador.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
            self.btn_caja.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
            self.bcv_display_frame.grid(row=3, column=0, padx=20, pady=30, sticky="ew")
            self.btn_cerrar_app.grid(row=7, column=0, padx=20, pady=20, sticky="s")

        admin_frames = ["AdministracionMenu", "InventarioModule", "ReportesModule", "BCVRateModule"]
        
        is_leaving_admin = (current_frame_name in admin_frames) and (page_name not in admin_frames)

        if is_leaving_admin and self.admin_logged_in:
            self.admin_logged_in = False

        frame = self.frames[page_name]
        frame.tkraise()
        
        if hasattr(frame, 'reset_focus'):
            frame.reset_focus()
        elif hasattr(frame, 'focus_barcode_entry'): 
            frame.focus_barcode_entry()

    def get_current_frame_name(self):
        for name, frame in self.frames.items():
            if frame.winfo_ismapped():
                return name
        return "StartPage" 

    def admin_login_success(self):
        self.admin_logged_in = True
        self.show_frame("AdministracionMenu")

    def handle_admin_click(self):
        if self.admin_logged_in:
            self.show_frame("AdministracionMenu")
            return
        
        AdminAuthWindow(self, self.admin_login_success)

    def admin_logout(self):
        self.admin_logged_in = False
        self.show_frame("StartPage")
        messagebox.showinfo("Sesión Cerrada", "La sesión de administrador ha sido cerrada manualmente.")

    def update_sidebar_bcv_rate(self, tasa):
        if tasa is not None:
            self.bcv_rate_display.configure(text=f"Bs. {tasa:,.4f}")
        else:
            self.bcv_rate_display.configure(text="Bs. N/D")

    def get_latest_rate_from_module(self):
        bcv_module = self.frames.get("BCVRateModule")
        if bcv_module and hasattr(bcv_module, 'get_latest_rate_from_db'): 
            return bcv_module.get_latest_rate_from_db() 
        return None

    def refresh_bcv_rate_from_db(self):
        latest_rate = self.get_latest_rate_from_module()
        self.update_sidebar_bcv_rate(latest_rate)
        
    def load_initial_bcv_rate(self):
        self.refresh_bcv_rate_from_db()

    def start_bcv_auto_update(self):
        self.update_bcv_rate()
        
        UPDATE_INTERVAL_MS = 3600000 
        self.after(UPDATE_INTERVAL_MS, self.start_bcv_auto_update)

    def update_bcv_rate(self):
        tasa_scraped = BCVRateModule.get_current_rate_api()
        
        if tasa_scraped is not None:
            bcv_module = self.frames.get("BCVRateModule")
            if bcv_module:
                bcv_module.check_and_update_rate_scheduled(tasa_scraped)
            
            self.refresh_bcv_rate_from_db()
            
        else:
            self.refresh_bcv_rate_from_db() 


# ⭐ PUNTO DE ENTRADA MODIFICADO
def start_app():
    """Función de arranque que maneja la verificación de licencia."""
    temp_root = ctk.CTk()
    temp_root.withdraw()

    def license_success():
        """Llamado si la licencia es válida o ya existe el archivo."""
        temp_root.destroy()
        app = MainApplication()
        app.mainloop()

    def license_failure():
        """Llamado si la licencia falla."""
        temp_root.destroy()
        sys.exit(1)

    if check_license_file():
        license_success()
    else:
        LicenseAuthWindow(temp_root, license_success, license_failure)
        temp_root.mainloop()


if __name__ == "__main__":
    start_app()