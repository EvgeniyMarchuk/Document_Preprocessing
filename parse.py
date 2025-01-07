from pathlib import Path
from typing import Optional
import shutil
import re
import sys
import os
sys.path.insert(0, os.path.abspath("./MegaParse/libs"))

from megaparse.src.megaparse.megaparse import MegaParse
from megaparse.src.megaparse.parser.megaparse_vision import MegaParseVision
from langchain_openai import ChatOpenAI

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc.labels import DocItemLabel
from docling_core.types.doc import DoclingDocument, ImageRefMode, PictureItem

from markitdown import MarkItDown


IMAGE_RESOLUTION_SCALE = 2.0

DEFAULT_EXPORT_LABELS = {
    DocItemLabel.TITLE,
    DocItemLabel.DOCUMENT_INDEX,
    DocItemLabel.SECTION_HEADER,
    DocItemLabel.PARAGRAPH,
    DocItemLabel.TABLE,
    DocItemLabel.PICTURE,
    DocItemLabel.FORMULA,
    DocItemLabel.CHECKBOX_UNSELECTED,
    DocItemLabel.CHECKBOX_SELECTED,
    DocItemLabel.TEXT,
    DocItemLabel.LIST_ITEM,
    DocItemLabel.CODE,
    DocItemLabel.REFERENCE,
}


def save_as_markdown(
    self,
    filename: Path,
    artifacts_dir: Optional[Path] = None,
    delim: str = "\n",
    from_element: int = 0,
    to_element: int = sys.maxsize,
    labels: set[DocItemLabel] = DEFAULT_EXPORT_LABELS,
    strict_text: bool = False,
    image_placeholder: str = "<!-- image -->",
    image_mode: ImageRefMode = ImageRefMode.PLACEHOLDER,
    indent: int = 4,
    text_width: int = -1,
    page_no: Optional[int] = None,
):
    """Save to markdown."""
    artifacts_dir, reference_path = self._get_output_paths(filename, artifacts_dir)

    if image_mode == ImageRefMode.REFERENCED:
        os.makedirs(artifacts_dir, exist_ok=True)

    new_doc = self._make_copy_with_refmode(
        artifacts_dir, image_mode, reference_path=reference_path
    )

    md_out = new_doc.export_to_markdown(
        delim=delim,
        from_element=from_element,
        to_element=to_element,
        labels=labels,
        strict_text=strict_text,
        image_placeholder=image_placeholder,
        image_mode=image_mode,
        indent=indent,
        text_width=text_width,
        page_no=page_no,
    )

    with open(filename, "w", encoding='utf-8') as fw: #добавил encoding
        fw.write(md_out)

DoclingDocument.save_as_markdown = save_as_markdown


class Parser():
    def __init__(self, mode):
        match mode:
            case 'doc_with_images':
                self.md = MarkItDown()
                self.doc_converter = self._docling_parser()
                self.convert = self.docx_with_img
            case 'doc_text_only':
                self.md = MarkItDown()
                self.convert = self.docx_text_only
            case 'pdf_with_text_layer':
                self.megaparse = self._megaparse_parser()
                self.convert = self.pdf_text_only
            case 'pdf_without_text_layer':
                self.megaparse = self._megaparse_parser()
                self.doc_converter = self._docling_parser()
                self.convert = self.pdf_with_img
            case 'pdf_with_images_docling':
                self.doc_converter = self._docling_parser()
                self.convert = self.pdf_with_img_docling
            case 'pdf_text_only_docling':
                self.doc_converter = self._docling_parser(img_flag=False)
                self.convert = self.pdf_text_only_docling

    def pdf_text_only_docling(self, name_of_file):
        input_doc_path = Path(f"./uploaded_files/{name_of_file}")
        output_dir = Path(f"./processed_files/parsed_{input_doc_path.name[:-4]}")

        temp_input_doc_path = input_doc_path.parent / 'temp_file.pdf'
        shutil.copy(input_doc_path, temp_input_doc_path)

        conv_res = self.doc_converter.convert(temp_input_doc_path)
        temp_input_doc_path.unlink()

        output_dir.mkdir(parents=True, exist_ok=True)

        md_file_path = output_dir / f"{input_doc_path.name[:-3]}md"
        conv_res.document.save_as_markdown(md_file_path)
