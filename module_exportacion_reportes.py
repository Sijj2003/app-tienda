import customtkinter as ctk
# Importamos filedialog para el diálogo nativo de "Guardar como..."
from tkinter import messagebox, ttk, Toplevel, filedialog
import sqlite3
import datetime
import calendar 
import os 

# Importación del calendario
try:
    from tkcalendar import Calendar
    CALENDAR_INSTALLED = True
except ImportError:
    CALENDAR_INSTALLED = False
    messagebox.showerror("Error de Dependencia", 
                         "La librería 'tkcalendar' no está instalada.\n"
                         "Por favor, instale la dependencia usando: pip install tkcalendar")
    # Clase simulada (Mock)
    class Calendar:
        def __init__(self, *args, **kwargs): pass
        def pack(self, *args, **kwargs): pass
        def selection_get(self): return datetime.date.today()

# Importación de la librería PDF (fpdf2)
try:
    from fpdf import FPDF 
    PDF_INSTALLED = True # Bandera de estado de la dependencia
except ImportError:
    PDF_INSTALLED = False
    # Definición de la clase Mock (simulada) para evitar fallos si no está instalada fpdf2
    class FPDF:
        def __init__(self, *args, **kwargs): pass
        def set_font(self, *args): pass
        def cell(self, *args, **kwargs): pass
        def add_page(self): pass
        def set_fill_color(self, *args): pass
        def set_text_color(self, *args): pass
        def output(self, *args): pass
        def rect(self, *args): pass
        def ln(self, *args): pass
        def get_y(self): return 0

# Asume que 'utils.py' contiene la configuración de la DB
from utils import setup_db, DB_NAME 
# Importamos el módulo de tasas para acceder a la lógica de DB (TasasBCV)
try:
    from module_bcv_rate import BCVRateModule 
except ImportError:
    # Clase mock si no existe para evitar el crash
    class MockBCVRateModule:
        def __init__(self, *args, **kwargs): pass
        def get_latest_rate_from_db(self): return None
    BCVRateModule = MockBCVRateModule


# --- ESTILOS DE FUENTE Y COLORES (CONSISTENTES) ---
DARK_BLUE_SOBRIO = "#34495E"
TEAL_SOBRIO = "#16A085"
GRAY_LIGHT = "#ECF0F1"
RED_ERROR = "#D35400"
GREEN_SUCCESS = "#27AE60"
FONT_SIZE_ACCESSIBLE = 18

# ===================================================================
# --- CLASE DE VENTANA MODAL PARA CALENDARIO ---
# ===================================================================

class CalendarModal(ctk.CTkToplevel):
    def __init__(self, master, current_date, callback, title="Seleccionar Fecha"):
        super().__init__(master, fg_color=master.cget("fg_color"))
        self.title(title)
        self.callback = callback
        
        # Lógica de centrado de la ventana y dimensiones mayores
        window_width = 400
        window_height = 480 
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        self.resizable(False, False)
        self.transient(master) 
        self.grab_set() 
        
        try:
            initial_date = datetime.datetime.strptime(current_date, "%Y-%m-%d").date()
        except:
            initial_date = datetime.date.today()
        
        # Contenedor CTkFrame con bordes suaves para un mejor look
        calendar_container = ctk.CTkFrame(self, corner_radius=15)
        calendar_container.pack(pady=20, padx=20, fill="both", expand=True)
        
        ctk.CTkLabel(calendar_container, text="Seleccione un día del calendario:", 
                     font=ctk.CTkFont(size=FONT_SIZE_ACCESSIBLE, weight="bold")).pack(pady=(10, 5))

        # TkCalendar widget 
        self.cal = Calendar(calendar_container, 
                            selectmode='day',
                            year=initial_date.year, 
                            month=initial_date.month, 
                            day=initial_date.day,
                            date_pattern='y-mm-dd',
                            font=('Helvetica', 14)) 
        self.cal.pack(pady=10, padx=10, fill="both", expand=True)

        # Botón de Aceptar (Estilizado)
        ctk.CTkButton(self, text="Aceptar Fecha", command=self._on_date_select, 
                      fg_color=GREEN_SUCCESS, hover_color="#229954", 
                      height=40, corner_radius=10, 
                      font=ctk.CTkFont(size=FONT_SIZE_ACCESSIBLE)).pack(pady=(0, 15), padx=20, fill='x')

    def _on_date_select(self):
        selected_date = self.cal.selection_get().strftime("%Y-%m-%d")
        self.callback(selected_date)
        self.destroy()

