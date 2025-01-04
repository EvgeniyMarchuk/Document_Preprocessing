import streamlit as st
import os
import shutil
from parse import Parser


st.title("File Preprocessing")
st.subheader("Выберите режим обработки файла:")

col1, col2 = st.columns(2)

with col1:
    if st.button("PDF with Text Layer", key="pdf_with_text_layer"):
        st.session_state["mode"] = "pdf_with_text_layer"
        st.write("Выбран режим: PDF with Text Layer")

    if st.button("DOCX/DOC (Text and Tables Only)", key="doc_text_only"):
        st.session_state["mode"] = "doc_text_only"
        st.write("Выбран режим: DOCX/DOC (Text and Tables Only)")

with col2:
    if st.button("PDF without Text Layer", key="pdf_without_text_layer"):
        st.session_state["mode"] = "pdf_without_text_layer"
        st.write("Выбран режим: PDF without Text Layer")

    if st.button("DOCX/DOC (With Images and Tables)", key="doc_with_images"):
        st.session_state["mode"] = "doc_with_images"
        st.write("Выбран режим: DOCX/DOC (With Images and Tables)")

uploaded_files = st.file_uploader("Upload your files", accept_multiple_files=True)
if uploaded_files:
    if "mode" not in st.session_state:
        st.warning("Сначала выберите режим обработки.")
    else:
        mode = st.session_state["mode"]
        st.write(f"{len(uploaded_files)} файл(ов) обрабатывается в режиме: {mode}")

        # Папка для сохранения обработанных файлов
        output_dir = f"processed_files"
        os.makedirs(output_dir, exist_ok=True)

        # Папка для сохранения загруженных на сайт файлов
        input_dir = f"uploaded_files"
        os.makedirs(input_dir, exist_ok=True)

        # очистка папок от сторонних файлов
        for file_name in os.listdir(output_dir):
            file_path = os.path.join(output_dir, file_name)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # Удаление файла или ссылки
                elif os.path.isdir(file_path):  
                    shutil.rmtree(file_path)  # Удаление директории
            except Exception as e:
                st.error(f"Failed to delete {file_path}. Reason: {e}")
        for file_name in os.listdir(input_dir):
            file_path = os.path.join(input_dir, file_name)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # Удаление файла или ссылки
                elif os.path.isdir(file_path):  
                    shutil.rmtree(file_path)  # Удаление директории
            except Exception as e:
                st.error(f"Failed to delete {file_path}. Reason: {e}")

        parser = Parser(st.session_state['mode'])
        for file in uploaded_files:
            file_name = file.name
            st.write(f"Обрабатывается файл: {file_name}")

            # Чтение содержимого файла
            file_bytes = file.read()  # Считывает все содержимое файла в байтах

            with open(os.path.join("uploaded_files", file_name), "wb") as f:
                f.write(file_bytes)
            
            #############################################################
            # TODO: тут добавить разные режимы в функцию Processing,    #
            # т.к. пока что только для pdf с Megaparse работает         #
            #############################################################
            parser.convert(file.name)

        # Архивация результатов
        zip_path = shutil.make_archive(f"processed_{mode}_files", "zip", output_dir)

        # Скачивание архива
        st.success("Файлы успешно обработаны!")
        st.download_button(
            label="Загрузить ZIP архив",
            data=open(zip_path, "rb").read(),
            file_name=f"processed_{mode}_files.zip",
            mime="application/zip"
        )