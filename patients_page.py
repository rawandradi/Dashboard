# patients_page.py
import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np


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

# Helpers لاستعمال نفس كروت الستايل
def _card_open(title: str):
    st.markdown(f"<div class='card pad'><div class='section-title'>{title}</div>", unsafe_allow_html=True)
def _card_close():
    st.markdown("</div>", unsafe_allow_html=True)

def _plot(fig):
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

def render(F: pd.DataFrame, THEME: dict):
    # Tabs لتنظيم الصفحة
    tab_overview, tab_demo, tab_geo, tab_outcomes = st.tabs(["Overview", "Demographics", "Geography", "Outcomes"])

    # ================= Overview =================
    with tab_overview:
        st.markdown("<div class='kpi-row'>", unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"<div class='card pad kpi'><div><div class='num'>{F['PatientId'].nunique():,}</div><div class='lbl'>Distinct patients</div></div></div>", unsafe_allow_html=True)
        with k2:
            female = (F['Gender'].eq('F').mean()*100) if len(F) else 0
            st.markdown(f"<div class='card pad kpi'><div><div class='num'>{female:.1f}%</div><div class='lbl'>Female share</div></div></div>", unsafe_allow_html=True)
        with k3:
            med_age = F['Age'].median() if len(F) else 0
            st.markdown(f"<div class='card pad kpi'><div><div class='num'>{med_age:.0f}</div><div class='lbl'>Median age</div></div></div>", unsafe_allow_html=True)
        with k4:
            top_nb = F['Neighbourhood'].mode().iloc[0] if len(F) else '—'
            st.markdown(f"<div class='card pad kpi'><div><div class='num'>{top_nb}</div><div class='lbl'>Top neighborhood</div></div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        col1, col2 = st.columns([2,1])
        with col1:
            _card_open("Age distribution")
            _plot(px.histogram(F, x="Age", nbins=30, color_discrete_sequence=[THEME["primary"]]))
            _card_close()
        with col2:
            _card_open("Gender split")
            if len(F):
                g = F["Gender"].value_counts().reset_index()
                g.columns = ["Gender","Count"]
                fig = px.pie(g, names="Gender", values="Count", hole=.65,
                             color="Gender", color_discrete_map={"F":THEME["primary2"], "M":THEME["primary"]})
                fig.update_traces(textposition="inside", textinfo="percent+label")
                _plot(fig)
            else:
                st.info("No data.")
            _card_close()

    # ================= Demographics =================
    with tab_demo:
        col1, col2 = st.columns(2)
        with col1:
            _card_open("Age by gender (box)")
            if len(F):
                _plot(px.box(F, x="Gender", y="Age",
                             color="Gender",
                             color_discrete_map={"F":THEME["primary2"], "M":THEME["primary"]}))
            else:
                st.info("No data.")
            _card_close()
        with col2:
            _card_open("No-show % by age bin")
            if len(F):
                bins = pd.cut(F["Age"], bins=[0,12,18,35,50,65,120],
                              labels=["Child","Teen","18-35","36-50","51-65","65+"])
                ns = F.groupby(bins, observed=True)["NoShow"].mean().mul(100).reset_index()
                ns.columns = ["AgeBin","No-Show %"]
                fig = px.bar(ns, x="AgeBin", y="No-Show %", color_discrete_sequence=[THEME["warn"]])
                fig.update_traces(texttemplate="%{y:.1f}%", textposition="outside")
                _plot(fig)
            else:
                st.info("No data.")
            _card_close()

        _card_open("No-show % by gender")
        if len(F):
            ns_g = F.groupby("Gender", observed=True)["NoShow"].mean().mul(100).reset_index()
            ns_g.columns = ["Gender","No-Show %"]
            fig = px.bar(ns_g, x="Gender", y="No-Show %",
                         color="Gender", color_discrete_map={"F":THEME["primary2"], "M":THEME["primary"]})
            fig.update_traces(texttemplate="%{y:.1f}%", textposition="outside")
            _plot(fig)
        else:
            st.info("No data.")
        _card_close()

    # ================= Geography =================
    with tab_geo:
        _card_open("Top neighborhoods (unique patients)")
        if len(F):
            nb = (F.groupby("Neighbourhood", observed=True)["PatientId"].nunique()
                    .sort_values(ascending=False).head(15).reset_index())
            nb.columns = ["Neighbourhood","Patients"]
            fig = px.bar(nb, x="Patients", y="Neighbourhood", orientation="h",
                         color_discrete_sequence=[THEME["primary"]])
            fig.update_layout(yaxis=dict(categoryorder="total ascending"))
            _plot(fig)
        else:
            st.info("No data.")
        _card_close()

    # ================= Outcomes =================
    with tab_outcomes:
        _card_open("No-show heatmap (AgeBin × Weekday)")
        if len(F):
            bins = pd.cut(F["Age"], bins=[0,12,18,35,50,65,120],
                          labels=["Child","Teen","18-35","36-50","51-65","65+"])
            wk = F["AppointmentDay"].dt.day_name()
            mat = (F.assign(AgeBin=bins, Weekday=wk)
                     .groupby(["AgeBin","Weekday"], observed=True)["NoShow"]
                     .mean().mul(100).unstack().reindex(columns=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]))
            fig = px.imshow(mat, color_continuous_scale="Blues", aspect="auto",
                            labels=dict(color="No-Show %"))
            _plot(fig)
        else:
            st.info("No data.")
        _card_close()
