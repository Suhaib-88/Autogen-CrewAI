from typing import Any, Optional, Type
from embedchain.loaders.directory_loader import DirectoryLoader
from pydantic.v1 import BaseModel, Field
from ..rag.rag_tool import RagTool

class FixedDirectorySearchToolSchema(BaseModel):
    search_query:str= Field(..., description='Mandatory search query you want to use to search the Directory content')


class DirectorySearchToolSchema(FixedDirectorySearchToolSchema):
    directory: str= Field(..., description='Mandatory directory path you want to search')

class DirectorySearchTool(RagTool):
    name:str= "Search a Directory's content"
    description:str= ("A tool that can be used to semanticly search a query from code Directory content")

    args_schema: Type[BaseModel]= DirectorySearchToolSchema

    def __init__(self, directory, **kwargs):
        super().__init__(**kwargs)
        if directory is not None:
            self.add(directory)
            self.description=f'A tool that can be used to serach a query the {directory}'
            self.args_schema= FixedDirectorySearchToolSchema
            self._generate_description()

    
    def add(self, *args,**kwargs)-> None:
        kwargs['loader']= DirectoryLoader(config= dict(recursive=True))
        super().add(*args, **kwargs)

    def _before_run(self, query: str,**kwargs:Any):
        if "directory" in kwargs:
            self.add(kwargs['directory'])

    def _run(self,search_query: str, **kwargs:Any):
        return super()._run(query= search_query)
    
    
