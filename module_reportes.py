# module_reportes.py (VERSIÓN CON CONTROL DE TAMAÑO DE VISUALIZACIÓN)

import customtkinter as ctk
from tkinter import messagebox, simpledialog, ttk
import sqlite3
import json
from utils import setup_db, DB_NAME

# --- ESTILOS DE FUENTE Y COLORES (CONSISTENTES) ---
DARK_BLUE_SOBRIO = "#34495E"
TEAL_SOBRIO = "#16A085"
GRAY_LIGHT = "#ECF0F1"

# ⭐ CONFIGURACIONES DE TAMAÑO PARA TREEVIEW ⭐
SIZE_CONFIGS = {
    "Pequeño": {"font_content": 12, "font_header": 14, "row_height": 28},
    "Mediano": {"font_content": 16, "font_header": 18, "row_height": 35},
    "Grande": {"font_content": 18, "font_header": 20, "row_height": 40}, # Uniforme con BCV (Máxima Accesibilidad)
}
DEFAULT_SIZE = "Grande" # Usamos el tamaño accesible como predeterminado

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue") 

class ReportesModule(ctk.CTkFrame):
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.conn = setup_db()
        
        self.current_size = DEFAULT_SIZE # Variable de estado para el tamaño actual
        
        self.create_widgets()
        
        # Aplicar el estilo inicial después de crear los Treeviews
        self.apply_treeview_style(self.current_size) 
        
        self.load_sales_reports()
        self.load_advance_reports()
        self.load_recharge_reports()
        
    def create_widgets(self):
        # --- Cabecera ---
        ctk.CTkLabel(self, 
                     text="📊 Reportes de Ventas y Transacciones", 
                     font=ctk.CTkFont(size=40, weight="bold"),
                     text_color=DARK_BLUE_SOBRIO).pack(pady=(35, 20))
        
        # --- Contenedor de Pestañas (Tabview) ---
        self.tab_view = ctk.CTkTabview(self, fg_color=GRAY_LIGHT)
        self.tab_view.pack(padx=30, pady=15, fill="both", expand=True)
        
        # --- 1. Pestaña de Ventas ---
        self.sales_tab = self.tab_view.add("Reporte de Ventas")
        self.sales_tab.grid_columnconfigure(0, weight=1)
        self.sales_tab.grid_rowconfigure(1, weight=1)
        
        self._create_sales_filter_frame(self.sales_tab)
        self._create_sales_tree(self.sales_tab) # Crea el Treeview (sin estilo inicial)

        # --- 2. Pestaña de Avance de Efectivo ---
        self.advance_tab = self.tab_view.add("Avance de Efectivo")
        self.advance_tab.grid_columnconfigure(0, weight=1)
        self.advance_tab.grid_rowconfigure(1, weight=1)

        self._create_advance_filter_frame(self.advance_tab)
        self._create_advance_tree(self.advance_tab) # Crea el Treeview (sin estilo inicial)

    # ===================================================================
    # --- LÓGICA DE ESTILO DINÁMICO (NUEVO) ---
    # ===================================================================
    
    def apply_treeview_style(self, size_name):
        """Aplica el estilo de fuente y altura al Treeview de Ventas y Avances."""
        if size_name not in SIZE_CONFIGS:
            return
            
        config = SIZE_CONFIGS[size_name]
        font_content = config["font_content"]
        font_header = config["font_header"]
        row_height = config["row_height"]

        s = ttk.Style()
        s.theme_use('default')
        
        # Configuración del estilo Treeview (aplicado a ambos)
        s.configure("Report.Treeview", 
                    rowheight=row_height, 
                    font=('Helvetica', font_content), 
                    background=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"]),
                    foreground=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"]),
                    fieldbackground=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"]),
                    borderwidth=0 
                    )
        s.map("Report.Treeview", 
              background=[('selected', '#7F8C8D')], 
              foreground=[('selected', 'white')])

        # Encabezados (Consistentemente grandes y oscuros)
        s.configure("Report.Treeview.Heading", 
                    font=('Helvetica', font_header, 'bold'),
                    background=DARK_BLUE_SOBRIO, 
                    foreground="white", 
                    relief="flat")
        s.layout("Report.Treeview", [('Report.Treeview.treearea', {'sticky': 'nswe'})]) 

    def apply_new_size(self, size_name):
        """Maneja el cambio de tamaño desde el OptionMenu y aplica el nuevo estilo."""
        self.current_size = size_name
        self.apply_treeview_style(size_name)

    # ===================================================================
    # --- WIDGETS Y LÓGICA DE VENTAS ---
    # ===================================================================

    def _create_sales_filter_frame(self, master):
        filter_frame = ctk.CTkFrame(master, fg_color="transparent")
        filter_frame.grid(row=0, column=0, sticky='ew', padx=15, pady=(15, 10))
        filter_frame.grid_columnconfigure(3, weight=1) # Columna para el botón de recarga (a la derecha)

        # 1. Filtro por Estado (Fila 0)
        ctk.CTkLabel(filter_frame, 
                     text="Filtrar Ventas por Estado:", 
                     font=ctk.CTkFont(size=20, weight="normal"),
                     text_color=DARK_BLUE_SOBRIO).grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")
        
        self.sales_filter_var = ctk.StringVar(value="Todas")
        statuses = ["Todas", "Completada", "Cancelada"]
        self.sales_filter_option = ctk.CTkOptionMenu(filter_frame, 
                                                     values=statuses, 
                                                     variable=self.sales_filter_var,
                                                     command=self.load_sales_reports,
                                                     width=200, 
                                                     height=35) 
        self.sales_filter_option.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # 2. Control de Tamaño (Fila 1)
        ctk.CTkLabel(filter_frame, 
                     text="Tamaño Visualización:", 
                     font=ctk.CTkFont(size=20, weight="normal"),
                     text_color=DARK_BLUE_SOBRIO).grid(row=1, column=0, padx=(10, 5), pady=5, sticky="w")
        
        self.sales_size_var = ctk.StringVar(value=DEFAULT_SIZE)
        sizes = list(SIZE_CONFIGS.keys())
        self.sales_size_option = ctk.CTkOptionMenu(filter_frame,
                                                    values=sizes,
                                                    variable=self.sales_size_var,
                                                    command=self.apply_new_size,
                                                    width=200,
                                                    height=35)
        self.sales_size_option.grid(row=1, column=1, padx=10, pady=5, sticky="w")


        # 3. Botón Recargar (Columna 3, abarca 2 filas)
        ctk.CTkButton(filter_frame, 
                      text="🔄 Recargar Reporte", 
                      command=self.load_sales_reports,
                      fg_color="transparent", 
                      border_width=2,
                      border_color=DARK_BLUE_SOBRIO,
                      text_color=DARK_BLUE_SOBRIO,
                      hover_color="#CCD1D1",
                      height=50 # Altura mejorada
                      ).grid(row=0, column=3, rowspan=2, padx=(10, 0), pady=5, sticky="e")

    def _create_sales_tree(self, master):
        # NOTA: La configuración de estilo 'Report.Treeview' se maneja ahora en apply_treeview_style(self, size_name)
        
        columns = ("ID", "Fecha", "Hora", "Total ($)", "Total (Bs)", "Tasa BCV", "Método Pago", "Estado", "Productos")
        self.report_tree = ttk.Treeview(master, columns=columns, show="headings", style="Report.Treeview")
        
        # Asignación de Encabezados (LÓGICA INTACTA)
        self.report_tree.heading("ID", text="ID")
        self.report_tree.heading("Fecha", text="Fecha")
        self.report_tree.heading("Hora", text="Hora")
        self.report_tree.heading("Total ($)", text="Total ($)")      
        self.report_tree.heading("Total (Bs)", text="Total (Bs)")    
        self.report_tree.heading("Tasa BCV", text="Tasa BCV")        
        self.report_tree.heading("Método Pago", text="Método Pago")
        self.report_tree.heading("Estado", text="Estado")
        self.report_tree.heading("Productos", text="Productos") 

        # Ajuste de anchos (LÓGICA INTACTA)
        self.report_tree.column("ID", width=60, stretch=False)
        self.report_tree.column("Fecha", width=130, stretch=False)
        self.report_tree.column("Hora", width=110, stretch=False)
        self.report_tree.column("Total ($)", width=130, stretch=False, anchor='e')      
        self.report_tree.column("Total (Bs)", width=170, stretch=False, anchor='e')     
        self.report_tree.column("Tasa BCV", width=120, stretch=False, anchor='e')        
        self.report_tree.column("Método Pago", width=150, stretch=False)
        self.report_tree.column("Estado", width=130, stretch=False)
        self.report_tree.column("Productos", width=350, stretch=True) 

        self.report_tree.grid(row=1, column=0, sticky='nsew', padx=15, pady=(0, 15))
        
        vsb = ttk.Scrollbar(master, orient="vertical", command=self.report_tree.yview)
        vsb.grid(row=1, column=0, sticky='nse', padx=15, pady=(0, 15))
        self.report_tree.configure(yscrollcommand=vsb.set)

    # LÓGICA: _format_products_for_display SE MANTIENE
    def _format_products_for_display(self, detail_json):
        if not detail_json:
            return "Sin Detalle"
        try:
            products = json.loads(detail_json)
            formatted = ", ".join([f"{p['nombre']} ({p['cantidad']})" for p in products])
            return formatted if len(formatted) < 80 else formatted[:77] + "..."
        except:
            return "Error de Formato"

    # LÓGICA: load_sales_reports SE MANTIENE
    def load_sales_reports(self, event=None):
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)

        status = self.sales_filter_var.get()
        
        query = """
            SELECT 
                id, fecha, hora, total_venta, monto_total_bs, tasa_bcv, detalle, metodo_pago, estado 
            FROM Ventas
        """
        params = []
        
        if status != "Todas":
            query += " WHERE estado = ?"
            params.append(status)
        
        query += " ORDER BY id DESC" 
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            reports = cursor.fetchall()
            
            for i, row in enumerate(reports): 
                report_id, fecha, hora, total_venta, monto_total_bs, tasa_bcv, detalle_json, metodo_pago, estado = row
                
                total_venta = total_venta if total_venta is not None else 0.0
                monto_total_bs = monto_total_bs if monto_total_bs is not None else 0.0
                tasa_bcv = tasa_bcv if tasa_bcv is not None else 0.0
                
                status_tag = 'completed' if estado == 'Completada' else 'cancelled'
                stripe_tag = 'oddrow' if i % 2 != 0 else 'evenrow' 
                
                monto_usd_str = f"$ {total_venta:,.2f}" 
                
                try:
                    formatted_bs_str = "{:,.2f}".format(monto_total_bs).replace(",", "_TEMP_").replace(".", ",").replace("_TEMP_", ".")
                    monto_bs_str = f"Bs. {formatted_bs_str}"
                except:
                    monto_bs_str = f"Bs. {monto_total_bs:,.2f}"
                
                tasa_bcv_str = f"{tasa_bcv:,.4f}" 
                
                productos_str = self._format_products_for_display(detalle_json)
                
                self.report_tree.insert('', 'end', 
                                        iid=report_id, 
                                        values=(
                                            report_id, 
                                            fecha, 
                                            hora, 
                                            monto_usd_str,      
                                            monto_bs_str,       
                                            tasa_bcv_str,       
                                            metodo_pago, 
                                            estado, 
                                            productos_str
                                        ),
                                        tags=(stripe_tag, status_tag,)) 
            
            # Definición de colores para tags (LÓGICA INTACTA)
            self.report_tree.tag_configure('evenrow', background=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"]))
            self.report_tree.tag_configure('oddrow', background='#EBEBEB' if ctk.get_appearance_mode() == "Light" else '#2E2E2E')
            self.report_tree.tag_configure('completed', background='#B5EAD7', foreground='black') 
            self.report_tree.tag_configure('cancelled', background='#FF9AA2', foreground='black') 
            
        except Exception as e:
            messagebox.showerror("Error DB", f"Error al cargar reportes de ventas: {e}")

    # ===================================================================
    # --- WIDGETS Y LÓGICA DE AVANCE DE EFECTIVO ---
    # ===================================================================

    def _create_advance_filter_frame(self, master):
        filter_frame = ctk.CTkFrame(master, fg_color="transparent")
        filter_frame.grid(row=0, column=0, sticky='ew', padx=15, pady=(15, 10))
        filter_frame.grid_columnconfigure(3, weight=1) # Columna para el botón de recarga (a la derecha)
        
        # 1. Filtro por Estado (Fila 0)
        ctk.CTkLabel(filter_frame, 
                     text="Filtrar Avances por Estado:", 
                     font=ctk.CTkFont(size=20, weight="normal"),
                     text_color=DARK_BLUE_SOBRIO).grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")
        
        self.advance_filter_var = ctk.StringVar(value="Todos")
        statuses = ["Todos", "Concretado", "Cancelado"]
        self.advance_filter_option = ctk.CTkOptionMenu(filter_frame, 
                                                     values=statuses, 
                                                     variable=self.advance_filter_var,
                                                     command=self.load_advance_reports,
                                                     width=200, 
                                                     height=35) 
        self.advance_filter_option.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # 2. Control de Tamaño (Fila 1)
        ctk.CTkLabel(filter_frame, 
                     text="Tamaño Visualización:", 
                     font=ctk.CTkFont(size=20, weight="normal"),
                     text_color=DARK_BLUE_SOBRIO).grid(row=1, column=0, padx=(10, 5), pady=5, sticky="w")
        
        self.advance_size_var = ctk.StringVar(value=DEFAULT_SIZE)
        sizes = list(SIZE_CONFIGS.keys())
        self.advance_size_option = ctk.CTkOptionMenu(filter_frame,
                                                    values=sizes,
                                                    variable=self.advance_size_var,
                                                    command=self.apply_new_size,
                                                    width=200,
                                                    height=35)
        self.advance_size_option.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        # 3. Botón Recargar (Columna 3, abarca 2 filas)
        ctk.CTkButton(filter_frame, 
                      text="🔄 Recargar Reporte", 
                      command=self.load_advance_reports,
                      fg_color="transparent", 
                      border_width=2,
                      border_color=DARK_BLUE_SOBRIO,
                      text_color=DARK_BLUE_SOBRIO,
                      hover_color="#CCD1D1",
                      height=50
                      ).grid(row=0, column=3, rowspan=2, padx=(10, 0), pady=5, sticky="e")
    
    def _create_advance_tree(self, master):
        # NOTA: La configuración de estilo 'Report.Treeview' se maneja ahora en apply_treeview_style(self, size_name)

        columns = ("ID", "Fecha/Hora", "Monto Entregado", "Comisión (20%)", "Total a Pagar", "Método Pago", "Estado")
        self.advance_tree = ttk.Treeview(master, columns=columns, show="headings", style="Report.Treeview")
        
        for col in columns: # Asignación de Encabezados (LÓGICA INTACTA)
            self.advance_tree.heading(col, text=col)
        
        # Ajuste de anchos (LÓGICA INTACTA)
        self.advance_tree.column("ID", width=70, stretch=False)
        self.advance_tree.column("Fecha/Hora", width=190, stretch=False)
        self.advance_tree.column("Monto Entregado", width=190, stretch=False, anchor='e')
        self.advance_tree.column("Comisión (20%)", width=190, stretch=False, anchor='e')
        self.advance_tree.column("Total a Pagar", width=190, stretch=False, anchor='e')
        self.advance_tree.column("Método Pago", width=160, stretch=False)
        self.advance_tree.column("Estado", width=140, stretch=True)

        self.advance_tree.grid(row=1, column=0, sticky='nsew', padx=15, pady=(0, 15))
        
        vsb = ttk.Scrollbar(master, orient="vertical", command=self.advance_tree.yview)
        vsb.grid(row=1, column=0, sticky='nse', padx=15, pady=(0, 15))
        self.advance_tree.configure(yscrollcommand=vsb.set)
        
    # LÓGICA: load_advance_reports SE MANTIENE 
    def load_advance_reports(self, event=None):
        for item in self.advance_tree.get_children():
            self.advance_tree.delete(item)

        status = self.advance_filter_var.get()
        query = "SELECT id, fecha_hora, monto_entregado, comision, monto_total, metodo_pago, estado FROM AvancesEfectivo"
        params = []
        
        if status != "Todos":
            query += " WHERE estado = ?"
            params.append(status)
        
        query += " ORDER BY id DESC" 
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            reports = cursor.fetchall()
            
            for i, row in enumerate(reports): 
                report_id, fecha_hora, monto_entregado, comision, monto_total, metodo_pago, estado = row
                
                monto_entregado_str = f"Bs. {monto_entregado:,.2f}"
                comision_str = f"Bs. {comision:,.2f}"
                monto_total_str = f"Bs. {monto_total:,.2f}"
                
                status_tag = 'completed' if estado == 'Concretado' else 'cancelled'
                stripe_tag = 'oddrow' if i % 2 != 0 else 'evenrow'
                
                self.advance_tree.insert('', 'end', 
                                        iid=report_id, 
                                        values=(report_id, fecha_hora, monto_entregado_str, comision_str, monto_total_str, metodo_pago, estado),
                                        tags=(stripe_tag, status_tag,))

            # Definición de colores para tags (LÓGICA INTACTA)
            self.advance_tree.tag_configure('evenrow', background=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"]))
            self.advance_tree.tag_configure('oddrow', background='#EBEBEB' if ctk.get_appearance_mode() == "Light" else '#2E2E2E')

            self.advance_tree.tag_configure('completed', background='#B5EAD7', foreground='black') 
            self.advance_tree.tag_configure('cancelled', background='#FF9AA2', foreground='black') 

        except Exception as e:
            messagebox.showerror("Error DB", f"Error al cargar reportes de avances de efectivo: {e}")

           # Pestaña de Recarga Telefónica
           
        self.recharge_tab = self.tab_view.add("Recarga Telefónica")
        self.recharge_tab.grid_columnconfigure(0, weight=1)
        self.recharge_tab.grid_rowconfigure(1, weight=1)

        self._create_recharge_filter_frame(self.recharge_tab)
        self._create_recharge_tree(self.recharge_tab)


    # ===================================================================
    # --- WIDGETS Y LÓGICA DE RECARGA TELEFÓNICA (NUEVOS MÉTODOS) ---
    # ===================================================================

    def _create_recharge_filter_frame(self, master):
        filter_frame = ctk.CTkFrame(master, fg_color="transparent")
        filter_frame.grid(row=0, column=0, sticky='ew', padx=15, pady=(15, 10))
        filter_frame.grid_columnconfigure(3, weight=1) 
        
        # 1. Filtro por Estado (Fila 0)
        ctk.CTkLabel(filter_frame, 
                     text="Filtrar Recargas por Estado:", 
                     font=ctk.CTkFont(size=20, weight="normal"),
                     text_color=DARK_BLUE_SOBRIO).grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")
        
        self.recharge_filter_var = ctk.StringVar(value="Todos")
        statuses = ["Todos", "Concretado", "Cancelado"]
        self.recharge_filter_option = ctk.CTkOptionMenu(filter_frame, 
                                                     values=statuses, 
                                                     variable=self.recharge_filter_var,
                                                     command=self.load_recharge_reports,
                                                     width=200, 
                                                     height=35) 
        self.recharge_filter_option.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # 2. Control de Tamaño (Fila 1) - Reutiliza el OptionMenu general
        ctk.CTkLabel(filter_frame, 
                     text="Tamaño Visualización:", 
                     font=ctk.CTkFont(size=20, weight="normal"),
                     text_color=DARK_BLUE_SOBRIO).grid(row=1, column=0, padx=(10, 5), pady=5, sticky="w")
        
        # Reutilizamos la variable de ventas/avances y el comando de aplicar estilo
        self.recharge_size_option = ctk.CTkOptionMenu(filter_frame,
                                                    values=list(SIZE_CONFIGS.keys()),
                                                    variable=self.sales_size_var, 
                                                    command=self.apply_new_size,
                                                    width=200,
                                                    height=35)
        self.recharge_size_option.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        # 3. Botón Recargar (Columna 3, abarca 2 filas)
        ctk.CTkButton(filter_frame, 
                      text="🔄 Recargar Reporte", 
                      command=self.load_recharge_reports,
                      fg_color="transparent", 
                      border_width=2,
                      border_color=DARK_BLUE_SOBRIO,
                      text_color=DARK_BLUE_SOBRIO,
                      hover_color="#CCD1D1",
                      height=50
                      ).grid(row=0, column=3, rowspan=2, padx=(10, 0), pady=5, sticky="e")
    
    def _create_recharge_tree(self, master):
        columns = ("ID", "Fecha/Hora", "Número", "Monto Base", "Comisión (15%)", "Total a Cobrar", "Estado")
        self.recharge_tree = ttk.Treeview(master, columns=columns, show="headings", style="Report.Treeview")
        
        for col in columns: 
            self.recharge_tree.heading(col, text=col)
        
        # Ajuste de anchos (Similar al de Avances)
        self.recharge_tree.column("ID", width=60, stretch=False)
        self.recharge_tree.column("Fecha/Hora", width=190, stretch=False)
        self.recharge_tree.column("Número", width=170, stretch=False)
        self.recharge_tree.column("Monto Base", width=170, stretch=False, anchor='e')
        self.recharge_tree.column("Comisión (15%)", width=170, stretch=False, anchor='e')
        self.recharge_tree.column("Total a Cobrar", width=180, stretch=False, anchor='e')
        self.recharge_tree.column("Estado", width=140, stretch=True)

        self.recharge_tree.grid(row=1, column=0, sticky='nsew', padx=15, pady=(0, 15))
        
        vsb = ttk.Scrollbar(master, orient="vertical", command=self.recharge_tree.yview)
        vsb.grid(row=1, column=0, sticky='nse', padx=15, pady=(0, 15))
        self.recharge_tree.configure(yscrollcommand=vsb.set)
        
    def load_recharge_reports(self, event=None):
        for item in self.recharge_tree.get_children():
            self.recharge_tree.delete(item)

        status = self.recharge_filter_var.get()
        # Se asume que la tabla se llama RecargasTelefonicas
        query = "SELECT id, fecha_hora, numero, monto_base, comision, monto_total, estado FROM RecargasTelefonicas"
        params = []
        
        if status != "Todos":
            query += " WHERE estado = ?"
            params.append(status)
        
        query += " ORDER BY id DESC" 
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            reports = cursor.fetchall()
            
            for i, row in enumerate(reports): 
                # row: id, fecha_hora, numero, monto_base, comision, monto_total, estado
                report_id, fecha_hora, numero, monto_base, comision, monto_total, estado = row
                
                monto_base_str = f"Bs. {monto_base:,.2f}"
                comision_str = f"Bs. {comision:,.2f}"
                monto_total_str = f"Bs. {monto_total:,.2f}"
                
                status_tag = 'completed' if estado == 'Concretado' else 'cancelled'
                stripe_tag = 'oddrow' if i % 2 != 0 else 'evenrow'
                
                self.recharge_tree.insert('', 'end', 
                                        iid=report_id, 
                                        values=(report_id, fecha_hora, numero, monto_base_str, comision_str, monto_total_str, estado),
                                        tags=(stripe_tag, status_tag,))

            # Definición de colores para tags (Reutilizando los tags de avance)
            self.recharge_tree.tag_configure('evenrow', background=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"]))
            self.recharge_tree.tag_configure('oddrow', background='#EBEBEB' if ctk.get_appearance_mode() == "Light" else '#2E2E2E')

            self.recharge_tree.tag_configure('completed', background='#B5EAD7', foreground='black') 
            self.recharge_tree.tag_configure('cancelled', background='#FF9AA2', foreground='black') 

        except Exception as e:
            messagebox.showerror("Error DB", f"Error al cargar reportes de recargas: {e}\nAsegúrese de que la tabla 'RecargasTelefonicas' exista en la base de datos.")