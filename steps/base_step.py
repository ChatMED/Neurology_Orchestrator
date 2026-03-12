from typing import Generic

from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.utils.pydantic import TBaseModel

class BaseStep(object):

    def __init__(self, system_prompt, base_class:Generic[TBaseModel]):
        self.base_class = base_class
        self.llm = init_chat_model("openai:gpt-4.1")
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    system_prompt
                ),
                ("human", "{query}"),
            ]
        ).partial(schema=base_class.model_json_schema())

    def execute(self, input_text):
        parser = PydanticOutputParser(pydantic_object=self.base_class)
        query = input_text
        chain = self.prompt | self.llm | parser
        report = chain.invoke({"query": query})
        return report

    def iterate(self, row, target_column, source_column=None, source_columns=[]):
        if source_columns is None:
            source_columns = []
        value = ""
        if source_column is not None and source_column == "*":
            value = "\n".join([str(i) for i in row.tolist()])
        else:
            if source_column is not None:
                value = row[source_column]
            elif len(source_columns) > 0:
                value = "\n".join(row[source_columns].tolist())
        output = self.execute(value)
        row[target_column] = output.model_dump_json()
        return row