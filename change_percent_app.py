import streamlit as st
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
import difflib

st.title("📊 MT vs PE Change % Calculator (Updated)")

def read_xliff_text(file_bytes):
    """Extract all target text from XLIFF (handles zip, plain XML, and namespaces)"""
    text = ""
    if not file_bytes:
        return text
    try:
        # Try as zip
        with zipfile.ZipFile(BytesIO(file_bytes)) as z:
            for name in z.namelist():
                if name.endswith(".xlf") or name.endswith(".xliff"):
                    with z.open(name) as f:
                        tree = ET.parse(f)
                        root = tree.getroot()
                        # Extract all <target> text
                        for t in root.findall(".//{*}target"):
                            if t.text:
                                text += t.text + " "
    except zipfile.BadZipFile:
        # Not a zip, treat as plain XML
        try:
            root = ET.fromstring(file_bytes)
            for t in root.findall(".//{*}target"):
                if t.text:
                    text += t.text + " "
        except ET.ParseError:
            # Fallback: decode all text
            text = file_bytes.decode("utf-8", errors="ignore")
    return text.strip()

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
            # Read uploaded files as bytes
            mt_bytes = mt_file.read()
            pe_bytes = pe_file.read()

            mt_text = read_xliff_text(mt_bytes)
            pe_text = read_xliff_text(pe_bytes)

            # Debug info
            st.write("MT text length:", len(mt_text))
            st.write("PE text length:", len(pe_text))

            if not mt_text or not pe_text:
                st.warning("One of the files has no target text. Check the file contents.")
            else:
                change_percent = 100 - levenshtein_ratio(mt_text, pe_text)
                st.success(f"✅ Change % between MT and PE: {change_percent:.2f}%")
        except Exception as ex:
            st.error(f"⚠️ Error: {ex}")
