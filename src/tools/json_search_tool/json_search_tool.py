from typing import Any, Optional, Type
from embedchain.models.data_type import DataType
from pydantic.v1 import BaseModel, Field
from ..rag.rag_tool import RagTool

class FixedJSONSearchToolSchema(BaseModel):
    search_query:str= Field(..., description='Mandatory search query you want to use to search the CSV content')


class JSONSearchToolSchema(FixedCSVSearchToolSchema):
    json_path: str= Field(..., description='Mandatory Json path you want to search')

class JSONSearchTool(RagTool):
    name:str= "Search a Json's content"
    description:str= ("A tool that can be used to semanticly search a query from JSON content")

    args_schema: Type[BaseModel]= JSONSearchToolSchema

    def __init__(self, json_path, **kwargs):
        super().__init__(**kwargs)
        if json_path is not None:
            self.add(json_path)
            self.description=f'A tool that can be used to serach a query the {json_path}'
            self.args_schema= JSONSearchToolSchema
            self._generate_description()

    
    def add(self, *args,**kwargs)-> None:
        kwargs['data_type']= DataType.CSV
        super().add(*args, **kwargs)

    def _before_run(self, query:str, **kwargs:Any)->Any:
        if 'json_path' in kwargs:
            self.add(kwargs['json_path'])

    def _run(self,search_query: str, **kwargs:Any):
        return super()._run(query= search_query)
    
    
