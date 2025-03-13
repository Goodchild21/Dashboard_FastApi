import json
import uuid
from urllib.parse import parse_qs, unquote_plus

import nh3
from fastapi import Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRouter
from fastapi_csrf_protect import CsrfProtect
from sqlalchemy import select

from app.database.db import CurrentAsyncSession
from app.database.security import current_active_user
from app.models.groups import Group as GroupModelDB
from app.models.groups import UserGroupLink as UserGroupLinkModelDB
from app.models.users import Role as UserRoleModelDB
from app.models.users import User as UserModelDB
from app.models.users import UserProfile as UserProfileModelDB
from app.routes.view.errors import handle_error
from app.routes.view.view_crud import SQLAlchemyCRUD
from app.schema.group import GroupCreate
from app.schema.group import GroupUserLink as GroupUserLinkCreate
from app.templates import templates


group_view_route = APIRouter()


group_crud = SQLAlchemyCRUD[GroupModelDB](
    GroupModelDB, related_models={UserModelDB: "users"}
)
user_crud = SQLAlchemyCRUD[UserModelDB](
    UserModelDB,
    related_models={UserProfileModelDB: "profile", UserRoleModelDB: "role"},
)


# Определение маршрута для перехода на страницу группы
@group_view_route.get("/groups", response_class=HTMLResponse)
async def get_groups(
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
                status_code=403, detail="Вы не авторизованы для этой страницы"
            )
        # Доступ к файлам cookie с помощью объекта Request
        groups = await group_crud.read_all(db, skip, limit, join_relationships=True)
        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

        response = templates.TemplateResponse(
            "pages/groups.html",
            {
                "request": request,
                "groups": groups,
                "user_type": current_user.is_superuser,
                "csrf_token": csrf_token,
            },
        )

        csrf_protect.set_csrf_cookie(signed_token, response)

        return response
    except Exception as e:
        csrf_token = request.headers.get("X-CSRF-Token")
        return handle_error(
            "pages/groups.html",
            {
                "request": request,
                "csrf_token": csrf_token,
            },
            e,
        )


# Определение маршрута для получения профиля пользователя на базе id
@group_view_route.get("/get_user_profile/{user_id}", response_class=HTMLResponse)
async def get_user_profile(
    request: Request,
    user_id: uuid.UUID,
    db: CurrentAsyncSession,
    current_user: UserModelDB = Depends(current_active_user),
):
    # if not current_user.is_superuser:
    #     raise HTTPException(status_code=403, detail="Not authorized to add groups")
    user_profile = await user_crud.read_by_primary_key(
        db, user_id, join_relationships=True
    )
    return templates.TemplateResponse(
        "partials/group/group_user_profile.html",
        {
            "request": request,
            "user_profile": user_profile,
            "user_type": current_user.is_superuser,
        },
    )


# Определение маршрута для добавления новой группы в базу данных
@group_view_route.get("/get_create_group", response_class=HTMLResponse)
async def get_create_group(
    request: Request,
    current_user: UserModelDB = Depends(current_active_user),
):
    # superuser
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Отсутствует авторизация для данной группы!")
    # Перенаправление на страницу добавления группы после успешного создания группы
    csrf_token = request.headers.get("X-CSRF-Token")

    response = templates.TemplateResponse(
        "partials/group/add_group.html",
        {
            "request": request,
            "user_type": current_user.is_superuser,
            "csrf_token": csrf_token,
        },
    )

    return response


# Маршрут для получения группы по ID
@group_view_route.get("/get_group/{group_id}", response_class=HTMLResponse)
async def get_group_by_id(
    request: Request,
    group_id: uuid.UUID,
    db: CurrentAsyncSession,
    current_user: UserModelDB = Depends(current_active_user),
):
    # superuser
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Отсутствует авторизация для добавления группы!")
    group = await group_crud.read_by_primary_key(db, group_id)

    csrf_token = request.headers.get("X-CSRF-Token")

    return templates.TemplateResponse(
        "partials/group/edit_group.html",
        {
            "request": request,
            "group": group,
            "user_type": current_user.is_superuser,
            "csrf_token": csrf_token,
        },
    )