# ===================================================================
# --- CLASE HELPER PARA GENERACIÓN DE PDF ---
# ===================================================================

class PDFReportGenerator(FPDF):
    """Clase personalizada para generar reportes con formato profesional."""

    def __init__(self, title, date_range, rate_info):
        super().__init__('P', 'mm', 'A4')
        self.title = title
        self.date_range = date_range
        self.rate_info = rate_info
        
        self.WIDTH = 210 
        self.HEIGHT = 297 
        self.MARGIN = 10
        
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        self.write_header()

    def header(self):
        # Logo o título principal
        self.set_font('Arial', 'B', 15)
        self.set_text_color(52, 73, 94) 
        self.cell(0, 5, 'INVERSIONES MARTINEZ', 0, 1, 'L')
        
        # Línea de separación
        self.ln(2)
        self.set_fill_color(52, 73, 94)
        self.rect(self.MARGIN, self.get_y(), self.WIDTH - 2 * self.MARGIN, 0.5, 'F')
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(127, 140, 141) 
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', 0, 0, 'C')
        self.set_x(self.MARGIN)
        self.cell(0, 10, 'Generado por Sistema de Gestión Martinez', 0, 0, 'R')

    def write_header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(22, 160, 133) 
        self.cell(0, 8, self.title, 0, 1, 'L')
        
        self.set_font('Arial', '', 11)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, f'Período: {self.date_range}', 0, 1, 'L')
        self.cell(0, 6, self.rate_info, 0, 1, 'L')
        self.ln(5)
    
    def title_section(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(236, 240, 241) 
        self.set_text_color(52, 73, 94)
        self.cell(0, 7, title, 0, 1, 'L', 1)
        self.ln(1)

    def write_table(self, header, data, col_widths, align='L'):
        # Cabecera
        self.set_font('Arial', 'B', 9)
        self.set_fill_color(52, 73, 94) 
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(header):
            self.cell(col_widths[i], 7, h, 1, 0, 'C', 1)
        self.ln()

        # Filas de datos
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)
        fill = False
        for row in data:
            self.set_fill_color(236, 240, 241) if fill else self.set_fill_color(255, 255, 255)
            for i, item in enumerate(row):
                if item is None: item = ''
                
                # Alineación a la derecha para montos
                if i in [len(row)-1, len(row)-2]:
                    self.cell(col_widths[i], 6, str(item), 'LR', 0, 'R', fill)
                else:
                    self.cell(col_widths[i], 6, str(item), 'LR', 0, align, fill)
            self.ln()
            fill = not fill
        # Línea de cierre
        self.cell(sum(col_widths), 0, '', 'T', 1, 'L')
        self.ln(3)


# ===================================================================
# --- CLASE PRINCIPAL: ExportacionReportesModule (Resumen Ejecutivo) ---
# ===================================================================

