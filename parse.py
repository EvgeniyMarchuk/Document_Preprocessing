from pathlib import Path
from typing import Optional
import shutil
import re
import sys
import os


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
    def convert(self, file_path, output_path='./'):
        match file_path.split('.')[-1]:
            case 'pdf':
                self.pdf_parse(file_path, output_path)
            case 'docx':
                self.docx_parse(file_path, output_path)
    
    def pdf_parse(self, file_path, output_path='./'):  
        input_doc_path = Path(file_path)
        output_dir = Path(output_path) / f"parsed_{input_doc_path.name}"

        temp_input_doc_path = input_doc_path.parent / 'temp_file.pdf'
        shutil.copy(input_doc_path, temp_input_doc_path)

        doc_converter = self._docling_parse()

        conv_res = doc_converter.convert(temp_input_doc_path)
        temp_input_doc_path.unlink()

        output_dir.mkdir(parents=True, exist_ok=True)

        md_filename = output_dir / f"{input_doc_path.name}.md"
        images_dir = output_dir / "images/"
        images_dir.mkdir(parents=True, exist_ok=True)
        conv_res.document.save_as_markdown(md_filename, artifacts_dir=images_dir, image_mode=ImageRefMode.REFERENCED)

        self._make_zip(output_dir)
        
    def docx_parse(self, file_path, output_path='./'):

        input_doc_path = Path(file_path)
        output_dir = Path(output_path) / f"parsed_{input_doc_path.name}"

        doc_converter = self._docling_parse()
        conv_res = doc_converter.convert(input_doc_path)

        output_dir.mkdir(parents=True, exist_ok=True)

        images_list = self._get_images(output_dir, conv_res.document)

        md_filename = output_dir / f"{input_doc_path.name}.md"

        md = MarkItDown()
        parsed_text = md.convert(input_doc_path.as_posix()).text_content
        result = self._insert_ref(parsed_text, images_list)

        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write(result)        
        
        self._make_zip(output_dir)
        
    def _insert_ref(self, text, images_list):
        res = ''
        pattern = r"\(data:image\/([a-zA-Z]+);base64\.\.\.\)"
        last_pos = 0
        for ind, match in enumerate(re.finditer(pattern, text)):
            # print(match.group())
            # print(parsed_text[match.start():match.end()])
            res += text[last_pos:match.start()] + f'({images_list[ind]})'
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

    def _make_zip(self, output_dir):
        shutil.make_archive(output_dir, 'zip', root_dir=output_dir.parent, base_dir=output_dir.name)
        shutil.rmtree(output_dir)

    def _docling_parse(self):
        pipeline_options = PdfPipelineOptions()
        pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
        pipeline_options.generate_picture_images = True

        return DocumentConverter(
                    format_options={
                        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                    }
                )
    
if __name__ == "__main__":
    list = ['./raw_files/for_parse/4.0 Ремонт кабельных линий (ЦУ).docx',
            './raw_files/for_parse/Опл001_Опросный лист ОЛ24.001.1012.050821 (Вездеход на ко.pdf', 
            './raw_files/for_parse/ТП_лодка.pdf',
            './raw_files/for_parse/45160618.docx']
    parse = Parser()
    for name in list:
        parse.convert(name)