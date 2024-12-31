import sys
import os
sys.path.insert(0, os.path.abspath("./MegaParse/libs"))

from megaparse.src.megaparse.megaparse import MegaParse
from megaparse.src.megaparse.parser.megaparse_vision import MegaParseVision
from langchain_openai import ChatOpenAI


def Processing(name_of_files):
    os.environ["OPENAI_API_KEY"] = "YOUR API KEY"

    model = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))  # Подключаем модель через API

    parser = MegaParseVision(model=model)

    megaparse = MegaParse(parser)

    for name_of_file in name_of_files:
        response = megaparse.load(f"./test_files/{name_of_file}")

        # Сохранение результата в Markdown
        output_path = f"./processed_files/{name_of_file[:-3]}md"
        megaparse.save(output_path)
        print(f"Результат сохранён в: {output_path}")
