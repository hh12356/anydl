import flet as ft
from core.manager import DownloadManager
import os
import asyncio
import re #正则表达式
import json
from pathlib import Path #文件路径工具

def get_spotdl_config_path():
    #os.path.expanduser("~"):把~解析为登录用户文件夹
    return os.path.join(os.path.expanduser("~"), ".config", "spotdl", "config.json")

def load_spotdl_config():
    path = get_spotdl_config_path()
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                #从文件对象读取JSON文本，直接转换成Python对象（dict / list）
                return json.load(f)
        except:
            pass
    return {}

def save_spotdl_config(data):
    path = get_spotdl_config_path()
    #建父目录
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        #将data写入文件，缩进为4
        json.dump(data, f, indent=4)

#读cookie用的浏览器，写死火狐。
#Windows上Chrome/Edge的cookie被App-Bound加密了，yt-dlp解不开，会报
#"Failed to decrypt with DPAPI"(yt-dlp issue #1097)。列出来的可选浏览器里
#只有firefox不是那套机制，所以不给用户选了，省得选完一脸问号
COOKIE_BROWSER = "firefox"

def normalize_trim_time(raw, field_name):
    """把裁剪时间统一成 yt-dlp 认的 HH:MM:SS。
    偷懒写法也收：SS、MM:SS 都行，缺的部分补 00。
    返回 (规范化后的字符串, 错误信息)。错误信息是 None 表示通过；
    返回空字符串表示这一项没填。"""
    s = (raw or "").strip()
    if not s:
        return "", None

    #中文输入法下冒号会打成全角，数字也可能是全角。yt-dlp拿到只会甩个看不懂的错，
    #所以在这里先拦下来，并且指出到底是哪个字符不对。
    #中文输入法会把冒号打成全角。三种长得几乎一样的全角冒号都列上，
    #码点写注释里是因为代码里半角全角肉眼分不出来，只能靠码点核对：
    #第一个是常见的全角冒号 U+FF1A，后面两个是变体 U+2236 / U+FE55
    FULLWIDTH_COLONS = "：∶﹕"
    for ch in s:
        if ch in FULLWIDTH_COLONS:
            return None, f"{field_name}: full-width colon '{ch}'. Use the half-width ':' instead."
        if ch.isdigit() and not ch.isascii():
            return None, f"{field_name}: full-width digit '{ch}'. Switch the input method to half-width."
        if ch not in "0123456789:. ":
            return None, f"{field_name}: unexpected character '{ch}'. Use SS, MM:SS or HH:MM:SS."

    parts = [p.strip() for p in s.split(":")]
    if len(parts) > 3 or any(p == "" for p in parts):
        return None, f"{field_name}: '{s}' is not a valid time. Use SS, MM:SS or HH:MM:SS."

    #不足三段就从左边补 00，这样下面只用处理一种形状
    parts = ["00"] * (3 - len(parts)) + parts
    try:
        h, m, sec = int(parts[0]), int(parts[1]), float(parts[2])
    except ValueError:
        return None, f"{field_name}: '{s}' has something in it that isn't a number."

    #先按秒归一，多出来的进位。用户写"90"就是想要90秒，直接报"秒不能超过60"太挡路，
    #进位成00:01:30更顺手。先round再拆，否则59.999会被格式化成"60"
    total = round(h * 3600 + m * 60 + sec, 2)
    h, rem = divmod(total, 3600)
    m, sec = divmod(rem, 60)

    #秒是整数就别写成 5.0，yt-dlp认但看着别扭
    sec_text = f"{sec:05.2f}".rstrip("0").rstrip(".").zfill(2)
    return f"{int(h):02d}:{int(m):02d}:{sec_text}", None

