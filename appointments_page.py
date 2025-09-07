# appointments_page.py
import streamlit as st
import plotly.express as px
import pandas as pd



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

warnings.simplefilter("ignore", RuntimeWarning)



def _card_open(title: str):
    st.markdown(f"<div class='card pad'><div class='section-title'>{title}</div>", unsafe_allow_html=True)

def _card_close():
    st.markdown("</div>", unsafe_allow_html=True)

def _plot(fig):
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

def render(F: pd.DataFrame, THEME: dict):
    # -------- Normalize datetimes (remove any timezone to avoid tz-aware vs tz-naive issues) --------
    F = F.copy()
    for col in ["AppointmentDay", "ScheduledDay"]:
        s = pd.to_datetime(F[col], errors="coerce")
        # If the series has timezone info, drop it safely
        if getattr(s.dt, "tz", None) is not None:
            s = s.dt.tz_localize(None)
        F[col] = s

    # Precompute lead time (days), drop NA and negatives (if any)
    if len(F):
        lead_td = (F["AppointmentDay"] - F["ScheduledDay"])
        lead_days = lead_td.dt.days
        lead_days_clean = lead_days.dropna()
        lead_days_pos = lead_days_clean[lead_days_clean >= 0]
        avg_lead = float(lead_days_pos.mean()) if len(lead_days_pos) else 0.0
    else:
        lead_days_pos = pd.Series(dtype="float64")
        avg_lead = 0.0

    tab_vol, tab_quality, tab_cohorts = st.tabs(["Volume & Timing", "Quality (No-show)", "Cohorts"])

    # ===================== Volume & Timing =====================
    with tab_vol:
        st.markdown("<div class='kpi-row'>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown(
                f"<div class='card pad kpi'><div><div class='num'>{len(F):,}</div>"
                f"<div class='lbl'>Appointments</div></div></div>",
                unsafe_allow_html=True,
            )

        with c2:
            show_rate = (F["Show"].mean() * 100) if len(F) else 0
            st.markdown(
                f"<div class='card pad kpi'><div><div class='num'>{show_rate:.1f}%</div>"
                f"<div class='lbl'>Show rate</div></div></div>",
                unsafe_allow_html=True,
            )

        with c3:
            st.markdown(
                f"<div class='card pad kpi'><div><div class='num'>{avg_lead:.1f}</div>"
                f"<div class='lbl'>Avg lead time (days)</div></div></div>",
                unsafe_allow_html=True,
            )

        with c4:
            sms_pct = (F["SMS_received"].mean() * 100) if len(F) else 0
            st.markdown(
                f"<div class='card pad kpi'><div><div class='num'>{sms_pct:.0f}%</div>"
                f"<div class='lbl'>SMS sent</div></div></div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        l, r = st.columns([2, 1])

        with l:
            _card_open("Lead time distribution")
            if len(lead_days_pos):
                df_lead = pd.DataFrame({"Days": lead_days_pos})
                fig = px.histogram(
                    df_lead, x="Days", nbins=30,
                    color_discrete_sequence=[THEME["primary"]],
                    labels={"Days": "Days between scheduling and appointment"}
                )
                _plot(fig)
            else:
                st.info("No data.")
            _card_close()

            _card_open("Appointments by weekday")
            if len(F):
                wk = F["AppointmentDay"].dt.day_name()
                w = (
                    wk.value_counts()
                    .reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
                    .dropna()
                    .astype(int)
                    .reset_index()
                )
                w.columns = ["Weekday", "Appointments"]
                fig = px.bar(w, x="Weekday", y="Appointments", color_discrete_sequence=[THEME["primary"]])
                _plot(fig)
            else:
                st.info("No data.")
            _card_close()

        with r:
            _card_open("Monthly trend")
            if len(F):
                tm = F.groupby("Month", observed=True).size().reset_index(name="Appointments")
                fig = px.area(tm, x="Month", y="Appointments", color_discrete_sequence=[THEME["primary"]])
                fig.update_traces(mode="lines", line_shape="spline")
                _plot(fig)
            else:
                st.info("No data.")
            _card_close()

    # ===================== Quality (No-show) =====================
    with tab_quality:
        l, r = st.columns([1, 1])

        with l:
            _card_open("No-show % by SMS")
            if len(F):
                sms = (
                    F.groupby("SMS_received", observed=True)["NoShow"]
                    .mean()
                    .mul(100)
                    .rename({0: "No SMS", 1: "SMS Sent"})
                    .reset_index()
                )
                sms.columns = ["SMS", "No-Show %"]
                fig = px.bar(
                    sms, x="SMS", y="No-Show %", text="No-Show %",
                    color="SMS", color_discrete_sequence=[THEME["primary"], THEME["accent"]]
                )
                fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                _plot(fig)
            else:
                st.info("No data.")
            _card_close()

        with r:
            _card_open("No-show % by weekday")
            if len(F):
                ns_w = (
                    F.assign(Weekday=F["AppointmentDay"].dt.day_name())
                    .groupby("Weekday", observed=True)["NoShow"]
                    .mean()
                    .mul(100)
                    .reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
                    .reset_index()
                )
                ns_w.columns = ["Weekday", "No-Show %"]
                fig = px.bar(ns_w, x="Weekday", y="No-Show %", color_discrete_sequence=[THEME["warn"]])
                fig.update_traces(texttemplate="%{y:.1f}%", textposition="outside")
                _plot(fig)
            else:
                st.info("No data.")
            _card_close()

        _card_open("Top neighborhoods by no-show %")
        if len(F):
            ns_nb = (
                F.groupby("Neighbourhood", observed=True)["NoShow"]
                .mean()
                .mul(100)
                .sort_values(ascending=False)
                .head(12)
                .reset_index()
            )
            ns_nb.columns = ["Neighbourhood", "No-Show %"]
            fig = px.bar(
                ns_nb, x="No-Show %", y="Neighbourhood", orientation="h",
                color_discrete_sequence=[THEME["warn"]]
            )
            fig.update_layout(yaxis=dict(categoryorder="total ascending"))
            _plot(fig)
        else:
            st.info("No data.")
        _card_close()

    # ===================== Cohorts =====================
    with tab_cohorts:
        _card_open("Visit count distribution (per patient)")
        if len(F):
            counts = F.groupby("PatientId", observed=True).size()
            vc = counts.value_counts().sort_index().head(10).reset_index()
            vc.columns = ["Visits", "Patients"]
            fig = px.bar(vc, x="Visits", y="Patients", color_discrete_sequence=[THEME["primary"]])
            _plot(fig)
        else:
            st.info("No data.")
        _card_close()

        _card_open("New patients by month (first visit)")
        if len(F):
            first_month = (
                F.sort_values("AppointmentDay")
                .groupby("PatientId", observed=True)["Month"]
                .first()
                .value_counts()
                .sort_index()
                .reset_index()
            )
            first_month.columns = ["Month", "New patients"]
            fig = px.area(first_month, x="Month", y="New patients", color_discrete_sequence=[THEME["primary"]])
            fig.update_traces(mode="lines", line_shape="spline")
            _plot(fig)
        else:
            st.info("No data.")
        _card_close()
