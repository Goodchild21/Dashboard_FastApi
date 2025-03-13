import json
import uuid

import nh3
from fastapi import Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRouter
from fastapi_csrf_protect import CsrfProtect

from app.database.db import CurrentAsyncSession
from app.database.security import current_active_user
from app.models.users import Role as RoleModelDB
from app.models.users import User as UserModelDB
from app.routes.view.errors import handle_error
from app.routes.view.view_crud import SQLAlchemyCRUD
from app.schema.users import RoleCreate
from app.templates import templates

role_view_route = APIRouter()


role_crud = SQLAlchemyCRUD[RoleModelDB](RoleModelDB)


# Определение маршрута просмотра для перехода на страницу ролей
@role_view_route.get("/role", response_class=HTMLResponse)
async def get_role(
    request: Request,
    db: CurrentAsyncSession,
    current_user: UserModelDB = Depends(current_active_user),
    skip: int = 0,
    limit: int = 100,
    csrf_protect: CsrfProtect = Depends(),
):
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=403, detail="Нет авторизации для данной страницы"
            )
        # Доступ к кукам с помощью объекта Request
        roles = await role_crud.read_all(db, skip, limit)
        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
        response = templates.TemplateResponse(
            "pages/role.html",
            {
                "request": request,
                "roles": roles,
                "user_type": current_user.is_superuser,
                "csrf_token": csrf_token,
            },
        )
        csrf_protect.set_csrf_cookie(signed_token, response)
        return response
    except Exception as e:
        csrf_token = request.headers.get("X-CSRF-Token")
        return handle_error(
            "pages/role.html", {"request": request, "csrf_token": csrf_token}, e
        )


# Роутер для получения отображения формы и добавления новой роли в базу данных
@role_view_route.get("/get_create_roles", response_class=HTMLResponse)
async def get_create_roles(
    request: Request,
    current_user: UserModelDB = Depends(current_active_user),
    csrf_protect: CsrfProtect = Depends(),
):
    # superuser
    try:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Нет авторизации")
        # Добавления роли на страницу после успешного создания роли

        csrf_token = request.headers.get("X-CSRF-Token")
        response = templates.TemplateResponse(
            "partials/role/add_role.html",
            {
                "request": request,
                "csrf_token": csrf_token,
                "user_type": current_user.is_superuser,
            },
        )

        return response
    except Exception as e:
        csrf_token = request.headers.get("X-CSRF-Token")
        return handle_error(
            "partials/role/add_role.html",
            {
                "request": request,
                "csrf_token": csrf_token,
                "user_type": current_user.is_superuser,
            },
            e,
        )


# Роутер записи для добавления новой роли в базу данных
@role_view_route.post("/post_create_roles", response_class=HTMLResponse)
async def post_create_roles(
    request: Request,
    response: Response,
    db: CurrentAsyncSession,
    current_user: UserModelDB = Depends(current_active_user),
    csrf_protect: CsrfProtect = Depends(),
):
    try:

        await csrf_protect.validate_csrf(request)
        # superuser
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Отсутствует авторизация для добавления формы")

        form = await request.form()

        # Очистка полей формы перед проверкой по модели Pydantic.
        role_create = RoleCreate(
            role_name=nh3.clean(str(form.get("role_name"))),
            role_desc=nh3.clean(str(form.get("role_desc"))),
        )

        existing_role = await role_crud.read_by_column(
            db, "role_name", role_create.role_name
        )

        if existing_role:
            raise HTTPException(status_code=400, detail="Role name already exists")
        await role_crud.create(dict(role_create), db)

        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

        # Перенаправление на страницу добавления роли после успешного создания роли
        headers = {
            "HX-Location": "/role",
            "HX-Trigger": json.dumps(
                {
                    "showAlert": {
                        "type": "added",
                        "message": f"{role_create.role_name} успешно дабавлено",
                        "source": "role-page",
                    },
                }
            ),
            "HX-Push-Url": "true",
            "csrf_token": csrf_token,
        }

        response = HTMLResponse(content="", headers=headers)

        csrf_protect.unset_csrf_cookie(response)

        csrf_protect.set_csrf_cookie(signed_token, response)

        return response
    except Exception as e:
        csrf_token = request.headers.get("X-CSRF-Token")
        return handle_error(
            "partials/role/add_role.html",
            {
                "request": request,
                "csrf_token": csrf_token,
                "user_type": current_user.is_superuser,
            },
            e,
        )


