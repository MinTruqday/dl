from typing import Optional, Union

from pydantic import BaseModel

class Collection(BaseModel):
    source: str
    pages: Optional[Union[int, str]] = 1
