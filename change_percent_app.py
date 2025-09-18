import streamlit as st
import Levenshtein
import docx
import pandas as pd

st.title("Change % Calculator (Levenshtein Distance)")

st.write("Upload two files (TXT, DOCX, or XLSX): the original MT output and the post-edited version.")

file1 = st.file_uploader("Upload Original File", type=["txt", "docx", "xlsx"])
file2 = st.file_uploader("Upload Edited File", type=["txt", "docx", "xlsx"])

def read_file(uploaded_file):
    if uploaded_file.name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8")

    elif uploaded_file.name.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])

    elif uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file, dtype=str)
        return "\n".join(df.astype(str).fillna("").values.flatten())

    else:
        return ""

if file1 and file2:
    text1 = read_file(file1)
    text2 = read_file(file2)

    distance = Levenshtein.distance(text1, text2)
    change_percent = (distance / max(1, len(text1))) * 100

    st.subheader("Results")
    st.write(f"Levenshtein Distance: **{distance} edits**")
    st.write(f"Change %: **{change_percent:.2f}%**")

    with st.expander("Show Uploaded Texts"):
        st.text_area("Original Text", text1, height=150)
        st.text_area("Edited Text", text2, height=150)
