; anydl 自解压启动器（NSIS 脚本）
;
; 作用：把 PyInstaller 打出来的 dist\anydl 文件夹包成单个 exe。
; 第一次双击：解压到目标目录（慢，要等一会儿）并启动；
; 之后每次双击：检测到已经解压过，跳过解压直接启动（快）。
;
; 编译：makensis installer.nsi     产物 anydl.exe 出现在本文件同级目录
;
; 注意这不是安装包：不写注册表、不加卸载项、不问安装路径。卸载 = 删掉解压出来的文件夹。

Unicode true
Name "anydl"
OutFile "anydl.exe"
SetCompressor /SOLID lzma   ; 压缩率高，300MB 的文件夹能压到一半以下

; 兜底目录：exe 放在哪个盘，就解压到哪个盘的 anydl 文件夹
InstallDir "$EXEDIR\anydl"
; 不往 Program Files 写，所以不需要管理员权限
RequestExecutionLevel user
; 不显示安装向导，双击就开始干活
SilentInstall normal

!include LogicLib.nsh
Page instfiles
ShowInstDetails show

Section
  ; 第一步：先定好解压到哪个目录，再去查"解压完成"标记。
  ; 顺序不能反 —— 要是先按兜底路径查标记，第二次运行时标记在 D 盘、查的是 C 盘，
  ; 会以为没解压过，于是每次都重解压一遍（三分钟），"首次自解压"就白做了。
  ;
  ; 要求不装在 C 盘：依次找 D~H 盘，用第一个存在的盘。
  ; 一个都没有（机器上只有 C 盘）就退回 $EXEDIR，也就是 exe 自己所在的目录
  StrCpy $R1 ""
  ${If} ${FileExists} "D:\*.*"
    StrCpy $R1 "D:"
  ${ElseIf} ${FileExists} "E:\*.*"
    StrCpy $R1 "E:"
  ${ElseIf} ${FileExists} "F:\*.*"
    StrCpy $R1 "F:"
  ${ElseIf} ${FileExists} "G:\*.*"
    StrCpy $R1 "G:"
  ${ElseIf} ${FileExists} "H:\*.*"
    StrCpy $R1 "H:"
  ${EndIf}
  ${If} $R1 != ""
    StrCpy $INSTDIR "$R1\anydl"
  ${EndIf}

  ; 只看"解压完成"标记，不看目录在不在：
  ; 万一上次解压到一半被中断（磁盘满、杀软拦截），标记不存在，这次会重新解压
  ${IfNot} ${FileExists} "$INSTDIR\.installed"
    DetailPrint "正在解压到 $INSTDIR（只需这一次，以后会直接启动）..."
    SetOutPath "$INSTDIR"
    File /r "dist\anydl\*"

    FileOpen $0 "$INSTDIR\.installed" w
    FileClose $0
  ${EndIf}

  ; 启动应用。Exec 是分离进程，应用独立于启动器运行
  DetailPrint "启动 anydl..."
  Exec '"$INSTDIR\anydl.exe"'

  ; 主动关掉启动器窗口。NSIS 的 instfiles 页走完后默认会停在那儿等用户点"关闭"，
  ; 对自解压启动器来说没必要 —— 应用都已经起来了，这个窗口就该自己消失
  Quit
SectionEnd
