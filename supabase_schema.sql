-- ==========================================
-- Esquema de Base de Datos para Supabase
-- Sistema de Tutorías
-- ==========================================

-- 1. Tabla de Roles (Estudiante, Docente, Administrador)
CREATE TABLE public.roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Insertar roles por defecto
INSERT INTO public.roles (nombre, descripcion) VALUES
('Estudiante', 'Usuario que puede inscribirse y ver tutorías.'),
('Docente', 'Usuario que crea tutorías y sube materiales.'),
('Administrador', 'Usuario con control total del sistema.');

-- 2. Tabla de Usuarios
-- En Supabase es buena práctica que auth_id referencie a auth.users,
-- pero aquí definimos una tabla pública para manejar la información extra.
CREATE TABLE public.usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_id UUID UNIQUE, -- Referencia opcional a la tabla auth.users de Supabase
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(255) NOT NULL,
    rol_id INTEGER REFERENCES public.roles(id) ON DELETE SET NULL,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Tabla de Tutorías
CREATE TABLE public.tutorias (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    docente_id UUID NOT NULL REFERENCES public.usuarios(id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    cupo_maximo INTEGER NOT NULL CHECK (cupo_maximo > 0),
    estado VARCHAR(50) DEFAULT 'Programada', -- 'Programada', 'En curso', 'Finalizada', 'Cancelada'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Tabla de Inscripciones
CREATE TABLE public.inscripciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tutoria_id UUID NOT NULL REFERENCES public.tutorias(id) ON DELETE CASCADE,
    estudiante_id UUID NOT NULL REFERENCES public.usuarios(id) ON DELETE CASCADE,
    fecha_inscripcion TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    estado VARCHAR(50) DEFAULT 'Confirmada', -- 'Confirmada', 'Cancelada', 'Asistió'
    UNIQUE(tutoria_id, estudiante_id) -- Un estudiante solo debe inscribirse una vez por tutoría
);

-- 5. Tabla de Materiales
CREATE TABLE public.materiales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tutoria_id UUID NOT NULL REFERENCES public.tutorias(id) ON DELETE CASCADE,
    nombre_archivo VARCHAR(255) NOT NULL,
    url_archivo TEXT NOT NULL, -- Ruta o URL del archivo subido en Supabase Storage
    subido_por UUID NOT NULL REFERENCES public.usuarios(id) ON DELETE SET NULL,
    fecha_subida TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ==========================================
-- Configuración de Seguridad (Opcional - RLS)
-- ==========================================
-- Estas directivas son muy importantes en Supabase para asegurar que los
-- datos no sean modificables desde la API sin autorización adecuada.
ALTER TABLE public.roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tutorias ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inscripciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.materiales ENABLE ROW LEVEL SECURITY;

-- Políticas de lectura básicas para que los datos puedan ser visualizados por usuarios conectados
CREATE POLICY "Lectura publica de roles" ON public.roles FOR SELECT USING (true);
CREATE POLICY "Lectura publica de tutorias" ON public.tutorias FOR SELECT USING (true);
CREATE POLICY "Lectura publica de usuarios activos" ON public.usuarios FOR SELECT USING (activo = true);
CREATE POLICY "Lectura publica de inscripciones" ON public.inscripciones FOR SELECT USING (true);
CREATE POLICY "Lectura publica de materiales" ON public.materiales FOR SELECT USING (true);

-- ==========================================
-- Índices para Rendimiento
-- ==========================================
CREATE INDEX idx_tutorias_docente ON public.tutorias(docente_id);
CREATE INDEX idx_inscripciones_estudiante ON public.inscripciones(estudiante_id);
