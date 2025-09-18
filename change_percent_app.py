import streamlit as st
import Levenshtein

st.title("Change % Calculator (Levenshtein Distance)")

st.write("Upload two text files: the original MT output and the post-edited version.")

file1 = st.file_uploader("Upload Original File", type=["txt"])
file2 = st.file_uploader("Upload Edited File", type=["txt"])

if file1 and file2:
    text1 = file1.read().decode("utf-8")
    text2 = file2.read().decode("utf-8")

    distance = Levenshtein.distance(text1, text2)
    change_percent = (distance / max(1, len(text1))) * 100

    st.subheader("Results")
    st.write(f"Levenshtein Distance: **{distance} edits**")
    st.write(f"Change %: **{change_percent:.2f}%**")

    with st.expander("Show Uploaded Texts"):
        st.text_area("Original Text", text1, height=150)
        st.text_area("Edited Text", text2, height=150)
