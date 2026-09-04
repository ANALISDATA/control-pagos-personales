import io
import re
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
        div[data-testid="stTextInputRootElement"], div[data-testid="stTextAreaRootElement"],
        div[data-testid="stNumberInputContainer"],
        div[data-testid="stNumberInput"] > div, div[data-testid="stDateInput"] > div {
            background: rgba(255,255,255,0.10) !important;
            border: 1px solid rgba(255,255,255,0.18) !important;
            border-radius: 10px !important;
        }
        div[data-testid="stNumberInput"] button, div[data-testid="stDateInput"] svg { color: #eaf6ff !important; }
        div[data-testid="InputInstructions"] { display: none !important; }
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
                radial-gradient(ellipse 160% 70% at 22% -18%, rgba(255,255,255,0.5), transparent 55%),
                radial-gradient(rgba(255,255,255,0.16) 1.1px, transparent 1.6px),
                linear-gradient(155deg, #eaf7ff 0%, #bfe8ff 14%, #7dd3fc 32%, #38bdf8 52%, #0ea5e9 72%, #0369a1 100%) !important;
            background-size: auto, 15px 15px, auto;
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
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-front-active)::after {
            content: "";
            position: absolute;
            top: -60%;
            left: -30%;
            width: 45%;
            height: 220%;
            background: linear-gradient(100deg, transparent, rgba(255,255,255,0.7), transparent);
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
            div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-front-active)::after { animation: none; }
        }
        .cc-map-bg {
            position: absolute;
            right: -40px;
            bottom: -20px;
            width: 320px;
            height: 290px;
            background-repeat: no-repeat;
            background-position: center;
            background-size: contain;
            pointer-events: none;
            z-index: 0;
        }
        .cc-row { display: flex; justify-content: space-between; align-items: flex-start; position: relative; z-index: 1; }
        .logo-crop { width: 108px; height: 43px; overflow: hidden; }
        .logo-crop img { width: 108px; height: auto; display: block; }
        .tier-tag {
            font-size: 0.68rem; letter-spacing: 0.14em; font-weight: 900; color: #4a3200;
            border: none; border-radius: 999px; padding: 0.25rem 0.7rem;
            background: linear-gradient(135deg, #fef3c7, #fbbf24 55%, #b8860b);
            box-shadow: 0 2px 5px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.6);
        }
        .barcode-caption {
            text-align: center;
            font-size: 0.58rem;
            letter-spacing: 0.14em;
            color: #062a3f;
            opacity: 0.6;
            font-weight: 700;
            margin: -0.4rem 0 0.5rem 0;
        }
        .stripe-bar {
            height: 2.6rem;
            margin: -1.4rem -1.5rem 1.2rem -1.5rem;
            background: repeating-linear-gradient(180deg, #0b0f14, #0b0f14 2px, #14181d 2px, #14181d 4px);
            box-shadow: inset 0 -2px 4px rgba(0,0,0,0.4);
            position: relative;
            z-index: 1;
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
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-card-marker) div[data-baseweb="base-input"],
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-card-marker) div[data-testid="stTextInputRootElement"] {
            background: rgba(255,255,255,0.55) !important;
            border: 1px solid rgba(6,42,63,0.3) !important;
            box-shadow: none !important;
        }
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-card-marker) input {
            color: #04202f !important; caret-color: #04202f;
        }
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-card-marker) div[data-testid="stFormSubmitButton"] > button {
            background:
                linear-gradient(90deg, #ffffff 0%, transparent 6%, transparent 94%, #ffffff 100%),
                repeating-linear-gradient(90deg,
                    #0b0b0c 0px, #0b0b0c 3px, #ffffff 3px, #ffffff 5px,
                    #0b0b0c 5px, #0b0b0c 6px, #ffffff 6px, #ffffff 10px,
                    #0b0b0c 10px, #0b0b0c 13px, #ffffff 13px, #ffffff 14px
                ) !important;
            background-size: 100% 100%, 40px 100% !important;
            border: 1px solid rgba(0,0,0,0.2) !important;
            box-shadow: 0 6px 16px rgba(0,0,0,0.4), inset 0 0 0 1px rgba(255,255,255,0.4) !important;
            display: flex !important;
            align-items: center;
            justify-content: center;
        }
        div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .cc-card-marker) div[data-testid="stFormSubmitButton"] > button p {
            background: #ffffff !important;
            color: #0b0b0c !important;
            padding: 0.4rem 1.2rem;
            border-radius: 6px;
            font-weight: 900 !important;
            letter-spacing: 0.1em;
            box-shadow: 0 1px 5px rgba(0,0,0,0.3);
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


MAP_DATA_URI = "data:image/png;base64,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"


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
                <span class="cc-front-active" style="display:none"></span>
                <div class="cc-map-bg" style="background-image:url('{MAP_DATA_URI}');"></div>
                <div class="cc-row">
                    <div class="logo-crop"><img src="{LOGO_DATA_URI}" alt="ISTHO"></div>
                    <div class="tier-tag">GOLD</div>
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
                <div class="stripe-bar"></div>
                <div class="cc-row">
                    <div class="logo-crop"><img src="{LOGO_DATA_URI}" alt="ISTHO"></div>
                    <div class="tier-tag">GOLD</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")
            with st.form("login"):
                email = st.text_input("Correo electrónico")
                password = st.text_input("Contraseña", type="password")
                st.markdown('<div class="barcode-caption">ESCANEA O TOCA PARA INGRESAR</div>', unsafe_allow_html=True)
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


def _format_money(value):
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return ""
    return f"{n:,}".replace(",", ".")


def _parse_money(text):
    digits = re.sub(r"\D", "", text or "")
    return float(digits) if digits else 0.0


def _reformat_valor_input():
    st.session_state.valor_input = _format_money(_parse_money(st.session_state.get("valor_input", "")))


def payment_form(editing=None):
    defaults = editing or {}
    editing_id = defaults.get("id", "new")
    if st.session_state.get("_valor_editing_id") != editing_id:
        st.session_state._valor_editing_id = editing_id
        st.session_state.valor_input = _format_money(defaults.get("amount", 0)) if defaults.get("amount") else ""

    st.text_input(
        "Valor", key="valor_input", on_change=_reformat_valor_input,
        placeholder="0", help="Se formatea con puntos de miles al salir del campo.",
    )

    with st.form("payment_form", clear_on_submit=editing is None):
        a, b = st.columns(2)
        payment_date = a.date_input("Fecha del pago", value=date.fromisoformat(defaults.get("payment_date", str(date.today()))))
        beneficiary = b.text_input("Beneficiario", value=defaults.get("beneficiary", ""))
        c, d = st.columns(2)
        category = c.text_input("Categoría", value=defaults.get("category", ""), placeholder="Ej. Transporte")
        payment_method = d.selectbox("Medio de pago", ["Cuenta personal", "Tarjeta personal", "Efectivo", "Otro"], index=["Cuenta personal", "Tarjeta personal", "Efectivo", "Otro"].index(defaults.get("payment_method", "Cuenta personal")))
        e, f = st.columns(2)
        accounting_status = e.selectbox("Estado contable", ["Pendiente de contabilizar", "Contabilizado"], index=0 if defaults.get("accounting_status", "Pendiente de contabilizar") == "Pendiente de contabilizar" else 1)
        reimbursement_status = f.selectbox("Estado de reembolso", ["Pendiente de reembolsar", "Reembolsado", "No aplica"], index=["Pendiente de reembolsar", "Reembolsado", "No aplica"].index(defaults.get("reimbursement_status", "Pendiente de reembolsar")))
        description = st.text_input("Concepto", value=defaults.get("description", ""), placeholder="Descripción del gasto")
        comments = st.text_area("Comentarios", value=defaults.get("comments") or "", placeholder="Factura, referencia u observaciones")
        submitted = st.form_submit_button("Actualizar pago" if editing else "Guardar pago", type="primary", use_container_width=True)
    if submitted:
        amount = _parse_money(st.session_state.get("valor_input", ""))
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
            st.session_state.valor_input = ""


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
