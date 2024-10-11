from abc import abstractmethod, ABC
from typing import Any
from pydantic import Field,model_validator
from base_tool import BaseTool
from pydantic import BaseModel


class Adapter(BaseModel,ABC):
    class Config:
        arbitary_types_allowed= True

    @abstractmethod
    def query(self, question:str)-> str:
        """Query the knowledge base with question and return the answer"""

    def add(self, *args, **kwargs)->None:
        "Add content to the knowledge base"


class RagTool(BaseTool):
    class _AdapterPlaceHolder(Adapter):
        def query (self, question:str)-> str:
            raise NotImplementedError

        def add (self, *args, **kwargs:Any)-> None:
            raise NotImplementedError
        
    name:str= "Knowledge base"
    description: str= "A knowledge base that van be ised to answer questions"
    summarize:bool = False
    adapter:Adapter = Field(default_Factory= _AdapterPlaceHolder)
    config:dict[str, Any] | None= None

    @model_validator(mode= 'after')
    def _set_default_adapter(self):
        if isinstance(self.adapter, RagTool._AdapterPlaceHolder):
            from embedchain import App
            from adapters.embedchain_adapter import EmbedchainAdapter
            app= App.from_config(config= self.config) if self.config else App()
            self.adapter= EmbedchainAdapter(app= app, summarize= self.summarize)

        return self
        

    def add(self, *args:Any, **kwargs:Any):
        self.adapter.add(*args, **kwargs)

    def _run(self, query:str, **kwargs:Any)-> Any:
        self._before_run(query,**kwargs)

        return f"Relevant Content: \n{self.adapter.query(query)}"
    
    def _before_run(self,query,**kwargs):
        pass

 