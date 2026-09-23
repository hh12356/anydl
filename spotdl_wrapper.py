import asyncio
import sys

# Python 3.14+ deprecated and modified asyncio.get_event_loop() to throw a RuntimeError 
# if no loop is running in the current thread. SpotDL spawns threads that use this, 
# which causes a fatal crash. We monkey-patch it here to auto-create a loop if missing.
# Python 3.14 及以上版本弃用并修改了 asyncio.get_event_loop ()，当当前线程没有正在运行的事件循环时，该函数会抛出运行时错误
# SpotDL 会创建使用该函数的线程，这会导致程序严重崩溃。我们在此处对其进行猴子补丁，在缺少事件循环时自动创建。
_old_get_event_loop = getattr(asyncio, "get_event_loop", None)

def _get_event_loop_patch():
    try:
        #当前进程没有loop直接抛RuntimeError
        return asyncio.get_running_loop()
    except RuntimeError:
        #手动创建
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

asyncio.get_event_loop = _get_event_loop_patch

from spotdl.console import console_entry_point

if __name__ == "__main__":
    sys.argv = sys.argv[1:] # Remove the wrapper script from args so spotdl parses correctly
    #调用 spotdl 主入口  spotdl:spotify下载工具
    console_entry_point()
