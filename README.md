# Control de pagos personales — versión Streamlit

Esta versión sigue el patrón de la aplicación de Infratelco: Streamlit para la interfaz, Python para la lógica privada y Supabase para usuarios y datos. El usuario no necesita entrar al panel de Supabase durante la operación diaria.

## Perfiles

- **Administrador:** registra, edita, elimina y exporta pagos; también crea el usuario de consulta desde el módulo **Usuarios**.
- **Consulta y descarga:** solo puede abrir **Reportes** y descargar el Excel actualizado.

## Configuración inicial sin instalar programas

1. Ya ejecutaste `../supabase-schema.sql`; conserva esas tablas.
2. Copia `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml`.
3. En Supabase, abre **Project Settings → API** y copia:
   - Project URL.
   - `anon public key`.
   - `service_role key`.
4. Elige un `SETUP_CODE` largo y privado. No debe ser una contraseña reutilizada.
5. En Streamlit Cloud, pega estos cuatro valores en **Advanced settings → Secrets**. Nunca subas ese archivo ni las claves a GitHub.
6. Cuando abras la aplicación por primera vez, aparecerá **Crear administrador inicial**. Escribe el nombre, correo, contraseña y el mismo `SETUP_CODE`. La pantalla se desactiva automáticamente después de crear el primer administrador.
7. Ingresa como administrador y usa **Usuarios** para crear la cuenta de consulta y descarga.

## Publicación como Infratelco

1. Crea un repositorio privado en GitHub y sube el contenido de esta carpeta. El archivo `.gitignore` evita subir `secrets.toml`.
2. En Streamlit Community Cloud, crea una app desde ese repositorio y selecciona `app.py` como archivo principal.
3. En **App settings → Secrets**, pega el mismo contenido de `secrets.toml`.
4. Publica. A partir de ese momento, se usa la URL de Streamlit; el administrador crea el usuario exportador directamente desde la aplicación.

## Seguridad

La `service_role key` se usa exclusivamente en el servidor de Streamlit para crear usuarios y administrar datos. No debe estar en HTML, JavaScript, GitHub ni ser compartida por chat. La aplicación anterior en HTML queda como prototipo; para publicar utiliza esta carpeta `streamlit`. `Crear_Administrador.py` queda como alternativa técnica para instalación local, pero no es necesario para publicar en Streamlit Cloud.
