from typing import Any, Type, Optional
from pydantic import BaseModel, Field
from ..base_tool import BaseTool

class FixedFileReadToolSchema(BaseModel):
    pass

class FileReadToolSchema(FixedFileReadToolSchema):
    file_path: str= Field(..., description='Mandatory file path you want to read')


class FileReadTool(BaseTool):
    name:str= "Read a file content"
    description:str= "A tool that can be used to read a file content"
    args_schema: Type[BaseModel]= FileReadToolSchema
    file_path: Optional[str]= None
    
    def __init__(self, file_path:Optional[str], **kwargs:Any)->None:
        super().__init__(**kwargs)
        if file_path is not None:
            self.file_path= file_path
            self.description= f'A tool that can be used to read a file content from {file_path}'
            self.args_schema= FileReadToolSchema
            self._generate_description()

    def _run(self, **kwargs:Any)->Any:

        try:
            file_path= kwargs.get('file_path', self.file_path)
            with open(file_path, 'r') as file:
                content= file.read()
            return content
        except Exception as e:
            return f'Error reading file: {e}'
    