# Определение эндпоинта для получения записи на основе id
@role_view_route.get("/get_role/{role_id}", response_class=HTMLResponse)
async def get_role_by_id(
    request: Request,
    role_id: uuid.UUID,
    db: CurrentAsyncSession,
    current_user: UserModelDB = Depends(current_active_user),
    # csrf_protect: CsrfProtect = Depends(),
):
    try:
        # superuser
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Нет авторизации")
        role = await role_crud.read_by_primary_key(db, role_id)

        csrf_token = request.headers.get("X-CSRF-Token")

        response = templates.TemplateResponse(
            "partials/role/edit_role.html",
            {
                "request": request,
                "role": role,
                "csrf_token": csrf_token,
                "user_type": current_user.is_superuser,
            },
        )

        return response
    except Exception as e:
        csrf_token = request.headers.get("X-CSRF-Token")
        return handle_error(
            "partials/role/edit_role.html",
            {
                "request": request,
                "csrf_token": csrf_token,
                "user_type": current_user.is_superuser,
            },
            e,
        )


# Эндпоинт для обновления записи на основе идентификатора
@role_view_route.put("/post_update_role/{role_id}", response_class=HTMLResponse)
async def post_update_role(
    request: Request,
    response: Response,
    role_id: uuid.UUID,
    db: CurrentAsyncSession,
    current_user: UserModelDB = Depends(current_active_user),
    csrf_protect: CsrfProtect = Depends(),
):
    try:
        await csrf_protect.validate_csrf(request)
        # superuser
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Нет авторизации")

        form = await request.form()

        # Очистка полей формы перед проверкой по модели Pydantic.
        role_update = RoleCreate(
            role_name=nh3.clean(str(form.get("role_name"))),
            role_desc=nh3.clean(str(form.get("role_desc"))),
        )

        await role_crud.update(db, role_id, dict(role_update))

        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
        # Перенаправление на страницу добавления роли после успешного создания роли
        headers = {
            "HX-Location": "/role",
            "HX-Trigger": json.dumps(
                {
                    "showAlert": {
                        "type": "updated",
                        "message": f"{role_update.role_name} успешно добавлено",
                        "source": "role-page",
                    },
                }
            ),
            "HX-Boost": "true",
            "csrf_token": csrf_token,
        }
        response = HTMLResponse(content="", headers=headers)

        csrf_protect.unset_csrf_cookie(response)

        csrf_protect.set_csrf_cookie(signed_token, response)

        return response
    except Exception as e:
        role = await role_crud.read_by_primary_key(db, role_id)
        csrf_token = request.headers.get("X-CSRF-Token")
        return handle_error(
            "partials/role/edit_role.html",
            {"request": request, "role": role, "csrf_token": csrf_token},
            e,
        )


# Роутер на удаление роли на основе id
@role_view_route.delete("/delete_role/{role_id}", response_class=HTMLResponse)
async def delete_role(
    request: Request,
    role_id: uuid.UUID,
    db: CurrentAsyncSession,
    current_user: UserModelDB = Depends(current_active_user),
    csrf_protect: CsrfProtect = Depends(),
):
    try:
        await csrf_protect.validate_csrf(request)
        # superuser
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=403, detail="Нет авторизации"
            )
        await role_crud.delete(db, role_id)

        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
        role_name = request.headers.get("X-Role-Name")
        headers = {
            "HX-Location": "/role",
            "HX-Trigger": json.dumps(
                {
                    "showAlert": {
                        "type": "deleted",
                        "message": f"{role_name} успешно удалено",
                        "source": "role-page",
                    },
                }
            ),
            "HX-Boost": "true",
            "csrf_token": csrf_token,
        }

        response = HTMLResponse(content="", headers=headers)

        csrf_protect.unset_csrf_cookie(response)

        csrf_protect.set_csrf_cookie(signed_token, response)

        return response
    except Exception as e:
        csrf_token = request.headers.get("X-CSRF-Token")
        return handle_error(
            "pages/role.html",
            {
                "request": request,
                "csrf_token": csrf_token,
                "user_type": current_user.is_superuser,
            },
            e,
        )
