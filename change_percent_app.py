import streamlit as st
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
import difflib

st.set_page_config(page_title="MT vs PE Change % Calculator", layout="wide")
st.title("📊 MT vs PE Change % Calculator")

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

            # Extract source segments for strict validation
            mt_sources = read_xliff_text(mt_bytes, tag="source")
            pe_sources = read_xliff_text(pe_bytes, tag="source")

            if mt_sources != pe_sources:
                st.error("❌ MT and PE files have mismatched source segments. Calculation stopped.")
            else:
                # Extract target texts
                mt_targets = read_xliff_text(mt_bytes, tag="target")
                pe_targets = read_xliff_text(pe_bytes, tag="target")

                # Combine all targets for overall change %
                mt_text = " ".join(mt_targets)
                pe_text = " ".join(pe_targets)

                if not mt_text or not pe_text:
                    st.warning("One of the files has no target text. Check the file contents.")
                else:
                    change_percent = 100 - levenshtein_ratio(mt_text, pe_text)

                    # Colored badge display
                    if change_percent < 20:
                        st.success(f"✅ Change %: {change_percent:.2f}% – Minimal editing needed")
                    elif change_percent < 50:
                        st.warning(f"⚠️ Change %: {change_percent:.2f}% – Moderate editing required")
                    else:
                        st.error(f"❌ Change %: {change_percent:.2f}% – Heavy post-editing required")

                    # Summary Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total Segments", len(mt_sources))
                    col2.metric("MT Target Words", len(mt_text.split()))
                    col3.metric("PE Target Words", len(pe_text.split()))
                    col4.metric("Segment Difference", abs(len(mt_targets)-len(pe_targets)))

        except Exception as ex:
            st.error(f"⚠️ Error: {ex}")
