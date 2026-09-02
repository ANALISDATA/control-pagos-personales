import io
import hmac
from datetime import date

import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Control de pagos", page_icon="💳", layout="wide")


def configured():
    required = {"SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY", "SETUP_CODE"}
    return required.issubset(set(st.secrets.keys()))


def service_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_ROLE_KEY"])


def auth_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])


def get_profile(user_id):
    response = service_client().table("profiles").select("id,full_name,role").eq("id", user_id).single().execute()
    return response.data


def login_screen():
    left, center, right = st.columns([1, 1.25, 1])
    with center:
        st.title("Control de pagos personales")
        st.caption("Registro y conciliación de pagos realizados desde cuentas personales.")
        with st.form("login"):
            email = st.text_input("Correo electrónico")
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Ingresar", use_container_width=True)
        if submitted:
            try:
                session = auth_client().auth.sign_in_with_password({"email": email.strip(), "password": password})
                profile = get_profile(session.user.id)
                st.session_state.profile = profile
                st.rerun()
            except Exception:
                st.error("No fue posible iniciar sesión. Verifica el correo y la contraseña.")


def initial_setup_needed():
    response = service_client().table("profiles").select("id", count="exact").eq("role", "administrator").execute()
    return (response.count or 0) == 0


def initial_setup_screen():
    left, center, right = st.columns([1, 1.25, 1])
    with center:
        st.title("Crear administrador inicial")
        st.info("Este paso aparece una sola vez. Después, el acceso se realiza desde la pantalla de inicio de sesión.")
        with st.form("initial_setup"):
            name = st.text_input("Nombre completo")
            email = st.text_input("Correo electrónico")
            password = st.text_input("Contraseña", type="password", help="Mínimo 8 caracteres.")
            setup_code = st.text_input("Código de configuración", type="password")
            submitted = st.form_submit_button("Crear administrador", use_container_width=True)
        if submitted:
            if not hmac.compare_digest(setup_code, st.secrets["SETUP_CODE"]):
                st.error("El código de configuración no es correcto.")
                return
            if not name.strip() or "@" not in email or len(password) < 8:
                st.error("Completa nombre, correo válido y una contraseña de mínimo 8 caracteres.")
                return
            try:
                client = service_client()
                created = client.auth.admin.create_user({"email": email.strip().lower(), "password": password, "email_confirm": True, "user_metadata": {"full_name": name.strip()}})
                profile = {"id": created.user.id, "full_name": name.strip(), "role": "administrator"}
                client.table("profiles").insert(profile).execute()
                st.session_state.profile = profile
                st.success("Administrador creado correctamente.")
                st.rerun()
            except Exception as error:
                st.error(f"No fue posible crear el administrador: {error}")


def currency(value):
    return f"${float(value or 0):,.0f}".replace(",", ".")


def payments_between(start_date, end_date):
    response = (
        service_client().table("payments").select("*")
        .gte("payment_date", str(start_date)).lte("payment_date", str(end_date))
        .order("payment_date", desc=True).execute()
    )
    return response.data or []


def payment_form(editing=None):
    defaults = editing or {}
    with st.form("payment_form", clear_on_submit=editing is None):
        a, b, c = st.columns(3)
        payment_date = a.date_input("Fecha del pago", value=date.fromisoformat(defaults.get("payment_date", str(date.today()))))
        beneficiary = b.text_input("Beneficiario", value=defaults.get("beneficiary", ""))
        amount = c.number_input("Valor", min_value=0.0, step=1000.0, value=float(defaults.get("amount", 0)))
        category = a.text_input("Categoría", value=defaults.get("category", ""), placeholder="Ej. Transporte")
        payment_method = b.selectbox("Medio de pago", ["Cuenta personal", "Tarjeta personal", "Efectivo", "Otro"], index=["Cuenta personal", "Tarjeta personal", "Efectivo", "Otro"].index(defaults.get("payment_method", "Cuenta personal")))
        accounting_status = c.selectbox("Estado contable", ["Pendiente de contabilizar", "Contabilizado"], index=0 if defaults.get("accounting_status", "Pendiente de contabilizar") == "Pendiente de contabilizar" else 1)
        reimbursement_status = a.selectbox("Estado de reembolso", ["Pendiente de reembolsar", "Reembolsado", "No aplica"], index=["Pendiente de reembolsar", "Reembolsado", "No aplica"].index(defaults.get("reimbursement_status", "Pendiente de reembolsar")))
        description = st.text_input("Concepto", value=defaults.get("description", ""), placeholder="Descripción del gasto")
        comments = st.text_area("Comentarios", value=defaults.get("comments") or "", placeholder="Factura, referencia u observaciones")
        submitted = st.form_submit_button("Actualizar pago" if editing else "Guardar pago", use_container_width=True)
    if submitted:
        if not beneficiary.strip() or not category.strip() or not description.strip() or amount <= 0:
            st.error("Completa beneficiario, valor, categoría y concepto.")
            return
        payload = {"payment_date": str(payment_date), "beneficiary": beneficiary.strip(), "amount": amount,
                   "category": category.strip(), "payment_method": payment_method,
                   "accounting_status": accounting_status, "reimbursement_status": reimbursement_status,
                   "description": description.strip(), "comments": comments.strip() or None}
        client = service_client()
        if editing:
            client.table("payments").update(payload).eq("id", editing["id"]).execute()
            st.success("Pago actualizado.")
        else:
            client.table("payments").insert(payload).execute()
            st.success("Pago guardado.")


