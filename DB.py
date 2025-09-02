import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="No-Show Appointments Explorer", layout="wide")

# -------- Sidebar: Upload & Column Mapping --------
st.sidebar.title("No-Show Appointments")
st.sidebar.caption("Upload your CSV then map columns if names differ.")
file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

# Default column names (change if your file uses different names)
colmap_defaults = {
    "scheduled": "ScheduledDay",
    "appointment": "AppointmentDay",
    "no_show": "No-show",          # values typically "Yes"/ "No"
    "age": "Age",
    "gender": "Gender",
    "neighborhood": "Neighbourhood",
    "scholarship": "Scholarship",
    "hipertension": "Hipertension",
    "diabetes": "Diabetes",
    "alcoholism": "Alcoholism",
    "handcap": "Handcap",
    "sms": "SMS_received",
    "patient_id": "PatientId",
}

def mapping_widget(df):
    st.sidebar.markdown("### Column mapping")
    mapped = {}
    for k, v in colmap_defaults.items():
        options = ["<none>"] + list(df.columns)
        default = options.index(v) if v in df.columns else 0
        mapped[k] = st.sidebar.selectbox(k.replace("_"," ").title(), options, index=default, key=f"map_{k}")
        if mapped[k] == "<none>":
            mapped[k] = None
    return mapped

@st.cache_data
def load_df(file):
    return pd.read_csv(file)

def safe_parse_date(s):
    return pd.to_datetime(s, errors="coerce")

