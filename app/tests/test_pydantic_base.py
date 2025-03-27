from typing import Optional

import pytest
from pydantic import BaseModel

from ..schema.pydantic_base import pydantic_partial


class TestPartialModel:
    # Функция возвращает новую BaseModel со всеми необязательными полями, если exclude_fields равно None.
    def test_all_fields_optional_if_exclude_fields_is_none(self):
        #
        class MyModel(BaseModel):
            field1: int
            field2: str

        # Объект
        partial = pydantic_partial()(MyModel)

        # Утверждения
        assert issubclass(partial, BaseModel)
        assert "field1" in partial.schema()["properties"]
        assert "field2" in partial.schema()["properties"]
        if "type" in partial.schema()["properties"]["field1"]:
            assert partial.schema()["properties"]["field1"]["type"] == "integer"
        if "type" in partial.schema()["properties"]["field2"]:
            assert partial.schema()["properties"]["field2"]["type"] == "string"

    # Функция возвращает новую BaseModel с указанными полями (необязательно), если exclude_fields — это список имен полей.
    def test_specified_fields_optional_if_exclude_fields_is_list(self):
        #
        class MyModel(BaseModel):
            field1: int
            field2: str
            field3: float

        # Объект
        partial = pydantic_partial(exclude_fields=["field1", "field3"])(MyModel)

        # Утверждения
        assert issubclass(partial, BaseModel)
        assert "field1" not in partial.__annotations__
        assert partial.__annotations__["field2"] == Optional[str]
        assert "field3" not in partial.__annotations__

    # Функция возвращает новую BaseModel с тем же именем и модулем, что и у исходной модели.
    def test_same_name_and_module_as_original_model(self):
        #
        class MyModel(BaseModel):
            field1: int
            field2: str

        # Объект
        partial = pydantic_partial()(MyModel)

        # Утверждения
        assert partial.__name__ == "MyModel"
        assert partial.__module__ == MyModel.__module__

    # Функция возвращает новую BaseModel без полей, если exclude_fields — пустой список.
    def test_no_fields_if_exclude_fields_is_empty_list(self):
        #
        class MyModel(BaseModel):
            field1: int
            field2: str

        # Объект
        partial = pydantic_partial(exclude_fields=[])(MyModel)

        # Утверждения
        assert issubclass(partial, BaseModel)
        assert len(partial.__annotations__) == 2

    # Функция возвращает новую BaseModel без полей, если exclude_fields содержит все имена полей.
    def test_no_fields_if_exclude_fields_contains_all_field_names(self):
        #
        class MyModel(BaseModel):
            field1: int
            field2: str

        # Объект
        partial = pydantic_partial(exclude_fields=["field1", "field2"])(MyModel)

        # Утверждения
        assert issubclass(partial, BaseModel)
        assert len(partial.__annotations__) == 0

    # Функция вызывает исключение, если исходная модель не является подклассом BaseModel.
    def test_exception_if_original_model_not_subclass_of_BaseModel(self):
        #
        class MyModel:
            field1: int
            field2: str

        # Объект и утверждения
        with pytest.raises(TypeError):
            pydantic_partial()(MyModel)
