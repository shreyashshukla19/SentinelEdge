import streamlit as st
import pandas as pd
import plotly.express as px
from database import SafetyDatabase
from agent import SafetyAgent

st.set_page_config(page_title="Compliance & AI Audit", page_icon="📊", layout="wide")

db = SafetyDatabase()
agent = SafetyAgent()

st.title("📊 Compliance Audit & AI Intelligence")
st.markdown("Deep-dive historical safety analytics, zone compliance tracking, and automated Llama 3 root-cause insights.")

rows = db.get_all_incidents()

if rows:
    df = pd.DataFrame(rows, columns=["Timestamp", "Violation Type", "Zone", "Confidence", "ImagePath"])
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    
    # Top KPI Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Incidents Logged", len(df))
    with col2:
        unique_zones = df["Zone"].nunique()
        st.metric("Monitored Zones Affected", unique_zones)
    with col3:
        avg_conf = f"{df['Confidence'].mean() * 100:.1f}%"
        st.metric("Avg Detection Confidence", avg_conf)
    with col4:
        st.metric("AI Agent Status", "Online (Llama 3)")

    st.markdown("---")

    # Analytics Charts Section
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Violation Frequency Over Time")
        df_sorted = df.sort_values("Timestamp")
        fig_time = px.histogram(df_sorted, x="Timestamp", color="Violation Type", barmode="stack", title="Incident Timelines")
        st.plotly_chart(fig_time, use_container_width=True)

    with c2:
        st.subheader("Zone Risk Concentration")
        fig_zone = px.bar(df, x="Zone", color="Violation Type", title="Violations per Industrial Sector", barmode="group")
        st.plotly_chart(fig_zone, use_container_width=True)

    st.markdown("---")

    # AI Agent Executive Report Section
    st.subheader("🤖 Local LLM Executive Safety Analysis")
    st.markdown("Trigger local Ollama (Llama 3) to process audit telemetry and formulate corrective measures.")

    if st.button("Generate Comprehensive AI Report", type="primary"):
        with st.spinner("Analyzing safety logs via local Llama 3 model..."):
            report = agent.analyze_safety_trends()
            st.markdown("### Executive Action Plan")
            st.success(report)
else:
    st.info("No safety incident telemetry found in database. Run detections or log test violations to populate audit analytics.")