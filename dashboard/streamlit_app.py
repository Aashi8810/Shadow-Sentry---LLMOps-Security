import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Shadow Sentry Control Panel", layout="wide")
st.title("🛡️ Shadow Sentry — LLM Security Gateway")

API_BASE = "http://127.0.0.1:8000/v1/admin"

try:
    stats_resp = requests.get(f"{API_BASE}/stats").json()
    logs_resp = requests.get(f"{API_BASE}/logs").json()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total System Traffic", stats_resp.get("total_requests", 0))
    col2.metric("Blocked Attack Vectors", stats_resp.get("blocked_count", 0), delta_color="inverse")
    col3.metric("Current Mitigation Integrity", "Active Level 100%")
    
    st.subheader("⚠️ Threat Vector Risk Breakdown")
    if stats_resp.get("by_risk_level"):
        df_stats = pd.DataFrame(list(stats_resp["by_risk_level"].items()), columns=["Risk Tier", "Incident Count"])
        st.bar_chart(data=df_stats, x="Risk Tier", y="Incident Count")
        
    st.subheader("🕵️ Live Request Audit Stream")
    if logs_resp:
        df_logs = pd.DataFrame(logs_resp)
        st.dataframe(df_logs[["timestamp", "user_id", "endpoint", "risk_score", "risk_level", "blocked", "detection_reasons"]])
except Exception as e:
    st.error(f"Failed connection to gateway framework endpoint: {e}")