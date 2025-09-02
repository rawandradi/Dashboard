import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ======================
# Page Config
# ======================
st.set_page_config(
    page_title="No-Show Insights",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================
# Load Data
# ======================
df = pd.read_csv("noshowappointments-kagglev2-may-2016.csv")

# ======================
# Sidebar Controls
# ======================
st.sidebar.title('Controllers')
st.sidebar.markdown('-----')
FilterByGender = st.sidebar.multiselect("select Gender : ",options=df['Gender'].unique())
medical_condition_filter = st.sidebar.multiselect("select medical condition",options=['Hipertension','Diabetes','Handcap','Alcoholism','non','ALL'])
age_filter = st.sidebar.slider("Select Age Range:", int(df['Age'].min()), int(df['Age'].max()), (0, 100))
sms_filter = st.sidebar.radio("SMS Reminder:", ["All", "Yes", "No"])
No_Show_filter = st.sidebar.radio("missed  appointment : ",["ALL","Yes",'No'])
# ======================
# Custom CSS
# ======================
st.markdown("""
    <style>
    .block-container {
        max-width: 95% !important;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    .kpi-card {
        background: #f9f9f9;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .kpi-number {
        font-size: 28px;
        font-weight: bold;
        color: #0074c2;
    }
    </style>
""", unsafe_allow_html=True)

# ======================
# Header
# ======================
st.markdown("<h2 style='color:#0074c2;'>No-Show Insights: Understanding Patient Appointment Behavior</h2>", unsafe_allow_html=True)
st.markdown("##### Explore patterns and insights behind patient appointment attendance.")

# ======================
# KPI Section
# ======================

# ======================
# Visualization Section
# ======================

# ======================
# Data Table
# ======================
