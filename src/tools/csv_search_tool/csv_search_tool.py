from typing import Any, Optional, Type
from embedchain.models.data_type import DataType
from pydantic.v1 import BaseModel, Field
from ..rag.rag_tool import RagTool

class FixedCSVSearchToolSchema(BaseModel):
    search_query:str= Field(..., description='Mandatory search query you want to use to search the CSV content')


class CSVSearchToolSchema(FixedCSVSearchToolSchema):
    csv: str= Field(..., description='Mandatory csv path you want to search')

class CodeDocsSearchTool(RagTool):
    name:str= "Search a code CSV content"
    description:str= ("A tool that can be used to semanticly search a query from CSV content")

    args_schema: Type[BaseModel]= FixedCSVSearchToolSchema

    def __init__(self, docs_url, **kwargs):
        super().__init__(**kwargs)
        if docs_url is not None:
            self.add(docs_url)
            self.description=f'A tool that can be used to serach a query the {docs_url}'
            self.args_schema= FixedCSVSearchToolSchema
            self._generate_description()

    
    def add(self, *args,**kwargs)-> None:
        kwargs['data_type']= DataType.CSV
        super().add(*args, **kwargs)

    def _before_run(self, query:str, **kwargs:Any)->Any:
        if 'csv' in kwargs:
            self.add(kwargs['csv'])

    def _run(self,search_query: str, **kwargs:Any):
        return super()._run(query= search_query)
    
    
