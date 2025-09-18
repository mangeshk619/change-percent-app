import streamlit as st
import Levenshtein
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO

st.title("Change % Calculator (Levenshtein Distance)")

st.write("Upload XLIFF (.xlf/.xliff) or MXLFF (.mxliff) files.")

file1 = st.file_uploader("Upload Original File", type=["xlf", "xliff", "mxliff"])
file2 = st.file_uploader("Upload Edited File", type=["xlf", "xliff", "mxliff"])

def is_zip(file):
    start = file.read(4)
    file.seek(0)
    return start == b'PK\x03\x04'

def read_xliff(uploaded_file):
    if uploaded_file.name.endswith(".mxliff") and is_zip(uploaded_file):
        text_segments = []
        z = zipfile.ZipFile(BytesIO(uploaded_file.read()))
        for name in z.namelist():
            if name.endswith((".xlf", ".xliff")):
                with z.open(name) as f:
                    text_segments.append(read_xlf_content(f))
        return "\n".join(text_segments)
    else:
        uploaded_file.seek(0)  # reset pointer
        return read_xlf_content(uploaded_file)

def read_xlf_content(f):
    tree = ET.parse(f)
    root = tree.getroot()
    ns = {"xliff": "urn:oasis:names:tc:xliff:document:1.2"}
    text_segments = []
    for elem in root.findall(".//xliff:target", ns):  # target only
        text_segments.append(elem.text or "")
    return "\n".join(text_segments)

if file1 and file2:
    text1 = read_xliff(file1)
    text2 = read_xliff(file2)

    distance = Levenshtein.distance(text1, text2)
    change_percent = (distance / max(1, len(text1))) * 100

    st.subheader("Results")
    st.write(f"Levenshtein Distance: **{distance} edits**")
    st.write(f"Change %: **{change_percent:.2f}%**")

    with st.expander("Show Extracted Texts"):
        st.text_area("Original Text", text1, height=200)
        st.text_area("Edited Text", text2, height=200)