class ExportacionReportesModule(ctk.CTkFrame):
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.conn = setup_db() 
        self.bcv_rate_module = BCVRateModule(parent=self, controller=None)
        self.current_summary_data = {} 
        self.current_date_range = ("", "") 
        today_str = datetime.date.today().strftime("%Y-%m-%d") 
        self.selected_day = today_str # Para 'Día'
        self.selected_start_day = today_str # Para 'Período Personalizado'
        self.selected_end_day = today_str # Para 'Período Personalizado'

        self.create_widgets()
        self.load_summary_data()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) 

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=30, pady=(35, 20), sticky="ew")
        header_frame.grid_columnconfigure((0, 2), weight=1)
        
        ctk.CTkLabel(header_frame, 
                     text="📈 Resumen Ejecutivo y Exportación", 
                     font=ctk.CTkFont(size=35, weight="bold"),
                     text_color=DARK_BLUE_SOBRIO).grid(row=0, column=0, sticky="w")
        
        # Botones de Acción
        action_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        action_frame.grid(row=0, column=2, sticky="e")
        
        ctk.CTkButton(action_frame, 
                      text="🔄 Recargar", 
                      command=self.load_summary_data,
                      fg_color=DARK_BLUE_SOBRIO,
                      hover_color="#5D6D7E",
                      height=40,
                      font=ctk.CTkFont(size=FONT_SIZE_ACCESSIBLE, weight="bold")
                      ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(action_frame, 
                      text="📄 Exportar a PDF", 
                      command=self.export_to_pdf,
                      fg_color=GREEN_SUCCESS,
                      hover_color="#1ABC9C",
                      height=40,
                      font=ctk.CTkFont(size=FONT_SIZE_ACCESSIBLE, weight="bold")
                      ).pack(side="left")
                      
        # ----------------------------------------------------------------------
        # --- Panel de Opciones de Filtro (Fecha y Período) ---
        # ----------------------------------------------------------------------
        filter_frame = ctk.CTkFrame(self, fg_color=GRAY_LIGHT, corner_radius=10)
        filter_frame.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="ew")
        filter_frame.columnconfigure(0, weight=0) # Período
        filter_frame.columnconfigure(1, weight=1) # Controles de Fecha
        filter_frame.columnconfigure(2, weight=0) # Botón Aplicar
        
        # Filtro de Período
        ctk.CTkLabel(filter_frame, 
                     text="Período:", 
                     font=ctk.CTkFont(size=FONT_SIZE_ACCESSIBLE, weight="bold"),
                     text_color=DARK_BLUE_SOBRIO).grid(row=0, column=0, padx=(20, 5), pady=15, sticky="w")
        
        self.period_combobox = ctk.CTkComboBox(filter_frame,
                                              values=["Día", "Período Personalizado", "Mes"], # OPCIONES MODIFICADAS
                                              command=self._on_period_change,
                                              width=200,
                                              height=35,
                                              font=ctk.CTkFont(size=FONT_SIZE_ACCESSIBLE))
        self.period_combobox.set("Día")
        self.period_combobox.grid(row=0, column=0, padx=(100, 20), pady=15, sticky="w")
        
        # Controles de Fecha (Inicio/Fin o Día)
        date_control_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        date_control_frame.grid(row=0, column=1, padx=(5, 5), pady=15, sticky="w")
        
        # Control de Fecha de INICIO / DÍA
        self.label_date_start = ctk.CTkLabel(date_control_frame, 
                     text="Fecha seleccionada:", 
                     font=ctk.CTkFont(size=FONT_SIZE_ACCESSIBLE, weight="bold"),
                     text_color=DARK_BLUE_SOBRIO)
        self.label_date_start.pack(side="left", padx=(0, 10))
        
        self.date_display_label = ctk.CTkLabel(date_control_frame,
                                               text=self.selected_day,
                                               width=120,
                                               fg_color="#DDE3E9",
                                               corner_radius=5,
                                               font=ctk.CTkFont(size=FONT_SIZE_ACCESSIBLE))
        self.date_display_label.pack(side="left", padx=(0, 5))

        self.calendar_button = ctk.CTkButton(date_control_frame,
                                             text="📅", 
                                             command=lambda: self._open_calendar_modal("start"),
                                             width=35,
                                             height=35,
                                             fg_color=DARK_BLUE_SOBRIO,
                                             hover_color="#5D6D7E")
        self.calendar_button.pack(side="left", padx=(0, 15))
        
        # Control de Fecha de FIN (solo para Período Personalizado)
        self.label_date_end = ctk.CTkLabel(date_control_frame, 
                     text="Fin:", 
                     font=ctk.CTkFont(size=FONT_SIZE_ACCESSIBLE, weight="bold"),
                     text_color=DARK_BLUE_SOBRIO)
        # self.label_date_end.pack(side="left", padx=(0, 10)) # Inicialmente oculto
        
        self.date_display_label_end = ctk.CTkLabel(date_control_frame,
                                               text=self.selected_end_day,
                                               width=120,
                                               fg_color="#DDE3E9",
                                               corner_radius=5,
                                               font=ctk.CTkFont(size=FONT_SIZE_ACCESSIBLE))
        # self.date_display_label_end.pack(side="left", padx=(0, 5)) # Inicialmente oculto

        self.calendar_button_end = ctk.CTkButton(date_control_frame,
                                             text="📅", 
                                             command=lambda: self._open_calendar_modal("end"),
                                             width=35,
                                             height=35,
                                             fg_color=DARK_BLUE_SOBRIO,
                                             hover_color="#5D6D7E")
        # self.calendar_button_end.pack(side="left") # Inicialmente oculto

        # Botón APLICAR
        ctk.CTkButton(filter_frame, 
                      text="APLICAR", 
                      command=self.load_summary_data,
                      fg_color=TEAL_SOBRIO,
                      hover_color="#138D75",
                      height=35,
                      font=ctk.CTkFont(size=FONT_SIZE_ACCESSIBLE, weight="bold")
                      ).grid(row=0, column=2, padx=(10, 20), pady=15, sticky="e")
                      
        # Configuración del Treeview para el resumen
        style = ttk.Style(self)
        style.theme_use("clam") 
        style.configure("Summary.Treeview.Heading", 
                            font=('Helvetica', FONT_SIZE_ACCESSIBLE + 2, 'bold'), 
                            background=DARK_BLUE_SOBRIO, 
                            foreground="white",
                            rowheight=50) 
        style.configure("Summary.Treeview", 
                            font=('Helvetica', FONT_SIZE_ACCESSIBLE), 
                            rowheight=45,
                            background="#ECF0F1", 
                            foreground="#2C3E50") 
        style.map('Summary.Treeview', background=[('selected', DARK_BLUE_SOBRIO)])
        
        self.summary_tree = ttk.Treeview(self, 
                                         columns=("Concepto", "Total BS", "Total USD"), 
                                         show='headings', 
                                         style="Summary.Treeview")
        self.summary_tree.heading("Concepto", text="CONCEPTO")
        self.summary_tree.heading("Total BS", text="TOTAL BS.")
        self.summary_tree.heading("Total USD", text="TOTAL USD ($)")
        
        self.summary_tree.column("Concepto", width=300, anchor="w", stretch=True)
        self.summary_tree.column("Total BS", width=200, anchor="e", stretch=False)
        self.summary_tree.column("Total USD", width=200, anchor="e", stretch=False)
        
        self.summary_tree.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 30))
        
        self.rate_info_label = ctk.CTkLabel(self, 
                                             text="Tasa BCV utilizada para conversiones: N/A", 
                                             font=ctk.CTkFont(size=FONT_SIZE_ACCESSIBLE - 2, slant="italic"),
                                             text_color="#7F8C8D")
        self.rate_info_label.grid(row=3, column=0, padx=30, pady=(5, 10), sticky="w")
        
        # Inicializa la configuración de controles
        self._on_period_change("Día") 


    def _open_calendar_modal(self, date_type):
        """Abre la ventana modal del calendario para seleccionar una fecha (Inicio o Fin)."""
        if not CALENDAR_INSTALLED:
            messagebox.showerror("Error", "La librería 'tkcalendar' no está instalada.")
            return

        period = self.period_combobox.get()
        
        if period == "Mes":
            messagebox.showwarning("Advertencia", "No se puede seleccionar una fecha específica cuando el Período es 'Mes'.")
            return
            
        if period == "Día" and date_type == "end":
            # Esto no debería pasar si los controles están bien configurados, pero como seguridad.
            return 
        
        if date_type == "start":
            current_date = self.selected_day if period == "Día" else self.selected_start_day
            title = "Seleccionar Día" if period == "Día" else "Seleccionar Fecha de Inicio"
            
            def update_date(selected_date):
                if period == "Día":
                    self.selected_day = selected_date
                    self.date_display_label.configure(text=selected_date)
                elif period == "Período Personalizado":
                    self.selected_start_day = selected_date
                    self.date_display_label.configure(text=selected_date)
            
        else: # date_type == "end" (Solo para Período Personalizado)
            current_date = self.selected_end_day
            title = "Seleccionar Fecha de Fin"
            
            def update_date(selected_date):
                self.selected_end_day = selected_date
                self.date_display_label_end.configure(text=selected_date)
            
        CalendarModal(self.controller, current_date, update_date, title=title)
        
    def _on_period_change(self, choice):
        """Activa/desactiva y reconfigura los controles de fecha según el período."""
        
        # Ocultar todos los controles de Fecha de Fin
        self.label_date_end.pack_forget()
        self.date_display_label_end.pack_forget()
        self.calendar_button_end.pack_forget()
        
        if choice == "Día":
            self.label_date_start.configure(text="Fecha seleccionada:")
            self.calendar_button.configure(state="normal", command=lambda: self._open_calendar_modal("start"))
            self.date_display_label.configure(text=self.selected_day)
            
        elif choice == "Período Personalizado":
            self.label_date_start.configure(text="Inicio:")
            self.calendar_button.configure(state="normal", command=lambda: self._open_calendar_modal("start"))
            self.date_display_label.configure(text=self.selected_start_day)
            
            # Mostrar controles de Fin
            self.label_date_end.pack(side="left", padx=(0, 10))
            self.date_display_label_end.configure(text=self.selected_end_day)
            self.date_display_label_end.pack(side="left", padx=(0, 5))
            self.calendar_button_end.pack(side="left")

        elif choice == "Mes":
            self.label_date_start.configure(text="Mes seleccionado:")
            self.calendar_button.configure(state="disabled")
            
            # Muestra el mes del día actualmente seleccionado (no la fecha completa)
            try:
                 date_obj = datetime.datetime.strptime(self.selected_day, "%Y-%m-%d").date()
            except ValueError:
                 date_obj = datetime.date.today()
            
            self.date_display_label.configure(text=date_obj.strftime("%B %Y"))
            

    def _get_rate_for_date(self, date_time_str: str) -> tuple[float, str]:
        """Obtiene la tasa BCV más reciente anterior o igual a la fecha/hora dada."""
        try:
            transaction_dt = datetime.datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
            transaction_date_str = transaction_dt.strftime("%Y-%m-%d %H:%M:%S")
            
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT tasa, fecha_registro 
                FROM TasasBCV 
                WHERE fecha_registro <= ?
                ORDER BY fecha_registro DESC 
                LIMIT 1
            """, (transaction_date_str,))
            
            result = cursor.fetchone()
            if result:
                return float(result[0]), str(result[1])
            
            # Si no hay tasa anterior, buscar la más reciente en general (podría ser posterior)
            latest_rate = self.bcv_rate_module.get_latest_rate_from_db()
            if latest_rate:
                 cursor.execute("SELECT fecha_registro FROM TasasBCV ORDER BY fecha_registro DESC LIMIT 1")
                 latest_date_result = cursor.fetchone()
                 latest_date = latest_date_result[0] if latest_date_result else "N/D"
                 return float(latest_rate), f"{latest_date} (Más Reciente)"
                 
            return 0.0, "N/A (Sin tasa en DB)"
        
        except Exception:
            return 0.0, "ERROR"


    def _get_filter_dates(self) -> tuple[str, str, str]:
        """Calcula las fechas de inicio y fin basadas en el período seleccionado."""
        
        period = self.period_combobox.get()
        
        try:
            today = datetime.datetime.strptime(self.selected_day, "%Y-%m-%d").date()
        except:
             today = datetime.date.today()
        
        if period == "Día":
            # Uso de self.selected_day
            filter_date_start = today
            filter_date_end = today
            date_range_str = filter_date_start.strftime("%Y-%m-%d")

        elif period == "Período Personalizado":
            # Uso de self.selected_start_day y self.selected_end_day
            try:
                start_date = datetime.datetime.strptime(self.selected_start_day, "%Y-%m-%d").date()
                end_date = datetime.datetime.strptime(self.selected_end_day, "%Y-%m-%d").date()
            except ValueError:
                start_date = datetime.date.today()
                end_date = datetime.date.today()
                
            # Asegurar que el inicio no sea posterior al fin
            if start_date > end_date:
                start_date, end_date = end_date, start_date # Swap
                
            filter_date_start = start_date
            filter_date_end = end_date
            date_range_str = f"Período del {filter_date_start.strftime('%Y-%m-%d')} al {filter_date_end.strftime('%Y-%m-%d')}"

        elif period == "Mes":
            # El mes es el del día actualmente seleccionado (self.selected_day)
            start_of_month = today.replace(day=1)
            _, days_in_month = calendar.monthrange(today.year, today.month)
            end_of_month = today.replace(day=days_in_month)
            
            filter_date_start = start_of_month
            filter_date_end = end_of_month
            date_range_str = f"Mes de {today.strftime('%B %Y')}"
            
        return filter_date_start.strftime("%Y-%m-%d"), filter_date_end.strftime("%Y-%m-%d"), date_range_str


    def load_summary_data(self):
        """Carga y calcula los datos del resumen ejecutivo para el período seleccionado."""
        
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)
            
        date_start, date_end, date_range_str = self._get_filter_dates()
        self.current_date_range = (date_start, date_end) 

        # Tasa usada para la conversión del total (se usa la tasa del final del período)
        tasa_general, tasa_fecha = self._get_rate_for_date(f"{date_end} 23:59:59")
        self.current_summary_data = {} 
        
        totals = {
            "Ventas (Neto)": {"Bs": 0.0, "USD": 0.0},
            "Devoluciones": {"Bs": 0.0, "USD": 0.0},
            "Avances de Efectivo (Monto Entregado)": {"Bs": 0.0, "USD": 0.0},
            "Ganancia Avances (Comisión)": {"Bs": 0.0, "USD": 0.0},
            "Recargas Telefónicas (Monto Base)": {"Bs": 0.0, "USD": 0.0},
            "Ganancia Recargas (Comisión)": {"Bs": 0.0, "USD": 0.0},
        }

        query_date_filter = "fecha BETWEEN ? AND ?" if date_start != date_end else "fecha = ?"
        params = (date_start, date_end) if date_start != date_end else (date_start,)

        # 1. Ventas y Devoluciones (Tabla Ventas)
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
                SELECT estado, monto_total_bs, total_venta
                FROM Ventas
                WHERE {query_date_filter} AND estado IN ('Completada', 'Devolucion')
            """, params)
            
            for estado, monto_bs, monto_usd in cursor.fetchall():
                if estado == 'Completada':
                    totals["Ventas (Neto)"]["Bs"] += (monto_bs if monto_bs is not None else 0.0)
                    totals["Ventas (Neto)"]["USD"] += (monto_usd if monto_usd is not None else 0.0)
                elif estado == 'Devolucion':
                    # Las devoluciones restan montos
                    totals["Devoluciones"]["Bs"] -= (monto_bs if monto_bs is not None else 0.0)
                    totals["Devoluciones"]["USD"] -= (monto_usd if monto_usd is not None else 0.0)
        except Exception:
            pass


        # 2. Avances de Efectivo (Tabla AvancesEfectivo)
        query_date_filter_adv = "substr(fecha_hora, 1, 10) BETWEEN ? AND ?" if date_start != date_end else "substr(fecha_hora, 1, 10) = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
                SELECT fecha_hora, monto_entregado, comision
                FROM AvancesEfectivo
                WHERE {query_date_filter_adv} AND estado = 'Concretado'
            """, params)

            for fecha_hora, monto_entregado, comision in cursor.fetchall():
                # Nota: Se usa la tasa del momento de la transacción para la conversión a USD
                rate_adv, _ = self._get_rate_for_date(fecha_hora)
                
                totals["Avances de Efectivo (Monto Entregado)"]["Bs"] += monto_entregado
                totals["Avances de Efectivo (Monto Entregado)"]["USD"] += (monto_entregado / rate_adv) if rate_adv > 0 else 0.0
                
                totals["Ganancia Avances (Comisión)"]["Bs"] += comision
                totals["Ganancia Avances (Comisión)"]["USD"] += (comision / rate_adv) if rate_adv > 0 else 0.0
                
        except Exception:
            pass

        # 3. Recargas Telefónicas (Tabla RecargasTelefonicas)
        query_date_filter_rec = "substr(fecha_hora, 1, 10) BETWEEN ? AND ?" if date_start != date_end else "substr(fecha_hora, 1, 10) = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
                SELECT fecha_hora, monto_base, comision
                FROM RecargasTelefonicas
                WHERE {query_date_filter_rec} AND estado = 'Concretado'
            """, params)

            for fecha_hora, monto_base, comision in cursor.fetchall():
                # Nota: Se usa la tasa del momento de la transacción para la conversión a USD
                rate_rec, _ = self._get_rate_for_date(fecha_hora)
                
                totals["Recargas Telefónicas (Monto Base)"]["Bs"] += monto_base
                totals["Recargas Telefónicas (Monto Base)"]["USD"] += (monto_base / rate_rec) if rate_rec > 0 else 0.0
                
                totals["Ganancia Recargas (Comisión)"]["Bs"] += comision
                totals["Ganancia Recargas (Comisión)"]["USD"] += (comision / rate_rec) if rate_rec > 0 else 0.0
                
        except Exception:
            pass


        # --- Mostrar Resultados en Treeview y Guardar Datos ---
        total_bs_general = 0.0
        total_usd_general = 0.0
        
        self.rate_info_label.configure(text=f"Tasa de BCV para {date_range_str} (tomada de {tasa_fecha}): 1$ = Bs. {tasa_general:,.4f}")
        
        for i, (concepto, data) in enumerate(totals.items()):
            tag = 'negative' if 'Devoluciones' in concepto or data["Bs"] < 0 else 'positive'
            monto_bs_str = f"Bs. {data['Bs']:,.2f}"
            monto_usd_str = f"$ {data['USD']:,.2f}"
            
            self.summary_tree.insert('', 'end', 
                                     values=(concepto, monto_bs_str, monto_usd_str),
                                     tags=(tag, 'oddrow' if i % 2 != 0 else 'evenrow'))
            
            total_bs_general += data["Bs"]
            total_usd_general += data["USD"]

        self.summary_tree.insert('', 'end', values=("", "", ""), tags=('separator'))
        
        final_values = ("TOTAL GENERAL (NETO)", f"Bs. {total_bs_general:,.2f}", f"$ {total_usd_general:,.2f}")
        self.summary_tree.insert('', 'end', values=final_values, tags=('grand_total'))

        self.current_summary_data = {
            "totals": totals,
            "grand_total": final_values,
            "date_range_str": date_range_str,
            "tasa_general": tasa_general,
            "tasa_fecha": tasa_fecha
        }
        
        # Configuración de Tags de Estilo 
        self.summary_tree.tag_configure('negative', foreground=RED_ERROR)
        self.summary_tree.tag_configure('positive', foreground=DARK_BLUE_SOBRIO)
        self.summary_tree.tag_configure('grand_total', 
                                        font=('Helvetica', FONT_SIZE_ACCESSIBLE + 4, 'bold'), 
                                        background=TEAL_SOBRIO, 
                                        foreground='white')
        self.summary_tree.tag_configure('separator', background='#7F8C8D')
        self.summary_tree.tag_configure('evenrow', background=GRAY_LIGHT)
        self.summary_tree.tag_configure('oddrow', background="#DDE3E9")


    def _fetch_detailed_transactions(self, date_start, date_end):
        """Obtiene los datos detallados de las transacciones para el período."""
        detailed_data = {
            "Ventas": [], 
            "Avances": [], 
            "Recargas": []
        }
        
        query_date_filter = "fecha BETWEEN ? AND ?" if date_start != date_end else "fecha = ?"
        params = (date_start, date_end) if date_start != date_end else (date_start,)
        
        # 1. Ventas y Devoluciones
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
                SELECT id, fecha, hora, estado, monto_total_bs, total_venta
                FROM Ventas
                WHERE {query_date_filter}
                ORDER BY fecha DESC, hora DESC
            """, params)
            
            for id, fecha, hora, estado, monto_bs, monto_usd in cursor.fetchall():
                detailed_data["Ventas"].append((id, f"{fecha} {hora}", estado, 
                                                 f"Bs. {monto_bs:,.2f}", f"$ {monto_usd:,.2f}"))
        except Exception: pass

        # 2. Avances de Efectivo
        query_date_filter_adv = "substr(fecha_hora, 1, 10) BETWEEN ? AND ?" if date_start != date_end else "substr(fecha_hora, 1, 10) = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
                SELECT id, fecha_hora, monto_entregado, comision, estado
                FROM AvancesEfectivo
                WHERE {query_date_filter_adv}
                ORDER BY fecha_hora DESC
            """, params)

            for id, fecha_hora, monto_entregado, comision, estado in cursor.fetchall():
                rate, _ = self._get_rate_for_date(fecha_hora)
                monto_usd = (monto_entregado / rate) if rate > 0 and monto_entregado else 0.0
                comision_usd = (comision / rate) if rate > 0 and comision else 0.0
                
                detailed_data["Avances"].append((id, fecha_hora, estado, 
                                                  f"Bs. {monto_entregado:,.2f}", f"Bs. {comision:,.2f}", 
                                                  f"$ {monto_usd:,.2f}", f"$ {comision_usd:,.2f}"))
        except Exception: pass

        # 3. Recargas Telefónicas
        query_date_filter_rec = "substr(fecha_hora, 1, 10) BETWEEN ? AND ?" if date_start != date_end else "substr(fecha_hora, 1, 10) = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
                SELECT id, fecha_hora, numero, monto_base, comision, monto_total, estado
                FROM RecargasTelefonicas
                WHERE {query_date_filter_rec}
                ORDER BY fecha_hora DESC
            """, params)

            for id, fecha_hora, numero, monto_base, comision, monto_total, estado in cursor.fetchall():
                detailed_data["Recargas"].append((id, fecha_hora, numero, estado, 
                                                   f"Bs. {monto_base:,.2f}", f"Bs. {comision:,.2f}", 
                                                   f"Bs. {monto_total:,.2f}"))
        except Exception: pass
        
        return detailed_data


    def export_to_pdf(self):
        """
        Genera el reporte PDF y utiliza filedialog.asksaveasfilename() 
        para permitir al usuario elegir la ubicación de guardado (ventana nativa de Windows).
        """
        
        if not self.current_summary_data:
             messagebox.showwarning("Advertencia", "Recargue el resumen antes de exportar.")
             return
        
        # FIX: Verificar la bandera de instalación de FPDF
        if not PDF_INSTALLED:
             messagebox.showerror("Error de Dependencia", 
                                 "La librería 'fpdf2' no está instalada y es necesaria para exportar a PDF.\n"
                                 "Por favor, instale la dependencia usando: pip install fpdf2")
             return

        date_start, date_end = self.current_date_range
        
        # 1. Obtener datos detallados y configurar PDF
        detailed_data = self._fetch_detailed_transactions(date_start, date_end)
        
        report_title = "Reporte Ejecutivo de Transacciones"
        date_range_str = self.current_summary_data["date_range_str"]
        tasa_general = self.current_summary_data["tasa_general"]
        tasa_fecha = self.current_summary_data["tasa_fecha"]
        rate_info = f"Tasa de BCV: 1$ = Bs. {tasa_general:,.4f} (Fecha: {tasa_fecha})"
        
        pdf = PDFReportGenerator(report_title, date_range_str, rate_info)
        pdf.alias_nb_pages() 
        
        # 2. Agregar contenido
        
        # I. Resumen Económico
        pdf.title_section("I. Resumen Económico del Período")
        summary_header = ["CONCEPTO", "TOTAL BS.", "TOTAL USD ($)"]
        summary_data = []
        for concepto, data in self.current_summary_data["totals"].items():
            summary_data.append((concepto, f"Bs. {data['Bs']:,.2f}", f"$ {data['USD']:,.2f}"))
        summary_data.append(("", "", ""))
        summary_data.append(self.current_summary_data["grand_total"])
        pdf.write_table(summary_header, summary_data, [80, 55, 55])
        
        # II. Ventas y Devoluciones
        pdf.title_section("\nII. Movimientos de Ventas y Devoluciones")
        sales_header = ["ID Venta", "Fecha/Hora", "Estado", "Monto Total (Bs)", "Monto Total (USD)"]
        sales_data = detailed_data["Ventas"]
        pdf.write_table(sales_header, sales_data, [20, 40, 30, 50, 50])
        
        # III. Avances de Efectivo
        pdf.title_section("\nIII. Movimientos de Avance de Efectivo")
        advances_header = ["ID", "Fecha/Hora", "Estado", "Entregado (Bs)", "Comisión (Bs)", "Entregado (USD)", "Comisión (USD)"]
        advances_data = detailed_data["Avances"]
        pdf.write_table(advances_header, advances_data, [10, 30, 20, 30, 30, 30, 30])
        
        # IV. Recargas Telefónicas
        pdf.title_section("\nIV. Movimientos de Recargas Telefónicas")
        recharges_header = ["ID", "Fecha/Hora", "Número", "Estado", "Monto Base", "Comisión", "Total Bs."]
        recharges_data = detailed_data["Recargas"]
        pdf.write_table(recharges_header, recharges_data, [10, 35, 25, 20, 30, 25, 30])

        
        # 3. Diálogo de guardado
        date_tag = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"Reporte_Ejecutivo_{date_tag}.pdf"

        # Abre el diálogo para que el usuario elija dónde guardar (Ventana Nativa)
        full_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=default_filename,
            filetypes=[("Archivos PDF", "*.pdf")],
            title="Guardar Reporte PDF"
        )

        if not full_path:
            # El usuario canceló la operación
            return

        try:
            # 💡 CORRECCIÓN APLICADA: Se elimina el argumento 'F' para evitar el error de 3 argumentos
            pdf.output(full_path) 
            
            messagebox.showinfo("Éxito", f"Reporte guardado exitosamente en: \n{full_path}")
            
        except Exception as e:
            messagebox.showerror("Error al guardar PDF", 
                                 f"No se pudo guardar el archivo. Verifique que no esté abierto o pruebe otra ubicación.\n\nDetalle del Error: {e}")