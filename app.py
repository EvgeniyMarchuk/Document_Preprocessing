import streamlit as st
import os
import shutil
from parser_megaparse import Processing
import sys

st.title("File Preprocessing")
st.write("Upload your files, process them, and download the results as a ZIP archive.")

uploaded_files = st.file_uploader("Upload your files", accept_multiple_files=True)
if uploaded_files:
    print(f"{uploaded_files = }")
    # Папка для сохранения обработанных файлов
    output_dir = "processed_files"
    os.makedirs(output_dir, exist_ok=True)

    # очистка папки от сторонних файлов
    for file_name in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file_name)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # Удаление файла или ссылки
            elif os.path.isdir(file_path):  
                shutil.rmtree(file_path)  # Удаление директории
        except Exception as e:
            st.error(f"Failed to delete {file_path}. Reason: {e}")

    st.write(f"{len(uploaded_files)} files are processing now:")
    for file in uploaded_files:
        st.write(file.name)
        Processing([file.name])

    # Архивация результатов
    zip_path = shutil.make_archive("processed_files", "zip", output_dir)

    # Скачивание архива
    st.success("Files processed successfully!")
    st.download_button(
        label="Download ZIP Archive",
        data=open(zip_path, "rb").read(),
        file_name="processed_files.zip",
        mime="application/zip"
    )
