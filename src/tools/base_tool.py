
from abc import abstractmethod, ABC
from typing import Any, Callable, Optional, Type
from pydantic import BaseModel, ConfigDict, Field, validator
from pydantic.v1 import BaseModel as V1BaseModel

class BaseTool(BaseModel, ABC):
    class _ArgsSchemaPlaceholder(V1BaseModel):
        pass
    model_config = ConfigDict()

    name:str
    description:str
    args_schema: Type[V1BaseModel]= Field(default_factory=_ArgsSchemaPlaceholder)
    description_updated:bool = False
    cache_function: Optional[Callable]= lambda _args, _result: True

    @validator("args_schema", always=True, pre=True)
    def _default_args_schema(cls, v:Type[V1BaseModel])-> Type[V1BaseModel]:
        if not isinstance(v, cls._ArgsSchemaPlaceholder):
            return v
        return type(f"{cls.__name__} Schema", (V1BaseModel), {
            "__annnotations__": {k:v for k, v in cls.__run.__annotations__.items() if k!= 'return'}})
    
    def model_post_init(self, __context: Any) -> None:
        self._generate_description()
        return super().model_post_init(__context)
    
    def run(self, *args:Any, ** kwargs:Any)->Any:
        print(f'USing tool: {self.name}')
        return self._run(*args,**kwargs)
    
    @abstractmethod
    def _run(self, *args, **kwargs):
        ''''''

    def to_langchain(self)->StructuredTool:
        self._set_args_schema()
        return StructuredTool(name= self.name, description = self.description, args_schema= self.args_schema, func= self._run)
    
    def _set_args_schema(self):
        if self.args_schema is None:
            class_name= f"{self.__class__.__name__} Schema"
            self.args_schema= type(class_name, (V1BaseModel), {
                "__annotations__": { k: v for k, v in self._run.__annotations__.items() if k!= 'return'}
            })
    
    def _generate_description(self):
        args=[]
        for arg, attribute in self.args_schema.schema()['properties'].items():
            if "type" in attribute:
                args.append(f'{arg}: {attribute['type']}')
        description = self.description.replace("\n",' ')
        self.description = f'{self.name}({','.join(args)}) - {description}'

