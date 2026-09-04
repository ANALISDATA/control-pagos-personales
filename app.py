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
        header[data-testid="stHeader"] { background: transparent; }
        .stApp {
            background:
                radial-gradient(ellipse 620px 460px at 50% 0%, rgba(56,189,248,0.14), transparent 62%),
                radial-gradient(circle at 20% 0%, #123246 0%, #0a2233 45%, #071620 100%);
        }
        .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 700px; }

        h1, h2, h3, h4 { color: #eaf6ff; letter-spacing: -0.01em; }
        p, span, label, [data-testid="stMarkdownContainer"] { color: #dcecf5; }
        [data-testid="stCaptionContainer"] { color: #8fb4c9; }
        hr { margin: 1.1rem 0; border-color: rgba(255,255,255,0.08); }

        div.stButton > button, div[data-testid="stFormSubmitButton"] > button,
        div.stDownloadButton > button {
            border-radius: 12px;
            min-height: 3rem;
            font-weight: 600;
            font-size: 1rem;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            color: #eaf6ff;
            transition: transform 0.05s ease-in-out;
        }
        div.stButton > button:active, div[data-testid="stFormSubmitButton"] > button:active {
            transform: scale(0.98);
        }
        div.stButton > button[kind="primary"], div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
            background: linear-gradient(135deg, #38bdf8, #0369a1);
            border: none;
            box-shadow: 0 6px 16px rgba(14, 165, 233, 0.35);
        }
        input, textarea, select { font-size: 1rem !important; color: #eaf6ff !important; }
        input::placeholder, textarea::placeholder { color: rgba(234,246,255,0.4) !important; }
        div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="base-input"],
        div[data-testid="stNumberInput"] > div, div[data-testid="stDateInput"] > div {
            background: rgba(255,255,255,0.10) !important;
            border: 1px solid rgba(255,255,255,0.18) !important;
            border-radius: 10px !important;
        }
        div[data-testid="stNumberInput"] button, div[data-testid="stDateInput"] svg { color: #eaf6ff !important; }
        [data-baseweb="select"] span, [data-baseweb="select"] div { color: #eaf6ff !important; }

        [data-testid="stMetric"] {
            background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 55%, #0369a1 100%);
            padding: 1.3rem 1.4rem;
            border-radius: 20px;
            box-shadow: 0 10px 24px rgba(3, 105, 161, 0.35);
        }
        [data-testid="stMetricLabel"] { color: #e0f4ff !important; text-transform: uppercase; font-size: 0.72rem !important; letter-spacing: 0.06em; }
        [data-testid="stMetricValue"], [data-testid="stMetricDelta"] { color: #ffffff !important; }
        [data-testid="stMetricValue"] { font-size: 1.9rem; font-weight: 800; }

        /* generic frosted-glass card look, scoped to containers that carry .glass-card-marker
           as their first, non-column child (see glass_marker()) */
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .glass-card-marker) {
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
            background: linear-gradient(135deg, #bae6fd, #38bdf8 55%, #0369a1);
            color: #04202f; font-weight: 700; font-size: 1.05rem;
            flex-shrink: 0;
        }

        /* --- login card (front + revealed form share this look) --- */
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-card-marker) {
            position: relative;
            overflow: hidden;
            border-radius: 20px;
            border: none !important;
            background:
                radial-gradient(ellipse 160% 70% at 22% -18%, rgba(255,255,255,0.55), transparent 55%),
                repeating-conic-gradient(from 0deg at 50% 45%, rgba(255,255,255,0.06) 0deg 4deg, transparent 4deg 8deg),
                linear-gradient(155deg, #eaf7ff 0%, #bfe8ff 14%, #7dd3fc 32%, #38bdf8 52%, #0ea5e9 72%, #0369a1 100%) !important;
            box-shadow:
                0 30px 60px rgba(2, 20, 32, 0.55),
                0 0 46px rgba(56, 189, 248, 0.25),
                inset 0 1px 1px rgba(255,255,255,0.65) !important;
            padding: 1.4rem 1.5rem 1.6rem !important;
            transition: box-shadow 0.3s ease, filter 0.3s ease;
        }
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-card-marker):hover {
            filter: brightness(1.08);
            box-shadow:
                0 34px 70px rgba(2, 20, 32, 0.6),
                0 0 70px rgba(56, 189, 248, 0.5),
                inset 0 1px 1px rgba(255,255,255,0.75) !important;
        }
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-card-marker)::after {
            content: "";
            position: absolute;
            top: -60%;
            left: -30%;
            width: 45%;
            height: 220%;
            background: linear-gradient(100deg, transparent, rgba(255,255,255,0.85), transparent);
            transform: translateX(-40%) rotate(12deg);
            pointer-events: none;
            animation: card-shine 3.2s ease-in-out infinite;
            z-index: 5;
        }
        @keyframes card-shine {
            0%   { transform: translateX(-40%) rotate(12deg); }
            38%  { transform: translateX(360%) rotate(12deg); }
            100% { transform: translateX(360%) rotate(12deg); }
        }
        @media (prefers-reduced-motion: reduce) {
            div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-card-marker)::after { animation: none; }
        }
        .cc-row { display: flex; justify-content: space-between; align-items: flex-start; }
        .logo-crop { width: 108px; height: 43px; overflow: hidden; }
        .logo-crop img { width: 108px; height: auto; display: block; }
        .tier-tag {
            font-size: 0.6rem; letter-spacing: 0.14em; font-weight: 800; color: #062a3f;
            border: 1px solid rgba(6,42,63,0.35); border-radius: 999px; padding: 0.25rem 0.6rem;
            background: rgba(255,255,255,0.18);
        }
        .chip-row { display: flex; align-items: center; gap: 0.6rem; margin: 1.1rem 0 1.3rem; }
        .cc-chip {
            width: 2.3rem; height: 1.7rem; border-radius: 5px;
            background: linear-gradient(135deg, #fff8e4, #d9a635 55%, #8a641f);
            border: 1px solid rgba(0,0,0,0.15);
            box-shadow: inset 0 1px 1px rgba(255,255,255,0.7);
            position: relative;
        }
        .cc-chip::before, .cc-chip::after { content: ""; position: absolute; background: rgba(0,0,0,0.18); }
        .cc-chip::before { top: 50%; left: 15%; right: 15%; height: 1px; }
        .cc-chip::after { left: 50%; top: 15%; bottom: 15%; width: 1px; }
        .contactless { color: #062a3f; opacity: 0.8; }
        .cc-number {
            font-family: 'Courier New', ui-monospace, monospace;
            font-size: 1.18rem; letter-spacing: 0.15em; font-weight: 700; color: #062a3f;
            font-variant-numeric: tabular-nums;
            text-shadow: 0 1px 0 rgba(255,255,255,0.6), 0 -1px 1px rgba(6,42,63,0.35);
        }
        .cc-meta-row { display: flex; justify-content: flex-end; margin-top: 0.55rem; }
        .meta-label { display: block; font-size: 0.52rem; letter-spacing: 0.1em; color: #062a3f; opacity: 0.65; }
        .meta-value {
            display: block; font-family: 'Courier New', ui-monospace, monospace;
            font-size: 0.85rem; font-weight: 700; color: #062a3f; letter-spacing: 0.06em;
        }
        .cc-bottom-row { display: flex; justify-content: space-between; align-items: flex-end; margin-top: 0.9rem; }
        .holder-name {
            display: block; font-size: 0.82rem; font-weight: 700; letter-spacing: 0.05em; color: #062a3f;
            text-shadow: 0 1px 0 rgba(255,255,255,0.6), 0 -1px 1px rgba(6,42,63,0.3);
            margin-top: 0.1rem;
        }
        .seal {
            width: 2.5rem; height: 2.5rem; border-radius: 999px;
            display: flex; align-items: center; justify-content: center;
            font-size: 0.62rem; font-weight: 800; color: #062a3f;
            background: radial-gradient(circle at 35% 30%, rgba(255,255,255,0.75), rgba(255,255,255,0.15) 60%, transparent 62%), rgba(255,255,255,0.22);
            border: 1px solid rgba(6,42,63,0.3);
            box-shadow: inset 0 1px 1px rgba(255,255,255,0.6);
        }
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-card-marker) label p,
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-card-marker) p {
            color: #062a3f !important; font-weight: 600;
        }
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-card-marker) div[data-baseweb="input"],
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-card-marker) div[data-baseweb="base-input"] {
            background: rgba(255,255,255,0.55) !important;
            border: 1px solid rgba(6,42,63,0.3) !important;
        }
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-card-marker) input {
            color: #04202f !important; caret-color: #04202f;
        }
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-card-marker) div[data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(135deg, #123246, #071620) !important;
            color: #eaf6ff !important; border: none !important;
            box-shadow: 0 6px 16px rgba(0,0,0,0.4) !important;
        }
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-card-marker) [data-testid="stForm"] {
            border: none !important; background: transparent !important;
        }
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-card-marker) div.stButton > button {
            background: rgba(6,42,63,0.12) !important;
            color: #062a3f !important;
            border: 1px solid rgba(6,42,63,0.3) !important;
        }

        .stTabs [data-baseweb="tab-list"] { gap: 0.4rem; background: rgba(255,255,255,0.04); padding: 0.3rem; border-radius: 14px; }
        .stTabs [data-baseweb="tab"] { border-radius: 10px; font-weight: 600; color: #8fb4c9; }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #38bdf8, #0369a1) !important;
            color: #ffffff !important;
        }

        @media (max-width: 640px) {
            .block-container { padding-left: 1rem; padding-right: 1rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


LOGO_DATA_URI = "data:image/png;base64,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"


def glass_marker():
    st.markdown('<span class="glass-card-marker" style="display:none"></span>', unsafe_allow_html=True)


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
    if "login_reveal" not in st.session_state:
        st.session_state.login_reveal = False

    submitted = False
    email = password = ""

    with st.container(border=True):
        st.markdown('<span class="cc-card-marker" style="display:none"></span>', unsafe_allow_html=True)

        if not st.session_state.login_reveal:
            st.markdown(
                f"""
                <div class="cc-row">
                    <div class="logo-crop"><img src="{LOGO_DATA_URI}" alt="ISTHO"></div>
                    <div class="tier-tag">FINANCIERA</div>
                </div>
                <div class="chip-row">
                    <div class="cc-chip"></div>
                    <svg class="contactless" width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                        <path d="M6 12a6 6 0 0 1 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        <path d="M4 12a8 8 0 0 1 8-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" opacity="0.7"/>
                        <path d="M2 12a10 10 0 0 1 10-10" stroke="currentColor" stroke-width="2" stroke-linecap="round" opacity="0.45"/>
                    </svg>
                </div>
                <div class="cc-number">•••• •••• •••• 0000</div>
                <div class="cc-meta-row">
                    <div>
                        <span class="meta-label">VALID THRU</span>
                        <span class="meta-value">12/29</span>
                    </div>
                </div>
                <div class="cc-bottom-row">
                    <div>
                        <span class="meta-label">TITULAR</span>
                        <span class="holder-name">BIBIANA SARMIENTO</span>
                    </div>
                    <div class="seal">IST</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")
            if st.button("Ingresar →", type="primary", use_container_width=True):
                st.session_state.login_reveal = True
                st.rerun()
        else:
            st.markdown(
                f"""
                <div class="cc-row">
                    <div class="logo-crop"><img src="{LOGO_DATA_URI}" alt="ISTHO"></div>
                    <div class="tier-tag">FINANCIERA</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")
            with st.form("login"):
                email = st.text_input("Correo electrónico")
                password = st.text_input("Contraseña", type="password")
                submitted = st.form_submit_button("Ingresar", type="primary", use_container_width=True)
            if st.button("← Volver", use_container_width=True):
                st.session_state.login_reveal = False
                st.rerun()

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
    st.markdown("<h2 style='text-align:center;'>🔐 Crear administrador inicial</h2>", unsafe_allow_html=True)
    st.info("Este paso aparece una sola vez. Después, el acceso se realiza desde la pantalla de inicio de sesión.")
    with st.container(border=True):
        glass_marker()
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
            glass_marker()
            icon_col, info_col, amount_col = st.columns([0.6, 2.4, 1.2])
            icon_col.markdown(avatar(row["beneficiary"]), unsafe_allow_html=True)
            info_col.markdown(
                f"<div style='font-weight:700;'>{row['beneficiary']}</div>"
                f"<div style='color:#8fb4c9; font-size:0.8rem;'>{row['payment_date']} · {row['category']}</div>",
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
        glass_marker()
        header, logout = st.columns([4, 1])
        with header:
            st.markdown(
                f"""
                <div style="display:flex; align-items:center; gap:0.8rem;">
                    {avatar(profile['full_name'])}
                    <div>
                        <div style="font-weight:700; font-size:1.05rem; color:#eaf6ff;">{profile['full_name']}</div>
                        <div style="color:#8fb4c9; font-size:0.82rem;">{'Administrador' if profile['role'] == 'administrator' else 'Consulta y descarga'}</div>
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
