# CN OMEGA Web App（中文版）

本文件说明如何开源并使用本地推演模型网页前端。该前端提供场景参数设置、模型运行触发、日志查看和结果文件浏览能力。

English version: [WEB_APP_README.en.md](WEB_APP_README.en.md)

## 开源范围

建议上传到本仓库的本地网页前端文件包括：

- `web_app.py`：本地 Web 服务和浏览器界面，使用 Python 标准库实现，不额外引入 Flask/FastAPI。
- `omega_web_runner.py`：单次场景运行器。网页每提交一次场景，都会启动一个独立 Python 进程调用本地 `omega_model.omega.run_omega()`。
- `WEB_APP_README.md`：中文版本地网页前端说明。
- `WEB_APP_README.en.md`：英文版本地网页前端说明。

## 启动

推荐在项目根目录运行前台服务：

```powershell
python web_app.py
```

浏览器打开：

```text
http://127.0.0.1:8765
```

停止服务：在运行 `python web_app.py` 的终端按 `Ctrl+C`。

## 局域网 / 服务器访问

默认只监听本机 `127.0.0.1`。如果要让同一局域网或服务器反向代理访问，可以显式设置监听地址：

```powershell
$env:OMEGA_WEB_HOST="0.0.0.0"
$env:OMEGA_WEB_PORT="8765"
python web_app.py
```

随后用运行机器的局域网 IP 或服务器域名访问，例如：

```text
http://<运行机器IP>:8765
```

注意：当前版本没有登录系统。谁能访问这个地址，谁就能在运行机器上启动一次模型任务。公开部署前应放在受控网络、VPN 或带身份验证的反向代理后面。

## 页面功能

- 左侧设置场景参数、选择政策输入、上传本次运行使用的 CSV 文件，并查看历史运行记录。
- 右侧展示关键指标卡片、趋势图、模型日志和输出文件列表。
- “排放标准”内置基准 `ghg_standards-cm_cn.csv` 和加严 `ghg_standards-cm_cn_strict.csv` 两类选择。
- “政策与输入文件”支持按本次运行上传 CSV；上传文件保存在该次运行的 `uploads/` 目录，不覆盖 `omega_model/test_inputs`。
- 已接入的输入文件项包括：排放标准、NEV 积分要求、上游排放方法、新能源销售份额约束、生产约束、补贴/价格修正。
- 已接入的高级数值项包括：电池产能年份、电池产能上限、第二阶段生产约束开关。

## 运行输出

单次运行目录形如：

```text
web_runs/20260427_203000_ab12cd34/
```

其中：

- `request.json`：页面提交的场景参数。
- `status.json`：运行状态。
- `run.log`：模型进程控制台输出。
- `summary.json`：网页读取的摘要数据。
- `uploads/`：本次运行通过网页上传的输入文件。
- `outputs/`：OMEGA 原始输出文件，包括 `_summary_results.csv`、图表和明细 CSV。

`web_runs/` 是本地运行产物，不应提交到公开仓库。

## 依赖

网页服务本身只使用 Python 标准库。模型运行所需依赖由用户本地的 `omega_model/` 环境决定。

建议使用与 `omega_model` 已验证环境一致的 Python 版本启动本网页，例如：

```powershell
python --version
python web_app.py
```

## 稳定性说明

这个版本是本地研究原型，重点是把已有模型包装成非代码用户可操作的网页。模型仍在本机运行，不上传到外部服务器，也不需要访问互联网。

如果要在后台启动，可以使用相对工作目录：

```powershell
Start-Process -FilePath python -ArgumentList 'web_app.py' -WorkingDirectory (Get-Location) -WindowStyle Hidden
```

后台方式不如前台方式直观；调试阶段建议使用前台启动。