@group_view_route.post("/post_create_group", response_class=HTMLResponse)
async def post_create_group(
    request: Request,
    response: Response,
    db: CurrentAsyncSession,
    current_user: UserModelDB = Depends(current_active_user),
    csrf_protect: CsrfProtect = Depends(),
):
    await csrf_protect.validate_csrf(request)

    # superuser
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Отсутствует авторизация для добавления группы!")

    try:
        form = await request.form()

        # Iterate over the form fields and sanitize the values before validating against the Pydantic model
        group_create = GroupCreate(
            group_name=nh3.clean(str(form.get("group_name"))),
            group_desc=nh3.clean(str(form.get("group_desc"))),
        )

        existing_group = await group_crud.read_by_column(
            db, "group_name", group_create.group_name
        )

        if existing_group:
            raise HTTPException(status_code=400, detail="Название группы уже существует")
        await group_crud.create(dict(group_create), db)

        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

        # Перенаправление на страницу добавления группы после успешного создания группы
        headers = {
            "HX-Location": "/groups",
            "HX-Trigger": json.dumps(
                {
                    "showAlert": {
                        "type": "added",
                        "message": "Группа добавлена",
                        "source": "group-page",
                    }
                }
            ),
            "csrf_token": csrf_token,
        }

        response = HTMLResponse(content="", headers=headers)

        # Отключение CSRF-cookie
        csrf_protect.unset_csrf_cookie(response)

        # Установка нового CSRF-файла cookie для проверки при последующих запросах
        csrf_protect.set_csrf_cookie(signed_token, response)

        return response

    except Exception as e:
        csrf_token = request.headers.get("X-CSRF-Token")
        return handle_error(
            "partials/group/add_group.html",
            {
                "request": request,
                "csrf_token": csrf_token,
                "user_type": current_user.is_superuser,
            },
            e,
        )


# Маршрут для обновления группы
@group_view_route.put("/post_update_group{group_id}", response_class=HTMLResponse)
async def post_update_group(
    request: Request,
    # response: Response,
    group_id: uuid.UUID,
    db: CurrentAsyncSession,
    current_user: UserModelDB = Depends(current_active_user),
    csrf_protect: CsrfProtect = Depends(),
):

    try:
        await csrf_protect.validate_csrf(request)
        # superuser
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Отсутствует авторизация для добавления группы!")

        form = await request.form()

        # Очистка полей формы перед проверкой по модели Pydantic.
        group_update = GroupCreate(
            group_name=nh3.clean(str(form.get("group_name"))),
            group_desc=nh3.clean(str(form.get("group_desc"))),
        )

        await group_crud.update(db, group_id, dict(group_update))

        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

        # Перенаправление на страницу добавления группы после успешного создания группы
        headers = {
            "HX-Location": "/groups",
            "HX-Trigger": json.dumps(
                {
                    "showAlert": {
                        "type": "updated",
                        "message": "Группа обновлена",
                        "source": "group-page",
                    }
                }
            ),
            "csrf_token": csrf_token,
        }
        response = HTMLResponse(content="", headers=headers)

        csrf_protect.unset_csrf_cookie(response)

        csrf_protect.set_csrf_cookie(signed_token, response)

        return response
    except Exception as e:
        group = await group_crud.read_by_primary_key(db, group_id)
        csrf_token = request.headers.get("X-CSRF-Token")
        return handle_error(
            "partials/group/edit_group.html",
            {
                "request": request,
                "group": group,
                "csrf_token": csrf_token,
                "user_type": current_user.is_superuser,
            },
            e,
        )


# Маршрут для удаления группы
@group_view_route.delete("/delete_group/{group_id}", response_class=HTMLResponse)
async def delete_group(
    request: Request,
    group_id: uuid.UUID,
    db: CurrentAsyncSession,
    current_user: UserModelDB = Depends(current_active_user),
    csrf_protect: CsrfProtect = Depends(),
):

    try:
        await csrf_protect.validate_csrf(request)

        extra_info = await request.body()

        parsed_values = parse_qs(unquote_plus(extra_info.decode()))

        group_name = parsed_values["group_name"][0]

        # superuser
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Отсутствует авторизация для добавления группы!")
        await group_crud.delete(db, group_id)

        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

        headers = {
            "HX-Location": "/groups",
            "HX-Trigger": json.dumps(
                {
                    "showAlert": {
                        "type": "deleted",
                        "message": f"Группа {group_name} удалена",
                        "source": "group-page",
                    }
                }
            ),
            "csrf_token": csrf_token,
        }
        response = HTMLResponse(content="", headers=headers)

        csrf_protect.unset_csrf_cookie(response)

        csrf_protect.set_csrf_cookie(signed_token, response)

        return response
    except Exception as e:
        csrf_token = request.headers.get("X-CSRF-Token")
        return handle_error(
            "pages/groups.html",
            {
                "request": request,
                "csrf_token": csrf_token,
            },
            e,
        )



################# Маршруты распределения групп пользователей #################


