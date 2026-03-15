import streamlit as st
import pandas as pd
from datetime import datetime
from db import get_session, Tutoria, Inscripcion
import uuid
import requests
from streamlit_lottie import st_lottie

def load_css():
    with open("frontend/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()

def load_lottie(url):
    try:
        r = requests.get(url, timeout=4)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

if not st.session_state.get("autenticado"):
    st.warning("Acceso restringido. Inicia sesión primero.")
    st.stop()
if st.session_state.rol != "Docente":
    st.error("Acceso denegado. Módulo exclusivo para docentes.")
    st.stop()

# ── Header ──────────────────────────────────────────────────
st.markdown(f"""
<div style="animation: fadeUp 0.5s ease; margin-bottom: 2rem;">
    <div class="section-label">Portal Académico — Docente</div>
    <div class="page-title">Gestión de sesiones</div>
    <div class="page-subtitle">Programa nuevas tutorías y administra tus estudiantes inscritos.</div>
</div>
""", unsafe_allow_html=True)

# ── DB Helpers ───────────────────────────────────────────────
def crear_tutoria(docente_id, titulo, descripcion, fecha, h_inicio, h_fin, cupo):
    session = get_session()
    if not session:
        return False, "Error de conexión."
    try:
        session.add(Tutoria(
            docente_id=uuid.UUID(docente_id),
            titulo=titulo,
            descripcion=descripcion,
            fecha=fecha,
            hora_inicio=h_inicio,
            hora_fin=h_fin,
            cupo_maximo=cupo,
            estado='Programada'
        ))
        session.commit()
        return True, "Sesión creada y publicada correctamente."
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()

def get_mis_tutorias(docente_id):
    session = get_session()
    if not session:
        return []
    try:
        tutorias = session.query(Tutoria).filter_by(
            docente_id=uuid.UUID(docente_id)
        ).order_by(Tutoria.fecha.desc()).all()
        result = []
        for t in tutorias:
            inscritos = session.query(Inscripcion).filter_by(tutoria_id=t.id, estado='Confirmada').count()
            inscripciones = session.query(Inscripcion).filter_by(tutoria_id=t.id, estado='Confirmada').all()
            estudiantes = [{"Estudiante": i.estudiante.nombre_completo, "Correo": i.estudiante.email} for i in inscripciones]
            result.append({
                "titulo": t.titulo,
                "fecha": t.fecha.strftime("%d %b %Y"),
                "horario": f"{t.hora_inicio.strftime('%H:%M')} – {t.hora_fin.strftime('%H:%M')}",
                "cupo_max": t.cupo_maximo,
                "inscritos": inscritos,
                "estado": t.estado,
                "estudiantes": estudiantes
            })
        return result
    except Exception as e:
        st.error(f"Error al cargar sesiones: {e}")
        return []
    finally:
        session.close()

# ── Tabs ─────────────────────────────────────────────────────
tab_crear, tab_mis = st.tabs(["Nueva sesión", "Mis sesiones"])

with tab_crear:
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("""
        <div style="padding: 1rem 0; animation: fadeUp 0.6s ease;">
            <div class="section-label" style="margin-bottom: 12px;">¿Qué puedes hacer aquí?</div>
            <p style="color:#94a3b8; font-size:0.9rem; line-height:1.6;">
                Registra una nueva tutoría con su tema, horario y aforo. 
                Una vez publicada, los estudiantes podrán inscribirse desde su panel.
            </p>
        </div>
        """, unsafe_allow_html=True)
        lottie = load_lottie("https://lottie.host/1bdedc71-cb8e-4a6c-9dd6-9f170afc07ba/Y5J09pPjS4.json")
        if lottie:
            st_lottie(lottie, height=220)

    with col_right:
        with st.form("form_crear_tutoria", clear_on_submit=True):
            titulo = st.text_input("Título de la sesión", placeholder="Ej: Álgebra Lineal — Vectores")
            desc = st.text_area("Descripción", placeholder="Temas a cubrir, materiales requeridos...", height=90)

            c1, c2 = st.columns(2)
            with c1:
                fecha = st.date_input("Fecha", min_value=datetime.now().date())
            with c2:
                cupo = st.number_input("Cupo máximo", min_value=1, max_value=100, value=15)

            c3, c4 = st.columns(2)
            with c3:
                h_inicio = st.time_input("Hora de inicio")
            with c4:
                h_fin = st.time_input("Hora de fin")

            submitted = st.form_submit_button("Publicar sesión", type="primary", use_container_width=True)
            if submitted:
                if not titulo:
                    st.warning("El título es obligatorio.")
                elif h_inicio >= h_fin:
                    st.error("La hora de inicio debe ser anterior a la de fin.")
                else:
                    ok, msg = crear_tutoria(
                        st.session_state.usuario_id, titulo, desc, fecha, h_inicio, h_fin, cupo
                    )
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

with tab_mis:
    mis_tutorias = get_mis_tutorias(st.session_state.usuario_id)

    if mis_tutorias:
        for tut in mis_tutorias:
            pct = int((tut["inscritos"] / tut["cupo_max"]) * 100) if tut["cupo_max"] else 0
            estado_cls = "tag-green" if tut["estado"] == "Programada" else "tag-red"
            with st.container(border=True):
                h1, h2 = st.columns([3, 1])
                with h1:
                    st.markdown(f"**{tut['titulo']}** — {tut['fecha']}")
                    st.caption(f"Horario: {tut['horario']}")
                with h2:
                    st.markdown(f'<span class="tag {estado_cls}">{tut["estado"]}</span>', unsafe_allow_html=True)
                    st.progress(pct)
                    st.caption(f'{tut["inscritos"]} / {tut["cupo_max"]} inscritos')
                if tut["estudiantes"]:
                    st.dataframe(pd.DataFrame(tut["estudiantes"]), use_container_width=True, hide_index=True)
                else:
                    st.markdown('<p style="color:#64748b; font-size:0.88rem; margin:0;">Sin estudiantes inscritos aún.</p>', unsafe_allow_html=True)

    else:
        st.markdown('<p style="color:#64748b;">No has creado ninguna sesión todavía. Ve a la pestaña "Nueva sesión".</p>', unsafe_allow_html=True)
