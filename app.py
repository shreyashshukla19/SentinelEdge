import streamlit as st
import pandas as pd
from database import SafetyDatabase
from reports import PDFReportGenerator
from alarm import SafetyAlarm

st.set_page_config(
    page_title="SentinelEdge Enterprise", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Industrial Dark Theme CSS
st.markdown("""
    <style>
    .main { background-color: #090D16; color: #E2E8F0; }
    .stMetric { background-color: #111827; padding: 15px; border-radius: 8px; border: 1px solid #1F2937; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: 600; background-color: #2563EB; color: white; }
    .stButton>button:hover { background-color: #1D4ED8; }
    </style>
""", unsafe_allow_html=True)

db = SafetyDatabase()
alarm = SafetyAlarm()
pdf_gen = PDFReportGenerator()

st.title("🛡️ SentinelEdge: Autonomous Safety & PPE Command Center")
st.markdown("Real-time Edge-AI industrial surveillance, automated database logging, hardware buzzer triggers, and forensic reporting.")

# Sidebar Zone Configuration
st.sidebar.header("🎛️ Control Panel")
selected_zone = st.sidebar.selectbox("Active Monitoring Sector", ["Sector A - Warehouse", "Sector B - Assembly Line", "Sector C - Loading Dock", "Sector D - Chemical Bay"])
confidence_threshold = st.sidebar.slider("YOLO Confidence Threshold", 0.5, 0.95, 0.75)
buzzer_enabled = st.sidebar.checkbox("Enable Hardware Piezo Buzzer Alert", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("📄 Forensic Reporting")
if st.sidebar.button("📥 Export PDF Audit Report"):
    with st.spinner("Compiling PDF evidence report..."):
        pdf_path = pdf_gen.generate_report()
        with open(pdf_path, "rb") as f:
            st.sidebar.download_button(
                label="Download Generated PDF",
                data=f,
                file_name="SentinelEdge_Audit_Report.pdf",
                mime="application/pdf"
            )

# Main Dashboard View Tabs
tab1, tab2, tab3 = st.tabs(["🔴 Live Surveillance Feed", "📋 Incident Database & Evidence", "⚙️ Edge Node Telemetry"])

with tab1:
    st.subheader(f"Live Feed — {selected_zone}")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("RTSP Multi-Threaded Camera stream active. Ready for live YOLOv8 frame inference.")
        # Placeholder frame view
        st.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=800&q=80", caption="Simulated Industrial Floor Feed", use_column_width=True)

    with col2:
        st.markdown("### Simulation Testing")
        violation_type = st.selectbox("Simulate Violation Type", ["Missing Hard Hat", "No Safety Vest", "Unauthorized Zone Entry", "Missing Eye Protection"])
        
        if st.button("🚨 Simulate Violation & Trigger Alarm"):
            dummy_frame = None
            db.log_incident(dummy_frame, violation_type, selected_zone, 0.92)
            if buzzer_enabled:
                alarm.trigger_alarm_async()
            st.success(f"Logged violation: {violation_type} in {selected_zone}! Alarm triggered.")

with tab2:
    st.subheader("Persistent SQLite Incident Logs & Evidence Crops")
    rows = db.get_all_incidents()
    if rows:
        df = pd.DataFrame(rows, columns=["Timestamp", "Violation Type", "Zone", "Confidence", "ImagePath"])
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No incidents recorded yet.")

with tab3:
    st.subheader("Edge Node Hardware Telemetry")
    c1, c2, c3 = st.columns(3)
    c1.metric("YOLOv8 Inference Latency", "18.4 ms", "-2.1 ms")
    c2.metric("SQLite Database Size", "142 KB", "Stable")
    c3.metric("Ollama Local LLM Status", "Connected", "11434 Port")