async def main_app(page: ft.Page):
    page.title = "anydl"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = ft.Colors.GREY_50 #设置背景颜色

    manager = DownloadManager()

    # Load spotdl config
    spotdl_config = load_spotdl_config()
    current_client_id = spotdl_config.get("client_id", "")
    current_client_secret = spotdl_config.get("client_secret", "")
    #检测到公用id，清空重新生成
    if current_client_id == "5f573c9620494bae87890c0f08a60293":
        current_client_id = ""
        current_client_secret = ""

    #输入框
    client_id_field = ft.TextField(label="Spotify Client ID", value=current_client_id, password=True, can_reveal_password=True)
    client_secret_field = ft.TextField(label="Spotify Client Secret", value=current_client_secret, password=True, can_reveal_password=True)

    #抖音这种站点要"新鲜的访客cookie"。用--cookies-from-browser让yt-dlp每次去火狐现读，
    #比手动导出cookies.txt好：只要在火狐里访问过该站点，cookie就一直是新鲜的，永不过期。
    #不需要登录，打开过网站就行。火狐是写死的(见 COOKIE_BROWSER)，所以这里没有下拉框

    def save_settings_click(e):
        #strip去掉首尾空格 带默认公用id密匙
        spotdl_config["client_id"] = client_id_field.value.strip() or "5f573c9620494bae87890c0f08a60293"
        spotdl_config["client_secret"] = client_secret_field.value.strip() or "212476d9b0f3472eaa762d90b19b0ba8"
        save_spotdl_config(spotdl_config)

        if current_tool_id == "music":
            if spotdl_config.get("client_id", "") != "5f573c9620494bae87890c0f08a60293":
                spotify_api_info_text.value = "Currently using: Custom API"
            else:
                spotify_api_info_text.value = "Currently using: Default Built-in API (May face rate limits)"

        #关闭设置弹窗
        settings_dlg.open = False
        page.update()

    settings_dlg = ft.AlertDialog(
        title=ft.Text("Settings"),
        content=ft.Column([
            ft.Text("Custom Spotify API Keys (Optional - Bypasses Rate Limits)", weight=ft.FontWeight.BOLD),
            ft.TextButton("Open Spotify Developer Dashboard", icon=ft.Icons.OPEN_IN_NEW, url="https://developer.spotify.com/dashboard", style=ft.ButtonStyle(color=ft.Colors.BLUE)),
            ft.Text("Leave blank to use the default built-in API.", size=12, color=ft.Colors.GREY_600),
            client_id_field,
            client_secret_field,
            ft.Divider(),
            ft.Text("Douyin Cookies (Firefox Only)", weight=ft.FontWeight.BOLD),
            ft.Text("Douyin needs fresh visitor cookies, and Firefox is the only browser "
                    "anydl can read them from. Open douyin.com in Firefox once - logging in "
                    "is not required.\n"
                    "Chrome and Edge will not work: Windows encrypts their cookies in a way "
                    "yt-dlp cannot decrypt.",
                    size=12, color=ft.Colors.GREY_600),
        ], tight=True),
        actions=[
            #setattr():赋值
            ft.TextButton("Cancel", on_click=lambda e: setattr(settings_dlg, 'open', False) or page.update()),
            ft.TextButton("Save", on_click=save_settings_click)
        ]
    )

    def open_settings(e):
        #必须先放进overlay才能用.open=True显示
        if settings_dlg not in page.overlay:
            page.overlay.append(settings_dlg)
        settings_dlg.open = True
        page.update()

    settings_btn = ft.IconButton(
        icon=ft.Icons.SETTINGS,
        #tooltip:鼠标悬浮时弹出的提示
        tooltip="Settings",
        on_click=open_settings
    )

    # Determine default download path 确定默认下载路径
    default_download_path = os.path.join(os.path.expanduser("~"), "Downloads", "ANYDL")

    # Removed FilePicker for Web Compatibility 移除文件选择器，提升网页兼容性

    #视频窗口里站点不再让用户选，粘什么下什么，所以这些站点差异只能从URL自己认。
    #direct:  国内站点绕开系统代理直连。yt-dlp会自动读Windows注册表里的系统代理，
    #         用户开着Clash的话请求就从境外节点出去，b站/抖音看到境外IP直接风控
    #         (抖音返回403，报出来却是"Fresh cookies are needed"——非常误导)
    #cookies: 抖音要新鲜的访客cookie，从火狐现读，不用登录，在火狐里打开过一次站点就行
    SITE_RULES = {
        "bilibili.com": {"direct": True},
        "b23.tv": {"direct": True},        #b站短链
        "douyin.com": {"direct": True, "cookies": True},
        "iesdouyin.com": {"direct": True, "cookies": True},
    }

    def site_rule(url):
        """按URL里出现的域名查上面那张表，认不出来就返回空规则，当普通站点处理"""
        host = (url or "").lower()
        for domain, rule in SITE_RULES.items():
            #用 in 而不是 endswith("."+domain)：这样 v.douyin.com、b23.tv 这类
            #子域和短链都能盖住。代价是理论上 notbilibili.com 会误判，但下载器这场景无所谓
            if domain in host:
                return rule
        return {}

    #首页就两张卡。视频那些站全走同一个引擎(yt-dlp)，站点差异见上面的 SITE_RULES；
    #音乐那边是引擎不同(spotdl/scdl)，所以在 start_download 里按域名分
    TOOLS = {
        "video": {
            "name": "Video Downloader",
            "desc": "YouTube, Bilibili, Douyin, TikTok, Facebook, Instagram, X",
            "hint": "Paste any video URL",
            "color": ft.Colors.RED_600,
            "icon": ft.Icons.VIDEO_LIBRARY
        },
        "music": {
            "name": "Music Downloader",
            "desc": "Spotify & SoundCloud to MP3",
            "hint": "Paste Spotify/SoundCloud URL, or search",
            "color": "#21c25e",
            "icon": ft.Icons.LIBRARY_MUSIC
        },
    }

    current_tool_id = "video" # Default placeholder 默认占位符

    # -------------------------------------------------------------
    # Shared State & Elements
    # -------------------------------------------------------------
    home_title = ft.Text("What would you like to download?", size=32, weight=ft.FontWeight.W_500, color=ft.Colors.BLACK)
    tool_title = ft.Text("", size=36, color=ft.Colors.BLACK, weight=ft.FontWeight.W_400)
    tool_desc = ft.Text("", size=16, color=ft.Colors.GREY_700)
    
    url_input = ft.TextField(
        border=ft.InputBorder.NONE,
        expand=True,
        color=ft.Colors.BLACK,
        cursor_color=ft.Colors.BLACK,
        hint_style=ft.TextStyle(color=ft.Colors.GREY_500),
        content_padding=ft.Padding.only(left=15, right=15, top=10, bottom=10)
    )
    
    search_border = ft.Container(
        content=url_input,
        border_radius=ft.BorderRadius.only(top_left=4, bottom_left=4),
        bgcolor=ft.Colors.WHITE,
        expand=True,
        height=50,
        padding=0
    )
    
    download_btn_container = ft.Container(
        content=ft.Row([
            ft.Text("Download", color=ft.Colors.WHITE, weight=ft.FontWeight.W_500, size=16),
            ft.Icon(ft.Icons.DOWNLOAD, color=ft.Colors.WHITE, size=20)
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=5),#设置控件居中
        padding=ft.Padding.only(left=20, right=20),
        border_radius=ft.BorderRadius.only(top_right=4, bottom_right=4),
        height=50,
        ink=True
    )



    #这一行里所有控件的统一高度，保证永远齐平。
    #要调只改这一处，别只改其中一个控件——之前"两个框不一样高"就是这么来的
    OPTION_H = 56

    # Format Selector (yt-dlp only)
    format_dropdown = ft.Dropdown(
        options=[
            ft.dropdown.Option("video", text="Best Video (MP4)"),
            ft.dropdown.Option("audio", text="Audio Only (MP3)"),
        ],
        value="video",
        width=180,
        height=OPTION_H,
        content_padding=ft.Padding.only(left=10, right=10),
        text_size=12,
        visible=False
    )

    #裁剪时间段输入框（只有走yt-dlp引擎的工具才显示）
    #偷懒写法都收：SS、MM:SS、HH:MM:SS，开跑前由 normalize_trim_time 统一补成 HH:MM:SS。
    #两个都留空 = 不裁剪，下载整个视频；只填结束、开始留空 = 从0开始
    #别用dense=True：dense是"砍掉竖向留白"，已经定了高度再叠dense等于压两遍，框会变得很扁
    trim_start_field = ft.TextField(
        hint_text="Start (SS/MM:SS)",
        tooltip="SS, MM:SS or HH:MM:SS. Empty = from the beginning.",
        width=175, height=OPTION_H, text_size=12,
        content_padding=ft.Padding.symmetric(vertical=10, horizontal=10)
    )
    trim_end_field = ft.TextField(
        hint_text="End (empty = to end)",
        tooltip="SS, MM:SS or HH:MM:SS. Empty = keep to the end.",
        width=185, height=OPTION_H, text_size=12,
        content_padding=ft.Padding.symmetric(vertical=10, horizontal=10)
    )

    #另开文件夹勾选框
    playlist_checkbox = ft.Checkbox(label="Create separate folder for playlist", value=False)
    #第一行：格式选择 + 两个裁剪框
    #这里不用wrap=True自动换行。Flutter的Wrap在宽度宽松时会缩到"最宽那一行"的宽度，
    #居中基准跟着缩，换下去那行就偏了(试过套一层Row+expand撑宽也没用)。
    #直接拆成两行写死，各自CENTER，结果就是确定的
    options_row = ft.Row(
        [format_dropdown, trim_start_field, trim_end_field],
        alignment=ft.MainAxisAlignment.CENTER, spacing=20
    )
    #第二行：勾选框自己一行，居中
    playlist_row = ft.Row(
        [playlist_checkbox],
        alignment=ft.MainAxisAlignment.CENTER
    )
    
    spotify_api_info_text = ft.Text("", size=12, color=ft.Colors.GREY_600, visible=False, italic=True)

    #抖音专属提示，粘了抖音链接才显示。yt-dlp要读火狐里的访客cookie，
    #没先在火狐里打开过一次抖音的话，会报"Fresh cookies ... are needed"。
    #站点合并之后别的站都不需要火狐，所以开头就把"只有抖音要"说清楚，
    #免得用户以为下个YouTube也得装火狐
    douyin_cookie_hint = ft.Column([
        ft.Text("Only Douyin needs Firefox. Open douyin.com in Firefox once "
                "(no login needed) so anydl can read the visitor cookies; "
                "every other site works without it.",
                size=12, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
        ft.TextButton("Download Firefox", icon=ft.Icons.OPEN_IN_NEW,
                      url="https://www.mozilla.org/firefox/new/",
                      style=ft.ButtonStyle(color=ft.Colors.BLUE)),
    ], width=600, spacing=0, visible=False,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def on_url_change(e):
        #粘进来是抖音链接才提示火狐那件事。一直挂着太占地方，视频窗口是"什么都能粘"的
        douyin_cookie_hint.visible = "douyin" in (url_input.value or "").lower()
        page.update()

    url_input.on_change = on_url_change

    #日志 自动滚动到底部
    log_area = ft.ListView(expand=True, spacing=5, auto_scroll=True)
    
    # Progress Bar (hidden by default, starts indeterminate) 进度条（默认隐藏，初始为不确定模式）
    progress_bar = ft.ProgressBar(width=400, color=ft.Colors.BLUE_400, bgcolor=ft.Colors.GREY_200, value=None)
    progress_text = ft.Text("0%", size=12, color=ft.Colors.GREY_600)
    progress_container = ft.Container(
        content=ft.Row([progress_bar, progress_text], alignment=ft.MainAxisAlignment.CENTER), 
        margin=ft.Margin.only(top=10, bottom=10), 
        visible=False
    )

    log_container = ft.Container(
        content=log_area,
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, ft.Colors.GREY_200),
        border_radius=ft.BorderRadius.all(4),
        padding=10,
        margin=ft.Margin.only(top=10),
        height=200,
        visible=False
    )

    # -------------------------------------------------------------
    # Logic & Background Processes
    # -------------------------------------------------------------
    # State for tracking playlist progress 用于跟踪播放列表进度的状态
    playlist_state = {"total": 0, "downloaded": 0}

    def log_message(msg_type, msg, batch_update=False):
        color = ft.Colors.BLACK
        if msg_type == "ERROR":
            color = ft.Colors.RED_400
        elif msg_type == "STATUS":
            color = ft.Colors.BLUE_400
        elif msg_type == "STDERR":
            color = ft.Colors.ORANGE_400

        #append进log，加载进度除外
        if not re.search(r'(\d{1,3}(?:\.\d+)?)%', msg):
            log_area.controls.append(ft.Text(f"[{msg_type}] {msg}", color=color, font_family="monospace", size=12))
        
        # Parse percentage from log output 从日志输出中解析百分比
        if msg_type in ["STDOUT", "STDERR"]:
            # 1. Look for explicit percentages (e.g. yt-dlp) 查找明确的百分比（例如 yt-dlp）
            match = re.search(r'(\d{1,3}(?:\.\d+)?)%', msg)
            if match:
                try:
                    pct = float(match.group(1))
                    if 0 <= pct <= 100:
                        progress_bar.value = pct / 100.0
                        progress_text.value = f"{pct:.1f}%"
                except ValueError:
                    pass
            
            # 2. Look for spotdl playlist total 查找 spotdl 播放列表总数
            total_match = re.search(r'Found (\d+) songs', msg)
            if total_match:
                #.group(1):第一个括号内的内容(str)
                playlist_state["total"] = int(total_match.group(1))
                playlist_state["downloaded"] = 0
                progress_bar.value = 0.0
                progress_text.value = "0%"

            # 3. Look for spotdl downloaded song 查找 spotdl 下载的歌曲
            if "Downloaded \"" in msg and playlist_state["total"] > 0:
                playlist_state["downloaded"] += 1
                pct = (playlist_state["downloaded"] / playlist_state["total"]) * 100
                progress_bar.value = pct / 100.0
                progress_text.value = f"{pct:.1f}%"

        # Hide loading spinner if process finished 进程完成时隐藏加载动画
        if "Process finished" in msg or msg_type == "ERROR":
            progress_bar.visible = False
            progress_container.visible = False
            progress_bar.value = None
            progress_text.value = "0%"
            download_btn_container.disabled = False
            url_input.disabled = False
            format_dropdown.disabled = False
            trim_start_field.disabled = False
            trim_end_field.disabled = False
            playlist_checkbox.disabled = False

            if "Process finished with exit code 0" in msg:
                if playlist_state["total"] > 0:
                    success_count = playlist_state["downloaded"]
                    failed_count = playlist_state["total"] - success_count
                    msg_text = f"Download completed!\n\nTotal: {playlist_state['total']}\nSuccess: {success_count}\nFailed/Missing: {failed_count}"
                else:
                    msg_text = "Download completed successfully!"
                    
                #弹窗提示框
                dlg = ft.AlertDialog(title=ft.Text("Success"), content=ft.Text(msg_text))
                def close_success(e, d=dlg):
                    d.open = False
                    page.update()
                dlg.actions = [ft.TextButton("OK", on_click=close_success)]
                page.overlay.append(dlg)
                dlg.open = True
            else:
                dlg = ft.AlertDialog(title=ft.Text("Error"), content=ft.Text("Download failed. Please check the logs for details."))
                def close_error(e, d=dlg):
                    d.open = False
                    page.update()
                dlg.actions = [ft.TextButton("OK", on_click=close_error)]
                page.overlay.append(dlg)
                dlg.open = True

        log_container.visible = True
        if not batch_update:
            page.update()

    def start_download(e):
        url = (url_input.value or "").strip()
        #分享文案整段粘进来的处理。b站/抖音的分享文本长这样：
        #"【标题】 https://v.douyin.com/xxxx 复制此链接打开抖音"，砍掉链接前后的中文废话。
        #对YouTube这种本来就只有一条链接的，这几行等于什么也没做
        start = url.find("https")
        if start != -1:   #find找不到会返回-1，不判断的话 url[-1:] 会取到最后一个字符
            url = url[start:]
        idx = url.rfind("复")
        if idx != -1:
            url = url[:idx]
        url = url.strip()

        if not url:
            log_message("ERROR", "URL cannot be empty")
            return

        #窗口ID -> 真正跑的引擎。视频窗口只有一个引擎；音乐窗口有俩，按域名分，
        #认不出来就交给spotdl，它支持直接敲关键词搜歌
        if current_tool_id == "video":
            engine = "yt-dlp"
        else:
            engine = "scdl" if "soundcloud.com" in url.lower() else "spotdl"

        #站点特殊规则(关代理/读cookie)，只对yt-dlp有意义
        rule = site_rule(url) if engine == "yt-dlp" else {}

        #裁剪时间开跑前先检查并规范化。中文输入法打出的全角冒号，yt-dlp只会甩个看不懂的
        #报错，不如在这里说清楚；顺便把"1:30"这种偷懒写法补成 yt-dlp 认的 HH:MM:SS
        trim_start, trim_end = "", ""
        if engine == "yt-dlp":
            trim_start, err = normalize_trim_time(trim_start_field.value, "Trim start")
            if err:
                log_message("ERROR", err)
                return
            trim_end, err = normalize_trim_time(trim_end_field.value, "Trim end")
            if err:
                log_message("ERROR", err)
                return
            #规范化结果写回输入框，用户能直接看到自己填的"1:30"变成了"00:01:30"
            trim_start_field.value = trim_start
            trim_end_field.value = trim_end
            page.update()



        # Ensure target directory exists
        target_dir = default_download_path
            
        try:
            Path(target_dir).mkdir(parents=True, exist_ok=True)
        except Exception as ex:
            log_message("ERROR", f"Failed to create directory: {ex}")
            return

        # Show loading state and reset progress
        playlist_state["total"] = 0
        playlist_state["downloaded"] = 0
        progress_bar.value = None
        progress_text.value = "0%"
        progress_bar.visible = True
        progress_container.visible = True
        download_btn_container.disabled = True
        url_input.disabled = True
        format_dropdown.disabled = True
        trim_start_field.disabled = True
        trim_end_field.disabled = True
        playlist_checkbox.disabled = True
        page.update()

        command = [engine]
        if engine == "yt-dlp":
            #格式设置
            if format_dropdown.value == "audio":
                command.extend(["-x", "--audio-format", "mp3"])
            elif format_dropdown.value == "video":
                command.extend(["--merge-output-format", "mp4"])
            if playlist_checkbox.value:
                command.extend(["-o", "anydl@sytrus - %(playlist)s/%(title)s.%(ext)s"])

            #cookie：抖音要，从火狐现读，浏览器固定火狐(见 COOKIE_BROWSER)
            if rule.get("cookies"):
                command.extend(["--cookies-from-browser", COOKIE_BROWSER])

            #国内站点强制直连。--proxy "" 是yt-dlp关代理的写法，
            #不加的话系统代理(Clash等)会被自动套上，抖音会因境外IP返回403
            if rule.get("direct"):
                command.extend(["--proxy", ""])

            #裁剪。trim_start/trim_end 是上面规范化过的，这里直接拼就行
            if trim_start or trim_end:
                command.extend(["--download-sections", f"*{trim_start or '00:00:00'}-{trim_end or 'inf'}"])
                #裁一段必定走ffmpeg，而ffmpeg默认是info级别日志，会往stderr吐一大堆自报家门的话：
                #"Metadata: / Stream #0:0 / Stream mapping: / Press [q] to stop / [libx264] using cpu
                #capabilities"，重编码时还每半秒刷一行"frame= 289 fps= 60 q=28.0 size=..."。
                #橙色堆满日志看着像报错，其实一条有用的都没有。压到warning级别，真警告和报错照旧。
                #这些是ffmpeg直接写stderr的，yt-dlp不读也不解析(见downloader/external.py的FFmpegFD，
                #它只等进程结束)，所以压掉不影响下载进度条。看进度条就行，别指望这期间的日志
                command.extend(["--downloader-args", "ffmpeg:-loglevel warning"])

                #关键帧重切。不加这个参数时yt-dlp是 -c copy 直接拷流，只能在关键帧上下刀：
                #HEVC常用open GOP，切口那几个前导帧解码时依赖前面的帧，拷出来时间戳是负的
                #(-6.23s这种)，播放器一律丢掉，开头就花/卡。加了就让ffmpeg重编码，刀口精确。
                #代价：这一条视频从 4秒/8.6MB 变成 11秒/27MB，编码也从HEVC变H.264。
                #只下音频时不加：音频流没这个问题，视频反正转完mp3就扔了，重编码纯浪费时间
                if format_dropdown.value != "audio":
                    command.extend(["--force-keyframes-at-cuts"])
        elif engine == "spotdl":
            if playlist_checkbox.value:
                command.extend(["--output", "anydl@sytrus - {list-name}/{artists} - {title}.{output-ext}"])
        elif engine == "scdl":
            command.extend(["-l"]) # scdl requires -l for the URL
            
        command.append(url)

        manager.start_download(command, cwd=target_dir)
        url_input.value = ""
        page.update()

    download_btn_container.on_click = start_download

    #轮询队列
    async def poll_queue(e=None):
        while True:
            messages = manager.get_messages()
            if messages:
                for msg_type, msg in messages:
                    log_message(msg_type, msg, batch_update=True)
                page.update()
            await asyncio.sleep(0.1)

    page.run_task(poll_queue)

    # -------------------------------------------------------------
    # Navigation Methods
    # -------------------------------------------------------------
    def show_home():
        tool_view.visible = False
        home_view.visible = True
        url_input.value=''
        page.update()

    #切换主题
    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.DARK
            page.bgcolor = ft.Colors.BLACK
            header.bgcolor = ft.Colors.SURFACE_CONTAINER_LOW
            footer.bgcolor = ft.Colors.BLACK
            header.border = ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_900))
            theme_btn.icon = ft.Icons.LIGHT_MODE
            logo_dl_text.color = ft.Colors.WHITE
            
            # Home View Colors
            home_title.color = ft.Colors.WHITE

            # Tool View Colors
            tool_title.color = ft.Colors.WHITE
            tool_desc.color = ft.Colors.GREY_400
            url_input.color = ft.Colors.BLACK # Keep input text readable in white box
            back_button.style = ft.ButtonStyle(color=ft.Colors.GREY_400)
            format_dropdown.color = ft.Colors.WHITE

            # Update cards to dark mode
            for card in cards:
                card.bgcolor = ft.Colors.GREY_900
                card.border = ft.Border.all(1, ft.Colors.GREY_800)
                card.content.controls[2].color = ft.Colors.WHITE # Name text
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            page.bgcolor = ft.Colors.GREY_50
            header.bgcolor = ft.Colors.WHITE
            footer.bgcolor = ft.Colors.GREY_50
            header.border = ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200))
            theme_btn.icon = ft.Icons.DARK_MODE
            logo_dl_text.color = ft.Colors.BLACK

            # Home View Colors
            home_title.color = ft.Colors.BLACK

            # Tool View Colors
            tool_title.color = ft.Colors.BLACK
            tool_desc.color = ft.Colors.GREY_700
            url_input.color = ft.Colors.BLACK
            back_button.style = ft.ButtonStyle(color=ft.Colors.GREY_700)
            format_dropdown.color = ft.Colors.BLACK

            # Update cards to light mode
            for card in cards:
                card.bgcolor = ft.Colors.WHITE
                card.border = ft.Border.all(1, ft.Colors.GREY_200)
                card.content.controls[2].color = ft.Colors.BLACK # Name text
        page.update()

    theme_btn = ft.IconButton(
        icon=ft.Icons.DARK_MODE,
        tooltip="Toggle Theme",
        on_click=toggle_theme
    )

    def show_tool(tool_id):
        #拿到外层函数定义的变量
        nonlocal current_tool_id
        current_tool_id = tool_id
        t = TOOLS[tool_id]
        
        tool_title.value = t["name"]
        tool_desc.value = t["desc"]
        url_input.hint_text = t["hint"]
        search_border.border = ft.Border.all(2, t["color"])
        download_btn_container.bgcolor = t["color"]
        
        #格式和裁剪只有视频窗口有，音乐那两个引擎(spotdl/scdl)不认这些参数
        is_video = tool_id == "video"
        format_dropdown.visible = is_video
        format_dropdown.disabled = not is_video
        trim_start_field.visible = is_video
        trim_end_field.visible = is_video

        #切换工具时清空裁剪输入
        trim_start_field.value = ""
        trim_end_field.value = ""

        if tool_id == "music":
            current_conf = load_spotdl_config()
            if current_conf.get("client_id", "") and current_conf.get("client_id", "") != "5f573c9620494bae87890c0f08a60293":
                spotify_api_info_text.value = "Currently using: Custom API"
            else:
                spotify_api_info_text.value = "Currently using: Default Built-in API (May face rate limits)"
            spotify_api_info_text.visible = True
        else:
            spotify_api_info_text.visible = False

        #抖音提示只在粘了抖音链接时才冒出来(见 url_input.on_change)，别的时候不占地方
        douyin_cookie_hint.visible = False

        log_area.controls.clear()
        log_container.visible = False

        home_view.visible = False
        tool_view.visible = True
        page.update()

    # -------------------------------------------------------------
    # Tool View
    # -------------------------------------------------------------
    back_button = ft.TextButton(
        "Back to Home", 
        icon=ft.Icons.ARROW_BACK,
        on_click=lambda _: show_home(),
        style=ft.ButtonStyle(color=ft.Colors.GREY_700)
    )

    tool_view = ft.Container(
        visible=False,
        expand=True,
        content=ft.Column(
            [
                ft.Container(
                    content=back_button,
                    alignment=ft.Alignment(-1, -1),
                    padding=ft.Padding.only(left=20, top=20)
                ),
                ft.Container(height=20),
                tool_title,
                tool_desc,
                ft.Container(height=30),
                ft.Row(
                    [
                        search_border,
                        download_btn_container
                    ],
                    spacing=0,
                    width=700
                ),
                progress_container,
                ft.Container(height=10),
                options_row,
                playlist_row,
                spotify_api_info_text,
                douyin_cookie_hint,
                log_container
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        )
    )

    # -------------------------------------------------------------
    # Home View
    # -------------------------------------------------------------
    cards = []
    for t_id, t_data in TOOLS.items(): #键值对
        card = ft.Container(
            content=ft.Column([
                ft.Icon(t_data["icon"], size=48, color=t_data["color"]),
                ft.Container(height=10),
                ft.Text(t_data["name"], size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                ft.Text(t_data["desc"], size=12, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            width=280,
            height=220,
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=ft.BorderRadius.all(8),
            border=ft.Border.all(1, ft.Colors.GREY_200),
            ink=True,
            on_click=lambda e, id=t_id: show_tool(id)
        )
        cards.append(card)

    home_view = ft.Container(
        visible=True,
        expand=True,
        content=ft.Column([
            ft.Container(height=40),
            home_title,
            ft.Container(height=40),
            #就两张卡了，不用GridView——它按列宽铺，两张会全挤在左边。
            #也别套wrap=True自动换行，Flet里Wrap的宽度是按"最宽那一行"算的，居中基准会跟着跑
            ft.Row(cards, alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

    # -------------------------------------------------------------
    # Header, Footer & Assembly 页眉、页脚与组件
    # -------------------------------------------------------------
    logo_dl_text = ft.TextSpan("DL", style=ft.TextStyle(color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD, size=22))

    header = ft.Container(
        content=ft.Row([
            ft.Container(
                content=ft.Row([
                    ft.Text(spans=[
                        ft.TextSpan("ANY", style=ft.TextStyle(color="#21c25e", weight=ft.FontWeight.BOLD, size=22)),
                        logo_dl_text,
                    ])
                ]),
                on_click=lambda _: show_home()
            ),
            ft.Row([settings_btn, theme_btn])
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.Padding.only(left=30, right=30, top=10, bottom=10),
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200))
    )

    footer = ft.Container(
        content=ft.Row([
            ft.Text("See repository at", size=12, color=ft.Colors.GREY_600),
            ft.TextButton(
                "hh12356/anydl",
                url="https://github.com/hh12356/anydl",
                style=ft.ButtonStyle(color="#21c25e", padding=ft.Padding.all(0))
            )
        ], alignment=ft.MainAxisAlignment.CENTER),
        padding=ft.Padding.only(bottom=20)
    )

    page.add(
        ft.Column([
            header,
            ft.Container(content=ft.Column([home_view, tool_view], expand=True), expand=True),
            footer
        ], expand=True, spacing=0)
    )

