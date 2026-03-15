import streamlit as st
import time
import pandas as pd
from datetime import datetime
from db import get_session, Tutoria, Inscripcion
from streamlit_extras.metric_cards import style_metric_cards
import uuid
import requests
from streamlit_lottie import st_lottie

def load_css():
    with open("frontend/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()
style_metric_cards(border_left_color="#6366f1", background_color="rgba(0,0,0,0)")

def load_lottie(url):
    try:
        r = requests.get(url, timeout=4)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

if not st.session_state.get("autenticado"):
    st.warning("Acceso restringido. Por favor inicia sesión.")
    st.stop()
if st.session_state.rol != "Estudiante":
    st.error("No tienes permisos para acceder a este módulo.")
    st.stop()

# ── Header ──────────────────────────────────────────────────
st.markdown(f"""
<div style="animation: fadeUp 0.5s ease; margin-bottom: 2rem;">
    <div class="section-label">Portal Académico — Estudiante</div>
    <div class="page-title">Tutorías disponibles</div>
    <div class="page-subtitle">Inscríbete en sesiones programadas por tus docentes.</div>
</div>
""", unsafe_allow_html=True)

# ── DB helpers ───────────────────────────────────────────────
def get_tutorias_disponibles():
    session = get_session()
    if not session:
        return []
    try:
        hoy = datetime.now().date()
        tutorias = session.query(Tutoria).filter(
            Tutoria.fecha >= hoy, Tutoria.estado != 'Cancelada'
        ).all()
        data = []
        for t in tutorias:
            inscritos = session.query(Inscripcion).filter_by(tutoria_id=t.id, estado='Confirmada').count()
            data.append({
                "id": str(t.id),
                "titulo": t.titulo,
                "desc": t.descripcion or "",
                "docente": t.docente.nombre_completo,
                "fecha": t.fecha.strftime("%d %b %Y"),
                "horario": f"{t.hora_inicio.strftime('%H:%M')} – {t.hora_fin.strftime('%H:%M')}",
                "cupo_max": t.cupo_maximo,
                "inscritos": inscritos,
                "disponibles": t.cupo_maximo - inscritos,
            })
        return data
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return []
    finally:
        session.close()

def get_mis_inscripciones(estudiante_id):
    session = get_session()
    if not session:
        return []
    try:
        inscripciones = session.query(Inscripcion).filter_by(
            estudiante_id=uuid.UUID(estudiante_id)
        ).all()
        return [
            {
                "Tutoría": i.tutoria.titulo,
                "Docente": i.tutoria.docente.nombre_completo,
                "Fecha": i.tutoria.fecha.strftime("%d %b %Y"),
                "Estado": "Confirmada" if i.estado == "Confirmada" else "Cancelada",
            }
            for i in inscripciones
        ]
    except Exception as e:
        st.error(f"Error al cargar historial: {e}")
        return []
    finally:
        session.close()

def inscribir_tutoria(estudiante_id, tutoria_id):
    session = get_session()
    if not session:
        return False, "Error de conexión."
    try:
        existe = session.query(Inscripcion).filter_by(
            estudiante_id=uuid.UUID(estudiante_id),
            tutoria_id=uuid.UUID(tutoria_id)
        ).first()
        if existe:
            return False, "Ya estás inscrito en esta tutoría."
        tutoria = session.query(Tutoria).filter_by(id=uuid.UUID(tutoria_id)).first()
        inscritos = session.query(Inscripcion).filter_by(tutoria_id=uuid.UUID(tutoria_id), estado='Confirmada').count()
        if inscritos >= tutoria.cupo_maximo:
            return False, "Sin cupos disponibles."
        session.add(Inscripcion(
            tutoria_id=uuid.UUID(tutoria_id),
            estudiante_id=uuid.UUID(estudiante_id),
            estado='Confirmada'
        ))
        session.commit()
        return True, "Inscripción confirmada."
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()

# ── Tabs ─────────────────────────────────────────────────────
tab_explorar, tab_historial = st.tabs(["Explorar sesiones", "Mi historial"])

with tab_explorar:
    tutorias = get_tutorias_disponibles()

    if tutorias:
        cols = st.columns(3)
        for i, tut in enumerate(tutorias):
            with cols[i % 3]:
                with st.container(border=True):
                    pct = int((tut["inscritos"] / tut["cupo_max"]) * 100) if tut["cupo_max"] > 0 else 0
                    disponible = tut["disponibles"] > 0

                    # Status tag
                    tag_cls = "tag-green" if disponible else "tag-red"
                    tag_txt = "Con cupo" if disponible else "Sin cupo"
                    st.markdown(f'<span class="tag {tag_cls}">{tag_txt}</span>', unsafe_allow_html=True)
                    st.markdown(f"**{tut['titulo']}**")
                    st.caption(f"{tut['docente']}  ·  {tut['fecha']}  ·  {tut['horario']}")
                    
                    if tut["desc"]:
                        st.markdown(f'<p style="font-size:0.82rem; color:#64748b; margin: 4px 0 8px;">{tut["desc"][:120] + ("…" if len(tut["desc"]) > 120 else "")}</p>', unsafe_allow_html=True)

                    st.progress(pct)
                    st.caption(f"{tut['inscritos']} / {tut['cupo_max']} inscritos")

                    if disponible:
                        if st.button("Inscribirse", key=f"ins_{tut['id']}", use_container_width=True, type="primary"):
                            ok, msg = inscribir_tutoria(st.session_state.usuario_id, tut["id"])
                            if ok:
                                st.toast(msg)
                                time.sleep(0.8)
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.button("Sin cupos", key=f"dis_{tut['id']}", disabled=True, use_container_width=True)
    else:
        lottie = load_lottie("https://assets10.lottiefiles.com/packages/lf20_fp1bpeuw.json")
        col = st.columns([1,2,1])[1]
        with col:
            if lottie:
                st_lottie(lottie, height=200)
            st.markdown('<p style="text-align:center; color:#64748b;">No hay tutorías disponibles por el momento.</p>', unsafe_allow_html=True)

with tab_historial:
    inscripciones = get_mis_inscripciones(st.session_state.usuario_id)

    c1, c2, _ = st.columns([1, 1, 2])
    with c1:
        st.metric("Total inscripciones", len(inscripciones))
    with c2:
        confirmadas = sum(1 for i in inscripciones if i["Estado"] == "Confirmada")
        st.metric("Confirmadas", confirmadas)
    style_metric_cards(border_left_color="#6366f1", background_color="rgba(0,0,0,0)")

    st.markdown('<hr class="divider-line">', unsafe_allow_html=True)

    if inscripciones:
        df = pd.DataFrame(inscripciones)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Estado": st.column_config.TextColumn("Estado"),
                "Fecha": st.column_config.TextColumn("Fecha programada"),
            }
        )
    else:
        st.info("Aún no te has inscrito a ninguna sesión.")
