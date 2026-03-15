# 📘 TUToreS — Plataforma de Gestión Académica

TUToreS es una solución moderna y profesional diseñada para conectar a estudiantes y docentes, facilitando la programación, inscripción y seguimiento de tutorías académicas.

## ✨ Características Principales

- **Diseño SaaS Premium**: Interfaz oscura inspirada en estándares modernos (Glassmorphism, Inter & Space Grotesk fonts).
- **Seguridad Robusta**: Sistema de autenticación con contraseñas y roles (Estudiante, Docente, Administrador).
- **Dashboard de Analytics**: Gráficos dinámicos para administradores sobre la ocupación y uso de la plataforma.
- **Gestión en Tiempo Real**: Sincronización inmediata con **Supabase (PostgreSQL)**.

---

## 🛠️ Requisitos e Instalación

### 1. Clonar y preparar el entorno
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
.\venv\Scripts\activate

# Instalar dependencias
pip install -r frontend/requirements.txt
```

### 2. Configurar Credenciales
Este proyecto utiliza `streamlit secrets` para la conexión a la base de datos.
1. Ve a la carpeta `frontend/.streamlit/`.
2. Verás un archivo llamado `secrets.toml.example`.
3. Haz una copia del archivo y llámala simplemente `secrets.toml`.
4. Abre `secrets.toml` y pega tu URL de conexión de Supabase (Connection Pooling):
   ```toml
   [database]
   url = "postgresql://postgres.ID:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres"
   ```

### 3. Ejecutar la Aplicación
```bash
streamlit run frontend/main.py
```

---

## 👥 Colaboración (Git)

Si vas a subir cambios:
1. Asegúrate de que tu `secrets.toml` **NUNCA** se suba (está protegido por `.gitignore`).
2. Sigue el flujo estándar:
   ```bash
   git add .
   git commit -m "Descripción clara del cambio"
   git push origin main
   ```

---
*Desarrollado para la Hackathon UTS — 2026*
