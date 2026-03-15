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
style_metric_cards(border_left_color="#6366f1", background_color="rgba(0,0,0,0)")

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
        font-size: 3rem;
        font-weight: 700;
        letter-spacing: -1px;
        background: linear-gradient(135deg, #818cf8 0%, #6366f1 60%, #4f46e5 100%);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
        margin-bottom: 0.5rem;
    }
    .login-tagline {
        color: #475569;
        font-size: 1rem;
        font-weight: 400;
        margin-bottom: 2rem;
    }
    .feature-point {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 6px 0;
        font-size: 0.88rem;
        color: #94a3b8;
    }
    .feature-dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: #6366f1;
        flex-shrink: 0;
    }
    .badge-version {
        display: inline-block;
        background: rgba(99,102,241,0.15);
        color: #818cf8;
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.72rem;
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
        st.markdown('<span class="badge-version">v2.0 · 2026</span>', unsafe_allow_html=True)
        st.markdown('<div class="login-brand">TUToreS</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-tagline">La plataforma académica que conecta estudiantes y docentes.</div>', unsafe_allow_html=True)

        st.markdown('<hr class="divider-line">', unsafe_allow_html=True)

        features = [
            "Gestión centralizada de tutorías académicas",
            "Panel de estudiantes con inscripción en tiempo real",
            "Herramientas avanzadas para docentes",
            "Analytics y reportes para administradores",
        ]
        for f in features:
            st.markdown(f'<div class="feature-point"><div class="feature-dot"></div>{f}</div>', unsafe_allow_html=True)

        # Lottie decorativa abajo
        lottie = load_lottie("https://lottie.host/1bdedc71-cb8e-4a6c-9dd6-9f170afc07ba/Y5J09pPjS4.json")
        if lottie:
            st_lottie(lottie, height=180, key="login_lottie")

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Panel derecho — Formulario de acceso ──
    with right:
        st.markdown("<div style='padding: 6vh 1vw;'>", unsafe_allow_html=True)

        st.markdown("### Acceso a la plataforma", unsafe_allow_html=True)
        st.markdown('<p style="color:#64748b; font-size:0.88rem; margin-bottom:1.8rem;">Ingresa tus credenciales institucionales para continuar.</p>', unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Correo institucional", placeholder="usuario@institucion.edu.co")
            password = st.text_input("Contraseña", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Iniciar sesión", use_container_width=True, type="primary")

            if submit:
                if not email or not password:
                    st.warning("Completa todos los campos para continuar.")
                    return
                with st.spinner("Verificando credenciales..."):
                    user = get_user_by_email(email)
                    time.sleep(0.4)

                if user and user.get("password") == password:
                    st.session_state.autenticado = True
                    st.session_state.rol = user["rol"]
                    st.session_state.usuario_id = user["id"]
                    st.session_state.usuario_nombre = user["nombre"]
                    st.success(f"Bienvenido, {user['nombre'].split(' ')[0]}.")
                    time.sleep(0.4)
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Verifica e intenta de nuevo.")

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
            <div style="font-family:'Space Grotesk',sans-serif; font-size:1.35rem; font-weight:700; color:#f1f5f9; letter-spacing:-0.5px;">TUToreS</div>
            <div style="font-size:0.72rem; color:#64748b; text-transform:uppercase; letter-spacing:0.09em; font-weight:600;">Plataforma Académica</div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        rol_color = {"Estudiante": "#34d399", "Docente": "#60a5fa", "Administrador": "#f472b6"}.get(st.session_state.rol, "#94a3b8")
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07); border-radius:10px; padding:14px;">
            <div style="font-size:0.75rem; color:#64748b; margin-bottom:4px;">Sesión activa</div>
            <div style="font-size:0.95rem; font-weight:600; color:#f1f5f9;">{st.session_state.usuario_nombre}</div>
            <div style="margin-top: 6px;">
                <span style="background:rgba(255,255,255,0.06); color:{rol_color}; border-radius:4px; padding:2px 8px; font-size:0.72rem; font-weight:600;">{st.session_state.rol}</span>
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
            st.markdown(f'<div style="padding:6px 4px; font-size:0.87rem; color:#94a3b8;">{item}</div>', unsafe_allow_html=True)

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
        <div style="font-size:0.72rem; color:#6366f1; font-weight:600; letter-spacing:0.09em; text-transform:uppercase; margin-bottom:4px;">Panel Principal</div>
        <div class="page-title">Hola, {st.session_state.usuario_nombre.split(' ')[0]}.</div>
        <div class="page-subtitle">Accede a tu módulo desde el menú lateral para comenzar.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="divider-line">', unsafe_allow_html=True)

    lottie_main = load_lottie("https://lottie.host/8cdfed70-e67f-4424-bff6-74db624f92d4/vK7B1g0x5Q.json")
    if lottie_main:
        col = st.columns([1,2,1])[1]
        with col:
            st_lottie(lottie_main, height=260, key="main_lottie")
