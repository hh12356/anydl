## Changes from upstream

做了很多优化用户体验的设计：

(1)从网页改成app

(2)更改界面结构，从9张卡片改为2张，更为简洁

(3)下载选项新增了bilibili和douyin

(4)从bilibili，抖音复制链接时，并不是单纯的url，会夹带标题等信息。改动新增了url处理，可以直接把复制的完整内容粘贴到输入框，提交时自动识别url

(5)新增视频裁剪trim功能，可以自定义下载片段，提取素材更方便

(6)输入裁剪时间时，可以只输入秒数或分钟+秒数，提交时自动解析，大大提高输入体验

(7)过滤log信息，提高其可读性

(8)修复了ERROR但弹窗Success的bug

注意：douyin视频下载时需先下载firefox浏览器并在firefox中打开douyin.com，ANYDL才能获取cookie完成下载