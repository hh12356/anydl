import subprocess #在python中调用外部程序
import threading #python的多线程工具
import queue
import os #操作系统底层接口
import sys #操作python运行环境
import shutil #实现高级文件操作


# 打包后 pip 生成的 spotdl.exe/scdl.exe/yt-dlp.exe 用不了：那只是启动器壳，
# 里面写死了解释器的绝对路径，发到别人机器上就失效。所以改成让程序自己当解释器，
# 用 "anydl.exe -m spotdl" 这种方式把引擎拉起来（main.py 里接住这个参数）。
# 左边是引擎名，右边是模块名
ENGINE_MODULES = {
    "yt-dlp": "yt_dlp",
    "spotdl": "spotdl",
    "scdl": "scdl",
}


class DownloadManager:
    #构造函数
    def __init__(self):
        self.output_queue = queue.Queue() #线程安全队列
        self.process = None #用于保存下载子进程，None即为当前未下载
        self.base_path = self._get_base_path() #拿到下载保存根目录

    def _get_base_path(self):
        """Returns the base path for the application, handling PyInstaller bundling."""
        if getattr(sys, 'frozen', False): #获取打包文件
            # If running as a bundled executable 如果以打包后的可执行文件运行
            return sys._MEIPASS #返回临时资源文件夹
        # If running as a raw script 如果为原始脚本运行
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _resolve_engine_path(self, engine_name):
        """
        Returns how to launch a given engine (yt-dlp, spotdl, etc.) 返回启动指定引擎的命令开头
        注意返回的是 list：开发环境里就一条路径，打包后是 [解释器, "-m", 模块名]
        Order of priority 优先级排序:
        1. Bundled app itself as an interpreter (for packaged builds)
        2. Bundled 'bin' folder (for portable builds)
        3. Local '.venv/bin' folder (for development)
        4. System PATH
        """
        # 1. 打包产物：让程序自己当解释器跑引擎，见上面 ENGINE_MODULES 的说明
        if getattr(sys, 'frozen', False) and engine_name in ENGINE_MODULES:
            return [sys.executable, "-m", ENGINE_MODULES[engine_name]]

        # 2. Check bundled bin folder 检查捆绑的 bin 文件夹
        bundled_path = os.path.join(self.base_path, "bin", engine_name)
        if os.name == 'nt': bundled_path += ".exe" #如果是windows系统则加".exe"后缀
        if os.path.exists(bundled_path):
            return [bundled_path]

        # 3. Check virtual environment 检查虚拟环境
        venv_path = os.path.join(self.base_path, ".venv", "bin", engine_name)
        if os.name == 'nt': venv_path = os.path.join(self.base_path, ".venv", "Scripts", engine_name + ".exe")
        if os.path.exists(venv_path):
            return [venv_path]

        # 4. Fallback to system PATH 回退至系统路径
        system_path = shutil.which(engine_name)
        if system_path:
            return [system_path]

        return [engine_name] # Return as is, hope for the best

    def start_download(self, command, cwd=None): #cwd:子进程工作目录，下载文件的默认目录
        """Starts the download process in a separate thread. 另开线程下载"""
        # Resolve the engine path (first element of command) 取出引擎（命令的第一个元素）
        engine = command[0]
        resolved_engine = self._resolve_engine_path(engine)

        # Reconstruct command with resolved engine 使用已解析引擎重构命令
        # resolved_engine 已经是 list（打包后可能不止一个元素），直接拼
        full_command = resolved_engine + command[1:]
        
        self.output_queue.put(("STATUS", f"Starting: {' '.join(full_command)}"))
        # 有cwd是告知用户输出目录
        if cwd:
            self.output_queue.put(("STATUS", f"Output directory: {cwd}"))

        #创建新进程 target:线程要执行的函数 args:传给函数的参数 daemon:守护线程
        thread = threading.Thread(target=self._run_process, args=(full_command, cwd), daemon=True)
        thread.start()

    def _run_process(self, command, cwd):
        """Runs the subprocess and captures stdout and stderr. 运行子进程并捕获标准输出和标准错误"""
        try:
            # Ensure FFmpeg is available in the path if bundled 捆绑部署时确保FFmpeg在系统路径中可用
            env = os.environ.copy()
            # bin/ 放引擎本体（yt-dlp.exe 等），ffmpeg.exe 在 bin/ffmpeg/bin/ 下
            for extra in ("bin", os.path.join("bin", "ffmpeg", "bin")):
                bundled_bin = os.path.join(self.base_path, extra)
                if os.path.exists(bundled_bin):
                    #将bundled_bin插到环境变量PATH的最前面，使子进程优先从这个目录找程序
                    env["PATH"] = bundled_bin + os.pathsep + env.get("PATH", "")

            self.process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, #输出自动解码成字符串,不返回原始二进制字节串
                bufsize=1, #子进程每输出一行，就立刻刷新管道
                env=env # Inject bundled bin into path for ffmpeg access 将捆绑的二进制文件注入路径以调用 ffmpeg
            )

            # Start threads to read stdout and stderr continuously 启动线程以持续读取标准输出和标准错误输出
            stdout_thread = threading.Thread(target=self._read_stream, args=(self.process.stdout, "STDOUT"), daemon=True)
            stderr_thread = threading.Thread(target=self._read_stream, args=(self.process.stderr, "STDERR"), daemon=True)
            
            stdout_thread.start()
            stderr_thread.start()

            #阻塞等待子进程执行结束
            self.process.wait()

            #继续执行
            stdout_thread.join()
            stderr_thread.join()
            
            self.output_queue.put(("STATUS", f"Process finished with exit code {self.process.returncode}"))
            
        except Exception as e:
            self.output_queue.put(("ERROR", str(e)))

    def _read_stream(self, stream, stream_type):
        """Reads from a stream and puts lines into the queue, handling carriage returns."""
        buffer = ""
        while True:
            try:
                char = stream.read(1)
            except UnicodeDecodeError:
                continue
            if not char:
                if buffer:
                    self.output_queue.put((stream_type, buffer.strip()))
                break
            if char in ['\r', '\n']:
                if buffer:
                    self.output_queue.put((stream_type, buffer.strip()))
                    buffer = ""
            else:
                buffer += char
        stream.close()

    def get_messages(self):
        """Returns all available messages from the queue without blocking. 不阻塞地从队列返回所有消息"""
        messages = []
        while not self.output_queue.empty():
            try:
                messages.append(self.output_queue.get_nowait())
            except queue.Empty:
                break
        return messages
