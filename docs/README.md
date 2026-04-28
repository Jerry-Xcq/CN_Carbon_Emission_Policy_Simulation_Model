# CN OMEGA GitHub Pages

这个目录是项目宣传页，适合直接作为 GitHub Pages 发布源。

## 本地预览

直接用浏览器打开：

```text
docs/index.html
```

或者在仓库根目录启动一个静态文件服务：

```powershell
python -m http.server 8080 -d docs
```

然后访问：

```text
http://127.0.0.1:8080
```

## 发布到 GitHub Pages

在 GitHub 仓库里进入：

```text
Settings -> Pages -> Build and deployment -> Source
```

选择：

```text
Deploy from a branch
```

然后把发布目录设为：

```text
main / docs
```

保存后，GitHub 会生成类似下面的访问地址：

```text
https://<your-github-username>.github.io/<repository-name>/
```

## 和运行端的关系

这个目录只负责项目展示，不运行 Python 模型。

真正的工作台仍然由仓库根目录的 `web_app.py` 提供：

```powershell
python web_app.py
```

浏览器访问：

```text
http://127.0.0.1:8765
```

如果后续部署到云服务器，建议把静态宣传页和运行端分开：

- GitHub Pages：项目介绍、论文/报告、截图、演示视频、下载入口。
- 云服务器：登录系统、任务队列、模型运行、结果存储和下载。

## 演示视频

首页已经预留了本地 Web 运行演示区域。录屏完成后，把视频保存为：

```text
docs/assets/cn-omega-demo.mp4
```

刷新 `docs/index.html` 后，页面会自动显示视频播放器。
