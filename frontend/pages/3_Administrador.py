import streamlit as st
import pandas as pd
import plotly.express as px
from db import get_session, Usuario, Rol, Tutoria, Inscripcion
from streamlit_extras.metric_cards import style_metric_cards
from sqlalchemy.orm import joinedload
import uuid

def load_css():
    with open("frontend/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()
style_metric_cards(border_left_color="#059669", background_color="#ffffff")

if not st.session_state.get("autenticado"):
    st.warning("Acceso restringido. Inicia sesión primero.")
    st.stop()
if st.session_state.rol != "Administrador":
    st.error("Acceso denegado. Módulo exclusivo para administradores.")
    st.stop()

# ── Header ──────────────────────────────────────────────────
st.markdown("""
<div style="animation: fadeUp 0.5s ease; margin-bottom: 2rem;">
    <div class="section-label">Sistema — Administración</div>
    <div class="page-title">Panel de Control</div>
    <div class="page-subtitle">Métricas, gestión de usuarios y configuración de la plataforma.</div>
</div>
""", unsafe_allow_html=True)

# ── DB Helpers ───────────────────────────────────────────────
def get_roles():
    session = get_session()
    if not session:
        return {}
    try:
        return {r.nombre: r.id for r in session.query(Rol).all()}
    finally:
        session.close()

def get_all_users():
    session = get_session()
    if not session:
        return []
    try:
        usuarios = session.query(Usuario).options(joinedload(Usuario.rol)).all()
        return [
            {
                "Nombre": u.nombre_completo,
                "Correo": u.email,
                "Rol": u.rol.nombre if u.rol else "Sin rol",
                "Estado": "Activo" if u.activo else "Inactivo",
                "_id": str(u.id),
                "_activo": u.activo,
            }
            for u in usuarios
        ]
    finally:
        session.close()

def crear_usuario(nombre, email, password, rol_nombre):
    session = get_session()
    if not session:
        return False, "Error de conexión."
    try:
        if session.query(Usuario).filter_by(email=email).first():
            return False, "El correo ya está registrado."
        roles = get_roles()
        session.add(Usuario(
            nombre_completo=nombre,
            email=email,
            password=password,
            rol_id=roles.get(rol_nombre),
            activo=True
        ))
        session.commit()
        return True, f"Cuenta creada para {nombre}."
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()

def toggle_estado(user_id, nuevo_estado):
    session = get_session()
    if not session:
        return False
    try:
        u = session.query(Usuario).filter_by(id=uuid.UUID(user_id)).first()
        if u:
            u.activo = nuevo_estado
            session.commit()
            return True
    except:
        session.rollback()
    finally:
        session.close()
    return False

def get_stats():
    session = get_session()
    if not session:
        return 0, 0, 0, 0
    try:
        return (
            session.query(Usuario).count(),
            session.query(Usuario).filter_by(activo=True).count(),
            session.query(Tutoria).count(),
            session.query(Inscripcion).count(),
        )
    finally:
        session.close()

def get_chart_data():
    session = get_session()
    if not session:
        return [], []
    try:
        tutorias = session.query(Tutoria).all()
        tut_data = [
            {
                "Tutoría": t.titulo[:28] + ("…" if len(t.titulo) > 28 else ""),
                "Inscritos": session.query(Inscripcion).filter_by(tutoria_id=t.id, estado='Confirmada').count()
            }
            for t in tutorias
        ]
        roles = session.query(Rol).all()
        rol_data = [
            {"Rol": r.nombre, "Cantidad": session.query(Usuario).filter_by(rol_id=r.id, activo=True).count()}
            for r in roles
        ]
        return tut_data, rol_data
    finally:
        session.close()

# ── Tabs ─────────────────────────────────────────────────────
tab_dash, tab_users, tab_new = st.tabs(["Dashboard", "Usuarios", "Nuevo usuario"])

# ─── TAB 1: Dashboard ────────────────────────────────────────
with tab_dash:
    total, activos, total_tut, total_ins = get_stats()

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Usuarios totales", total)
    with c2: st.metric("Usuarios activos", activos)
    with c3: st.metric("Tutorías creadas", total_tut)
    with c4: st.metric("Inscripciones", total_ins)

    st.markdown('<hr class="divider-line">', unsafe_allow_html=True)

    tut_data, rol_data = get_chart_data()
    chart1, chart2 = st.columns(2, gap="large")

    PLOTLY_LAYOUT = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#1e293b", size=12),
        margin=dict(l=0, r=0, t=28, b=0),
    )

    with chart1:
        st.markdown('<div class="section-label">Inscritos por tutoría</div>', unsafe_allow_html=True)
        if tut_data:
            df = pd.DataFrame(tut_data).sort_values("Inscritos", ascending=True)
            fig = px.bar(
                df, x="Inscritos", y="Tutoría", orientation="h",
                color="Inscritos",
                color_continuous_scale=["#dcfce7", "#10b981", "#059669"],
                template="plotly_white",
            )
            fig.update_traces(marker_line_width=0)
            fig.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False)
            fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.05)", zeroline=False)
            fig.update_yaxes(showgrid=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos suficientes para el gráfico.")

    with chart2:
        st.markdown('<div class="section-label">Distribución por rol</div>', unsafe_allow_html=True)
        if rol_data:
            df2 = pd.DataFrame(rol_data)
            fig2 = px.pie(
                df2, names="Rol", values="Cantidad",
                hole=0.55,
                color_discrete_sequence=["#059669", "#10b981", "#34d399"],
                template="plotly_white",
            )
            fig2.update_traces(textposition="outside", textfont_size=12)
            fig2.update_layout(
                **PLOTLY_LAYOUT,
                legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sin datos suficientes para el gráfico.")

# ─── TAB 2: Gestión de Usuarios ──────────────────────────────
with tab_users:
    todos = get_all_users()
    busqueda = st.text_input("Buscar por nombre o correo", placeholder="Filtra la lista de usuarios...", label_visibility="collapsed")

    filtrados = (
        [u for u in todos if busqueda.lower() in u["Nombre"].lower() or busqueda.lower() in u["Correo"].lower()]
        if busqueda else todos
    )

    df_tabla = pd.DataFrame([{k: v for k, v in u.items() if not k.startswith("_")} for u in filtrados])
    st.dataframe(
        df_tabla,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Estado": st.column_config.TextColumn("Estado"),
        }
    )

    st.markdown('<hr class="divider-line">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Cambiar estado de acceso</div>', unsafe_allow_html=True)

    opciones = {f"{u['Nombre']} — {u['Correo']}": u for u in todos}
    sel_label = st.selectbox("Seleccionar usuario", list(opciones.keys()), label_visibility="collapsed")
    if sel_label:
        sel = opciones[sel_label]
        col_toggle, _ = st.columns([1, 3])
        with col_toggle:
            accion = "Desactivar cuenta" if sel["_activo"] else "Activar cuenta"
            if st.button(accion, use_container_width=True):
                if toggle_estado(sel["_id"], not sel["_activo"]):
                    verb = "desactivada" if sel["_activo"] else "activada"
                    st.success(f"Cuenta {verb} correctamente.")
                    st.rerun()

# ─── TAB 3: Nuevo Usuario ────────────────────────────────────
with tab_new:
    col_form, col_help = st.columns([2, 1], gap="large")

    with col_help:
        st.markdown("""
        <div style="background: #f0fdf4; border: 1px solid #dcfce7; border-radius: 12px; padding: 20px; animation: fadeUp 0.5s ease;">
            <div class="section-label" style="margin-bottom: 10px;">Roles del sistema</div>
            <p style="color:#1e293b; font-size:0.85rem; line-height:1.7; margin:0;">
                <strong style="color:#065f46;">Estudiante</strong><br>
                Busca e inscribe sesiones.<br><br>
                <strong style="color:#065f46;">Docente</strong><br>
                Crea y administra tutorías propias.<br><br>
                <strong style="color:#065f46;">Administrador</strong><br>
                Control total de la plataforma.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_form:
        with st.form("form_nuevo_usuario", clear_on_submit=True):
            nombre = st.text_input("Nombre completo", placeholder="Juan Andrés Pérez")
            email = st.text_input("Correo institucional", placeholder="jperez@institucion.edu.co")
            pwd = st.text_input("Contraseña temporal", type="password")
            rol_sel = st.selectbox("Rol asignado", list(get_roles().keys()))
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Crear cuenta", type="primary", use_container_width=True)

            if submitted:
                if not nombre or not email or not pwd:
                    st.warning("Todos los campos son obligatorios.")
                else:
                    ok, msg = crear_usuario(nombre, email, pwd, rol_sel)
                    if ok:
                        st.success(msg)
                        st.toast("Usuario registrado en el sistema.")
                    else:
                        st.error(msg)
