from typing import Any, Optional, Type
from embedchain.models.data_type import DataType
from pydantic.v1 import BaseModel, Field
from ..rag.rag_tool import RagTool

class FixedMDXSearchToolSchema(BaseModel):
    search_query:str= Field(..., description='Mandatory search query you want to use to search the mdx content')


class MDXSearchToolSchema(FixedMDXSearchToolSchema):
    mdx: str= Field(..., description='Mandatory mdx path you want to search')

class MDXSearchTool(RagTool):
    name:str= "Search a code mdx content"
    description:str= ("A tool that can be used to semanticly search a query from mdx content")

    args_schema: Type[BaseModel]= MDXSearchToolSchema

    def __init__(self, docs_url, **kwargs):
        super().__init__(**kwargs)
        if docs_url is not None:
            self.add(docs_url)
            self.description=f'A tool that can be used to serach a query the {docs_url}'
            self.args_schema= MDXSearchToolSchema
            self._generate_description()

    
    def add(self, *args,**kwargs)-> None:
        kwargs['data_type']= DataType.MDX
        super().add(*args, **kwargs)

    def _before_run(self, query:str, **kwargs:Any)->Any:
        if 'mdx' in kwargs:
            self.add(kwargs['mdx'])

    def _run(self,search_query: str, **kwargs:Any):
        return super()._run(query= search_query)
    
    
