from typing import Dict, Union

from fastapi import HTTPException
from loguru import logger
from pydantic import ValidationError

from app.templates import templates


def handle_error(
    template: str,
    context: Dict,
    error: Union[ValidationError, HTTPException, Exception],
) -> templates.TemplateResponse:
    """
    Обрабатывает ошибки, возникающие во время обработки запроса, и возвращает шаблон
    ответа с соответствующими сообщениями об ошибках.

    Аргументы:
    template (str): Имя шаблона для рендеринга.
    context (dict): Это словарь, содержащий данные, которые будут переданы в шаблон.
    Он должен включать объект запроса и любые объекты базы данных, которые необходимо отобразить в шаблоне.
    Например, вы можете передать {"request": request, "group": await group_crud.read_by_primary_key(db, group_id)} в качестве контекста.
    error (Exception): Это исключение, возникшее во время выполнения вашего кода.

    Возвращает:
    Ответ FastAPI, содержащий отрисованный шаблон с сообщениями об ошибках.
    """
    logger.info(f"context: {context}, error: {error}")
    error_messages: list[str] = []
    if isinstance(error, ValidationError):
        if error.errors():
            error_messages = [
                f"{str(err['loc']).strip('(),')}: {err['msg']}"
                for err in error.errors()
            ]
        else:
            error_messages = ["Произошла непредвиденная ошибка проверки"]
    elif isinstance(error, HTTPException):
        error_messages = [error.detail]
    else:
        error_messages = ["Произошла непредвиденная ошибка: {}".format(error)]

    context["error_messages"] = error_messages
    logger.info(error_messages)
    return templates.TemplateResponse(template, context)
