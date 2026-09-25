import os
import sys

# 打包后这个 exe 自己就是解释器：外部引擎用 "anydl.exe -m <引擎名> <参数>" 的方式被拉起来。
# 为什么不在 bin/ 里放现成的 spotdl.exe：pip 生成的启动器壳里写死了解释器的绝对路径，
# 发到别人机器上就跑不起来；而且 scdl 连 __main__.py 都没有，没法用 "-m scdl" 直接跑。
# 映射：引擎名 -> (模块名, 入口函数名)，入口函数名为 None 表示模块自己有 __main__.py
ENGINE_ENTRY = {
    "yt_dlp": ("yt_dlp", None),
    "spotdl": ("spotdl", None),
    "scdl": ("scdl.scdl", "_main"),  # scdl 没有 __main__.py，只能手动调它的入口函数
}


def _run_engine_from_argv():
    """被当引擎解释器调用时，就地跑引擎，返回 True（调用方据此直接退出）"""
    if len(sys.argv) < 3 or sys.argv[1] != "-m" or sys.argv[2] not in ENGINE_ENTRY:
        return False

    module_name, func_name = ENGINE_ENTRY[sys.argv[2]]
    # 掐掉开头的 "-m 引擎名"，剩下的参数原样留给引擎自己解析
    sys.argv = [sys.argv[2]] + sys.argv[3:]

    # 打包成不弹控制台的 exe 后，sys.stdout 有可能是 None，引擎随便 print 一下就崩。
    # 平时被父进程用管道拉起来时管道是好的（日志能正常回传），这里只是兜底
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = sys.stdout

    if func_name is None:
        import runpy
        runpy.run_module(module_name, run_name="__main__")
    else:
        import importlib
        getattr(importlib.import_module(module_name), func_name)()
    return True


# 引擎调用跑完就走，后面的 flet 一行都不加载。这段只在打包产物里有意义：
# 开发环境里 .venv/Scripts 下有真的引擎 exe，根本不会走到这里
if __name__ == "__main__" and _run_engine_from_argv():
    sys.exit(0)

import flet as ft
from ui.app import main_app
import uvicorn

# Fix for uvicorn 0.23.2 compatibility with flet
old_init = uvicorn.Config.__init__
def new_init(self, *args, **kwargs):
    if kwargs.get('ws') == 'websockets-sansio':
        kwargs['ws'] = 'auto'
    old_init(self, *args, **kwargs)
uvicorn.Config.__init__ = new_init

# 打包后 flet 只会去 C:\Users\<用户>\.flet\client 找桌面客户端，找不到就联网下 97MB。
# 明明包里就带了一份却认不出来：flet_desktop 找的是 flet_desktop/app/flet-windows.zip 这个压缩包，
# 而 PyInstaller 钩子塞进去的是解压好的文件夹，对不上。这个环境变量在"查缓存"之前生效，
# 指过去就直接用包里那份 —— 离线可用，也不用往 C 盘写 97MB。用 setdefault 让用户自己设的值优先
if getattr(sys, 'frozen', False):
    os.environ.setdefault(
        "FLET_VIEW_PATH",
        os.path.join(sys._MEIPASS, "flet_desktop", "app", "flet"),
    )

if __name__ == '__main__':
    ft.run(main_app, view=ft.AppView.FLET_APP)
