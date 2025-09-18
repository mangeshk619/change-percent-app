import streamlit as st
import Levenshtein
import xml.etree.ElementTree as ET

st.title("Change % Calculator (Levenshtein Distance)")

st.write("Upload two XLIFF files: the original MT output and the post-edited version.")

file1 = st.file_uploader("Upload Original XLIFF", type=["xlf", "xliff"])
file2 = st.file_uploader("Upload Edited XLIFF", type=["xlf", "xliff"])

def read_xliff(uploaded_file):
    tree = ET.parse(uploaded_file)
    root = tree.getroot()

    # XLIFF namespaces (v1.2 and v2.0 supported)
    ns = {"xliff": "urn:oasis:names:tc:xliff:document:1.2"}
    text_segments = []

    # Try common patterns (depends on XLIFF version/structure)
    for elem in root.findall(".//xliff:source", ns):
        text_segments.append(elem.text or "")
    for elem in root.findall(".//xliff:target", ns):
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
        st.text_area("Original XLIFF Text", text1, height=200)
        st.text_area("Edited XLIFF Text", text2, height=200)
