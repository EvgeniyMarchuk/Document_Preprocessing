import streamlit as st
import os
import shutil
from parse import Parser

# Заголовок приложения
st.title("Обработка файлов в .md формат")
st.subheader("Выберите режим обработки файла:")

# Колонки для кнопок выбора режима
col1, col2 = st.columns(2)

with col1:
    if st.button("PDF без изображений (MegaParse)", key="pdf_text_megaparse"):
        st.session_state["mode"] = "pdf_text_megaparse"
        st.write("Выбран режим: PDF без изображений (MegaParse)")

    if st.button("DOCX без изображений", key="docx_text_only"):
        st.session_state["mode"] = "docx_text_only"
        st.write("Выбран режим: DOCX без изображений")

    if st.button("PDF без изображений (Docling)", key="pdf_text_docling"):
        st.session_state["mode"] = "pdf_text_docling"
        st.write("Выбран режим: PDF без изображений (Docling)")

with col2:
    if st.button("PDF с изображениями (MegaParse)", key="pdf_images_megaparse"):
        st.session_state["mode"] = "pdf_images_megaparse"
        st.write("Выбран режим: PDF с изображениями (MegaParse)")

    if st.button("DOCX с изображениями", key="docx_with_images"):
        st.session_state["mode"] = "docx_with_images"
        st.write("Выбран режим: DOCX с изображениями")

    if st.button("PDF с изображениями (Docling)", key="pdf_images_docling"):
        st.session_state["mode"] = "pdf_images_docling"
        st.write("Выбран режим: PDF с изображениями (Docling)")

# Инициализация session_state для отслеживания обработанных файлов
if "processed_files" not in st.session_state:
    st.session_state["processed_files"] = set()

# Файлы для загрузки
uploaded_files = st.file_uploader("Upload your files", accept_multiple_files=True)

if "quantity_of_documents" not in st.session_state:
    st.session_state["quantity_of_documents"] = len(uploaded_files)


if len(uploaded_files) != st.session_state["quantity_of_documents"]:
    output_dir = "processed_files"
    os.makedirs(output_dir, exist_ok=True)

    input_dir = "uploaded_files"
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
    
    st.session_state["processed_files"] = set()
    del st.session_state["quantity_of_documents"]


if uploaded_files:
    if "mode" not in st.session_state:
        st.warning("Сначала выберите режим обработки.")
    else:
        mode = st.session_state["mode"]
        st.write(f"{len(uploaded_files)} файл(ов) обрабатывается в режиме: {mode}")

        # Папка для сохранения обработанных файлов
        output_dir = "processed_files"
        os.makedirs(output_dir, exist_ok=True)

        # Папка для сохранения загруженных на сайт файлов
        input_dir = "uploaded_files"
        os.makedirs(input_dir, exist_ok=True)

        parser = Parser(mode)

        for file in uploaded_files:
            file_name = file.name

            # Проверяем, был ли файл уже обработан
            if file_name in st.session_state["processed_files"]:
                continue

            st.write(f"Обрабатывается файл: {file_name}")

            # Чтение содержимого файла в байтах
            file_bytes = file.read()

            # Сохраняем файл во временную директорию
            with open(os.path.join(input_dir, file_name), "wb") as f:
                f.write(file_bytes)

            # Обработка файла
            parser.convert(file_name)

            # Отмечаем файл как обработанный
            st.session_state["processed_files"].add(file_name)

            # Архивация результатов 
            zip_path = shutil.make_archive(f"parsed_{file_name}", "zip", root_dir=output_dir, base_dir=f'parsed_{file_name.rpartition(".")[0]}')
            
            # Скачивание архива
            st.success("Файл успешно обработан!")
            st.download_button(
                label="Загрузить ZIP архив",
                data=open(zip_path, "rb").read(),
                file_name=f"parsed_{file_name}.zip",
                mime="application/zip"
            )

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
