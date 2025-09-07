# DB.py — Aurora Pro Layout (modular routing, same-tab nav, stateful page)
# Run: streamlit run DB.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import date

# Sub-pages
from patients_page import render as render_patients
from appointments_page import render as render_appointments

# =================== PAGE ===================
st.set_page_config(
    page_title="Appointment Attendance Analytics",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Windows + older Streamlit workaround for stray asyncio RuntimeWarnings ---
# --- Windows + older Streamlit workaround for stray asyncio RuntimeWarnings ---
import sys, asyncio, warnings

if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

# Silence: "coroutine 'expire_cache' was never awaited" from streamlit.util
warnings.filterwarnings(
    "ignore",
    category=RuntimeWarning,
    module=r"streamlit\.util$",
)




# =================== THEME TOKENS ===================
LIGHT = {
    "bg_grad_top": "#f6f8ff", "bg_grad_mid": "#eef3ff", "bg_grad_end": "#ffffff",
    "card": "rgba(255,255,255,.72)", "card_border": "rgba(120,130,170,.16)",
    "ink": "#0f172a", "muted": "#667085", "primary": "#6C63FF", "primary2": "#A78BFA",
    "accent": "#22C55E", "warn": "#F59E0B", "danger": "#EF4444",
}
DARK = {
    "bg_grad_top": "#0b1020", "bg_grad_mid": "#0f172a", "bg_grad_end": "#121a31",
    "card": "rgba(17,23,42,.64)", "card_border": "rgba(255,255,255,.08)",
    "ink": "#e5e7eb", "muted": "#9aa3b2", "primary": "#8B7BFF", "primary2": "#7C3AED",
    "accent": "#34D399", "warn": "#FBBF24", "danger": "#F87171",
}

if "dark" not in st.session_state:
    st.session_state.dark = False
THEME = DARK if st.session_state.dark else LIGHT

# --------- small helpers for query params (new & old Streamlit) ----------
def _qp_get(key: str):
    try:
        return st.query_params.get(key)
    except Exception:
        v = st.experimental_get_query_params().get(key)
        return v[0] if isinstance(v, list) and v else v

def _qp_set(**kwargs):
    try:
        st.query_params.update(kwargs)
    except Exception:
        st.experimental_set_query_params(**kwargs)

# ===== Router state (keeps current page across reruns) =====
# ONE-TIME initialization from URL (or default). Do NOT resync on every rerun.
if "page" not in st.session_state:
    st.session_state.page = _qp_get("page") or "overview"

def current_page() -> str:
    return st.session_state.page

def goto(slug: str):
    st.session_state.page = slug
    _qp_set(page=slug)          # keep the URL in sync for deep-links

# Keep URL clean/accurate every run (no effect on state)
_qp_set(page=current_page())

# =================== GLOBAL CSS ===================
st.markdown(f"""
<style>
:root {{
  --bg-top:{THEME['bg_grad_top']}; --bg-mid:{THEME['bg_grad_mid']}; --bg-end:{THEME['bg_grad_end']};
  --card:{THEME['card']}; --card-border:{THEME['card_border']};
  --ink:{THEME['ink']}; --muted:{THEME['muted']};
  --p:{THEME['primary']}; --p2:{THEME['primary2']}; --acc:{THEME['accent']};
  --warn:{THEME['warn']}; --danger:{THEME['danger']};
}}
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

html, body, [data-testid='stAppViewContainer']{{
  font-family:'Inter',system-ui,-apple-system,Segoe UI,Roboto,Arial;
  color:var(--ink);
  background:
    radial-gradient(1300px 780px at 12% -10%, var(--bg-top), var(--bg-mid) 40%),
    radial-gradient(1400px 900px at 98% 0%, var(--bg-mid), var(--bg-end) 55%);
}}
.block-container{{max-width:1340px;padding-top:12px}}
[data-testid='stHeader']{{background:transparent}}

.card{{background:var(--card);backdrop-filter:blur(12px);border:1px solid var(--card-border);border-radius:22px;box-shadow:0 18px 44px rgba(17,24,39,.10)}}
.pad{{padding:18px}}
.smallmuted{{color:var(--muted);font-size:12px}}

/* Header */
.header-grid{{display:grid;grid-template-columns:1fr 360px 160px;gap:12px;align-items:center}}
.search{{width:100%;padding:10px 14px;border-radius:14px;border:1px solid var(--card-border);background:rgba(255,255,255,.65)}}

/* ===== Sidebar (website-like) ===== */
[data-testid="stSidebar"] {{
  padding: 16px 14px 20px;
  background:
    radial-gradient(420px 380px at 0 -40px, rgba(108,99,255,.12), transparent 60%),
    linear-gradient(180deg, rgba(255,255,255,.35), rgba(255,255,255,.18));
  backdrop-filter: blur(10px);
  border-right: 1px solid var(--card-border);
}}
.sidenav{{display:flex;flex-direction:column;height:100%;gap:12px}}
.sidenav .brand{{
  display:flex;align-items:center;gap:10px;
  font-weight:800;font-size:18px;padding:12px 14px;border-radius:14px;
  background:var(--card);border:1px solid var(--card-border);
  box-shadow:0 10px 20px rgba(17,23,42,.08)
}}
.sidenav .logo{{
  width:32px;height:32px;border-radius:10px;color:#fff;display:grid;place-items:center;
  background:linear-gradient(135deg,var(--p),var(--p2))
}}
.nav-section .label{{margin:10px 8px 8px;font-size:11px;color:var(--muted);letter-spacing:.02em}}

/* Active pill */
.nav-link{{
  position:relative;display:flex;align-items:center;gap:10px;
  padding:10px 12px;border-radius:12px;background:var(--card);
  border:1px solid var(--card-border);color:inherit;text-decoration:none
}}
.nav-link.active{{
  color:#fff;background:linear-gradient(135deg,rgba(108,99,255,.95),rgba(167,139,250,.95));
  border-color:transparent;box-shadow:0 12px 22px rgba(108,99,255,.28)
}}
.nav-link.active::before{{
  content:"";position:absolute;left:-10px;top:18%;width:4px;height:64%;
  border-radius:6px;background:linear-gradient(var(--p),var(--p2));
  box-shadow:0 0 0 4px rgba(108,99,255,.15)
}}
/* ==== Sidebar spacing (final, clean) ==== */

/* مسافة تحت عنوان Main */
[data-testid="stSidebar"] .nav-section .label{{
  margin: 12px 8px 12px;
}}

/* فجوة موحّدة بين عناصر الناف (active pill + buttons) */
[data-testid="stSidebar"] .nav-link,
[data-testid="stSidebar"] .stButton{{
  display: block;
  margin: 0 0 20px 0 !important;   /* غيّر 20px حسب ذوقك */
}}

/* نفس الفجوة للعنصر النشط */
[data-testid="stSidebar"] .nav-link.active{{
  margin-bottom: 20px !important;
}}

/* آخر عنصر بدون مسافة إضافية */
[data-testid="stSidebar"] .nav-link:last-of-type,
[data-testid="stSidebar"] .stButton:last-of-type{{
  margin-bottom: 0 !important;
}}

/* مسافة لطيفة فوق كرت البروفايل */
[data-testid="stSidebar"] .profile{{
  margin-top: 20px;
}}

/* أزرار الناف تُلبس نفس شكل الروابط */
[data-testid="stSidebar"] .stButton > button{{
  width:100%;
  display:flex; align-items:center; gap:10px;
  padding:10px 12px; border-radius:12px;
  border:1px solid var(--card-border); background:var(--card);
  color:inherit; text-align:left; transition:all .15s ease;
}}
[data-testid="stSidebar"] .stButton > button:hover{{
  border-color: rgba(108,99,255,.35);
  box-shadow: 0 6px 14px rgba(108,99,255,.12);
  transform: translateY(-1px);
}}
[data-testid="stSidebar"] .stButton > button::after{{
  content:"›"; margin-left:auto; opacity:.35; font-weight:700;
}}
[data-testid="stSidebar"] .stButton > button .ico{{ width:22px; text-align:center; }}

[data-testid="stSidebar"] .nav-link.active {{
  margin-bottom: 18px !important;  /* optional override */
}}

/* Footer/profile */
.sidenav .spacer{{flex:1 1 auto}}
.profile{{
  display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:12px;
  background:var(--card);border:1px solid var(--card-border)
}}
.profile .avatar{{
  width:30px;height:30px;border-radius:50%;
  background:linear-gradient(135deg,var(--p),var(--p2));
  box-shadow:0 6px 16px rgba(108,99,255,.25)
}}
.profile .meta .name{{font-weight:700;font-size:12.5px}}
.profile .meta .role{{color:var(--muted);font-size:11px}}

/* Layout helpers */
.ribbon{{display:grid;gap:12px;grid-template-columns:repeat(12,1fr)}}
@media (max-width:1200px){{.ribbon{{grid-template-columns:repeat(6,1fr)}}}}
@media (max-width:640px){{.ribbon{{grid-template-columns:repeat(2,1fr)}}}}
.kpi-row{{display:grid;gap:14px;grid-template-columns:repeat(4,1fr)}}
@media (max-width:1200px){{.kpi-row{{grid-template-columns:repeat(2,1fr)}}}}
@media (max-width:640px){{.kpi-row{{grid-template-columns:1fr}}}}
.kpi{{display:flex;gap:12px;align-items:center}}
.kpi .ico{{width:46px;height:46px;border-radius:14px;display:grid;place-items:center;color:#fff;background:linear-gradient(135deg,var(--p),var(--p2));box-shadow:0 10px 20px rgba(124,58,237,.25)}}
.kpi .num{{font-size:28px;font-weight:800}}
.kpi .lbl{{font-size:12px;color:var(--muted);margin-top:-6px}}
.grid-2{{display:grid;gap:16px;grid-template-columns:2fr 1fr}}
@media (max-width:1200px){{.grid-2{{grid-template-columns:1fr}}}}
.section-title{{font-weight:800;margin-bottom:8px}}

/* Soft noise layer */
[data-testid='stAppViewContainer']::before{{
  content:"";position:fixed;inset:0;pointer-events:none;opacity:.32;mix-blend-mode:soft-light;
  background-image:url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="160" height="160" viewBox="0 0 160 160"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/></filter><rect width="100%" height="100%" filter="url(#n)" opacity=".015"/></svg>')
}}
</style>
""", unsafe_allow_html=True)


# =================== SIDEBAR ===================
def render_sidebar():
    active = current_page()

    items = [
        ("overview",     "Overview",     "🏠"),
        ("patients",     "Patients",     "👥"),
        ("appointments", "Appointments", "📅"),
    ]

    # Brand
    st.sidebar.markdown(
        "<aside class='sidenav'>"
        "<div class='brand'><div class='logo'>🩺</div><div>Medical Data analysis</div></div>",
        unsafe_allow_html=True,
    )

    # Group label
    st.sidebar.markdown("<div class='nav-section'><div class='label'>Main</div></div>", unsafe_allow_html=True)

    # Buttons / active pill
    box = st.sidebar.container()
    with box:
        st.markdown("<div class='sidebar-nav'>", unsafe_allow_html=True)
        for slug, label, icon in items:
            if slug == active:
                st.markdown(
                    f"<div class='nav-link active'><span class='ico'>{icon}</span>{label}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.button(
                    f"{icon}  {label}",
                    key=f"nav_{slug}",
                    use_container_width=True,
                    on_click=goto,
                    args=(slug,),
                )
        st.markdown("</div>", unsafe_allow_html=True)

    # Footer/profile
    st.sidebar.markdown(
        "<div class='spacer'></div>"
        "<div class='profile'><div class='avatar'></div>"
        "<div class='meta'><div class='name'>Rawand Radi</div><div class='role'>Analyst</div></div>"
        "</div></aside>",
        unsafe_allow_html=True,
    )

render_sidebar()

# =================== DATA ===================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("noshowappointments-kagglev2-may-2016.csv")
    except Exception:
        rng = np.random.default_rng(13); n = 1400
        df = pd.DataFrame({
            "PatientId": rng.integers(1_000_000,9_999_999,n),
            "AppointmentID": rng.integers(10_000_000,99_999_999,n),
            "Gender": rng.choice(["F","M"], n, p=[0.65,0.35]),
            "ScheduledDay": pd.date_range(date(2016,1,1), periods=n, freq="D", tz="UTC"),
            "AppointmentDay": pd.date_range(date(2016,1,1), periods=n, freq="D", tz="UTC"),
            "Age": np.clip(rng.normal(39,16,n).astype(int), 0, 95),
            "Neighbourhood": rng.choice(["Centro","Jardim","Maria Ortiz","Sao Pedro","Resistencia","Tabuazeiro"], n),
            "Scholarship": rng.integers(0,2,n),
            "Hipertension": rng.integers(0,2,n, p=[0.75,0.25]),
            "Diabetes": rng.integers(0,2,n, p=[0.85,0.15]),
            "Alcoholism": rng.integers(0,2,n, p=[0.92,0.08]),
            "Handcap": rng.choice([0,1], n, p=[0.93,0.07]),
            "SMS_received": rng.integers(0,2,n, p=[0.45,0.55]),
            "No-show": rng.choice(["No","Yes"], n, p=[0.80,0.20]),
        })

    # Normalize dtypes & drop tz (prevents tz-aware/naive subtraction issues)
    df["ScheduledDay"] = pd.to_datetime(df["ScheduledDay"], errors="coerce")
    df["AppointmentDay"] = pd.to_datetime(df["AppointmentDay"], errors="coerce")
    for col in ["ScheduledDay", "AppointmentDay"]:
        try:
            df[col] = df[col].dt.tz_localize(None)
        except TypeError:
            pass

    df["AppointmentDate"] = df["AppointmentDay"].dt.date
    df["Month"] = df["AppointmentDay"].dt.to_period("M").astype(str)
    df["Weekday"] = df["AppointmentDay"].dt.day_name()
    df["Show"] = np.where(df["No-show"].astype(str).str.upper().eq("NO"), 1, 0)
    df["NoShow"] = 1 - df["Show"]
    return df

DF = load_data()

# =================== HEADER ===================
with st.container():
    st.markdown(
        "<div class='card pad header-grid'>"
        "<div><div style='font-weight:800;font-size:22px'>Appointment Attendance Analytics</div>"
        "<div class='smallmuted' style='margin-top:-6px'>Dashboard</div></div>"
        "<input class='search' placeholder='Search metrics, patients, neighborhoods…'>"
        "</div>", unsafe_allow_html=True)

# =================== FILTER RIBBON ===================
with st.container():
    st.markdown("<div class='card pad'><div class='ribbon'>", unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns([2.4,1.4,1.2,1.8,1.2])
    with c1:
        min_d, max_d = DF["AppointmentDate"].min(), DF["AppointmentDate"].max()
        start, end = st.date_input("Date range", (min_d, max_d))
    with c2:
        genders = st.multiselect("Gender", sorted(DF["Gender"].dropna().unique()))
    with c3:
        sms_sel = st.selectbox("SMS", ("All","Yes","No"))
    with c4:
        nb = st.multiselect("Neighborhood", sorted(DF["Neighbourhood"].dropna().unique()))
    with c5:
        a_min, a_max = int(DF["Age"].min()), int(DF["Age"].max())
        age_range = st.slider("Age", min_value=a_min, max_value=a_max, value=(a_min, a_max))
    st.markdown("</div></div>", unsafe_allow_html=True)

# Shared filter for all pages
mask = (DF["AppointmentDate"] >= start) & (DF["AppointmentDate"] <= end)
if genders: mask &= DF["Gender"].isin(genders)
if sms_sel != "All": mask &= DF["SMS_received"].eq(1 if sms_sel == "Yes" else 0)
if nb: mask &= DF["Neighbourhood"].isin(nb)
mask &= DF["Age"].between(*age_range)
F = DF.loc[mask].copy()

# =================== OVERVIEW (function) ===================
def render_overview(F: pd.DataFrame, THEME: dict):
    def sparkline(series, color):
        s = pd.Series(series)
        if s.size == 0:
            s = pd.Series([0])
        fig = px.area(y=s, height=90)
        fig.update_traces(mode="lines", line_shape="spline",
                          line_color=color, fill="tozeroy", hoverinfo="skip")
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                          paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)")
        return fig

    def kpi_with_spark(icon, value, label, series, color, delta=None, good=True):
        d_html = ""
        if delta is not None:
            pos = (good and delta >= 0) or (not good and delta < 0)
            d_html = (
                f"<div class='smallmuted' style='margin-top:2px;"
                f"color:{THEME['accent'] if pos else THEME['danger']}'>{delta:+.1f}%</div>"
            )
        st.markdown(
            f"<div class='card pad kpi'><div class='ico'>{icon}</div>"
            f"<div><div class='num'>{value}</div>{d_html}"
            f"<div class='lbl'>{label}</div></div></div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            sparkline(series, color),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    trend_month = F.groupby("Month", observed=True).size()

    st.markdown("<div class='kpi-row'>", unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_with_spark("📅", f"{len(F):,}", "Appointments",
                       trend_month.values[-12:], THEME["primary"])
    with k2:
        ns_rate = (F["NoShow"].mean() * 100) if len(F) else 0.0
        rolling_ns = (1 - F["Show"].rolling(20).mean().dropna()).values[-20:]
        kpi_with_spark("🚫", f"{ns_rate:.1f}%", "No-Show Rate",
                       rolling_ns, THEME["warn"], good=False)
    with k3:
        sms_pct = (F["SMS_received"].mean() * 100) if len(F) else 0.0
        kpi_with_spark("✉️", f"{sms_pct:.0f}%", "Received SMS",
                       F["SMS_received"].rolling(25).mean().dropna().values[-25:],
                       THEME["accent"])
    with k4:
        avg_age = (F["Age"].mean()) if len(F) else 0.0
        kpi_with_spark("👤", f"{avg_age:.0f}", "Avg Age (yrs)",
                       F["Age"].rolling(25).mean().dropna().values[-25:],
                       THEME["primary2"])
    st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='grid-2'>", unsafe_allow_html=True)
        left, right = st.columns([2, 1])

        with left:
            by_show = (
                F["No-show"].value_counts()
                .rename({'No': 'Show', 'Yes': 'No-Show'})
                .reset_index()
            )
            by_show.columns = ["Status", "Count"]
            fig1 = px.pie(
                by_show,
                names="Status",
                values="Count",
                hole=0.72,
                color="Status",
                color_discrete_map={"Show": THEME["primary"], "No-Show": THEME["warn"]},
            )
            fig1.update_traces(textposition="inside", textinfo="percent+label", pull=[0, 0.06])
            st.markdown(
                "<div class='card pad'><div class='section-title'>Attendance Breakdown</div>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

            trend_area = trend_month.reset_index(name="Appointments")
            fig3 = px.area(trend_area, x="Month", y="Appointments",
                           color_discrete_sequence=[THEME["primary"]])
            fig3.update_traces(mode="lines", line_shape="spline")
            st.markdown(
                "<div class='card pad' style='margin-top:16px'><div class='section-title'>Appointments Over Time</div>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            sms = (
                F.groupby("SMS_received", observed=True)["NoShow"]
                .mean().mul(100)
                .rename({0: "No SMS", 1: "SMS Sent"})
                .reset_index()
            )
            sms.columns = ["SMS", "No-Show %"]
            fig2 = px.bar(
                sms,
                x="SMS",
                y="No-Show %",
                text="No-Show %",
                color="SMS",
                color_discrete_sequence=[THEME["primary"], THEME["accent"]],
            )
            fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside", marker_line_width=0)
            st.markdown("<div class='card pad'><div class='section-title'>Effect of SMS</div>",
                        unsafe_allow_html=True)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='card pad'><div class='section-title'>Details</div>", unsafe_allow_html=True)
        cols = ["AppointmentID","PatientId","AppointmentDate","Gender","Age","Neighbourhood","SMS_received","Scholarship","No-show"]
        st.dataframe(F[cols].head(250), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

# =================== ROUTER ===================
page = current_page()
if page == "patients":
    render_patients(F, THEME)
elif page == "appointments":
    render_appointments(F, THEME)
else:
    render_overview(F, THEME)

# =================== FOOTER & TOGGLES ===================
st.markdown("<div class='smallmuted' style='text-align:center;padding:14px'>Aurora Layout • unified CSS • same-tab nav • stateful theme</div>", unsafe_allow_html=True)

# =============== THEME TOGGLE (preserve current page) ===============
if st.button("🌙 Dark" if not st.session_state.dark else "☀️ Light"):
    st.session_state.dark = not st.session_state.dark
    # do not touch page; URL already set above
    st.rerun()

