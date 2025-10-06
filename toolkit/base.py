from typing import Any, Callable, Dict, Optional, Type

from pydantic import BaseModel


class ToolSpec(BaseModel):
    name: str
    description: str
    args_schema: Optional[Type[BaseModel]] = None


class Tool:
    def __init__(self, spec: ToolSpec, handler: Callable[..., Dict[str, Any]]):
        self.spec = spec
        self.handler = handler

    def __call__(self, *args, **kwargs) -> Dict[str, Any]:
        return self.handler(*args, **kwargs)


