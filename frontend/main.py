import streamlit as st
import time
import requests
from streamlit_lottie import st_lottie
from db import get_session, Usuario
from streamlit_extras.metric_cards import style_metric_cards
from sqlalchemy.orm import joinedload

st.set_page_config(
    page_title="TUToreS — Plataforma Académica",
    page_icon="assets/icon.png" if False else "📘",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_css():
    with open("frontend/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    # Forzar sidebar siempre abierta vía JS
    st.markdown("""
    <script>
    const observer = new MutationObserver(() => {
        const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
        if (sidebar && sidebar.getAttribute('aria-expanded') === 'false') {
            const btn = window.parent.document.querySelector('[data-testid="collapsedControl"]');
            if (btn) btn.click();
        }
    });
    observer.observe(window.parent.document.body, { attributes: true, subtree: true });
    </script>
    """, unsafe_allow_html=True)
load_css()
style_metric_cards(border_left_color="#059669", background_color="#ffffff")

def load_lottie(url):
    try:
        r = requests.get(url, timeout=4)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

# Session state
for key, default in [("autenticado", False), ("rol", None), ("usuario_id", None), ("usuario_nombre", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

def get_user_by_email(email):
    session = get_session()
    if not session:
        return None
    try:
        user = session.query(Usuario).options(
            joinedload(Usuario.rol)
        ).filter(Usuario.email == email, Usuario.activo == True).first()
        if user:
            return {
                "id": str(user.id),
                "nombre": user.nombre_completo,
                "email": user.email,
                "password": user.password,
                "rol": user.rol.nombre if user.rol else None
            }
    except Exception as e:
        st.error(f"Error de conexión: {e}")
    finally:
        session.close()
    return None

# ─────────────────────────────────────────────────────────────
# LOGIN PAGE  —  Split-panel profesional
# ─────────────────────────────────────────────────────────────
def login():
    # Inyectar CSS extra para el panel izquierdo decorativo
    st.markdown("""
    <style>
    .login-brand {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 3.5rem;
        font-weight: 700;
        letter-spacing: -1px;
        color: #059669;
        line-height: 1.1;
        margin-bottom: 0.5rem;
    }
    .login-tagline {
        color: #64748b;
        font-size: 1.1rem;
        font-weight: 400;
        margin-bottom: 2rem;
    }
    .feature-point {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 6px 0;
        font-size: 0.9rem;
        color: #475569;
    }
    .feature-dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        background: #10b981;
        flex-shrink: 0;
    }
    .badge-version {
        display: inline-block;
        background: #d1fae5;
        color: #065f46;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        margin-bottom: 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    left, spacer, right = st.columns([2, 0.3, 2])

    # ── Panel izquierdo — Marca e info ──
    with left:
        st.markdown("<div style='padding: 4vh 2vw;'>", unsafe_allow_html=True)
        st.markdown('<span class="badge-version">CONVENIO UTS · 2026</span>', unsafe_allow_html=True)
        st.markdown('<div class="login-brand">TUToreS</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-tagline">Plataforma institucional de apoyo académico UTS.</div>', unsafe_allow_html=True)

        st.markdown('<hr class="divider-line">', unsafe_allow_html=True)

        features = [
            "Gestión de tutorías académicas",
            "Inscripción rápida de estudiantes",
            "Seguimiento docente institucional",
            "Reportes y métricas de gestión",
        ]
        for f in features:
            st.markdown(f'<div class="feature-point"><div class="feature-dot"></div>{f}</div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Panel derecho — Formulario de acceso ──
    with right:
        st.markdown("<div style='padding: 6vh 1vw;'>", unsafe_allow_html=True)

        st.markdown("### Inicio de Sesión", unsafe_allow_html=True)
        st.markdown('<p style="color:#64748b; font-size:0.9rem; margin-bottom:1.8rem;">Ingresa tus credenciales UTS para continuar.</p>', unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Correo electrónico", placeholder="usuario@uts.edu.co")
            password = st.text_input("Contraseña", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Entrar a la plataforma", use_container_width=True, type="primary")

            if submit:
                if not email or not password:
                    st.warning("Completa todos los campos.")
                    return
                with st.spinner("Autenticando..."):
                    user = get_user_by_email(email)
                    time.sleep(0.5)

                if user and user.get("password") == password:
                    st.session_state.autenticado = True
                    st.session_state.rol = user["rol"]
                    st.session_state.usuario_id = user["id"]
                    st.session_state.usuario_nombre = user["nombre"]
                    st.success(f"Bienvenido al portal institucional.")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Acceso denegado. Verifica tus credenciales.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("¿Problemas para acceder? Contacta al administrador de tu institución.")
        st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# SIDEBAR  —  Post-login
# ─────────────────────────────────────────────────────────────
def sidebar_menu():
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 8px 0 20px;">
            <div style="font-family:'Space Grotesk',sans-serif; font-size:1.35rem; font-weight:700; color:#059669; letter-spacing:-0.5px;">TUToreS</div>
            <div style="font-size:0.72rem; color:#64748b; text-transform:uppercase; letter-spacing:0.09em; font-weight:600;">Plataforma Académica UTS</div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        rol_color = {"Estudiante": "#059669", "Docente": "#2563eb", "Administrador": "#dc2626"}.get(st.session_state.rol, "#64748b")
        st.markdown(f"""
        <div style="background: #f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:14px;">
            <div style="font-size:0.75rem; color:#64748b; margin-bottom:4px;">Sesión activa</div>
            <div style="font-size:0.95rem; font-weight:600; color:#1e293b;">{st.session_state.usuario_nombre}</div>
            <div style="margin-top: 6px;">
                <span style="background:#d1fae5; color:{rol_color}; border-radius:4px; padding:2px 8px; font-size:0.72rem; font-weight:600;">{st.session_state.rol}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">Navegación</div>', unsafe_allow_html=True)

        nav_items = {
            "Estudiante": ["Inicio", "Explorar Tutorías", "Mi Historial"],
            "Docente": ["Inicio", "Mis Tutorías", "Crear Sesión"],
            "Administrador": ["Inicio", "Dashboard", "Usuarios", "Crear Usuario"],
        }.get(st.session_state.rol, [])
        for item in nav_items:
            st.markdown(f'<div style="padding:6px 4px; font-size:0.87rem; color:#475569; font-weight:500;">{item}</div>', unsafe_allow_html=True)

        st.divider()
        if st.button("Cerrar sesión", use_container_width=True, type="secondary"):
            for k in ["autenticado", "rol", "usuario_id", "usuario_nombre"]:
                st.session_state[k] = None if k != "autenticado" else False
            st.rerun()


# ─────────────────────────────────────────────────────────────
# ROUTING
# ─────────────────────────────────────────────────────────────
if not st.session_state.autenticado:
    login()
else:
    sidebar_menu()

    st.markdown(f"""
    <div style="animation: fadeUp 0.5s ease;">
        <div style="font-size:0.72rem; color:#059669; font-weight:600; letter-spacing:0.09em; text-transform:uppercase; margin-bottom:4px;">Portal Académico</div>
        <div class="page-title">Hola, {st.session_state.usuario_nombre.split(' ')[0]}.</div>
        <div class="page-subtitle">Panel principal institucional.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="divider-line">', unsafe_allow_html=True)

    lottie_main = load_lottie("https://lottie.host/8cdfed70-e67f-4424-bff6-74db624f92d4/vK7B1g0x5Q.json")
    if lottie_main:
        col = st.columns([1,2,1])[1]
        with col:
            st_lottie(lottie_main, height=260, key="main_lottie")
