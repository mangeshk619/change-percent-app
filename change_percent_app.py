import streamlit as st
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
import difflib
import pandas as pd
from datetime import datetime

# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(page_title="MT vs PE Change % Calculator", layout="wide")
st.title("📊 MT vs PE Change % Calculator")

# -----------------------------
# Initialize session state for history
# -----------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# -----------------------------
# Helper functions
# -----------------------------
def read_xliff_text(file_bytes, tag="target"):
    """Extract all <source> or <target> text from XLIFF (handles zip, plain XML, namespaces)."""
    text = []
    if not file_bytes:
        return text
    try:
        with zipfile.ZipFile(BytesIO(file_bytes)) as z:
            for name in z.namelist():
                if name.endswith((".xlf", ".xliff", ".mxliff")):
                    with z.open(name) as f:
                        tree = ET.parse(f)
                        root = tree.getroot()
                        for t in root.findall(f".//{{*}}{tag}"):
                            if t.text:
                                text.append(t.text.strip())
    except zipfile.BadZipFile:
        try:
            root = ET.fromstring(file_bytes)
            for t in root.findall(f".//{{*}}{tag}"):
                if t.text:
                    text.append(t.text.strip())
        except ET.ParseError:
            pass
    return text

def levenshtein_ratio(s1, s2):
    """Compute similarity ratio"""
    return difflib.SequenceMatcher(None, s1, s2).ratio() * 100

# -----------------------------
# File upload
# -----------------------------
st.markdown("Upload the **MT XLIFF** and **PE XLIFF** files to calculate change %:")

mt_file = st.file_uploader("Upload MT XLIFF", type=["xlf","xliff","mxliff"])
pe_file = st.file_uploader("Upload PE XLIFF", type=["xlf","xliff","mxliff"])

# -----------------------------
# Compute Change %
# -----------------------------
if st.button("Compute Change %"):
    if not mt_file or not pe_file:
        st.error("Please upload both MT and PE XLIFF files.")
    else:
        try:
            mt_bytes = mt_file.read()
            pe_bytes = pe_file.read()

            # Extract sources for validation
            mt_sources = read_xliff_text(mt_bytes, tag="source")
            pe_sources = read_xliff_text(pe_bytes, tag="source")

            if mt_sources != pe_sources:
                st.error("❌ MT and PE files have mismatched source segments. Calculation stopped.")
            else:
                # Extract targets
                mt_targets = read_xliff_text(mt_bytes, tag="target")
                pe_targets = read_xliff_text(pe_bytes, tag="target")

                mt_text = " ".join(mt_targets)
                pe_text = " ".join(pe_targets)

                if not mt_text or not pe_text:
                    st.warning("One of the files has no target text. Check the file contents.")
                else:
                    change_percent = 100 - levenshtein_ratio(mt_text, pe_text)

                    # Colored badges
                    if change_percent < 20:
                        st.error(f"🔴 Change %: {change_percent:.2f}% – Minimal editing")
                        category = "Minimal editing"
                    elif change_percent < 50:
                        st.warning(f"🟡 Change %: {change_percent:.2f}% – Moderate editing")
                        category = "Moderate editing"
                    else:
                        st.success(f"🟢 Change %: {change_percent:.2f}% – Heavy post-editing")
                        category = "Heavy post-editing"

                    # Summary metrics
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Segments", len(mt_sources))
                    col2.metric("MT Target Words", len(mt_text.split()))
                    col3.metric("PE Target Words", len(pe_text.split()))

                    # Timestamp for report
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    safe_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                    # Prepare report data
                    report_data = {
                        "Metric": [
                            "MT File Name",
                            "PE File Name",
                            "Total Segments",
                            "MT Target Words",
                            "PE Target Words",
                            "Change %",
                            "Category",
                            "Analysis Timestamp"
                        ],
                        "Value": [
                            mt_file.name,
                            pe_file.name,
                            len(mt_sources),
                            len(mt_text.split()),
                            len(pe_text.split()),
                            f"{change_percent:.2f}%",
                            category,
                            timestamp
                        ]
                    }
                    df = pd.DataFrame(report_data)

                    # Export Excel (fallback to CSV if openpyxl missing)
                    try:
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine="openpyxl") as writer:
                            df.to_excel(writer, index=False, sheet_name="QA Report")
                        st.download_button(
                            label="📥 Download Report (Excel)",
                            data=output.getvalue(),
                            file_name=f"QA_Report_{safe_timestamp}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except ImportError:
                        csv_output = df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label="📥 Download Report (CSV)",
                            data=csv_output,
                            file_name=f"QA_Report_{safe_timestamp}.csv",
                            mime="text/csv"
                        )

                    # -----------------------------
                    # Update session history
                    # -----------------------------
                    st.session_state.history.append({
                        "MT File": mt_file.name,
                        "PE File": pe_file.name,
                        "Total Segments": len(mt_sources),
                        "MT Words": len(mt_text.split()),
                        "PE Words": len(pe_text.split()),
                        "Change %": f"{change_percent:.2f}%",
                        "Category": category,
                        "Timestamp": timestamp
                    })

# -----------------------------
# Display upload & analysis history
# -----------------------------
if st.session_state.history:
    st.markdown("### 🕒 Upload & Analysis History")
    history_df = pd.DataFrame(st.session_state.history[::-1])  # recent first
    st.dataframe(history_df)
