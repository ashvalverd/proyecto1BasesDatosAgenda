import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

import customtkinter as ctk
import psycopg2

try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class AppAgenda(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Agenda 3 Patitos")
        self.geometry("1280x760")
        self.minsize(1050, 650)

        self.conn_params = {
            "dbname": "agenda",
            "user": "postgres",
            "password": "postgres",
            "host": "localhost",
            "port": "5432",
        }

        self.usuarios_combo = {}
        self.categorias_combo = {}
        self.categorias_padre_combo = {}
        self.ubicaciones_combo = {}
        self.tipos_disponibilidad_combo = {}
        self.eventos_combo = {}


        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.crear_sidebar()
        self.crear_area_principal()
        self.configurar_estilos()

        self.actualizar_todas_las_tablas()

        if DateEntry is None:
            self.after(500, lambda: messagebox.showwarning(
                "Calendario no instalado",
                "Para usar los selectores de fecha instala:\n\npip install tkcalendar"
            ))

    # -------------------- INFRAESTRUCTURA --------------------

    def obtener_conexion(self):
        conn = psycopg2.connect(**self.conn_params)
        with conn.cursor() as cur:
            cur.execute("SET search_path TO prototipo, public;")
        return conn

    def ejecutar_consulta(self, sql, params=None, fetch=False):
        conn = None
        try:
            conn = self.obtener_conexion()
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall() if fetch else None
            conn.commit()
            return rows
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def configurar_estilos(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=30, font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

    def crear_treeview(self, parent, columnas, widths):
        contenedor = ctk.CTkFrame(parent, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        tree = ttk.Treeview(contenedor, columns=columnas, show="headings")
        for col, width in zip(columnas, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="center")
        scroll_y = ttk.Scrollbar(contenedor, orient="vertical", command=tree.yview)
        scroll_x = ttk.Scrollbar(contenedor, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        return tree

    def seleccionar_modulo(self, nombre):
        self.tabview.set(nombre)
        for modulo, boton in self.botones_nav.items():
            boton.configure(fg_color=("gray75", "gray25") if modulo == nombre else "transparent")

    def crear_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=235, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        ctk.CTkLabel(
            self.sidebar_frame,
            text="📅 AGENDA 🦆🦆🦆",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(28, 5), sticky="w")

        ctk.CTkLabel(
            self.sidebar_frame,
            text="Gestión de usuarios, categorías y eventos",
            font=ctk.CTkFont(size=11),
            wraplength=190,
            justify="left"
        ).grid(row=1, column=0, padx=20, pady=(0, 25), sticky="w")

        self.botones_nav = {}
        for i, (nombre, icono) in enumerate([
            ("Usuarios", "👥"),
            ("Categorías", "📁"),
            ("Eventos", "🗓️"),
            ("Ubicaciones", "📍"),
            ("Disponibilidad", "🕒"),
            ("Tareas", "✅"),
        ], start=2):
            btn = ctk.CTkButton(
                self.sidebar_frame, text=f"{icono}  {nombre}",
                anchor="w", fg_color="transparent",
                command=lambda n=nombre: self.seleccionar_modulo(n)
            )
            btn.grid(row=i, column=0, padx=15, pady=5, sticky="ew")
            self.botones_nav[nombre] = btn

        ctk.CTkButton(
            self.sidebar_frame,
            text="🔄  Recargar datos",
            command=self.actualizar_todas_las_tablas
        ).grid(row=8, column=0, padx=15, pady=(20, 5), sticky="ew")

        ctk.CTkLabel(self.sidebar_frame, text="APARIENCIA", font=ctk.CTkFont(size=11, weight="bold")).grid(
            row=11, column=0, padx=20, pady=(10, 5), sticky="w"
        )
        self.option_mode = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["System", "Dark", "Light"],
            command=ctk.set_appearance_mode
        )
        self.option_mode.set("System")
        self.option_mode.grid(row=12, column=0, padx=15, pady=(0, 25), sticky="ew")

    def crear_area_principal(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self.main_container, command=self.al_cambiar_pestana)
        self.tabview.grid(row=0, column=0, sticky="nsew")

        self.tab_usuarios = self.tabview.add("Usuarios")
        self.tab_categorias = self.tabview.add("Categorías")
        self.tab_eventos = self.tabview.add("Eventos")
        self.tab_ubicaciones = self.tabview.add("Ubicaciones")
        self.tab_disponibilidad = self.tabview.add("Disponibilidad")
        self.tab_tareas = self.tabview.add("Tareas")

        self.configurar_pestana_usuarios()
        self.configurar_pestana_categorias()
        self.configurar_pestana_eventos()
        self.configurar_pestana_ubicaciones()
        self.configurar_pestana_disponibilidad()
        self.configurar_pestana_tareas()
        self.seleccionar_modulo("Usuarios")

    def al_cambiar_pestana(self):
        nombre = self.tabview.get()
        if nombre in self.botones_nav:
            for modulo, boton in self.botones_nav.items():
                boton.configure(fg_color=("gray75", "gray25") if modulo == nombre else "transparent")

    def crear_encabezado(self, parent, titulo, descripcion):
        ctk.CTkLabel(parent, text=titulo, font=ctk.CTkFont(size=24, weight="bold")).pack(
            anchor="w", padx=15, pady=(15, 0)
        )
        ctk.CTkLabel(parent, text=descripcion, font=ctk.CTkFont(size=12)).pack(
            anchor="w", padx=15, pady=(0, 12)
        )

    # -------------------- USUARIOS --------------------

    def configurar_pestana_usuarios(self):
        self.crear_encabezado(self.tab_usuarios, "Usuarios", "Registra, consulta y administra los usuarios de la agenda.")

        cuerpo = ctk.CTkFrame(self.tab_usuarios, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        tabla_frame = ctk.CTkFrame(cuerpo)
        tabla_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        form = ctk.CTkScrollableFrame(cuerpo, width=300)
        form.grid(row=0, column=1, sticky="nsew")

        self.tree_usuarios = self.crear_treeview(
            tabla_frame, ("ID", "Nombre", "Apellido", "Registro", "Activo"),
            (70, 160, 160, 160, 80)
        )
        self.tree_usuarios.bind("<<TreeviewSelect>>", self.cargar_usuario_seleccionado)

        ctk.CTkLabel(form, text="Formulario de usuario", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15))
        self.entry_nombre = ctk.CTkEntry(form, placeholder_text="Nombre")
        self.entry_nombre.pack(fill="x", padx=10, pady=6)
        self.entry_apellido = ctk.CTkEntry(form, placeholder_text="Apellido")
        self.entry_apellido.pack(fill="x", padx=10, pady=6)

        self.switch_usuario_activo = ctk.CTkSwitch(form, text="Usuario activo")
        self.switch_usuario_activo.select()
        self.switch_usuario_activo.pack(anchor="w", padx=12, pady=10)

        ctk.CTkButton(form, text="➕ Registrar usuario", command=self.agregar_usuario).pack(fill="x", padx=10, pady=(12, 5))
        ctk.CTkButton(form, text="💾 Actualizar seleccionado", command=self.actualizar_usuario).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🧹 Nuevo / Limpiar", command=self.limpiar_form_usuario, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🗑️ Eliminar seleccionado", command=self.eliminar_usuario, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)

    def usuario_seleccionado_id(self):
        sel = self.tree_usuarios.selection()
        return self.tree_usuarios.item(sel[0])["values"][0] if sel else None

    def cargar_usuario_seleccionado(self, _=None):
        sel = self.tree_usuarios.selection()
        if not sel:
            return
        vals = self.tree_usuarios.item(sel[0])["values"]
        self.entry_nombre.delete(0, tk.END); self.entry_nombre.insert(0, vals[1])
        self.entry_apellido.delete(0, tk.END); self.entry_apellido.insert(0, vals[2])
        if vals[4]:
            self.switch_usuario_activo.select()
        else:
            self.switch_usuario_activo.deselect()

    def limpiar_form_usuario(self):
        self.tree_usuarios.selection_remove(self.tree_usuarios.selection())
        self.entry_nombre.delete(0, tk.END)
        self.entry_apellido.delete(0, tk.END)
        self.switch_usuario_activo.select()

    def agregar_usuario(self):
        nombre, apellido = self.entry_nombre.get().strip(), self.entry_apellido.get().strip()
        if not nombre or not apellido:
            return messagebox.showwarning("Campos incompletos", "Indica nombre y apellido.")
        try:
            self.ejecutar_consulta("INSERT INTO usuarios (nombre, apellido, activo) VALUES (%s, %s, %s)",
                                   (nombre, apellido, self.switch_usuario_activo.get() == 1))
            self.limpiar_form_usuario(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Usuario registrado correctamente.")
        except Exception as e:
            messagebox.showerror("Error de base de datos", str(e))

    def actualizar_usuario(self):
        uid = self.usuario_seleccionado_id()
        if uid is None:
            return messagebox.showwarning("Selección requerida", "Selecciona un usuario para actualizar.")
        nombre, apellido = self.entry_nombre.get().strip(), self.entry_apellido.get().strip()
        if not nombre or not apellido:
            return messagebox.showwarning("Campos incompletos", "Indica nombre y apellido.")
        try:
            self.ejecutar_consulta("UPDATE usuarios SET nombre=%s, apellido=%s, activo=%s WHERE id_usuario=%s",
                                   (nombre, apellido, self.switch_usuario_activo.get() == 1, uid))
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Usuario actualizado.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def eliminar_usuario(self):
        uid = self.usuario_seleccionado_id()
        if uid is None:
            return messagebox.showwarning("Selección requerida", "Selecciona un usuario.")
        if not messagebox.askyesno("Confirmar", "¿Eliminar el usuario seleccionado?"):
            return
        try:
            self.ejecutar_consulta("DELETE FROM usuarios WHERE id_usuario=%s", (uid,))
            self.limpiar_form_usuario(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Eliminado", "Usuario eliminado.")
        except Exception as e:
            messagebox.showerror("No se pudo eliminar", str(e))

    def cargar_datos_usuarios(self):
        try:
            rows = self.ejecutar_consulta(
                "SELECT id_usuario, nombre, apellido, fecha_registro, activo FROM usuarios ORDER BY nombre, apellido",
                fetch=True
            )
            for item in self.tree_usuarios.get_children(): self.tree_usuarios.delete(item)
            self.usuarios_combo = {}
            for row in rows:
                registro = row[3].strftime("%Y-%m-%d %H:%M") if hasattr(row[3], "strftime") else row[3]
                self.tree_usuarios.insert("", "end", values=(row[0], row[1], row[2], registro, "Sí" if row[4] else "No"))
                etiqueta = f"{row[1]} {row[2]} — #{row[0]}"
                self.usuarios_combo[etiqueta] = row[0]
        except Exception as e:
            print(f"Error cargando usuarios: {e}")

    # -------------------- CATEGORÍAS --------------------

    def configurar_pestana_categorias(self):
        self.crear_encabezado(self.tab_categorias, "Categorías", "Organiza los eventos mediante categorías y subcategorías.")

        cuerpo = ctk.CTkFrame(self.tab_categorias, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3); cuerpo.grid_columnconfigure(1, weight=1); cuerpo.grid_rowconfigure(0, weight=1)

        tabla = ctk.CTkFrame(cuerpo); tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        form = ctk.CTkScrollableFrame(cuerpo, width=320); form.grid(row=0, column=1, sticky="nsew")

        self.tree_categorias = self.crear_treeview(tabla, ("ID", "Categoría", "Categoría padre"), (80, 230, 230))
        self.tree_categorias.bind("<<TreeviewSelect>>", self.cargar_categoria_seleccionada)

        ctk.CTkLabel(form, text="Formulario de categoría", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15))
        self.entry_cat_nombre = ctk.CTkEntry(form, placeholder_text="Nombre de la categoría")
        self.entry_cat_nombre.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(form, text="Categoría padre").pack(anchor="w", padx=10, pady=(10, 2))
        self.combo_cat_padre = ctk.CTkComboBox(form, values=["Sin categoría padre"], state="readonly")
        self.combo_cat_padre.set("Sin categoría padre")
        self.combo_cat_padre.pack(fill="x", padx=10, pady=6)

        ctk.CTkButton(form, text="➕ Crear categoría", command=self.agregar_categoria).pack(fill="x", padx=10, pady=(15, 5))
        ctk.CTkButton(form, text="💾 Actualizar seleccionada", command=self.actualizar_categoria).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🧹 Nueva / Limpiar", command=self.limpiar_form_categoria, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🗑️ Eliminar seleccionada", command=self.eliminar_categoria, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)

    def categoria_seleccionada_id(self):
        sel = self.tree_categorias.selection()
        return self.tree_categorias.item(sel[0])["values"][0] if sel else None

    def cargar_categoria_seleccionada(self, _=None):
        sel = self.tree_categorias.selection()
        if not sel: return
        vals = self.tree_categorias.item(sel[0])["values"]
        self.entry_cat_nombre.delete(0, tk.END); self.entry_cat_nombre.insert(0, vals[1])
        padre = vals[2]
        self.combo_cat_padre.set(padre if padre in self.categorias_padre_combo else "Sin categoría padre")

    def limpiar_form_categoria(self):
        self.tree_categorias.selection_remove(self.tree_categorias.selection())
        self.entry_cat_nombre.delete(0, tk.END); self.combo_cat_padre.set("Sin categoría padre")

    def _padre_id_actual(self):
        valor = self.combo_cat_padre.get()
        return None if valor == "Sin categoría padre" else self.categorias_padre_combo.get(valor)

    def agregar_categoria(self):
        nombre = self.entry_cat_nombre.get().strip()
        if not nombre: return messagebox.showwarning("Campo requerido", "Indica el nombre de la categoría.")
        try:
            self.ejecutar_consulta("INSERT INTO categorias (nombre, id_categoria_padre) VALUES (%s, %s)",
                                   (nombre, self._padre_id_actual()))
            self.limpiar_form_categoria(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Categoría creada.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def actualizar_categoria(self):
        cid = self.categoria_seleccionada_id()
        if cid is None: return messagebox.showwarning("Selección requerida", "Selecciona una categoría.")
        nombre = self.entry_cat_nombre.get().strip(); padre = self._padre_id_actual()
        if not nombre: return messagebox.showwarning("Campo requerido", "Indica el nombre.")
        if padre == cid: return messagebox.showwarning("Relación inválida", "Una categoría no puede ser su propia categoría padre.")
        try:
            self.ejecutar_consulta("UPDATE categorias SET nombre=%s, id_categoria_padre=%s WHERE id_categoria=%s",
                                   (nombre, padre, cid))
            self.actualizar_todas_las_tablas(); messagebox.showinfo("Éxito", "Categoría actualizada.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def eliminar_categoria(self):
        cid = self.categoria_seleccionada_id()
        if cid is None: return messagebox.showwarning("Selección requerida", "Selecciona una categoría.")
        if not messagebox.askyesno("Confirmar", "¿Eliminar la categoría seleccionada?"): return
        try:
            self.ejecutar_consulta("DELETE FROM categorias WHERE id_categoria=%s", (cid,))
            self.limpiar_form_categoria(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Eliminado", "Categoría eliminada.")
        except Exception as e:
            messagebox.showerror("No se pudo eliminar", str(e))

    def cargar_datos_categorias(self):
        try:
            rows = self.ejecutar_consulta("""
                SELECT c.id_categoria, c.nombre, p.nombre
                FROM categorias c
                LEFT JOIN categorias p ON p.id_categoria = c.id_categoria_padre
                ORDER BY c.nombre
            """, fetch=True)
            ids = self.ejecutar_consulta("SELECT id_categoria, nombre FROM categorias ORDER BY nombre", fetch=True)

            for item in self.tree_categorias.get_children(): self.tree_categorias.delete(item)
            self.categorias_combo = {}
            self.categorias_padre_combo = {}
            for cid, nombre in ids:
                etiqueta = f"{nombre} — #{cid}"
                self.categorias_combo[etiqueta] = cid
                self.categorias_padre_combo[etiqueta] = cid
            for row in rows:
                padre = "Sin categoría padre"
                if row[2] is not None:
                    # Buscar etiqueta completa del padre
                    for etiqueta, cid in self.categorias_padre_combo.items():
                        if etiqueta.startswith(f"{row[2]} —"):
                            padre = etiqueta; break
                self.tree_categorias.insert("", "end", values=(row[0], row[1], padre))

            valores_padre = ["Sin categoría padre"] + list(self.categorias_padre_combo.keys())
            self.combo_cat_padre.configure(values=valores_padre)
            if self.combo_cat_padre.get() not in valores_padre:
                self.combo_cat_padre.set("Sin categoría padre")
        except Exception as e:
            print(f"Error cargando categorías: {e}")

    # -------------------- EVENTOS --------------------

    def configurar_pestana_eventos(self):
        self.crear_encabezado(self.tab_eventos, "Eventos", "Programa eventos seleccionando usuarios, categorías, fechas y horas.")

        cuerpo = ctk.CTkFrame(self.tab_eventos, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3); cuerpo.grid_columnconfigure(1, weight=1); cuerpo.grid_rowconfigure(0, weight=1)

        tabla = ctk.CTkFrame(cuerpo); tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        form = ctk.CTkScrollableFrame(cuerpo, width=350); form.grid(row=0, column=1, sticky="nsew")

        self.tree_eventos = self.crear_treeview(
            tabla, ("ID", "Propietario", "Categoría", "Ubicación", "Título", "Inicio", "Fin"),
            (70, 170, 150, 180, 220, 150, 150)
        )
        self.tree_eventos.bind("<<TreeviewSelect>>", self.cargar_evento_seleccionado)

        ctk.CTkLabel(form, text="Formulario de evento", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 12))

        self.entry_ev_titulo = ctk.CTkEntry(form, placeholder_text="Título del evento")
        self.entry_ev_titulo.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(form, text="Propietario").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_ev_usuario = ctk.CTkComboBox(form, values=["Seleccione un usuario"], state="readonly")
        self.combo_ev_usuario.set("Seleccione un usuario")
        self.combo_ev_usuario.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Categoría").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_ev_categoria = ctk.CTkComboBox(form, values=["Seleccione una categoría"], state="readonly")
        self.combo_ev_categoria.set("Seleccione una categoría")
        self.combo_ev_categoria.pack(fill="x", padx=10, pady=4)


        ctk.CTkLabel(form, text="Ubicación").pack(
            anchor="w",
            padx=10,
            pady=(8, 2)
        )

        self.combo_ev_ubicacion = ctk.CTkComboBox(
             form,
            values=["Seleccione una ubicación"],
            state="readonly"
        )

        self.combo_ev_ubicacion.set("Seleccione una ubicación")
        self.combo_ev_ubicacion.pack(fill="x", padx=10, pady=4)

        

        ctk.CTkLabel(form, text="Inicio").pack(anchor="w", padx=10, pady=(10, 2))
        fila_inicio = ctk.CTkFrame(form, fg_color="transparent"); fila_inicio.pack(fill="x", padx=10)
        self.fecha_inicio = self.crear_selector_fecha(fila_inicio)
        self.fecha_inicio.pack(side="left", fill="x", expand=True)
        self.hora_inicio = ctk.CTkEntry(fila_inicio, placeholder_text="HH:MM", width=75)
        self.hora_inicio.pack(side="left", padx=(6, 0))

        ctk.CTkLabel(form, text="Fin").pack(anchor="w", padx=10, pady=(10, 2))
        fila_fin = ctk.CTkFrame(form, fg_color="transparent"); fila_fin.pack(fill="x", padx=10)
        self.fecha_fin = self.crear_selector_fecha(fila_fin)
        self.fecha_fin.pack(side="left", fill="x", expand=True)
        self.hora_fin = ctk.CTkEntry(fila_fin, placeholder_text="HH:MM", width=75)
        self.hora_fin.pack(side="left", padx=(6, 0))

        ctk.CTkButton(form, text="➕ Crear evento", command=self.agregar_evento).pack(fill="x", padx=10, pady=(16, 5))
        ctk.CTkButton(form, text="💾 Actualizar seleccionado", command=self.actualizar_evento).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🧹 Nuevo / Limpiar", command=self.limpiar_form_evento, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🗑️ Eliminar seleccionado", command=self.eliminar_evento, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)

        self.limpiar_form_evento()

    def crear_selector_fecha(self, parent):
        if DateEntry is not None:
            return DateEntry(parent, date_pattern="yyyy-mm-dd", font=("Arial", 10))
        return ttk.Entry(parent)

    def obtener_fecha(self, widget):
        if DateEntry is not None:
            return widget.get_date().strftime("%Y-%m-%d")
        return widget.get().strip()

    def establecer_fecha(self, widget, valor):
        fecha = valor.date() if hasattr(valor, "date") else datetime.strptime(str(valor)[:10], "%Y-%m-%d").date()
        if DateEntry is not None:
            widget.set_date(fecha)
        else:
            widget.delete(0, tk.END); widget.insert(0, fecha.strftime("%Y-%m-%d"))

    def evento_seleccionado_id(self):
        sel = self.tree_eventos.selection()
        return self.tree_eventos.item(sel[0])["values"][0] if sel else None

    def cargar_evento_seleccionado(self, _=None):
        seleccion = self.tree_eventos.selection()

        if not seleccion:
            return

        datos = self.tree_eventos.item(
            seleccion[0]
        )["values"]

        self.entry_ev_titulo.delete(0, tk.END)
        self.entry_ev_titulo.insert(0, datos[4])

        self.combo_ev_usuario.set(datos[1])
        self.combo_ev_categoria.set(datos[2])
        self.combo_ev_ubicacion.set(datos[3])

        try:
            inicio = datetime.strptime(
                str(datos[5]),
                "%Y-%m-%d %H:%M"
            )

            fin = datetime.strptime(
                str(datos[6]),
                "%Y-%m-%d %H:%M"
            )

            self.establecer_fecha(
                self.fecha_inicio,
                inicio
            )

            self.establecer_fecha(
                self.fecha_fin,
                fin
            )

            self.hora_inicio.delete(0, tk.END)
            self.hora_inicio.insert(
                0,
                inicio.strftime("%H:%M")
            )

            self.hora_fin.delete(0, tk.END)
            self.hora_fin.insert(
                0,
                fin.strftime("%H:%M")
            )

        except ValueError:
            pass

    def limpiar_form_evento(self):
        self.tree_eventos.selection_remove(self.tree_eventos.selection())
        self.entry_ev_titulo.delete(0, tk.END)
        self.combo_ev_usuario.set("Seleccione un usuario")
        self.combo_ev_categoria.set("Seleccione una categoría")
        self.combo_ev_ubicacion.set("Seleccione una ubicación")
        hoy = datetime.now()
        self.establecer_fecha(self.fecha_inicio, hoy); self.establecer_fecha(self.fecha_fin, hoy)
        self.hora_inicio.delete(0, tk.END); self.hora_inicio.insert(0, "09:00")
        self.hora_fin.delete(0, tk.END); self.hora_fin.insert(0, "10:00")

    def datos_evento_formulario(self):
        titulo = self.entry_ev_titulo.get().strip()

        usuario = self.usuarios_combo.get(
            self.combo_ev_usuario.get()
        )

        categoria = self.categorias_combo.get(
            self.combo_ev_categoria.get()
        )

        ubicacion = self.ubicaciones_combo.get(
            self.combo_ev_ubicacion.get()
        )

        try:
            inicio = datetime.strptime(
                f"{self.obtener_fecha(self.fecha_inicio)} "
                f"{self.hora_inicio.get().strip()}",
                "%Y-%m-%d %H:%M"
            )

            fin = datetime.strptime(
                f"{self.obtener_fecha(self.fecha_fin)} "
                f"{self.hora_fin.get().strip()}",
                "%Y-%m-%d %H:%M"
            )

        except ValueError:
            raise ValueError(
                "La hora debe tener formato HH:MM, por ejemplo 09:30."
            )

        if (
            not titulo
            or usuario is None
            or categoria is None
            or ubicacion is None
        ):
            raise ValueError(
                "Completa título, propietario, categoría y ubicación."
            )

        if fin <= inicio:
            raise ValueError(
                "La fecha y hora de finalización deben ser posteriores al inicio."
            )

        return usuario, categoria, ubicacion, titulo, inicio, fin

    def hay_conflicto_ubicacion(self, ubicacion, inicio, fin):
        filas = self.ejecutar_consulta(
            """
            SELECT id_evento
            FROM eventos
            WHERE id_ubicacion = %s
              AND fecha_inicio < %s
              AND fecha_fin > %s
            """,
            (ubicacion, fin, inicio),
            fetch=True
        )

        return len(filas) > 0

    def agregar_evento(self):
        try:
            usuario, categoria, ubicacion, titulo, inicio, fin = self.datos_evento_formulario()

            if self.hay_conflicto_ubicacion(ubicacion, inicio, fin):
                messagebox.showwarning(
                    "Conflicto de ubicación",
                    "Ya existe un evento en esa ubicación durante ese horario."
                )
                return
            
            self.ejecutar_consulta(
                """
                INSERT INTO eventos
                (id_usuario_propietario, id_categoria, id_ubicacion,
                 titulo, fecha_inicio, fecha_fin)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (usuario, categoria, ubicacion, titulo, inicio, fin)
            )

            self.limpiar_form_evento()
            self.cargar_datos_eventos()

            messagebox.showinfo(
                "Éxito",
                "Evento creado correctamente."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo crear el evento",
                str(e)
            )

    def actualizar_evento(self):
        eid = self.evento_seleccionado_id()

        if eid is None:
            messagebox.showwarning(
                "Selección requerida",
                "Selecciona un evento."
            )
            return

        try:
            usuario, categoria, ubicacion, titulo, inicio, fin = self.datos_evento_formulario()

            conflictos = self.ejecutar_consulta(
                """
                SELECT id_evento
                FROM eventos
                WHERE id_ubicacion = %s
                  AND fecha_inicio < %s
                  AND fecha_fin > %s
                  AND id_evento <> %s
                """,
                (ubicacion, fin, inicio, eid),
                fetch=True
            )

            if len(conflictos) > 0:
                messagebox.showwarning(
                    "Conflicto de ubicación",
                    "Ya existe otro evento en esa ubicación durante ese horario."
                )
                return

            self.ejecutar_consulta(
                """
                UPDATE eventos
                SET id_usuario_propietario=%s,
                    id_categoria=%s,
                    id_ubicacion=%s,
                    titulo=%s,
                    fecha_inicio=%s,
                    fecha_fin=%s
                WHERE id_evento=%s
                """,
                (
                    usuario,
                    categoria,
                    ubicacion,
                    titulo,
                    inicio,
                    fin,
                    eid
                )
            )

            self.cargar_datos_eventos()

            messagebox.showinfo(
                "Éxito",
                "Evento actualizado."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo actualizar",
                str(e)
            )
        
    def eliminar_evento(self):
        eid = self.evento_seleccionado_id()
        if eid is None: return messagebox.showwarning("Selección requerida", "Selecciona un evento.")
        if not messagebox.askyesno("Confirmar", "¿Eliminar el evento seleccionado?"): return
        try:
            self.ejecutar_consulta("DELETE FROM eventos WHERE id_evento=%s", (eid,))
            self.limpiar_form_evento(); self.cargar_datos_eventos()
            messagebox.showinfo("Eliminado", "Evento eliminado.")
        except Exception as e:
            messagebox.showerror("No se pudo eliminar", str(e))

    def cargar_datos_eventos(self):
        try:
            filas = self.ejecutar_consulta(
                """
                SELECT
                    eventos.id_evento,
                    usuarios.id_usuario,
                    usuarios.nombre,
                    usuarios.apellido,
                    categorias.id_categoria,
                    categorias.nombre,
                    ubicaciones.id_ubicacion,
                    ubicaciones.nombre,
                    eventos.titulo,
                    eventos.fecha_inicio,
                    eventos.fecha_fin
                FROM eventos
                JOIN usuarios
                    ON usuarios.id_usuario = eventos.id_usuario_propietario
                JOIN categorias
                    ON categorias.id_categoria = eventos.id_categoria
                JOIN ubicaciones
                    ON ubicaciones.id_ubicacion = eventos.id_ubicacion
                ORDER BY eventos.fecha_inicio DESC
                """,
                fetch=True
            )

            for item in self.tree_eventos.get_children():
                self.tree_eventos.delete(item)

            for fila in filas:
                usuario = f"{fila[2]} {fila[3]} — #{fila[1]}"
                categoria = f"{fila[5]} — #{fila[4]}"
                ubicacion = f"{fila[7]} — #{fila[6]}"

                inicio = fila[9].strftime(
                    "%Y-%m-%d %H:%M"
                )

                fin = fila[10].strftime(
                    "%Y-%m-%d %H:%M"
                )

                self.tree_eventos.insert(
                    "",
                    "end",
                    values=(
                        fila[0],
                        usuario,
                        categoria,
                        ubicacion,
                        fila[8],
                        inicio,
                        fin
                    )
                )

            valores_u = (
                ["Seleccione un usuario"]
                + list(self.usuarios_combo.keys())
            )

            valores_c = (
                ["Seleccione una categoría"]
                + list(self.categorias_combo.keys())
            )

            self.combo_ev_usuario.configure(
                values=valores_u
            )

            self.combo_ev_categoria.configure(
                values=valores_c
            )

        except Exception as e:
            print(f"Error cargando eventos: {e}")

    # -------------------- UBICACIONES --------------------

    def configurar_pestana_ubicaciones(self):
        self.crear_encabezado(
            self.tab_ubicaciones,
            "Ubicaciones",
            "Registra, consulta y administra los recintos de los eventos."
        )

        cuerpo = ctk.CTkFrame(self.tab_ubicaciones, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        tabla = ctk.CTkFrame(cuerpo)
        tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        form = ctk.CTkScrollableFrame(cuerpo, width=320)
        form.grid(row=0, column=1, sticky="nsew")

        self.tree_ubicaciones = self.crear_treeview(
            tabla,
            ("ID", "Nombre", "Dirección", "Ciudad", "Capacidad"),
            (70, 180, 250, 150, 100)
        )

        self.tree_ubicaciones.bind(
            "<<TreeviewSelect>>",
            self.cargar_ubicacion_seleccionada
        )

        ctk.CTkLabel(
            form,
            text="Formulario de ubicación",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 15))

        self.entry_ubi_nombre = ctk.CTkEntry(
            form,
            placeholder_text="Nombre de la ubicación"
        )
        self.entry_ubi_nombre.pack(fill="x", padx=10, pady=6)

        self.entry_ubi_direccion = ctk.CTkEntry(
            form,
            placeholder_text="Dirección"
        )
        self.entry_ubi_direccion.pack(fill="x", padx=10, pady=6)

        self.entry_ubi_ciudad = ctk.CTkEntry(
            form,
            placeholder_text="Ciudad"
        )
        self.entry_ubi_ciudad.pack(fill="x", padx=10, pady=6)

        self.entry_ubi_capacidad = ctk.CTkEntry(
            form,
            placeholder_text="Capacidad"
        )
        self.entry_ubi_capacidad.pack(fill="x", padx=10, pady=6)

        ctk.CTkButton(
            form,
            text="➕ Registrar ubicación",
            command=self.agregar_ubicacion
        ).pack(fill="x", padx=10, pady=(15, 5))

        ctk.CTkButton(
            form,
            text="💾 Actualizar seleccionada",
            command=self.actualizar_ubicacion
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            form,
            text="🧹 Nueva / Limpiar",
            command=self.limpiar_form_ubicacion,
            fg_color="gray"
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            form,
            text="🗑️ Eliminar seleccionada",
            command=self.eliminar_ubicacion,
            fg_color="#b33939",
            hover_color="#8f2d2d"
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            form,
            text="📊 Ver ranking de uso",
            command=self.mostrar_ranking_ubicaciones
        ).pack(fill="x", padx=10, pady=(15, 5))

    def mostrar_ranking_ubicaciones(self):
        try:
            filas = self.ejecutar_consulta(
                """
                SELECT
                    ubicaciones.id_ubicacion,
                    ubicaciones.nombre,
                    COUNT(eventos.id_evento) AS cantidad_eventos
                FROM ubicaciones
                LEFT JOIN eventos
                    ON ubicaciones.id_ubicacion = eventos.id_ubicacion
                GROUP BY
                    ubicaciones.id_ubicacion,
                    ubicaciones.nombre
                ORDER BY cantidad_eventos DESC
                """,
                fetch=True
            )

            ventana = ctk.CTkToplevel(self)
            ventana.title("Ranking de ubicaciones")
            ventana.geometry("600x450")

            ctk.CTkLabel(
                ventana,
                text="Ranking de ubicaciones por cantidad de eventos",
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(pady=(20, 10))

            tree_ranking = self.crear_treeview(
                ventana,
                ("ID", "Ubicación", "Cantidad de eventos"),
                (80, 280, 160)
            )

            for fila in filas:
                tree_ranking.insert(
                    "",
                    "end",
                    values=fila
                )

        except Exception as e:
            messagebox.showerror(
                "Error",
                str(e)
            )    

    def ubicacion_seleccionada_id(self):
        seleccion = self.tree_ubicaciones.selection()

        if seleccion:
            return self.tree_ubicaciones.item(
                seleccion[0]
            )["values"][0]

        return None

    def cargar_ubicacion_seleccionada(self, _=None):
        seleccion = self.tree_ubicaciones.selection()

        if not seleccion:
            return

        datos = self.tree_ubicaciones.item(
            seleccion[0]
        )["values"]

        self.entry_ubi_nombre.delete(0, tk.END)
        self.entry_ubi_nombre.insert(0, datos[1])

        self.entry_ubi_direccion.delete(0, tk.END)
        self.entry_ubi_direccion.insert(0, datos[2])

        self.entry_ubi_ciudad.delete(0, tk.END)
        self.entry_ubi_ciudad.insert(0, datos[3])

        self.entry_ubi_capacidad.delete(0, tk.END)
        self.entry_ubi_capacidad.insert(0, datos[4])

    def limpiar_form_ubicacion(self):
        self.tree_ubicaciones.selection_remove(
            self.tree_ubicaciones.selection()
        )

        self.entry_ubi_nombre.delete(0, tk.END)
        self.entry_ubi_direccion.delete(0, tk.END)
        self.entry_ubi_ciudad.delete(0, tk.END)
        self.entry_ubi_capacidad.delete(0, tk.END)

    def agregar_ubicacion(self):
        nombre = self.entry_ubi_nombre.get().strip()
        direccion = self.entry_ubi_direccion.get().strip()
        ciudad = self.entry_ubi_ciudad.get().strip()
        capacidad_texto = self.entry_ubi_capacidad.get().strip()

        if not nombre or not direccion or not ciudad or not capacidad_texto:
            messagebox.showwarning(
                "Campos incompletos",
                "Completa todos los campos."
            )
            return

        try:
            capacidad = int(capacidad_texto)

            if capacidad <= 0:
                messagebox.showwarning(
                    "Capacidad inválida",
                    "La capacidad debe ser mayor que cero."
                )
                return

            self.ejecutar_consulta(
                """
                INSERT INTO ubicaciones
                (nombre, direccion, ciudad, capacidad)
                VALUES (%s, %s, %s, %s)
                """,
                (nombre, direccion, ciudad, capacidad)
            )

            self.limpiar_form_ubicacion()
            self.cargar_datos_ubicaciones()

            messagebox.showinfo(
                "Éxito",
                "Ubicación registrada correctamente."
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                str(e)
            )

    def actualizar_ubicacion(self):
        id_ubicacion = self.ubicacion_seleccionada_id()

        if id_ubicacion is None:
            messagebox.showwarning(
                "Selección requerida",
                "Selecciona una ubicación."
            )
            return

        nombre = self.entry_ubi_nombre.get().strip()
        direccion = self.entry_ubi_direccion.get().strip()
        ciudad = self.entry_ubi_ciudad.get().strip()
        capacidad_texto = self.entry_ubi_capacidad.get().strip()

        if not nombre or not direccion or not ciudad or not capacidad_texto:
            messagebox.showwarning(
                "Campos incompletos",
                "Completa todos los campos."
            )
            return

        try:
            capacidad = int(capacidad_texto)

            if capacidad <= 0:
                messagebox.showwarning(
                    "Capacidad inválida",
                    "La capacidad debe ser mayor que cero."
                )
                return

            self.ejecutar_consulta(
                """
                UPDATE ubicaciones
                SET nombre=%s,
                    direccion=%s,
                    ciudad=%s,
                    capacidad=%s
                WHERE id_ubicacion=%s
                """,
                (
                    nombre,
                    direccion,
                    ciudad,
                    capacidad,
                    id_ubicacion
                )
            )

            self.cargar_datos_ubicaciones()

            messagebox.showinfo(
                "Éxito",
                "Ubicación actualizada."
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                str(e)
            )

    def eliminar_ubicacion(self):
        id_ubicacion = self.ubicacion_seleccionada_id()

        if id_ubicacion is None:
            messagebox.showwarning(
                "Selección requerida",
                "Selecciona una ubicación."
            )
            return

        confirmar = messagebox.askyesno(
            "Confirmar",
            "¿Eliminar la ubicación seleccionada?"
        )

        if not confirmar:
            return

        try:
            self.ejecutar_consulta(
                "DELETE FROM ubicaciones WHERE id_ubicacion=%s",
                (id_ubicacion,)
            )

            self.limpiar_form_ubicacion()
            self.cargar_datos_ubicaciones()

            messagebox.showinfo(
                "Eliminado",
                "Ubicación eliminada."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo eliminar",
                str(e)
            )

    def cargar_datos_ubicaciones(self):
        try:
            filas = self.ejecutar_consulta(
                """
                SELECT
                    id_ubicacion,
                    nombre,
                    direccion,
                    ciudad,
                    capacidad
                FROM ubicaciones
                ORDER BY nombre
                """,
                fetch=True
            )

            for item in self.tree_ubicaciones.get_children():
                self.tree_ubicaciones.delete(item)

            self.ubicaciones_combo = {}

            for fila in filas:
                self.tree_ubicaciones.insert(
                    "",
                    "end",
                    values=fila
                )

                etiqueta = f"{fila[1]} — #{fila[0]}"
                self.ubicaciones_combo[etiqueta] = fila[0]

            valores_ubicaciones = (
                ["Seleccione una ubicación"]
                + list(self.ubicaciones_combo.keys())
            )

            self.combo_ev_ubicacion.configure(
                values=valores_ubicaciones
            )

            if self.combo_ev_ubicacion.get() not in valores_ubicaciones:
                self.combo_ev_ubicacion.set(
                    "Seleccione una ubicación"
                )

        except Exception as e:
            print(f"Error cargando ubicaciones: {e}")

    # -------------------- DISPONIBILIDAD --------------------

    def configurar_pestana_disponibilidad(self):
        self.crear_encabezado(
            self.tab_disponibilidad,
            "Disponibilidad",
            "Registra horarios y consulta usuarios disponibles."
        )

        cuerpo = ctk.CTkFrame(
            self.tab_disponibilidad,
            fg_color="transparent"
        )
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        tabla = ctk.CTkFrame(cuerpo)
        tabla.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 8)
        )

        form = ctk.CTkScrollableFrame(
            cuerpo,
            width=330
        )
        form.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        self.tree_disponibilidad = self.crear_treeview(
            tabla,
            ("ID", "Usuario", "Fecha", "Inicio", "Fin", "Tipo"),
            (70, 200, 110, 90, 90, 140)
        )

        self.tree_disponibilidad.bind(
            "<<TreeviewSelect>>",
            self.cargar_disponibilidad_seleccionada
        )

        ctk.CTkLabel(
            form,
            text="Formulario de disponibilidad",
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        ).pack(pady=(10, 15))

        ctk.CTkLabel(
            form,
            text="Usuario"
        ).pack(
            anchor="w",
            padx=10,
            pady=(4, 2)
        )

        self.combo_disp_usuario = ctk.CTkComboBox(
            form,
            values=["Seleccione un usuario"],
            state="readonly"
        )
        self.combo_disp_usuario.set(
            "Seleccione un usuario"
        )
        self.combo_disp_usuario.pack(
            fill="x",
            padx=10,
            pady=4
        )

        ctk.CTkLabel(
            form,
            text="Fecha"
        ).pack(
            anchor="w",
            padx=10,
            pady=(8, 2)
        )

        self.fecha_disp = self.crear_selector_fecha(form)
        self.fecha_disp.pack(
            fill="x",
            padx=10,
            pady=4
        )

        ctk.CTkLabel(
            form,
            text="Hora inicio"
        ).pack(
            anchor="w",
            padx=10,
            pady=(8, 2)
        )

        self.hora_disp_inicio = ctk.CTkEntry(
            form,
            placeholder_text="HH:MM"
        )
        self.hora_disp_inicio.pack(
            fill="x",
            padx=10,
            pady=4
        )
        self.hora_disp_inicio.insert(0, "09:00")

        ctk.CTkLabel(
            form,
            text="Hora fin"
        ).pack(
            anchor="w",
            padx=10,
            pady=(8, 2)
        )

        self.hora_disp_fin = ctk.CTkEntry(
            form,
            placeholder_text="HH:MM"
        )
        self.hora_disp_fin.pack(
            fill="x",
            padx=10,
            pady=4
        )
        self.hora_disp_fin.insert(0, "10:00")

        ctk.CTkLabel(
            form,
            text="Tipo"
        ).pack(
            anchor="w",
            padx=10,
            pady=(8, 2)
        )

        self.combo_disp_tipo = ctk.CTkComboBox(
            form,
            values=["Seleccione un tipo"],
            state="readonly"
        )
        self.combo_disp_tipo.set(
            "Seleccione un tipo"
        )
        self.combo_disp_tipo.pack(
            fill="x",
            padx=10,
            pady=4
        )

        ctk.CTkButton(
            form,
            text="➕ Registrar disponibilidad",
            command=self.agregar_disponibilidad
        ).pack(
            fill="x",
            padx=10,
            pady=(15, 5)
        )

        ctk.CTkButton(
            form,
            text="💾 Actualizar seleccionada",
            command=self.actualizar_disponibilidad
        ).pack(
            fill="x",
            padx=10,
            pady=5
        )

        ctk.CTkButton(
            form,
            text="🧹 Nueva / Limpiar",
            command=self.limpiar_form_disponibilidad,
            fg_color="gray"
        ).pack(
            fill="x",
            padx=10,
            pady=5
        )

        ctk.CTkButton(
            form,
            text="🗑️ Eliminar seleccionada",
            command=self.eliminar_disponibilidad,
            fg_color="#b33939",
            hover_color="#8f2d2d"
        ).pack(
            fill="x",
            padx=10,
            pady=5
        )

        ctk.CTkButton(
            form,
            text="👥 Ver usuarios disponibles",
            command=self.mostrar_usuarios_disponibles
        ).pack(
            fill="x",
            padx=10,
            pady=(15, 5)
        )

    def disponibilidad_seleccionada_id(self):
        seleccion = self.tree_disponibilidad.selection()

        if seleccion:
            return self.tree_disponibilidad.item(
                seleccion[0]
            )["values"][0]

        return None

    def cargar_disponibilidad_seleccionada(self, _=None):
        seleccion = self.tree_disponibilidad.selection()

        if not seleccion:
            return

        datos = self.tree_disponibilidad.item(
            seleccion[0]
        )["values"]

        self.combo_disp_usuario.set(datos[1])
        self.establecer_fecha(
            self.fecha_disp,
            datos[2]
        )

        self.hora_disp_inicio.delete(
            0,
            tk.END
        )
        self.hora_disp_inicio.insert(
            0,
            datos[3]
        )

        self.hora_disp_fin.delete(
            0,
            tk.END
        )
        self.hora_disp_fin.insert(
            0,
            datos[4]
        )

        self.combo_disp_tipo.set(datos[5])

    def limpiar_form_disponibilidad(self):
        self.tree_disponibilidad.selection_remove(
            self.tree_disponibilidad.selection()
        )

        self.combo_disp_usuario.set(
            "Seleccione un usuario"
        )
        self.combo_disp_tipo.set(
            "Seleccione un tipo"
        )

        hoy = datetime.now()
        self.establecer_fecha(
            self.fecha_disp,
            hoy
        )

        self.hora_disp_inicio.delete(
            0,
            tk.END
        )
        self.hora_disp_inicio.insert(
            0,
            "09:00"
        )

        self.hora_disp_fin.delete(
            0,
            tk.END
        )
        self.hora_disp_fin.insert(
            0,
            "10:00"
        )

    def datos_disponibilidad_formulario(self):
        usuario = self.usuarios_combo.get(
            self.combo_disp_usuario.get()
        )

        tipo = self.tipos_disponibilidad_combo.get(
            self.combo_disp_tipo.get()
        )

        fecha = self.obtener_fecha(
            self.fecha_disp
        )

        try:
            inicio = datetime.strptime(
                self.hora_disp_inicio.get().strip(),
                "%H:%M"
            )

            fin = datetime.strptime(
                self.hora_disp_fin.get().strip(),
                "%H:%M"
            )

        except ValueError:
            raise ValueError(
                "La hora debe tener formato HH:MM."
            )

        if usuario is None or tipo is None:
            raise ValueError(
                "Selecciona un usuario y un tipo."
            )

        if fin <= inicio:
            raise ValueError(
                "La hora final debe ser posterior a la inicial."
            )

        return (
            usuario,
            tipo,
            fecha,
            inicio.strftime("%H:%M"),
            fin.strftime("%H:%M")
        )

    def agregar_disponibilidad(self):
        try:
            usuario, tipo, fecha, inicio, fin = (
                self.datos_disponibilidad_formulario()
            )

            self.ejecutar_consulta(
                """
                INSERT INTO disponibilidades
                (
                    fecha,
                    hora_inicio,
                    hora_fin,
                    id_usuario,
                    id_tipo_disponibilidad
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    fecha,
                    inicio,
                    fin,
                    usuario,
                    tipo
                )
            )

            self.limpiar_form_disponibilidad()
            self.cargar_datos_disponibilidad()

            messagebox.showinfo(
                "Éxito",
                "Disponibilidad registrada correctamente."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo registrar",
                str(e)
            )

    def actualizar_disponibilidad(self):
        did = self.disponibilidad_seleccionada_id()

        if did is None:
            messagebox.showwarning(
                "Selección requerida",
                "Selecciona una disponibilidad."
            )
            return

        try:
            usuario, tipo, fecha, inicio, fin = (
                self.datos_disponibilidad_formulario()
            )

            self.ejecutar_consulta(
                """
                UPDATE disponibilidades
                SET fecha=%s,
                    hora_inicio=%s,
                    hora_fin=%s,
                    id_usuario=%s,
                    id_tipo_disponibilidad=%s
                WHERE id_disponibilidad=%s
                """,
                (
                    fecha,
                    inicio,
                    fin,
                    usuario,
                    tipo,
                    did
                )
            )

            self.cargar_datos_disponibilidad()

            messagebox.showinfo(
                "Éxito",
                "Disponibilidad actualizada."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo actualizar",
                str(e)
            )

    def eliminar_disponibilidad(self):
        did = self.disponibilidad_seleccionada_id()

        if did is None:
            messagebox.showwarning(
                "Selección requerida",
                "Selecciona una disponibilidad."
            )
            return

        if not messagebox.askyesno(
            "Confirmar",
            "¿Eliminar la disponibilidad seleccionada?"
        ):
            return

        try:
            self.ejecutar_consulta(
                """
                DELETE FROM disponibilidades
                WHERE id_disponibilidad=%s
                """,
                (did,)
            )

            self.limpiar_form_disponibilidad()
            self.cargar_datos_disponibilidad()

            messagebox.showinfo(
                "Eliminado",
                "Disponibilidad eliminada."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo eliminar",
                str(e)
            )

    def cargar_datos_disponibilidad(self):
        try:
            filas = self.ejecutar_consulta(
                """
                SELECT
                    disponibilidades.id_disponibilidad,
                    usuarios.id_usuario,
                    usuarios.nombre,
                    usuarios.apellido,
                    disponibilidades.fecha,
                    disponibilidades.hora_inicio,
                    disponibilidades.hora_fin,
                    tipos_disponibilidad.id_tipo_disponibilidad,
                    tipos_disponibilidad.nombre
                FROM disponibilidades
                JOIN usuarios
                    ON usuarios.id_usuario =
                       disponibilidades.id_usuario
                JOIN tipos_disponibilidad
                    ON tipos_disponibilidad.id_tipo_disponibilidad =
                       disponibilidades.id_tipo_disponibilidad
                ORDER BY
                    disponibilidades.fecha,
                    disponibilidades.hora_inicio
                """,
                fetch=True
            )

            tipos = self.ejecutar_consulta(
                """
                SELECT
                    id_tipo_disponibilidad,
                    nombre
                FROM tipos_disponibilidad
                ORDER BY id_tipo_disponibilidad
                """,
                fetch=True
            )

            for item in self.tree_disponibilidad.get_children():
                self.tree_disponibilidad.delete(item)

            self.tipos_disponibilidad_combo = {}

            for tid, nombre in tipos:
                etiqueta = f"{nombre} — #{tid}"
                self.tipos_disponibilidad_combo[
                    etiqueta
                ] = tid

            for fila in filas:
                usuario = (
                    f"{fila[2]} {fila[3]} — #{fila[1]}"
                )
                tipo = (
                    f"{fila[8]} — #{fila[7]}"
                )

                self.tree_disponibilidad.insert(
                    "",
                    "end",
                    values=(
                        fila[0],
                        usuario,
                        fila[4],
                        str(fila[5])[:5],
                        str(fila[6])[:5],
                        tipo
                    )
                )

            valores_usuarios = (
                ["Seleccione un usuario"]
                + list(self.usuarios_combo.keys())
            )

            valores_tipos = (
                ["Seleccione un tipo"]
                + list(
                    self.tipos_disponibilidad_combo.keys()
                )
            )

            self.combo_disp_usuario.configure(
                values=valores_usuarios
            )

            self.combo_disp_tipo.configure(
                values=valores_tipos
            )

        except Exception as e:
            print(
                f"Error cargando disponibilidad: {e}"
            )

    def mostrar_usuarios_disponibles(self):
        fecha = self.obtener_fecha(
            self.fecha_disp
        )

        hora_inicio = (
            self.hora_disp_inicio.get().strip()
        )

        hora_fin = (
            self.hora_disp_fin.get().strip()
        )

        try:
            inicio = datetime.strptime(
                f"{fecha} {hora_inicio}",
                "%Y-%m-%d %H:%M"
            )

            fin = datetime.strptime(
                f"{fecha} {hora_fin}",
                "%Y-%m-%d %H:%M"
            )

            if fin <= inicio:
                raise ValueError(
                    "La hora final debe ser posterior a la inicial."
                )

            filas = self.ejecutar_consulta(
                """
                SELECT DISTINCT
                    usuarios.id_usuario,
                    usuarios.nombre,
                    usuarios.apellido
                FROM usuarios
                JOIN disponibilidades
                    ON disponibilidades.id_usuario =
                       usuarios.id_usuario
                JOIN tipos_disponibilidad
                    ON tipos_disponibilidad.id_tipo_disponibilidad =
                       disponibilidades.id_tipo_disponibilidad
                WHERE usuarios.activo = TRUE
                  AND disponibilidades.fecha = %s
                  AND tipos_disponibilidad.nombre = 'Disponible'
                  AND disponibilidades.hora_inicio <= %s
                  AND disponibilidades.hora_fin >= %s
                  AND usuarios.id_usuario NOT IN (
                      SELECT eventos.id_usuario_propietario
                      FROM eventos
                      WHERE eventos.fecha_inicio < %s
                        AND eventos.fecha_fin > %s

                      UNION

                      SELECT participaciones.id_invitado
                      FROM participaciones
                      JOIN eventos
                          ON eventos.id_evento =
                             participaciones.id_evento
                      WHERE eventos.fecha_inicio < %s
                        AND eventos.fecha_fin > %s
                  )
                ORDER BY
                    usuarios.nombre,
                    usuarios.apellido
                """,
                (
                    fecha,
                    hora_inicio,
                    hora_fin,
                    fin,
                    inicio,
                    fin,
                    inicio
                ),
                fetch=True
            )

            ventana = ctk.CTkToplevel(self)
            ventana.title(
                "Usuarios disponibles"
            )
            ventana.geometry("550x420")

            ctk.CTkLabel(
                ventana,
                text="Usuarios disponibles en el horario",
                font=ctk.CTkFont(
                    size=18,
                    weight="bold"
                )
            ).pack(
                pady=(20, 5)
            )

            ctk.CTkLabel(
                ventana,
                text=(
                    f"{fecha} de "
                    f"{hora_inicio} a {hora_fin}"
                )
            ).pack(
                pady=(0, 10)
            )

            tree = self.crear_treeview(
                ventana,
                ("ID", "Nombre", "Apellido"),
                (80, 200, 200)
            )

            for fila in filas:
                tree.insert(
                    "",
                    "end",
                    values=fila
                )

        except Exception as e:
            messagebox.showerror(
                "Error",
                str(e)
            )

    # -------------------- TAREAS --------------------

    def configurar_pestana_tareas(self):
        self.crear_encabezado(
            self.tab_tareas,
            "Tareas",
            "Registra tareas asociadas a eventos y usuarios responsables."
        )

        cuerpo = ctk.CTkFrame(
            self.tab_tareas,
            fg_color="transparent"
        )
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        tabla = ctk.CTkFrame(cuerpo)
        tabla.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 8)
        )

        form = ctk.CTkScrollableFrame(
            cuerpo,
            width=340
        )
        form.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        self.tree_tareas = self.crear_treeview(
            tabla,
            (
                "ID",
                "Evento",
                "Título",
                "Descripción",
                "Prioridad",
                "Fecha límite",
                "Responsable",
                "Estado"
            ),
            (60, 180, 180, 220, 100, 120, 180, 120)
        )

        self.tree_tareas.bind(
            "<<TreeviewSelect>>",
            self.cargar_tarea_seleccionada
        )

        ctk.CTkLabel(
            form,
            text="Formulario de tarea",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 15))

        ctk.CTkLabel(
            form,
            text="Evento"
        ).pack(anchor="w", padx=10, pady=(4, 2))

        self.combo_tarea_evento = ctk.CTkComboBox(
            form,
            values=["Seleccione un evento"],
            state="readonly"
        )
        self.combo_tarea_evento.set("Seleccione un evento")
        self.combo_tarea_evento.pack(
            fill="x",
            padx=10,
            pady=4
        )

        self.entry_tarea_titulo = ctk.CTkEntry(
            form,
            placeholder_text="Título"
        )
        self.entry_tarea_titulo.pack(
            fill="x",
            padx=10,
            pady=6
        )

        self.entry_tarea_descripcion = ctk.CTkEntry(
            form,
            placeholder_text="Descripción"
        )
        self.entry_tarea_descripcion.pack(
            fill="x",
            padx=10,
            pady=6
        )

        ctk.CTkLabel(
            form,
            text="Prioridad"
        ).pack(anchor="w", padx=10, pady=(8, 2))

        self.combo_tarea_prioridad = ctk.CTkComboBox(
            form,
            values=["Baja", "Media", "Alta"],
            state="readonly"
        )
        self.combo_tarea_prioridad.set("Media")
        self.combo_tarea_prioridad.pack(
            fill="x",
            padx=10,
            pady=4
        )

        ctk.CTkLabel(
            form,
            text="Fecha límite"
        ).pack(anchor="w", padx=10, pady=(8, 2))

        self.fecha_tarea = self.crear_selector_fecha(form)
        self.fecha_tarea.pack(
            fill="x",
            padx=10,
            pady=4
        )

        ctk.CTkLabel(
            form,
            text="Responsable"
        ).pack(anchor="w", padx=10, pady=(8, 2))

        self.combo_tarea_usuario = ctk.CTkComboBox(
            form,
            values=["Seleccione un usuario"],
            state="readonly"
        )
        self.combo_tarea_usuario.set(
            "Seleccione un usuario"
        )
        self.combo_tarea_usuario.pack(
            fill="x",
            padx=10,
            pady=4
        )

        ctk.CTkLabel(
            form,
            text="Estado"
        ).pack(anchor="w", padx=10, pady=(8, 2))

        self.combo_tarea_estado = ctk.CTkComboBox(
            form,
            values=[
                "Pendiente",
                "En progreso",
                "Completada",
                "Cancelada"
            ],
            state="readonly"
        )
        self.combo_tarea_estado.set("Pendiente")
        self.combo_tarea_estado.pack(
            fill="x",
            padx=10,
            pady=4
        )

        ctk.CTkButton(
            form,
            text="➕ Registrar tarea",
            command=self.agregar_tarea
        ).pack(fill="x", padx=10, pady=(15, 5))

        ctk.CTkButton(
            form,
            text="💾 Actualizar seleccionada",
            command=self.actualizar_tarea
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            form,
            text="🧹 Nueva / Limpiar",
            command=self.limpiar_form_tarea,
            fg_color="gray"
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            form,
            text="🗑️ Eliminar seleccionada",
            command=self.eliminar_tarea,
            fg_color="#b33939",
            hover_color="#8f2d2d"
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            form,
            text="📊 Ver carga por usuario",
            command=self.mostrar_carga_tareas
        ).pack(fill="x", padx=10, pady=(15, 5))

        ctk.CTkButton(
            form,
            text="⏰ Ver tareas vencidas",
            command=self.mostrar_tareas_vencidas
        ).pack(fill="x", padx=10, pady=5)

    def tarea_seleccionada_id(self):
        seleccion = self.tree_tareas.selection()

        if seleccion:
            return self.tree_tareas.item(
                seleccion[0]
            )["values"][0]

        return None

    def cargar_tarea_seleccionada(self, _=None):
        seleccion = self.tree_tareas.selection()

        if not seleccion:
            return

        datos = self.tree_tareas.item(
            seleccion[0]
        )["values"]

        self.combo_tarea_evento.set(datos[1])

        self.entry_tarea_titulo.delete(0, tk.END)
        self.entry_tarea_titulo.insert(0, datos[2])

        self.entry_tarea_descripcion.delete(0, tk.END)
        self.entry_tarea_descripcion.insert(0, datos[3])

        self.combo_tarea_prioridad.set(datos[4])

        self.establecer_fecha(
            self.fecha_tarea,
            datos[5]
        )

        self.combo_tarea_usuario.set(datos[6])
        self.combo_tarea_estado.set(datos[7])

    def limpiar_form_tarea(self):
        self.tree_tareas.selection_remove(
            self.tree_tareas.selection()
        )

        self.combo_tarea_evento.set(
            "Seleccione un evento"
        )

        self.entry_tarea_titulo.delete(0, tk.END)
        self.entry_tarea_descripcion.delete(0, tk.END)

        self.combo_tarea_prioridad.set("Media")

        self.establecer_fecha(
            self.fecha_tarea,
            datetime.now()
        )

        self.combo_tarea_usuario.set(
            "Seleccione un usuario"
        )

        self.combo_tarea_estado.set("Pendiente")

    def datos_tarea_formulario(self):
        evento = self.eventos_combo.get(
            self.combo_tarea_evento.get()
        )

        usuario = self.usuarios_combo.get(
            self.combo_tarea_usuario.get()
        )

        titulo = self.entry_tarea_titulo.get().strip()
        descripcion = (
            self.entry_tarea_descripcion.get().strip()
        )

        prioridad = self.combo_tarea_prioridad.get()
        estado = self.combo_tarea_estado.get()

        fecha_limite = self.obtener_fecha(
            self.fecha_tarea
        )

        if evento is None:
            raise ValueError(
                "Selecciona un evento."
            )

        if usuario is None:
            raise ValueError(
                "Selecciona un responsable."
            )

        if not titulo:
            raise ValueError(
                "Indica el título de la tarea."
            )

        return (
            evento,
            usuario,
            titulo,
            descripcion,
            prioridad,
            fecha_limite,
            estado
        )

    def agregar_tarea(self):
        try:
            (
                evento,
                usuario,
                titulo,
                descripcion,
                prioridad,
                fecha_limite,
                estado
            ) = self.datos_tarea_formulario()

            self.ejecutar_consulta(
                """
                INSERT INTO tareas
                (
                    titulo,
                    descripcion,
                    prioridad,
                    fecha_limite,
                    estado,
                    id_evento,
                    id_usuario_responsable
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    titulo,
                    descripcion,
                    prioridad,
                    fecha_limite,
                    estado,
                    evento,
                    usuario
                )
            )

            self.limpiar_form_tarea()
            self.cargar_datos_tareas()

            messagebox.showinfo(
                "Éxito",
                "Tarea registrada correctamente."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo registrar",
                str(e)
            )

    def actualizar_tarea(self):
        tid = self.tarea_seleccionada_id()

        if tid is None:
            messagebox.showwarning(
                "Selección requerida",
                "Selecciona una tarea."
            )
            return

        try:
            (
                evento,
                usuario,
                titulo,
                descripcion,
                prioridad,
                fecha_limite,
                estado
            ) = self.datos_tarea_formulario()

            self.ejecutar_consulta(
                """
                UPDATE tareas
                SET titulo=%s,
                    descripcion=%s,
                    prioridad=%s,
                    fecha_limite=%s,
                    estado=%s,
                    id_evento=%s,
                    id_usuario_responsable=%s
                WHERE id_tarea=%s
                """,
                (
                    titulo,
                    descripcion,
                    prioridad,
                    fecha_limite,
                    estado,
                    evento,
                    usuario,
                    tid
                )
            )

            self.cargar_datos_tareas()

            messagebox.showinfo(
                "Éxito",
                "Tarea actualizada."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo actualizar",
                str(e)
            )

    def eliminar_tarea(self):
        tid = self.tarea_seleccionada_id()

        if tid is None:
            messagebox.showwarning(
                "Selección requerida",
                "Selecciona una tarea."
            )
            return

        if not messagebox.askyesno(
            "Confirmar",
            "¿Eliminar la tarea seleccionada?"
        ):
            return

        try:
            self.ejecutar_consulta(
                """
                DELETE FROM tareas
                WHERE id_tarea=%s
                """,
                (tid,)
            )

            self.limpiar_form_tarea()
            self.cargar_datos_tareas()

            messagebox.showinfo(
                "Eliminado",
                "Tarea eliminada."
            )

        except Exception as e:
            messagebox.showerror(
                "No se pudo eliminar",
                str(e)
            )

    def cargar_datos_tareas(self):
        try:
            filas = self.ejecutar_consulta(
                """
                SELECT
                    tareas.id_tarea,
                    eventos.id_evento,
                    eventos.titulo,
                    tareas.titulo,
                    tareas.descripcion,
                    tareas.prioridad,
                    tareas.fecha_limite,
                    usuarios.id_usuario,
                    usuarios.nombre,
                    usuarios.apellido,
                    tareas.estado
                FROM tareas
                JOIN eventos
                    ON eventos.id_evento =
                       tareas.id_evento
                JOIN usuarios
                    ON usuarios.id_usuario =
                       tareas.id_usuario_responsable
                ORDER BY tareas.fecha_limite
                """,
                fetch=True
            )

            eventos = self.ejecutar_consulta(
                """
                SELECT id_evento, titulo
                FROM eventos
                ORDER BY titulo
                """,
                fetch=True
            )

            for item in self.tree_tareas.get_children():
                self.tree_tareas.delete(item)

            self.eventos_combo = {}

            for eid, titulo_evento in eventos:
                etiqueta = (
                    f"{titulo_evento} — #{eid}"
                )
                self.eventos_combo[etiqueta] = eid

            for fila in filas:
                evento = (
                    f"{fila[2]} — #{fila[1]}"
                )

                responsable = (
                    f"{fila[8]} {fila[9]} — #{fila[7]}"
                )

                self.tree_tareas.insert(
                    "",
                    "end",
                    values=(
                        fila[0],
                        evento,
                        fila[3],
                        fila[4] or "",
                        fila[5],
                        fila[6],
                        responsable,
                        fila[10]
                    )
                )

            valores_eventos = (
                ["Seleccione un evento"]
                + list(self.eventos_combo.keys())
            )

            valores_usuarios = (
                ["Seleccione un usuario"]
                + list(self.usuarios_combo.keys())
            )

            self.combo_tarea_evento.configure(
                values=valores_eventos
            )

            self.combo_tarea_usuario.configure(
                values=valores_usuarios
            )

        except Exception as e:
            print(
                f"Error cargando tareas: {e}"
            )

    def mostrar_carga_tareas(self):
        try:
            filas = self.ejecutar_consulta(
                """
                SELECT
                    usuarios.id_usuario,
                    usuarios.nombre,
                    usuarios.apellido,
                    COUNT(
                        CASE
                            WHEN tareas.estado = 'Pendiente'
                            THEN 1
                        END
                    ) AS pendientes,
                    COUNT(
                        CASE
                            WHEN tareas.estado = 'En progreso'
                            THEN 1
                        END
                    ) AS en_progreso,
                    COUNT(
                        CASE
                            WHEN tareas.estado IN
                                 ('Pendiente', 'En progreso')
                            THEN 1
                        END
                    ) AS total_activas
                FROM usuarios
                LEFT JOIN tareas
                    ON tareas.id_usuario_responsable =
                       usuarios.id_usuario
                GROUP BY
                    usuarios.id_usuario,
                    usuarios.nombre,
                    usuarios.apellido
                ORDER BY total_activas DESC
                """,
                fetch=True
            )

            ventana = ctk.CTkToplevel(self)
            ventana.title("Carga de tareas")
            ventana.geometry("750x450")

            ctk.CTkLabel(
                ventana,
                text="Carga de tareas por usuario",
                font=ctk.CTkFont(
                    size=18,
                    weight="bold"
                )
            ).pack(pady=(20, 10))

            tree = self.crear_treeview(
                ventana,
                (
                    "ID",
                    "Nombre",
                    "Apellido",
                    "Pendientes",
                    "En progreso",
                    "Total activas"
                ),
                (70, 150, 150, 110, 110, 110)
            )

            for fila in filas:
                tree.insert(
                    "",
                    "end",
                    values=fila
                )

        except Exception as e:
            messagebox.showerror(
                "Error",
                str(e)
            )

    def mostrar_tareas_vencidas(self):
        try:
            filas = self.ejecutar_consulta(
                """
                SELECT
                    tareas.id_tarea,
                    tareas.titulo,
                    usuarios.nombre,
                    usuarios.apellido,
                    tareas.fecha_limite,
                    tareas.estado
                FROM tareas
                JOIN usuarios
                    ON usuarios.id_usuario =
                       tareas.id_usuario_responsable
                WHERE tareas.fecha_limite < CURRENT_DATE
                  AND tareas.estado NOT IN
                      ('Completada', 'Cancelada')
                ORDER BY tareas.fecha_limite
                """,
                fetch=True
            )

            ventana = ctk.CTkToplevel(self)
            ventana.title("Tareas vencidas")
            ventana.geometry("750x450")

            ctk.CTkLabel(
                ventana,
                text="Tareas vencidas",
                font=ctk.CTkFont(
                    size=18,
                    weight="bold"
                )
            ).pack(pady=(20, 10))

            tree = self.crear_treeview(
                ventana,
                (
                    "ID",
                    "Tarea",
                    "Nombre",
                    "Apellido",
                    "Fecha límite",
                    "Estado"
                ),
                (70, 200, 130, 130, 120, 120)
            )

            for fila in filas:
                tree.insert(
                    "",
                    "end",
                    values=fila
                )

        except Exception as e:
            messagebox.showerror(
                "Error",
                str(e)
            )

    # -------------------- REFRESCO GENERAL --------------------

    def actualizar_todas_las_tablas(self):
        self.cargar_datos_usuarios()
        self.cargar_datos_categorias()
        self.cargar_datos_eventos()
        self.cargar_datos_ubicaciones()
        self.cargar_datos_disponibilidad()
        self.cargar_datos_tareas()



if __name__ == "__main__":
    app = AppAgenda()
    app.mainloop()

