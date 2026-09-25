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

    def save_settings_click(e):
        #strip去掉首尾空格 带默认公用id密匙
        spotdl_config["client_id"] = client_id_field.value.strip() or "5f573c9620494bae87890c0f08a60293"
        spotdl_config["client_secret"] = client_secret_field.value.strip() or "212476d9b0f3472eaa762d90b19b0ba8"
        save_spotdl_config(spotdl_config)
        
        if current_tool_id == "spotdl":
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
            client_secret_field
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

    TOOLS = {
        "bilibili": {
            "name": "Bilibili Downloader",
            "desc": "Bilibili to Video/Audio",
            "hint": "Paste Bilibili URL (You may keep the title)",
            "color": ft.Colors.PINK_400,
            "icon": ft.Icons.LIVE_TV
        },
        "douyin": {
            "name": "Douyin Downloader",
            "desc": "Douyin to Video/Audio",
            "hint": "Paste Douyin URL (You may keep the full link)",
            "color": ft.Colors.BLACK,
            "icon": ft.Icons.TIKTOK
        },
        "spotdl": {
            "name": "Spotify Downloader",
            "desc": "Spotify track/playlist to MP3",
            "hint": "Paste Spotify URL or search",
            "color": "#21c25e",
            "icon": ft.Icons.LIBRARY_MUSIC
        },
        "yt-dlp": {
            "name": "YouTube Downloader",
            "desc": "YouTube to Video/Audio",
            "hint": "Paste YouTube URL or search",
            "color": ft.Colors.RED_600,
            "icon": ft.Icons.VIDEO_LIBRARY
        },
        "tiktok": {
            "name": "TikTok Downloader",
            "desc": "TikTok Video to MP4",
            "hint": "Paste TikTok URL",
            "color": ft.Colors.CYAN_400,
            "icon": ft.Icons.MUSIC_VIDEO
        },
        "facebook": {
            "name": "Facebook Downloader",
            "desc": "Facebook Reels to Video/Audio",
            "hint": "Paste Facebook Video URL",
            "color": ft.Colors.BLUE_800,
            "icon": ft.Icons.FACEBOOK
        },
        "instagram": {
            "name": "Instagram Reels",
            "desc": "Instagram Reels to Video/Audio ",
            "hint": "Paste Instagram URL",
            "color": ft.Colors.PINK_500,
            "icon": ft.Icons.CAMERA_ALT
        },
        "twitter": {
            "name": "X (Twitter)",
            "desc": "X to Video/Audio",
            "hint": "Paste X/Twitter URL",
            "color": ft.Colors.BLACK,
            "icon": ft.Icons.WEB
        },
        "scdl": {
            "name": "SoundCloud Downloader",
            "desc": "SoundCloud to MP3",
            "hint": "Paste SoundCloud URL (Track or Playlist)",
            "color": ft.Colors.ORANGE_700,
            "icon": ft.Icons.CLOUD_DOWNLOAD
        },
    }
    
    current_tool_id = "yt-dlp" # Default placeholder 默认占位符

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



    # Format Selector (yt-dlp only)
    format_dropdown = ft.Dropdown(
        options=[
            ft.dropdown.Option("video", text="Best Video (MP4)"),
            ft.dropdown.Option("audio", text="Audio Only (MP3)"),
        ],
        value="video",
        width=180,
        height=40,
        content_padding=ft.Padding.only(left=10, right=10),
        text_size=12,
        visible=False
    )

    #另开文件夹勾选框
    playlist_checkbox = ft.Checkbox(label="Create separate folder for playlist", value=False)
    options_row = ft.Row([format_dropdown, playlist_checkbox], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
    
    spotify_api_info_text = ft.Text("", size=12, color=ft.Colors.GREY_600, visible=False, italic=True)

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
        url = url_input.value
        #针对bilibili,douyin链接的处理
        if current_tool_id in ["douyin","bilibili"]:
            url = url[url.find("https"):]
            idx = url.rfind("复")
            if idx != -1:
                url = url[:idx]

        if not url:
            log_message("ERROR", "URL cannot be empty")
            return
            
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
        playlist_checkbox.disabled = True
        page.update()

        # Map UI tool IDs to actual CLI engines 将界面工具ID映射至实际命令行引擎
        engine = current_tool_id
        if current_tool_id in ["tiktok", "facebook", "instagram", "twitter", "bilibili", "douyin"]:
            engine = "yt-dlp"

        command = [engine]
        if engine == "yt-dlp":
            #格式设置
            if format_dropdown.value == "audio":
                command.extend(["-x", "--audio-format", "mp3"])
            elif format_dropdown.value == "video":
                command.extend(["--merge-output-format", "mp4"])
            if playlist_checkbox.value:
                command.extend(["-o", "anydl@sytrus - %(playlist)s/%(title)s.%(ext)s"])
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
        
        # Tools using yt-dlp engine support format selection
        if tool_id in ["yt-dlp", "tiktok", "facebook", "instagram", "twitter", "bilibili", "douyin"]:
            format_dropdown.visible = True
            format_dropdown.disabled = False
        else:
            format_dropdown.visible = False
            
        if tool_id == "spotdl":
            current_conf = load_spotdl_config()
            if current_conf.get("client_id", "") and current_conf.get("client_id", "") != "5f573c9620494bae87890c0f08a60293":
                spotify_api_info_text.value = "Currently using: Custom API"
            else:
                spotify_api_info_text.value = "Currently using: Default Built-in API (May face rate limits)"
            spotify_api_info_text.visible = True
        else:
            spotify_api_info_text.visible = False

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
                spotify_api_info_text,
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
            ft.GridView(
                expand=True,
                runs_count=3,
                max_extent=300,
                child_aspect_ratio=1.3,
                spacing=20,
                run_spacing=20,
                controls=cards,
                padding=ft.Padding.only(left=40, right=40)
            )
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
                "sytrusz/anydl",
                url="https://github.com/sytrusz/anydl",
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

