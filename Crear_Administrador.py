"""Crea el primer administrador de la aplicación.

Ejecutar una sola vez después de configurar .streamlit/secrets.toml:
    python Crear_Administrador.py
"""
from getpass import getpass
import streamlit as st
from supabase import create_client


def main():
    url = st.secrets["SUPABASE_URL"]
    service_key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
    admin = create_client(url, service_key)

    print("Crear administrador de Control de pagos personales")
    name = input("Nombre completo: ").strip()
    email = input("Correo electrónico: ").strip().lower()
    password = getpass("Contraseña temporal (mínimo 8 caracteres): ")
    if not name or "@" not in email or len(password) < 8:
        raise SystemExit("Verifica el nombre, correo y una contraseña de mínimo 8 caracteres.")

    created = admin.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {"full_name": name},
    })
    admin.table("profiles").insert({
        "id": created.user.id,
        "full_name": name,
        "role": "administrator",
    }).execute()
    print(f"Administrador creado: {email}")


if __name__ == "__main__":
    main()
