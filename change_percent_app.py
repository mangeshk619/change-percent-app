import streamlit as st
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
import difflib
import pandas as pd

st.title("📊 MT vs PE Change % Calculator (Stable Cloud Version)")

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

            # Extract source segments
            mt_sources = read_xliff_text(mt_bytes, tag="source")
            pe_sources = read_xliff_text(pe_bytes, tag="source")

            # Build comparison table using emojis
            max_len = max(len(mt_sources), len(pe_sources))
            rows = []
            for i in range(max_len):
                mt_seg = mt_sources[i] if i < len(mt_sources) else ""
                pe_seg = pe_sources[i] if i < len(pe_sources) else ""
                match = "✔️" if mt_seg == pe_seg else "❌"
                rows.append({
                    "Segment #": i+1,
                    "MT Source": mt_seg,
                    "PE Source": pe_seg,
                    "Match": match
                })

            df = pd.DataFrame(rows)

            st.subheader("Source Segment Comparison (✔️ = match, ❌ = mismatch)")
            st.table(df)  # stable static table for Streamlit Cloud

            # Strict validation: stop if any mismatch
            if any(df["Match"] == "❌"):
                st.error("❌ MT and PE files have mismatched source segments. Calculation stopped.")
            else:
                mt_text = " ".join(read_xliff_text(mt_bytes, tag="target"))
                pe_text = " ".join(read_xliff_text(pe_bytes, tag="target"))

                st.write("MT target text length:", len(mt_text))
                st.write("PE target text length:", len(pe_text))

                if not mt_text or not pe_text:
                    st.warning("One of the files has no target text. Check the file contents.")
                else:
                    change_percent = 100 - levenshtein_ratio(mt_text, pe_text)
                    st.success(f"✅ Change % between MT and PE: {change_percent:.2f}%")
        except Exception as ex:
            st.error(f"⚠️ Error: {ex}")
