import streamlit as st
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
import difflib
import pandas as pd

st.title("📊 MT vs PE Change % Calculator (Mismatch Target View)")

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
    return difflib.SequenceMatcher(None, s1, s2).ratio() * 100

st.markdown("Upload the **MT XLIFF** and **PE XLIFF** files to calculate change %:")

mt_file = st.file_uploader("Upload MT XLIFF", type=["xlf","xliff","mxliff"])
pe_file = st.file_uploader("Upload PE XLIFF", type=["xlf","xliff","mxliff"])

if st.button("Compute Change %"):
    if not mt_file or not pe_file:
        st.error("Please upload both MT and PE XLIFF files.")
    else:
        try:
            mt_bytes = mt_file.read()
            pe_bytes = pe_file.read()

            # Extract source segments for validation
            mt_sources = read_xliff_text(mt_bytes, tag="source")
            pe_sources = read_xliff_text(pe_bytes, tag="source")

            # Strict validation: stop if any mismatch in source
            if mt_sources != pe_sources:
                st.error("❌ MT and PE files have mismatched source segments. Calculation stopped.")
            else:
                # Extract target segments
                mt_targets = read_xliff_text(mt_bytes, tag="target")
                pe_targets = read_xliff_text(pe_bytes, tag="target")

                # Build mismatch table
                max_len = max(len(mt_targets), len(pe_targets))
                rows = []
                for i in range(max_len):
                    mt_t = mt_targets[i] if i < len(mt_targets) else ""
                    pe_t = pe_targets[i] if i < len(pe_targets) else ""
                    if mt_t != pe_t:
                        rows.append({
                            "Segment #": i+1,
                            "MT Target": mt_t,
                            "PE Target": pe_t
                        })

                if rows:
                    df_mismatch = pd.DataFrame(rows)
                    st.subheader("⚠️ Mismatched Target Segments")
                    st.table(df_mismatch)  # only mismatches shown
                else:
                    st.success("✅ No mismatched target segments found.")

                # Compute overall change %
                mt_text = " ".join(mt_targets)
                pe_text = " ".join(pe_targets)
                change_percent = 100 - levenshtein_ratio(mt_text, pe_text)
                st.success(f"✅ Change % between MT and PE: {change_percent:.2f}%")

        except Exception as ex:
            st.error(f"⚠️ Error: {ex}")