def to_excel(rows):
    fields = {"payment_date": "Fecha", "beneficiary": "Beneficiario", "description": "Concepto", "category": "Categoría", "payment_method": "Medio de pago", "amount": "Valor", "accounting_status": "Estado contable", "reimbursement_status": "Estado reembolso", "comments": "Comentarios"}
    dataframe = pd.DataFrame(rows).reindex(columns=fields.keys()).rename(columns=fields)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Pagos personales")
        sheet = writer.book["Pagos personales"]
        for column, width in {"A": 14, "B": 28, "C": 42, "D": 20, "E": 22, "F": 16, "G": 27, "H": 27, "I": 40}.items():
            sheet.column_dimensions[column].width = width
        for cell in sheet["F"][1:]:
            cell.number_format = '#,##0.00'
    return output.getvalue()


def reports_page():
    st.subheader("Reportes y descarga")
    c1, c2, _ = st.columns([1, 1, 3])
    start_date = c1.date_input("Desde", value=date.today().replace(day=1))
    end_date = c2.date_input("Hasta", value=date.today())
    if end_date < start_date:
        st.error("La fecha final debe ser igual o posterior a la inicial.")
        return
    rows = payments_between(start_date, end_date)
    total = sum(float(row["amount"]) for row in rows)
    st.metric("Total del período", currency(total), f"{len(rows)} movimiento(s)")
    display = pd.DataFrame(rows)
    if display.empty:
        st.info("No hay movimientos en este período.")
        return
    columns = ["payment_date", "beneficiary", "description", "category", "amount", "accounting_status", "reimbursement_status"]
    st.dataframe(display[columns].rename(columns={"payment_date": "Fecha", "beneficiary": "Beneficiario", "description": "Concepto", "category": "Categoría", "amount": "Valor", "accounting_status": "Estado contable", "reimbursement_status": "Reembolso"}), hide_index=True, use_container_width=True)
    st.download_button("Descargar Excel actualizado", data=to_excel(rows), file_name=f"pagos-personales-{start_date}-a-{end_date}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)


def users_page():
    st.subheader("Usuario de consulta y descarga")
    st.caption("Este usuario podrá entrar solo a Reportes y descargar el Excel. No podrá modificar pagos.")
    with st.form("new_exporter"):
        name = st.text_input("Nombre completo")
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña temporal", type="password", help="Mínimo 8 caracteres.")
        submitted = st.form_submit_button("Crear usuario de consulta")
    if submitted:
        if not name.strip() or "@" not in email or len(password) < 8:
            st.error("Completa nombre, correo válido y una contraseña de mínimo 8 caracteres.")
            return
        try:
            client = service_client()
            created = client.auth.admin.create_user({"email": email.strip().lower(), "password": password, "email_confirm": True, "user_metadata": {"full_name": name.strip()}})
            client.table("profiles").insert({"id": created.user.id, "full_name": name.strip(), "role": "exporter"}).execute()
            st.success("Usuario creado. Entrega su correo y contraseña por un canal seguro.")
        except Exception as error:
            st.error(f"No fue posible crear el usuario: {error}")
    users = service_client().table("profiles").select("full_name,role,created_at").order("created_at", desc=True).execute().data or []
    st.dataframe(pd.DataFrame(users).rename(columns={"full_name": "Nombre", "role": "Rol", "created_at": "Creado"}), hide_index=True, use_container_width=True)


def administrator_page():
    st.subheader("Registrar pago" if "editing" not in st.session_state else "Editar pago")
    payment_form(st.session_state.get("editing"))
    if "editing" in st.session_state and st.button("Cancelar edición"):
        del st.session_state.editing
        st.rerun()
    st.divider()
    st.subheader("Movimientos recientes")
    rows = payments_between(date.today().replace(day=1), date.today())
    if not rows:
        st.info("Aún no hay movimientos este mes.")
        return
    for row in rows:
        left, middle, right = st.columns([5, 2, 2])
        left.write(f"**{row['payment_date']} · {row['beneficiary']}**  \n{row['description']} · {row['category']}")
        middle.write(currency(row["amount"]))
        if right.button("Editar", key=f"edit-{row['id']}"):
            st.session_state.editing = row
            st.rerun()
        if right.button("Eliminar", key=f"delete-{row['id']}"):
            service_client().table("payments").delete().eq("id", row["id"]).execute()
            st.rerun()


def app():
    if not configured():
        st.error("Falta configurar .streamlit/secrets.toml. Revisa el README.")
        st.stop()
    if "profile" not in st.session_state and initial_setup_needed():
        initial_setup_screen()
        return
    if "profile" not in st.session_state:
        login_screen()
        return
    profile = st.session_state.profile
    with st.sidebar:
        st.title("💳 Pagos personales")
        st.write(profile["full_name"])
        st.caption("Administrador" if profile["role"] == "administrator" else "Consulta y descarga")
        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    if profile["role"] == "administrator":
        page = st.sidebar.radio("Módulo", ["Gestión de pagos", "Reportes", "Usuarios"])
        if page == "Gestión de pagos":
            administrator_page()
        elif page == "Reportes":
            reports_page()
        else:
            users_page()
    else:
        reports_page()


app()
