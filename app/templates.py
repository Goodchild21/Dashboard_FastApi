from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader

# Создание среды Jinja2 с включенной автоматической перезагрузкой
jinja_env = Environment(loader=FileSystemLoader("app/templates"), auto_reload=True)

# Использование пользовательской среды в Jinja2Templates
templates = Jinja2Templates(env=jinja_env)
