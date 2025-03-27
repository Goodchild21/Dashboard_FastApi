import pytest
from pydantic import ValidationError

from app.schema.users import RoleBase, RoleCreate


def test_create_valid_roles():
    # Проверка допустимого ввода
    role = RoleCreate(role_name="admin", role_desc="Role description")
    assert role.role_name == "admin"
    assert role.role_desc == "Role description"


def test_create_invalid_roles():
    # Проверка недопустимого ввода
    with pytest.raises(ValidationError):
        RoleCreate(role_name="a", role_desc="Role description")
    with pytest.raises(ValidationError):
        RoleCreate(role_name="admin", role_desc="")


def test_create_roles_with_long_inputs():
    # Проверка валидности ввода, где role_name содержит более 50 символов, а role_desc содержит более 200 символов.
    with pytest.raises(ValidationError):
        RoleCreate(role_name="a" * 51, role_desc="Role description")
    with pytest.raises(ValidationError):
        RoleCreate(role_name="admin", role_desc="a" * 201)


def test_create_roles_with_default_desc():
    # Тестовое значение по умолчанию для role_desc
    role = RoleBase(role_name="admin")
    assert role.role_desc is None