# Добавить метод, который будет убирать пометки о наличии картинок

    def pdf_with_img_docling(self, name_of_file):
        input_doc_path = Path(f"./uploaded_files/{name_of_file}")
        output_dir = Path(f"./processed_files/parsed_{input_doc_path.name[:-4]}")

        temp_input_doc_path = input_doc_path.parent / 'temp_file.pdf'
        shutil.copy(input_doc_path, temp_input_doc_path)

        conv_res = self.doc_converter.convert(temp_input_doc_path)
        temp_input_doc_path.unlink()

        output_dir.mkdir(parents=True, exist_ok=True)

        md_file_path = output_dir / f"{input_doc_path.name[:-3]}md"
        images_dir = output_dir / "images/"
        images_dir.mkdir(parents=True, exist_ok=True)
        conv_res.document.save_as_markdown(md_file_path, artifacts_dir=images_dir, image_mode=ImageRefMode.REFERENCED)

    def pdf_text_only(self, name_of_file):
        self.megaparse.load(f"./uploaded_files/{name_of_file}")

        output_dir = Path(f"./processed_files/parsed_{name_of_file[:-4]}")
        output_dir.mkdir(parents=True, exist_ok=True)
        # Сохранение результата в Markdown
        md_file_path = output_dir / f"{name_of_file[:-3]}md"
        md_file_path = md_file_path.as_posix()
        self.megaparse.save(md_file_path)

    def pdf_with_img(self, name_of_file):
        input_doc_path = Path(f"./uploaded_files/{name_of_file}")
        output_dir = Path(f"./processed_files/parsed_{input_doc_path.name[:-4]}")
        temp_input_doc_path = input_doc_path.parent / 'temp_file.pdf'
        shutil.copy(input_doc_path, temp_input_doc_path)

        response = self.megaparse.load(f"./uploaded_files/{name_of_file}")
        conv_res = self.doc_converter.convert(temp_input_doc_path)
        temp_input_doc_path.unlink()

        output_dir.mkdir(parents=True, exist_ok=True)
        images_list = self._get_images(output_dir, conv_res.document)

        result = self._insert_ref(response, images_list, pattern = r"!\[Image\][^\s]*", prefix='![Image]')
        md_file_path = output_dir / f"{input_doc_path.name[:-3]}md"
        with open(md_file_path, 'w', encoding='utf-8') as f:
            f.write(result)   
        
    def docx_with_img(self, name_of_file):
        input_doc_path = Path(f"./uploaded_files/{name_of_file}")
        output_dir = Path(f"./processed_files/parsed_{input_doc_path.name.rpartition('.')[0]}")

        conv_res = self.doc_converter.convert(input_doc_path)
        parsed_text = self.md.convert(input_doc_path.as_posix()).text_content
        
        output_dir.mkdir(parents=True, exist_ok=True)
        images_list = self._get_images(output_dir, conv_res.document)

        result = self._insert_ref(parsed_text, images_list, pattern=r"\(data:image\/([a-zA-Z]+);base64\.\.\.\)")
        md_file_path = output_dir / f"{input_doc_path.name.rpartition('.')[0]}.md"
        with open(md_file_path, 'w', encoding='utf-8') as f:
            f.write(result)        

    def docx_text_only(self, name_of_file):
        input_doc_path = Path(f"./uploaded_files/{name_of_file}")
        output_dir = Path(f"./processed_files/parsed_{input_doc_path.name.rpartition('.')[0]}")

        parsed_text = self.md.convert(input_doc_path.as_posix()).text_content

        output_dir.mkdir(parents=True, exist_ok=True)

        md_file_path = output_dir / f"{input_doc_path.name.rpartition('.')[0]}.md"
        with open(md_file_path, 'w', encoding='utf-8') as f:
            f.write(parsed_text)        
            
    def _insert_ref(self, text, images_list, pattern, prefix=''):
        res = ''
        last_pos = 0
        n = len(images_list)
        for ind, match in enumerate(re.finditer(pattern, text)):
            # print(match.group())
            # print(parsed_text[match.start():match.end()])
            if ind >= n:
                res += text[last_pos:]
                break
            res += text[last_pos:match.start()] + f'{prefix}({images_list[ind]})'
            last_pos = match.end()
        return res
    
    def _get_images(self, output_dir, document):
        res = []
        picture_counter = 0
        images_dir = output_dir / 'images'
        images_dir.mkdir(parents=True, exist_ok=True)
        for element, _level in document.iterate_items():
            if isinstance(element, PictureItem):
                picture_counter += 1
                element_image_filename = (
                    images_dir / f"{picture_counter}.png"
                )
                res.append(Path('images/') / f'{picture_counter}.png')
                with element_image_filename.open("wb") as fp:
                    element.get_image(document).save(fp, "PNG")
        
        return res

    # def _make_zip(self, output_dir):
    #     shutil.make_archive(output_dir, 'zip', root_dir=output_dir.parent, base_dir=output_dir.name)
    #     shutil.rmtree(output_dir)

    def _megaparse_parser(self):
        os.environ["OPENAI_API_KEY"] = "YOR_API_KEY"

        model = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))  # Подключаем модель через API

        parser = MegaParseVision(model=model)

        return MegaParse(parser)

    def _docling_parser(self, img_flag=True):
        pipeline_options = PdfPipelineOptions()
        if img_flag:
            pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
            pipeline_options.generate_picture_images = True

        return DocumentConverter(
                    format_options={
                        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                    }
                )
