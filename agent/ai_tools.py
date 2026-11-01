from langchain_core.tools import tool

from config.settings.folder_conf import BASE_FOLDER# Таблица прав: для каждой папки — какие операции разрешены


PERMISSIONS = {
    (BASE_FOLDER / "public").resolve():    {"read"},
    (BASE_FOLDER / "workspace").resolve(): {"read", "write", "create"},
    (BASE_FOLDER / "system").resolve():    set(),          # ничего нельзя
}