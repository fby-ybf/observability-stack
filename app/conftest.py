"""pytest 配置。

放在 app/ 目录下的 conftest.py 会让 pytest 把本目录加入 sys.path，
这样 `from main import app` 在 CI（直接调用 pytest）与本地都能导入。
"""