# Добавление user в таблицу group_users
@group_view_route.get("/get_group_users/{group_id}", response_class=HTMLResponse)
async def get_group_users(
    request: Request,
    group_id: uuid.UUID,
    db: CurrentAsyncSession,
    current_user: UserModelDB = Depends(current_active_user),
):
    # superuser
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Отсутствует авторизация для добавления группы!")
    group = await group_crud.read_by_primary_key(db, group_id)
    users = await user_crud.read_all(db, join_relationships=True)
    group_users = await db.execute(
        select(UserGroupLinkModelDB).where(UserGroupLinkModelDB.group_id == group_id)
    )
    group_users = group_users.unique().scalars().all()
    await db.close()
    group_user_ids = [user.user_id for user in group_users]

    csrf_token = request.headers.get("X-CSRF-Token")
    return templates.TemplateResponse(
        "partials/group/add_group_user.html",
        {
            "request": request,
            "group": group,
            "users": users,
            "group_user_ids": group_user_ids,
            "csrf_token": csrf_token,
            "user_type": current_user.is_superuser,
        },
    )


# ============= Обновление модели UserGroupLink на основе выбранного пользователя для группы =======================
@group_view_route.post("/post_group_user_link/{group_id}", response_class=HTMLResponse)
async def post_group_user_link(
    request: Request,
    response: Response,
    group_id: uuid.UUID,
    db: CurrentAsyncSession,
    current_user: UserModelDB = Depends(current_active_user),
    csrf_protect: CsrfProtect = Depends(),
):

    try:
        await csrf_protect.validate_csrf(request)
        # superuser
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Отсутствует авторизация для добавления группы!")
        form = await request.form()

        all_users = set(form.getlist("all_users"))
        selected_users = set(form.getlist("users_selected"))
        # all_status = set(form.getlist("status")) #

        # Удаление уже выбранных пользователей из списка всех пользователей
        non_selected_users = all_users - selected_users
        db_data = []
        for user_id in form.getlist("users_selected"):
            group_user_link = GroupUserLinkCreate(
                group_id=uuid.UUID(nh3.clean(str(group_id))),
                user_id=uuid.UUID(nh3.clean(str(user_id))),
            )
            group_id = group_user_link.group_id
            user_id = group_user_link.user_id
            #
            existing_record = await db.scalar(
                select(UserGroupLinkModelDB).filter_by(
                    group_id=group_id, user_id=user_id
                )
            )
            if existing_record:
                print(f"Record with {user_id} already exists")
            else:
                db_data.append(
                    group_user_link.model_dump(exclude={"id"}, exclude_unset=True)
                )
        for user_id in non_selected_users:
            group_user_link = GroupUserLinkCreate(
                group_id=uuid.UUID(nh3.clean(str(group_id))),
                user_id=uuid.UUID(nh3.clean(str(user_id))),
            )
            group_id = group_user_link.group_id
            user_id = group_user_link.user_id
            existing_record = await db.scalar(
                select(UserGroupLinkModelDB).filter_by(
                    group_id=group_id, user_id=user_id
                )
            )
            if existing_record:
                await db.delete(existing_record)
                await db.commit()

        if len(db_data) > 0:
            db.add_all([UserGroupLinkModelDB(**link) for link in db_data])
            await db.commit()

        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

        headers = {
            "HX-Location": "/groups",
            "HX-Trigger": json.dumps(
                {
                    "showAlert": {
                        "type": "added",
                        "message": f"Состав группы изменен успешно!!!",
                        "source": "group-page",
                    }
                }
            ),
            "csrf_token": csrf_token,
        }

        response = HTMLResponse(content="", headers=headers)

        csrf_protect.unset_csrf_cookie(response)

        csrf_protect.set_csrf_cookie(signed_token, response)

        return response
    except Exception as e:
        group = await group_crud.read_by_primary_key(db, group_id)
        csrf_token = request.headers.get("X-CSRF-Token")
        return handle_error(
            "partials/group/add_group_user.html",
            {
                "request": request,
                "group": group,
                "csrf_token": csrf_token,
            },
            e,
        )


# ==================================В работе===================================
@group_view_route.put("/post_user_status", response_class=HTMLResponse)
async def post_user_status(
    request: Request,
    # user_id: user.id,
    # group_id: uuid.UUID,
    db: CurrentAsyncSession, #
    current_user: UserModelDB = Depends(current_active_user), #
    csrf_protect: CsrfProtect = Depends(), #
    ):
    pass
#     form = await request.form()
#
#     # name = "status"
#     status = str(form.get("status"))
#     # user_status = await db.select("user_status_in_group")
#
#     return print(status)