if file:
    df_raw = load_df(file)
    mapping = mapping_widget(df_raw)
    df = df_raw.copy()

    # Parse dates
    if mapping["scheduled"]:   df["scheduled"] = safe_parse_date(df[mapping["scheduled"]])
    if mapping["appointment"]: df["appointment"] = safe_parse_date(df[mapping["appointment"]])

    # Clean age
    if mapping["age"]:
        df["age"] = pd.to_numeric(df[mapping["age"]], errors="coerce")
        df.loc[(df["age"] < 0) | (df["age"] > 120), "age"] = np.nan

    # Normalize No-show to 0/1
    if mapping["no_show"]:
        ns = df[mapping["no_show"]].astype(str).str.strip().str.lower()
        df["no_show"] = np.where(ns.isin(["yes","1","true","t"]), 1,
                           np.where(ns.isin(["no","0","false","f"]), 0, np.nan))

    # Optional binary columns
    def bin_col(k):
        if mapping[k]:
            df[k] = pd.to_numeric(df[mapping[k]], errors="coerce").fillna(0).astype(int)

    for k in ["sms","scholarship","hipertension","diabetes","alcoholism","handcap"]:
        bin_col(k)

    # Categorical
    if mapping["gender"]:       df["gender"] = df[mapping["gender"]].astype(str)
    if mapping["neighborhood"]: df["neighborhood"] = df[mapping["neighborhood"]].astype(str)
    if mapping["patient_id"]:   df["patient_id"] = df[mapping["patient_id"]].astype(str)

    # Feature engineering
    if "scheduled" in df and "appointment" in df:
        df["lead_days"] = (df["appointment"] - df["scheduled"]).dt.days
        df["appt_dow"] = df["appointment"].dt.day_name()
        df["appt_date"] = df["appointment"].dt.date
    else:
        df["lead_days"] = np.nan
        df["appt_dow"] = np.nan
        df["appt_date"] = np.nan

    if "age" in df:
        bins = [-0.1, 0, 5, 12, 18, 30, 45, 60, 75, 120]
        labels = ["<1","1-5","6-12","13-18","19-30","31-45","46-60","61-75","75+"]
        df["age_band"] = pd.cut(df["age"], bins=bins, labels=labels)

    # -------- Filters --------
    st.title("🩺 No-Show Appointments Explorer")

    with st.expander("Filters", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        # Date range
        if df["appointment"].notna().any():
            min_d, max_d = df["appointment"].min(), df["appointment"].max()
            d_from, d_to = c1.date_input("Appointment from", min_d.date() if pd.notna(min_d) else None), \
                           c2.date_input("to", max_d.date() if pd.notna(max_d) else None)
        else:
            d_from = d_to = None

        # Neighborhood
        neigh_sel = c3.multiselect("Neighbourhood", sorted(df["neighborhood"].dropna().unique())[:100]) if "neighborhood" in df else []
        # Gender
        gender_sel = c4.multiselect("Gender", sorted(df["gender"].dropna().unique())[:10]) if "gender" in df else []

        # Age range slider
        if "age" in df and df["age"].notna().any():
            min_a, max_a = int(np.nanmin(df["age"])), int(np.nanmax(df["age"]))
            age_min, age_max = st.slider("Age range", min_value=min_a, max_value=max_a, value=(min_a, max_a))
        else:
            age_min = age_max = None

        # Binary toggles
        t1, t2, t3, t4 = st.columns(4)
        sms_only = t1.checkbox("SMS received = 1 filter", value=False)
        scholarship_only = t2.checkbox("Scholarship = 1 filter", value=False)
        chronic_only = t3.checkbox("Chronic (Hipertension/Diabetes) = 1 filter", value=False)
        lead_cap = t4.slider("Max lead days cap (for plots)", 0, 120, 60)

    # Apply filters
    mask = pd.Series(True, index=df.index)
    if d_from and d_to and "appt_date" in df:
        mask &= (pd.to_datetime(df["appt_date"]) >= pd.to_datetime(d_from)) & (pd.to_datetime(df["appt_date"]) <= pd.to_datetime(d_to))
    if neigh_sel:
        mask &= df["neighborhood"].isin(neigh_sel)
    if gender_sel:
        mask &= df["gender"].isin(gender_sel)
    if age_min is not None:
        mask &= df["age"].between(age_min, age_max)
    if sms_only and "sms" in df:
        mask &= df["sms"] == 1
    if scholarship_only and "scholarship" in df:
        mask &= df["scholarship"] == 1
    if chronic_only:
        conds = []
        for k in ["hipertension","diabetes"]:
            if k in df: conds.append(df[k] == 1)
        if conds:
            mask &= np.logical_or.reduce(conds)

    dff = df[mask].copy()

    # -------- KPIs --------
    k1, k2, k3, k4 = st.columns(4)
    total = len(dff)
    ns_rate = (dff["no_show"].mean()*100) if "no_show" in dff and total>0 else np.nan
    sms_rate = dff.loc[dff.get("sms", pd.Series(dtype=int))==1, "no_show"].mean()*100 if "sms" in dff and "no_show" in dff and (dff["sms"]==1).any() else np.nan
    schol_rate = dff.loc[dff.get("scholarship", pd.Series(dtype=int))==1, "no_show"].mean()*100 if "scholarship" in dff and "no_show" in dff and (dff["scholarship"]==1).any() else np.nan
    avg_lead = dff["lead_days"].clip(upper=365).mean() if "lead_days" in dff else np.nan

    k1.metric("Appointments (filtered)", f"{total:,}")
    k2.metric("No-Show Rate", f"{ns_rate:0.1f}%" if pd.notna(ns_rate) else "—")
    k3.metric("No-Show w/ SMS", f"{sms_rate:0.1f}%" if pd.notna(sms_rate) else "—")
    k4.metric("Avg Lead Days", f"{avg_lead:0.1f}" if pd.notna(avg_lead) else "—")

    st.markdown("---")

    # -------- Visuals --------
    # 1) No-show by Day of Week
    if "appt_dow" in dff and "no_show" in dff:
        order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        tmp = dff.groupby("appt_dow")["no_show"].mean().mul(100).reindex(order)
        fig = px.bar(tmp, labels={"value":"No-Show %","index":"Appointment DOW"}, text=tmp.round(1))
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    # 2) Lead time vs no-show
    if "lead_days" in dff and "no_show" in dff:
        dd = dff.copy()
        dd = dd[(dd["lead_days"] >= 0) & (dd["lead_days"] <= lead_cap)]
        if len(dd):
            fig2 = px.histogram(dd, x="lead_days", color="no_show",
                                barmode="group", marginal="box",
                                labels={"lead_days":"Lead Days","no_show":"No-Show (1=yes)"})
            st.plotly_chart(fig2, use_container_width=True)

    # 3) Age band no-show rate
    if "age_band" in dff and "no_show" in dff:
        tmp2 = dff.groupby("age_band")["no_show"].mean().mul(100)
        fig3 = px.bar(tmp2, labels={"value":"No-Show %","index":"Age Band"}, text=tmp2.round(1))
        fig3.update_traces(textposition="outside")
        st.plotly_chart(fig3, use_container_width=True)

    # 4) Neighborhood top/bottom
    if "neighborhood" in dff and "no_show" in dff:
        ns_by_n = dff.groupby("neighborhood")["no_show"].mean().mul(100).sort_values(ascending=False)
        st.subheader("Neighbourhoods by No-Show %")
        st.write(ns_by_n.head(10).round(1).to_frame("No-Show %"))

    # 5) SMS / Scholarship impact
    cols = []
    if "sms" in dff: cols.append("sms")
    if "scholarship" in dff: cols.append("scholarship")
    if cols and "no_show" in dff:
        st.subheader("Binary Factors Impact")
        tbl = dff.groupby(cols)["no_show"].mean().mul(100).round(1).to_frame("No-Show %")
        st.write(tbl)

    # Raw preview
    with st.expander("Raw filtered data"):
        st.dataframe(dff.head(200), use_container_width=True)

else:
    st.title("🩺 No-Show Appointments Explorer")
    st.write("Upload your **appointments CSV** from the left sidebar to begin.")
    st.markdown(
        """
        **Expected columns (typical names, can be remapped):**  
        `ScheduledDay`, `AppointmentDay`, `No-show`, `Age`, `Gender`, `Neighbourhood`,  
        `Scholarship`, `Hipertension`, `Diabetes`, `Alcoholism`, `Handcap`, `SMS_received`.
        """
    )
