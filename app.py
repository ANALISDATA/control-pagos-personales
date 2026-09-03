import io
import hmac
from datetime import date

import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Control de pagos", page_icon="💳", layout="centered")


def apply_style():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        #MainMenu, footer { visibility: hidden; }
        .stApp {
            background: radial-gradient(circle at 15% 0%, #241c40 0%, #14101f 45%, #0f0c1a 100%);
        }
        .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 700px; }

        h1, h2, h3, h4 { color: #f5f3ff; letter-spacing: -0.01em; }
        p, span, label, [data-testid="stMarkdownContainer"] { color: #ece9f7; }
        [data-testid="stCaptionContainer"] { color: #a79fc9; }
        hr { margin: 1.1rem 0; border-color: rgba(255,255,255,0.08); }

        div.stButton > button, div[data-testid="stFormSubmitButton"] > button,
        div.stDownloadButton > button {
            border-radius: 12px;
            min-height: 3rem;
            font-weight: 600;
            font-size: 1rem;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            color: #f5f3ff;
            transition: transform 0.05s ease-in-out;
        }
        div.stButton > button:active, div[data-testid="stFormSubmitButton"] > button:active {
            transform: scale(0.98);
        }
        div.stButton > button[kind="primary"], div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
            background: linear-gradient(135deg, #8b5cf6, #4f46e5);
            border: none;
            box-shadow: 0 6px 16px rgba(139, 92, 246, 0.35);
        }
        input, textarea, select { font-size: 1rem !important; color: #f5f3ff !important; }
        input::placeholder, textarea::placeholder { color: rgba(245,243,255,0.4) !important; }
        div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="base-input"],
        div[data-testid="stNumberInput"] > div, div[data-testid="stDateInput"] > div {
            background: rgba(255,255,255,0.10) !important;
            border: 1px solid rgba(255,255,255,0.18) !important;
            border-radius: 10px !important;
        }
        div[data-testid="stNumberInput"] button, div[data-testid="stDateInput"] svg { color: #f5f3ff !important; }
        [data-baseweb="select"] span, [data-baseweb="select"] div { color: #f5f3ff !important; }

        [data-testid="stMetric"] {
            background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 55%, #4338ca 100%);
            padding: 1.3rem 1.4rem;
            border-radius: 20px;
            box-shadow: 0 10px 24px rgba(76, 29, 149, 0.35);
        }
        [data-testid="stMetricLabel"] { color: #e4defc !important; text-transform: uppercase; font-size: 0.72rem !important; letter-spacing: 0.06em; }
        [data-testid="stMetricValue"], [data-testid="stMetricDelta"] { color: #ffffff !important; }
        [data-testid="stMetricValue"] { font-size: 1.9rem; font-weight: 800; }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,0.08) !important;
            box-shadow: 0 8px 20px rgba(0,0,0,0.25);
            background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
        }

        .status-pill {
            display: inline-block;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 600;
            margin: 0.15rem 0.25rem 0.15rem 0;
        }
        .pill-green { background: rgba(52, 211, 153, 0.15); color: #6ee7b7; }
        .pill-amber { background: rgba(251, 191, 36, 0.15); color: #fcd34d; }
        .pill-gray { background: rgba(255,255,255,0.08); color: #cbd2e1; }

        .avatar {
            display: inline-flex; align-items: center; justify-content: center;
            width: 2.6rem; height: 2.6rem; border-radius: 999px;
            background: linear-gradient(135deg, #a78bfa, #6366f1);
            color: #fff; font-weight: 700; font-size: 1.05rem;
            flex-shrink: 0;
        }
        .hero-icon {
            width: 4rem; height: 4rem; margin: 1rem auto 0.6rem auto; border-radius: 999px;
            display: flex; align-items: center; justify-content: center; font-size: 1.9rem;
            background: linear-gradient(135deg, #a78bfa, #4f46e5);
            box-shadow: 0 8px 22px rgba(99, 102, 241, 0.4);
        }

        .cc-row { display: flex; justify-content: space-between; align-items: flex-start; z-index: 1; position: relative; }
        .cc-brand { font-weight: 800; font-size: 1.05rem; letter-spacing: 0.02em; color: #3b2b0a; }
        .cc-sub { font-size: 0.62rem; letter-spacing: 0.14em; opacity: 0.75; margin-top: 0.1rem; color: #3b2b0a; }
        .cc-chip {
            width: 2.3rem; height: 1.7rem; border-radius: 5px; z-index: 1; position: relative;
            background: linear-gradient(135deg, #fff3cf, #b8860b);
            border: 1px solid rgba(0,0,0,0.15);
            margin: 0.9rem 0 0.7rem 0;
        }
        .cc-number { font-size: 1.05rem; letter-spacing: 0.14em; font-weight: 600; z-index: 1; position: relative; color: #3b2b0a; }
        .cc-foot { display: flex; justify-content: space-between; font-size: 0.6rem; letter-spacing: 0.08em; opacity: 0.85; z-index: 1; position: relative; color: #3b2b0a; margin-top: 0.6rem; }

        div.st-key-login_card > div[data-testid="stVerticalBlockBorderWrapper"] {
            background: linear-gradient(135deg, #f7e7b0 0%, #e0bd6e 28%, #c79a3e 52%, #9c7423 76%, #6b4f16 100%) !important;
            border: none !important;
            box-shadow: 0 18px 38px rgba(0,0,0,0.5), inset 0 1px 1px rgba(255,255,255,0.5) !important;
            border-radius: 20px !important;
        }
        .st-key-login_card label p, .st-key-login_card p { color: #3b2b0a !important; font-weight: 600; }
        .st-key-login_card div[data-baseweb="input"], .st-key-login_card div[data-baseweb="base-input"] {
            background: rgba(255,255,255,0.4) !important;
            border: 1px solid rgba(59,43,10,0.25) !important;
        }
        .st-key-login_card input { color: #2b1e08 !important; caret-color: #2b1e08; }
        .st-key-login_card div[data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(135deg, #241c40, #0f0c1a) !important;
            color: #f5f3ff !important;
            border: none !important;
            box-shadow: 0 6px 16px rgba(0,0,0,0.4) !important;
        }
        .st-key-login_card [data-testid="stForm"] { border: none !important; background: transparent !important; padding-top: 0.4rem; }

        .stTabs [data-baseweb="tab-list"] { gap: 0.4rem; background: rgba(255,255,255,0.04); padding: 0.3rem; border-radius: 14px; }
        .stTabs [data-baseweb="tab"] { border-radius: 10px; font-weight: 600; color: #b9b2d9; }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #8b5cf6, #4f46e5) !important;
            color: #ffffff !important;
        }

        @media (max-width: 640px) {
            .block-container { padding-left: 1rem; padding-right: 1rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_badge(text):
    tone = {
        "Contabilizado": "pill-green", "Reembolsado": "pill-green",
        "Pendiente de contabilizar": "pill-amber", "Pendiente de reembolsar": "pill-amber",
        "No aplica": "pill-gray",
    }.get(text, "pill-gray")
    return f'<span class="status-pill {tone}">{text}</span>'


def avatar(name):
    initial = (name or "?").strip()[:1].upper()
    return f'<span class="avatar">{initial}</span>'


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
    with st.container(border=True, key="login_card"):
        st.markdown(
            """
            <div class="cc-row">
                <div>
                    <div class="cc-brand">ISTHO S.A.S.</div>
                    <div class="cc-sub">FINANCIERA</div>
                </div>
                <div style="font-size:1.4rem; z-index:1;">💳</div>
            </div>
            <div class="cc-chip"></div>
            <div class="cc-number">•••• •••• •••• 0000</div>
            <div class="cc-foot" style="margin-bottom:0.6rem;">
                <span>CONTROL DE PAGOS</span>
                <span>PERSONALES</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login"):
            email = st.text_input("Correo electrónico")
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Ingresar", type="primary", use_container_width=True)
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
    st.markdown("<div class='hero-icon'>🔐</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; margin-top:0;'>Crear administrador inicial</h2>", unsafe_allow_html=True)
    st.info("Este paso aparece una sola vez. Después, el acceso se realiza desde la pantalla de inicio de sesión.")
    with st.container(border=True):
        with st.form("initial_setup"):
            name = st.text_input("Nombre completo")
            email = st.text_input("Correo electrónico")
            password = st.text_input("Contraseña", type="password", help="Mínimo 8 caracteres.")
            setup_code = st.text_input("Código de configuración", type="password")
            submitted = st.form_submit_button("Crear administrador", type="primary", use_container_width=True)
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
        submitted = st.form_submit_button("Actualizar pago" if editing else "Guardar pago", type="primary", use_container_width=True)
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
    c1, c2 = st.columns(2)
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
    table = display[columns].rename(columns={"payment_date": "Fecha", "beneficiary": "Beneficiario", "description": "Concepto", "category": "Categoría", "amount": "Valor", "accounting_status": "Estado contable", "reimbursement_status": "Reembolso"})

    def tint(value):
        colors = {
            "Contabilizado": "background-color: rgba(52,211,153,0.18); color: #6ee7b7;",
            "Reembolsado": "background-color: rgba(52,211,153,0.18); color: #6ee7b7;",
            "Pendiente de contabilizar": "background-color: rgba(251,191,36,0.18); color: #fcd34d;",
            "Pendiente de reembolsar": "background-color: rgba(251,191,36,0.18); color: #fcd34d;",
            "No aplica": "background-color: rgba(255,255,255,0.08); color: #cbd2e1;",
        }
        return colors.get(value, "")

    styled = table.style.map(tint, subset=["Estado contable", "Reembolso"]).format({"Valor": currency})
    st.dataframe(styled, hide_index=True, use_container_width=True)
    st.download_button("⬇️ Descargar Excel actualizado", data=to_excel(rows), file_name=f"pagos-personales-{start_date}-a-{end_date}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)


def users_page():
    st.subheader("Usuario de consulta y descarga")
    st.caption("Este usuario podrá entrar solo a Reportes y descargar el Excel. No podrá modificar pagos.")
    with st.form("new_exporter"):
        name = st.text_input("Nombre completo")
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña temporal", type="password", help="Mínimo 8 caracteres.")
        submitted = st.form_submit_button("Crear usuario de consulta", type="primary", use_container_width=True)
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
    st.divider()
    users = service_client().table("profiles").select("full_name,role,created_at").order("created_at", desc=True).execute().data or []
    st.dataframe(pd.DataFrame(users).rename(columns={"full_name": "Nombre", "role": "Rol", "created_at": "Creado"}), hide_index=True, use_container_width=True)


def administrator_page():
    st.subheader("Editar pago" if "editing" in st.session_state else "Registrar pago")
    payment_form(st.session_state.get("editing"))
    if "editing" in st.session_state and st.button("Cancelar edición", use_container_width=True):
        del st.session_state.editing
        st.rerun()
    st.divider()
    st.subheader("Movimientos recientes")
    rows = payments_between(date.today().replace(day=1), date.today())
    if not rows:
        st.info("Aún no hay movimientos este mes.")
        return
    for row in rows:
        with st.container(border=True):
            icon_col, info_col, amount_col = st.columns([0.6, 2.4, 1.2])
            icon_col.markdown(avatar(row["beneficiary"]), unsafe_allow_html=True)
            info_col.markdown(
                f"<div style='font-weight:700;'>{row['beneficiary']}</div>"
                f"<div style='color:#a79fc9; font-size:0.8rem;'>{row['payment_date']} · {row['category']}</div>",
                unsafe_allow_html=True,
            )
            amount_col.markdown(f"<div style='text-align:right; font-size:1.2rem; font-weight:700;'>{currency(row['amount'])}</div>", unsafe_allow_html=True)
            st.caption(row["description"])
            st.markdown(status_badge(row["accounting_status"]) + status_badge(row["reimbursement_status"]), unsafe_allow_html=True)
            b1, b2 = st.columns(2)
            if b1.button("✏️ Editar", key=f"edit-{row['id']}", use_container_width=True):
                st.session_state.editing = row
                st.rerun()
            if b2.button("🗑️ Eliminar", key=f"delete-{row['id']}", use_container_width=True):
                service_client().table("payments").delete().eq("id", row["id"]).execute()
                st.rerun()


def app():
    apply_style()
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
    with st.container(border=True):
        header, logout = st.columns([4, 1])
        with header:
            st.markdown(
                f"""
                <div style="display:flex; align-items:center; gap:0.8rem;">
                    {avatar(profile['full_name'])}
                    <div>
                        <div style="font-weight:700; font-size:1.05rem; color:#f5f3ff;">{profile['full_name']}</div>
                        <div style="color:#a79fc9; font-size:0.82rem;">{'Administrador' if profile['role'] == 'administrator' else 'Consulta y descarga'}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with logout:
            if st.button("🚪", use_container_width=True, help="Cerrar sesión"):
                st.session_state.clear()
                st.rerun()
    st.write("")
    if profile["role"] == "administrator":
        tab_pagos, tab_reportes, tab_usuarios = st.tabs(["Pagos", "Reportes", "Usuarios"])
        with tab_pagos:
            administrator_page()
        with tab_reportes:
            reports_page()
        with tab_usuarios:
            users_page()
    else:
        reports_page()


app()
