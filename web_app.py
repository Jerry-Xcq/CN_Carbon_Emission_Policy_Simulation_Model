"""
Local web app for the China-localized OMEGA model.

Run:
    python web_app.py
Then open:
    http://127.0.0.1:8765
"""

from __future__ import annotations

import json
import mimetypes
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
import cgi
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse


ROOT_DIR = Path(__file__).resolve().parent
RUNS_DIR = ROOT_DIR / "web_runs"
RUNNER = ROOT_DIR / "omega_web_runner.py"
HOST = os.environ.get("OMEGA_WEB_HOST", "127.0.0.1")
PORT = int(os.environ.get("OMEGA_WEB_PORT", "8765"))

PROCESSES: dict[str, subprocess.Popen] = {}
LOCK = threading.Lock()


INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>China Vehicle Carbon Emission Policy Simulation Platform</title>
  <style>
    :root {
      --bg: #f4f6f8;
      --panel: #ffffff;
      --ink: #17212b;
      --muted: #5d6978;
      --line: #d9e0e7;
      --blue: #22577a;
      --green: #2f7d64;
      --red: #b4463a;
      --amber: #9a6a21;
      --shadow: 0 8px 24px rgba(19, 32, 46, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font: 14px/1.45 "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
      letter-spacing: 0;
    }
    header {
      background: #183349;
      color: #fff;
      border-bottom: 1px solid #102536;
    }
    .topbar {
      max-width: 1320px;
      margin: 0 auto;
      min-height: 84px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 24px;
      padding: 18px 24px;
    }
    h1 {
      margin: 0;
      font-size: 24px;
      font-weight: 700;
      letter-spacing: 0;
    }
    .subtitle { color: #c7d4df; margin-top: 4px; }
    .contact-line {
      color: #c7d4df;
      margin-top: 4px;
      font-size: 12px;
    }
    .contact-email { white-space: nowrap; }
    .contact-lines {
      display: grid;
      gap: 3px;
    }
    .contact-lines span,
    .contact-lines .contact-person {
      display: block;
    }
    .contact-lines .contact-email {
      display: block;
    }
    .top-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 34px;
      padding: 0 12px;
      border: 1px solid rgba(255,255,255,.25);
      border-radius: 6px;
      color: #eaf1f6;
      white-space: nowrap;
    }
    .lang-toggle {
      height: 34px;
      border: 1px solid rgba(255,255,255,.35);
      border-radius: 6px;
      padding: 0 12px;
      background: transparent;
      color: #eaf1f6;
      font: inherit;
      font-weight: 800;
      cursor: pointer;
      white-space: nowrap;
    }
    .dot { width: 9px; height: 9px; border-radius: 50%; background: #8bc6ad; }
    main {
      max-width: 1320px;
      margin: 0 auto;
      padding: 22px 24px 36px;
      display: grid;
      grid-template-columns: 390px minmax(0, 1fr);
      gap: 18px;
    }
    section, aside {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }
    aside { padding: 18px; align-self: start; }
    .workspace { padding: 18px; min-width: 0; }
    h2 {
      margin: 0 0 14px;
      font-size: 17px;
      line-height: 1.2;
    }
    label {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin: 13px 0 6px;
    }
    input, select {
      width: 100%;
      height: 38px;
      border: 1px solid #cbd4dc;
      border-radius: 6px;
      padding: 0 10px;
      background: #fff;
      color: var(--ink);
      font: inherit;
    }
    input:focus, select:focus {
      border-color: var(--blue);
      outline: 2px solid rgba(34, 87, 122, .14);
    }
    .grid2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
    .checkrow {
      display: flex;
      align-items: center;
      gap: 10px;
      min-height: 38px;
      margin-top: 12px;
      color: var(--muted);
    }
    .checkrow input { width: 17px; height: 17px; }
    details {
      margin-top: 16px;
      border-top: 1px solid var(--line);
      padding-top: 12px;
    }
    summary {
      cursor: pointer;
      font-weight: 700;
      color: var(--ink);
    }
    .hint {
      color: var(--muted);
      font-size: 12px;
      margin-top: 6px;
    }
    input[type="file"] {
      height: auto;
      min-height: 38px;
      padding: 7px 10px;
    }
    .upload-field {
      display: none;
      margin-top: 7px;
    }
    .upload-field.visible { display: block; }
    button {
      height: 40px;
      border: 1px solid transparent;
      border-radius: 6px;
      padding: 0 14px;
      background: var(--blue);
      color: white;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }
    button.secondary {
      background: #fff;
      color: var(--blue);
      border-color: #b8c8d4;
      font-weight: 600;
    }
    button:disabled { opacity: .55; cursor: not-allowed; }
    .actions {
      display: flex;
      gap: 10px;
      margin-top: 18px;
    }
    .runs {
      margin-top: 18px;
      border-top: 1px solid var(--line);
      padding-top: 14px;
    }
    .run-item {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      margin-top: 8px;
      background: #fbfcfd;
      cursor: pointer;
    }
    .run-item.active { border-color: var(--blue); background: #eef5f8; }
    .run-title { font-weight: 700; color: var(--ink); overflow-wrap: anywhere; }
    .run-meta { color: var(--muted); font-size: 12px; margin-top: 3px; }
    .cards {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 16px;
    }
    .card {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 13px;
      min-height: 92px;
      background: #fbfcfd;
    }
    .card-label { color: var(--muted); font-size: 12px; }
    .card-value { margin-top: 10px; font-size: 24px; font-weight: 800; letter-spacing: 0; }
    .card-unit { color: var(--muted); font-size: 12px; margin-top: 2px; }
    .charts {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .chart-panel {
      border: 1px solid var(--line);
      border-radius: 8px;
      min-height: 320px;
      background: #fff;
      padding: 13px;
      overflow: hidden;
    }
    .chart-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 8px;
      font-weight: 700;
    }
    svg { width: 100%; height: 250px; display: block; }
    .axis { stroke: #aab5c1; stroke-width: 1; }
    .grid { stroke: #e8edf2; stroke-width: 1; }
    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: 8px 12px;
      color: var(--muted);
      font-size: 12px;
      margin-top: 8px;
    }
    .legend i {
      display: inline-block;
      width: 18px;
      height: 3px;
      border-radius: 2px;
      vertical-align: middle;
      margin-right: 5px;
    }
    .files {
      margin-top: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }
    .file-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 92px 92px;
      gap: 10px;
      align-items: center;
      min-height: 40px;
      padding: 0 12px;
      border-top: 1px solid var(--line);
    }
    .file-row:first-child { border-top: 0; background: #f7f9fb; color: var(--muted); font-size: 12px; }
    .file-row a { color: var(--blue); text-decoration: none; overflow-wrap: anywhere; }
    .file-group {
      border-top: 1px solid var(--line);
      background: #f7f9fb;
      color: var(--ink);
      font-weight: 700;
      min-height: 38px;
      display: flex;
      align-items: center;
      padding: 0 12px;
    }
    .section-title {
      margin: 18px 0 10px;
      font-size: 16px;
      font-weight: 800;
    }
    .details-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 16px;
    }
    .detail-item {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfd;
      padding: 10px 12px;
      min-height: 66px;
    }
    .detail-label {
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }
    .detail-value {
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .image-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-top: 10px;
    }
    .image-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      overflow: hidden;
    }
    .image-card img {
      width: 100%;
      display: block;
      background: #fff;
    }
    .image-caption {
      border-top: 1px solid var(--line);
      padding: 8px 10px;
      color: var(--muted);
      font-size: 12px;
      overflow-wrap: anywhere;
    }
    .logbox {
      margin-top: 14px;
      min-height: 260px;
      max-height: 520px;
      overflow: auto;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #111820;
      color: #d7e1ea;
      font: 12px/1.45 Consolas, monospace;
      white-space: pre-wrap;
    }
    .empty {
      min-height: 420px;
      display: grid;
      place-items: center;
      color: var(--muted);
      border: 1px dashed #cbd4dc;
      border-radius: 8px;
      background:
        linear-gradient(90deg, rgba(34,87,122,.08) 1px, transparent 1px),
        linear-gradient(rgba(34,87,122,.08) 1px, transparent 1px);
      background-size: 28px 28px;
    }
    .tag {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 5px;
      padding: 0 8px;
      background: #eef3f7;
      color: var(--muted);
      font-size: 12px;
      white-space: nowrap;
    }
    @media (max-width: 980px) {
      main { grid-template-columns: 1fr; }
      .cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .charts { grid-template-columns: 1fr; }
      .details-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .image-grid { grid-template-columns: 1fr; }
    }
    @media (max-width: 560px) {
      .topbar { align-items: flex-start; flex-direction: column; }
      .cards, .grid2, .details-grid { grid-template-columns: 1fr; }
      .file-row { grid-template-columns: minmax(0, 1fr) 74px; }
      .file-row span:nth-child(3), .file-row a:nth-child(3) { display: none; }
    }
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <div>
        <h1>China Vehicle Carbon Emission Policy Simulation Platform</h1>
        <div class="subtitle">Local scenario simulation cockpit</div>
        <div class="contact-line contact-lines">
          <span class="contact-person" data-contact="xjr"><span class="contact-main">Xu Jiarui, PhD Student, College of Transportation, Tongji University</span><span class="contact-email">Email: 2410824@tongji.edu.cn</span></span>
          <span class="contact-person" data-contact="lhb"><span class="contact-main">Liu Haobing, Professor and Doctoral Supervisor, College of Transportation, Tongji University</span><span class="contact-email">Email: liuhaobing@tongji.edu.cn</span></span>
        </div>
      </div>
      <div class="top-actions">
        <div class="status-pill"><span class="dot"></span><span id="serverState">Local service connected</span></div>
        <button class="lang-toggle" id="langToggle" type="button">中文</button>
      </div>
    </div>
  </header>
  <main>
    <aside>
      <h2>Scenario Parameters</h2>
      <form id="scenarioForm" enctype="multipart/form-data">
        <label for="session_name">Scenario name</label>
        <input id="session_name" name="session_name" value="Baseline policy scenario">

        <div class="grid2">
          <div>
            <label for="analysis_final_year">Final analysis year</label>
            <input id="analysis_final_year" name="analysis_final_year" type="number" min="2026" max="2040" value="2031">
          </div>
          <div>
            <label for="policy_preset">Emission standard</label>
            <select id="policy_preset" name="policy_preset">
              <option value="baseline">Baseline</option>
              <option value="strict">Stricter policy</option>
              <option value="upload">Upload file</option>
            </select>
            <input class="upload-field" id="policy_targets_upload" name="policy_targets_upload" type="file" accept=".csv">
          </div>
        </div>

        <label for="credit_market_efficiency">Credit trading efficiency</label>
        <input id="credit_market_efficiency" name="credit_market_efficiency" type="number" min="0" max="1" step="0.01" value="0.01">

        <div class="grid2">
          <div>
            <label for="bev_range_mi">BEV range, mi</label>
            <input id="bev_range_mi" name="bev_range_mi" type="number" min="100" max="800" value="320">
          </div>
          <div>
            <label for="phev_range_mi">PHEV range, mi</label>
            <input id="phev_range_mi" name="phev_range_mi" type="number" min="20" max="250" value="80">
          </div>
        </div>

        <div class="grid2">
          <div>
            <label for="consumer_pricing_multiplier_max">Max price multiplier</label>
            <input id="consumer_pricing_multiplier_max" name="consumer_pricing_multiplier_max" type="number" min="1" max="2" step="0.01" value="1.16">
          </div>
          <div>
            <label for="producer_market_category_ramp_limit">Transition ramp constraint</label>
            <input id="producer_market_category_ramp_limit" name="producer_market_category_ramp_limit" type="number" min="0.01" max="1" step="0.01" value="0.35">
          </div>
        </div>

        <label for="new_vehicle_price_elasticity_of_demand">New-vehicle demand price elasticity</label>
        <input id="new_vehicle_price_elasticity_of_demand" name="new_vehicle_price_elasticity_of_demand" type="number" min="-5" max="0" step="0.1" value="-1.2">

        <div class="checkrow">
          <input id="multiprocessing" name="multiprocessing" type="checkbox">
          <span>Enable multiprocessing</span>
        </div>

        <details>
          <summary>Policy and Input Files</summary>
          <div class="hint">Default scenario inputs are used unless an upload option is selected. Uploaded files only replace the corresponding input for this run.</div>

          <label for="nev_preset">NEV credit requirements</label>
          <select id="nev_preset" name="nev_preset">
            <option value="default">Default NEV requirements</option>
            <option value="upload">Upload NEV requirements file</option>
          </select>
          <input class="upload-field" id="nev_requirements_upload" name="nev_requirements_upload" type="file" accept=".csv">

          <label for="upstream_preset">Upstream emissions method</label>
          <select id="upstream_preset" name="upstream_preset">
            <option value="zero">Zero upstream emissions</option>
            <option value="upload">Upload upstream method file</option>
          </select>
          <input class="upload-field" id="fuel_upstream_methods_upload" name="fuel_upstream_methods_upload" type="file" accept=".csv">

          <label for="required_sales_share_preset">New-energy sales-share constraint</label>
          <select id="required_sales_share_preset" name="required_sales_share_preset">
            <option value="noacc">Default noACC2</option>
            <option value="floor_user">BEV/PHEV floor user</option>
            <option value="upload">Upload sales-share constraint file</option>
          </select>
          <input class="upload-field" id="required_sales_share_upload" name="required_sales_share_upload" type="file" accept=".csv">

          <label for="production_constraints_preset">Production constraints</label>
          <select id="production_constraints_preset" name="production_constraints_preset">
            <option value="cn_ice">China ICE constraints</option>
            <option value="general">General constraints</option>
            <option value="upload">Upload production constraint file</option>
          </select>
          <input class="upload-field" id="production_constraints_upload" name="production_constraints_upload" type="file" accept=".csv">

          <label for="price_modifications_preset">Incentive / price modifications</label>
          <select id="price_modifications_preset" name="price_modifications_preset">
            <option value="default">Default 0k BEV incentives</option>
            <option value="upload">Upload price modification file</option>
          </select>
          <input class="upload-field" id="vehicle_price_modifications_upload" name="vehicle_price_modifications_upload" type="file" accept=".csv">
        </details>

        <details>
          <summary>Advanced Numeric Parameters</summary>
          <label for="battery_GWh_limit_years">Battery capacity years</label>
          <input id="battery_GWh_limit_years" name="battery_GWh_limit_years" value="2025,2026,2027,2028,2029,2030">

          <label for="battery_GWh_limit">Battery capacity limit, GWh</label>
          <input id="battery_GWh_limit" name="battery_GWh_limit" value="3000,5000,8000,10000,20000,20000">

          <div class="checkrow">
            <input id="second_pass_production_constraints" name="second_pass_production_constraints" type="checkbox">
            <span>Apply second-pass production constraints</span>
          </div>
        </details>

        <div class="actions">
          <button id="runButton" type="submit">Run Scenario</button>
          <button class="secondary" id="refreshButton" type="button">Refresh</button>
        </div>
      </form>

      <div class="runs">
        <h2>Run History</h2>
        <div id="runList"></div>
      </div>
    </aside>

    <section class="workspace">
      <div id="content" class="empty">Waiting for a scenario run</div>
    </section>
  </main>

  <script>
    const state = { runs: [], selected: null, timer: null, lang: localStorage.getItem("cnCarbonWebLang") || "en" };
    const colors = ["#22577a", "#2f7d64", "#b4463a", "#9a6a21", "#6b5b95", "#287c91"];
    const zhText = {
      "China Vehicle Carbon Emission Policy Simulation Platform": "中国汽车碳排放政策推演平台",
      "Local scenario simulation cockpit": "本地情景推演控制台",
      "Xu Jiarui, PhD Student, College of Transportation, Tongji University, Email: 2410824@tongji.edu.cn": "许珈瑞，博士生，同济大学交通学院，邮箱：2410824@tongji.edu.cn",
      "Liu Haobing, Professor and Doctoral Supervisor, College of Transportation, Tongji University, Email: liuhaobing@tongji.edu.cn": "刘皓冰，教授，博导，同济大学交通学院，邮箱：liuhaobing@tongji.edu.cn",
      "Xu Jiarui, PhD Student, College of Transportation, Tongji University": "许珈瑞，博士生，同济大学交通学院",
      "Liu Haobing, Professor and Doctoral Supervisor, College of Transportation, Tongji University": "刘皓冰，教授，博导，同济大学交通学院",
      "Email: 2410824@tongji.edu.cn": "邮箱：2410824@tongji.edu.cn",
      "Email: liuhaobing@tongji.edu.cn": "邮箱：liuhaobing@tongji.edu.cn",
      "Local service connected": "本地服务已连接",
      "Scenario Parameters": "情景参数",
      "Scenario name": "情景名称",
      "Final analysis year": "最终分析年份",
      "Emission standard": "排放标准",
      "Baseline": "基准情景",
      "Stricter policy": "更严格政策",
      "Upload file": "上传文件",
      "Credit trading efficiency": "积分交易效率",
      "BEV range, mi": "纯电续驶里程，英里",
      "PHEV range, mi": "插混续驶里程，英里",
      "Max price multiplier": "最高价格倍率",
      "Transition ramp constraint": "转型爬坡约束",
      "New-vehicle demand price elasticity": "新车需求价格弹性",
      "Enable multiprocessing": "启用多进程",
      "Policy and Input Files": "政策与输入文件",
      "Default scenario inputs are used unless an upload option is selected. Uploaded files only replace the corresponding input for this run.": "未选择上传选项时使用默认情景输入；上传文件只替换本次运行对应输入。",
      "NEV credit requirements": "新能源汽车积分要求",
      "Default NEV requirements": "默认新能源汽车积分要求",
      "Upload NEV requirements file": "上传新能源汽车积分要求文件",
      "Upstream emissions method": "上游排放方法",
      "Zero upstream emissions": "上游排放置零",
      "Upload upstream method file": "上传上游方法文件",
      "New-energy sales-share constraint": "新能源销售占比约束",
      "Default noACC2": "默认无加速约束",
      "BEV/PHEV floor user": "用户设定纯电 / 插混下限",
      "Upload sales-share constraint file": "上传销售占比约束文件",
      "Production constraints": "生产约束",
      "China ICE constraints": "中国燃油车约束",
      "General constraints": "通用约束",
      "Upload production constraint file": "上传生产约束文件",
      "Incentive / price modifications": "激励 / 价格修正",
      "Default 0k BEV incentives": "默认纯电零补贴激励",
      "Upload price modification file": "上传价格修正文件",
      "Advanced Numeric Parameters": "高级数值参数",
      "Battery capacity years": "电池容量年份",
      "Battery capacity limit, GWh": "电池容量上限，吉瓦时",
      "Apply second-pass production constraints": "应用第二轮生产约束",
      "Run Scenario": "运行情景",
      "Refresh": "刷新",
      "Run History": "运行历史",
      "No runs yet": "暂无运行记录",
      "Waiting for a scenario run": "等待情景运行",
      "Queued": "排队中",
      "Running": "运行中",
      "Completed": "已完成",
      "Failed": "失败",
      "Status": "状态",
      "Run ID": "运行 ID",
      "run id": "运行 ID",
      "Waiting for log output": "等待日志输出",
      "Run Error": "运行错误",
      "request was not started": "请求未启动",
      "Run Details": "运行详情",
      "Scenario": "情景",
      "Final year": "最终年份",
      "Credit efficiency": "积分效率",
      "BEV range": "纯电续驶里程",
      "PHEV range": "插混续驶里程",
      "Multiprocessing": "多进程",
      "Summary source": "汇总文件来源",
      "Summary Indicators": "汇总指标",
      "Final-Year Sales": "最终年份销量",
      "Final-Year Battery Demand": "最终年份电池需求",
      "Final-Year Certified Emissions": "最终年份认证碳排放",
      "Final-Year Certified Carbon Emissions": "最终年份认证碳排放",
      "Final-Year Average Manufacturing Cost": "最终年份平均制造成本",
      "million vehicles": "百万辆",
      "million Mg": "百万 Mg",
      "USD / vehicle": "美元 / 辆",
      "Total Sales": "总销量",
      "Battery Demand": "电池需求",
      "Certified CO2e": "认证碳排放",
      "Market Share Fraction": "市场份额比例",
      "vehicles": "辆",
      "fraction": "比例",
      "Model Output Figures": "模型输出图片",
      "Output Files": "输出文件",
      "Output File": "输出文件",
      "Type": "类型",
      "Size": "大小",
      "Pass 0 - consolidated-policy outputs": "第 0 轮 - 合并车企政策推演输出",
      "Pass 1 - final manufacturer-level outputs": "第 1 轮 - 分车企政策推演输出",
      "Pass 0 - consolidated automaker policy projection outputs": "第 0 轮 - 合并车企政策推演输出",
      "Pass 1 - by-automaker policy projection outputs": "第 1 轮 - 分车企政策推演输出",
      "Baseline policy scenario": "基准政策情景",
      "baseline": "基准情景",
      "strict": "更严格政策",
      "upload": "上传文件",
      "default": "默认",
      "noacc": "默认无加速约束",
      "floor_user": "用户设定下限",
      "cn_ice": "中国燃油车约束",
      "general": "通用约束",
      "true": "是",
      "false": "否",
      "NA": "无",
      "sales_total": "总销量",
      "vehicle_GWh": "车辆电池需求",
      "vehicle_co2e_Mg": "车辆认证碳排放",
      "BEV": "纯电",
      "PHEV": "插混",
      "ICE": "燃油车",
      "car": "乘用轿车",
      "truck": "轻型货车"
    };
    const originalTextNodes = new WeakMap();

    function t(text) {
      return state.lang === "zh" && zhText[text] ? zhText[text] : text;
    }

    function replaceTextPreservingSpace(raw, translated) {
      const leading = raw.match(/^\s*/)[0];
      const trailing = raw.match(/\s*$/)[0];
      return `${leading}${translated}${trailing}`;
    }

    function applyLanguage() {
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
        acceptNode(node) {
          const parent = node.parentElement;
          if (!parent || ["SCRIPT", "STYLE"].includes(parent.tagName)) return NodeFilter.FILTER_REJECT;
          return node.nodeValue.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
        }
      });
      const nodes = [];
      while (walker.nextNode()) nodes.push(walker.currentNode);
      nodes.forEach(node => {
        if (!originalTextNodes.has(node)) originalTextNodes.set(node, node.nodeValue);
        const original = originalTextNodes.get(node);
        const key = original.trim();
        node.nodeValue = state.lang === "zh" && zhText[key]
          ? replaceTextPreservingSpace(original, zhText[key])
          : original;
      });
      document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";
      document.title = t("China Vehicle Carbon Emission Policy Simulation Platform");
      document.getElementById("langToggle").textContent = state.lang === "zh" ? "英文" : "中文";
      syncContactLayout();
      const scenarioName = document.getElementById("session_name");
      if (scenarioName && ["Baseline policy scenario", "基准政策情景"].includes(scenarioName.value)) {
        scenarioName.value = state.lang === "zh" ? zhText["Baseline policy scenario"] : "Baseline policy scenario";
      }
    }

    function syncContactLayout() {
      const contacts = {
        xjr: {
          en: ["Xu Jiarui, PhD Student, College of Transportation, Tongji University", "Email: 2410824@tongji.edu.cn"],
          zh: ["许珈瑞，博士生，同济大学交通学院，邮箱：2410824@tongji.edu.cn"]
        },
        lhb: {
          en: ["Liu Haobing, Professor and Doctoral Supervisor, College of Transportation, Tongji University", "Email: liuhaobing@tongji.edu.cn"],
          zh: ["刘皓冰，教授，博导，同济大学交通学院，邮箱：liuhaobing@tongji.edu.cn"]
        }
      };
      document.querySelectorAll("[data-contact]").forEach(item => {
        const data = contacts[item.dataset.contact];
        if (!data) return;
        const lines = state.lang === "zh" ? data.zh : data.en;
        item.innerHTML = lines.map((line, index) => `<span class="${index === 1 ? "contact-email" : "contact-main"}">${line}</span>`).join("");
      });
    }

    function fmt(n) {
      if (n === null || n === undefined || Number.isNaN(n)) return t("NA");
      return Number(n).toLocaleString("en-US");
    }

    function sizeFmt(bytes) {
      if (!bytes) return "0 B";
      const units = ["B", "KB", "MB", "GB"];
      let n = bytes, i = 0;
      while (n >= 1024 && i < units.length - 1) { n /= 1024; i += 1; }
      return `${n.toFixed(i ? 1 : 0)} ${units[i]}`;
    }

    function displayText(text) {
      const aliases = {
        "Final-Year Certified Emissions": "Final-Year Certified Carbon Emissions",
        "Pass 0 - consolidated-policy outputs": "Pass 0 - consolidated automaker policy projection outputs",
        "Pass 1 - final manufacturer-level outputs": "Pass 1 - by-automaker policy projection outputs"
      };
      return t(aliases[text] || text);
    }

    async function api(path, options) {
      const res = await fetch(path, options);
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    }

    function formPayload() {
      const form = document.getElementById("scenarioForm");
      const data = new FormData(form);
      data.set("multiprocessing", document.getElementById("multiprocessing").checked ? "true" : "false");
      data.set(
        "second_pass_production_constraints",
        document.getElementById("second_pass_production_constraints").checked ? "true" : "false"
      );
      return data;
    }

    function syncUploadFields() {
      [
        ["policy_preset", "policy_targets_upload"],
        ["nev_preset", "nev_requirements_upload"],
        ["upstream_preset", "fuel_upstream_methods_upload"],
        ["required_sales_share_preset", "required_sales_share_upload"],
        ["production_constraints_preset", "production_constraints_upload"],
        ["price_modifications_preset", "vehicle_price_modifications_upload"]
      ].forEach(([selectId, inputId]) => {
        const select = document.getElementById(selectId);
        const input = document.getElementById(inputId);
        if (!select || !input) return;
        input.classList.toggle("visible", select.value === "upload");
      });
    }

    function statusText(status) {
      const label = { queued: "Queued", running: "Running", completed: "Completed", failed: "Failed" }[status] || status;
      return t(label);
    }

    function renderRunList() {
      const list = document.getElementById("runList");
      if (!state.runs.length) {
        list.innerHTML = `<div class="run-meta">${t("No runs yet")}</div>`;
        return;
      }
      list.innerHTML = state.runs.map(run => `
        <div class="run-item ${state.selected === run.id ? "active" : ""}" data-id="${run.id}">
          <div class="run-title">${displayText(run.session_name || run.id)}</div>
          <div class="run-meta">${statusText(run.status)} · ${new Date((run.started_at || Date.now()/1000) * 1000).toLocaleString("en-US")}</div>
        </div>
      `).join("");
      list.innerHTML = list.innerHTML.replace(/ 路 /g, " - ");
      [...list.querySelectorAll(".run-item")].forEach(el => {
        el.addEventListener("click", () => selectRun(el.dataset.id));
      });
    }

    function points(series, w, h, pad, domain) {
      if (!series || !series.length) return "";
      const xs = series.map(d => d.year);
      const minX = Math.min(...xs), maxX = Math.max(...xs);
      const minY = domain.minY;
      const maxY = domain.maxY;
      return series.map(d => {
        const x = pad.l + ((d.year - minX) / Math.max(1, maxX - minX)) * (w - pad.l - pad.r);
        const y = h - pad.b - ((d.value - minY) / Math.max(1e-9, maxY - minY)) * (h - pad.t - pad.b);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      }).join(" ");
    }

    function lineChart(title, datasets, unit) {
      const w = 560, h = 250, pad = { l: 48, r: 18, t: 18, b: 34 };
      const all = datasets.flatMap(d => d.data || []);
      const years = all.map(d => d.year);
      const values = all.map(d => d.value);
      const minYear = years.length ? Math.min(...years) : 0;
      const maxYear = years.length ? Math.max(...years) : 0;
      let minValue = values.length ? Math.min(...values) : 0;
      let maxValue = values.length ? Math.max(...values) : 1;
      if (minValue === maxValue) {
        const delta = Math.abs(maxValue || 1) * 0.05;
        minValue -= delta;
        maxValue += delta;
      }
      const domain = { minY: minValue, maxY: maxValue };
      const ticks = [0, .25, .5, .75, 1];
      const grid = ticks.map(t => {
        const y = h - pad.b - t * (h - pad.t - pad.b);
        const raw = minValue + (maxValue - minValue) * t;
        const label = Number(raw.toPrecision(5)).toLocaleString("en-US");
        return `<line class="grid" x1="${pad.l}" y1="${y}" x2="${w-pad.r}" y2="${y}"></line><text x="6" y="${y+4}" fill="#6b7582" font-size="11">${label}</text>`;
      }).join("");
      const paths = datasets.map((d, i) => `<polyline fill="none" stroke="${colors[i % colors.length]}" stroke-width="2.4" points="${points(d.data, w, h, pad, domain)}"></polyline>`).join("");
      const markers = datasets.map((d, i) => (d.data || []).map(p => {
        const pts = points([p, ...d.data.filter(x => x !== p)], w, h, pad, domain).split(" ")[0].split(",");
        return `<circle cx="${pts[0]}" cy="${pts[1]}" r="3" fill="${colors[i % colors.length]}"></circle>`;
      }).join("")).join("");
      const legend = datasets.map((d, i) => `<span><i style="background:${colors[i % colors.length]}"></i>${displayText(d.name)}</span>`).join("");
      return `
        <div class="chart-panel">
          <div class="chart-title"><span>${title}</span><span class="tag">${unit}</span></div>
          <svg viewBox="0 0 ${w} ${h}" role="img">
            ${grid}
            <line class="axis" x1="${pad.l}" y1="${h-pad.b}" x2="${w-pad.r}" y2="${h-pad.b}"></line>
            <line class="axis" x1="${pad.l}" y1="${pad.t}" x2="${pad.l}" y2="${h-pad.b}"></line>
            <text x="${pad.l}" y="${h-9}" fill="#6b7582" font-size="11">${minYear}</text>
            <text x="${w-pad.r-28}" y="${h-9}" fill="#6b7582" font-size="11">${maxYear}</text>
            ${paths}${markers}
          </svg>
          <div class="legend">${legend}</div>
        </div>`;
    }

    function renderPending(run, logText = "") {
      document.getElementById("content").className = "";
      document.getElementById("content").innerHTML = `
        <div class="cards">
          <div class="card"><div class="card-label">${t("Status")}</div><div class="card-value">${statusText(run.status)}</div><div class="card-unit">${run.message || ""}</div></div>
          <div class="card"><div class="card-label">${t("Run ID")}</div><div class="card-value" style="font-size:16px;overflow-wrap:anywhere">${run.id}</div><div class="card-unit">${t("run id")}</div></div>
        </div>
        <div class="logbox">${escapeHtml(presentationLog(logText) || t("Waiting for log output"))}</div>`;
    }

    function escapeHtml(text) {
      return (text || "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
    }

    function presentationLog(text) {
      return (text || "")
        .replace(/OMEGA/gi, "simulation")
        .replace(/omega_model/gi, "model_package")
        .replace(/[A-Z]:\\[^\s]+/g, "[local path]");
    }

    function filePhase(name) {
      if ((name || "").startsWith("consolidate_1/")) return displayText("Pass 0 - consolidated automaker policy projection outputs");
      return displayText("Pass 1 - by-automaker policy projection outputs");
    }

    function renderFileGroups(files, runId) {
      const groups = {};
      (files || []).forEach(file => {
        const phase = filePhase(file.name);
        if (!groups[phase]) groups[phase] = [];
        groups[phase].push(file);
      });
      return Object.entries(groups).map(([phase, items]) => `
        <div class="file-group">${phase}</div>
        ${items.map(f => `
          <div class="file-row">
            <a href="/api/runs/${runId}/files/${encodeURIComponent(f.name)}">${f.name}</a>
            <span>${f.kind}</span>
            <span>${sizeFmt(f.size)}</span>
          </div>`).join("")}
      `).join("");
    }

    function requestDetails(summary, run) {
      const request = summary.request || {};
      const distanceUnit = state.lang === "zh" ? "英里" : "mi";
      const items = [
        [t("Scenario"), displayText(request.session_name || run.session_name || run.id)],
        [t("Final year"), request.analysis_final_year || t("NA")],
        [t("Emission standard"), displayText(request.policy_preset || "NA")],
        [t("Credit efficiency"), request.credit_market_efficiency || t("NA")],
        [t("BEV range"), request.bev_range_mi ? `${request.bev_range_mi} ${distanceUnit}` : t("NA")],
        [t("PHEV range"), request.phev_range_mi ? `${request.phev_range_mi} ${distanceUnit}` : t("NA")],
        [t("Multiprocessing"), displayText(String(request.multiprocessing || "false"))],
        [t("Summary source"), summary.summary_csv || t("NA")]
      ];
      return items.map(([label, value]) => `
        <div class="detail-item">
          <div class="detail-label">${label}</div>
          <div class="detail-value">${escapeHtml(String(value))}</div>
        </div>
      `).join("");
    }

    function renderImageGallery(files, runId) {
      const images = (files || []).filter(f => ["png", "jpg", "jpeg", "webp"].includes((f.kind || "").toLowerCase()));
      if (!images.length) return "";
      const preferred = images
        .filter(f => !f.name.startsWith("consolidate_1/"))
        .filter(f => /DualCreditCompliance|summary|market|compliance/i.test(f.name));
      const shown = (preferred.length ? preferred : images).slice(0, 8);
      return `
        <div class="section-title">${t("Model Output Figures")}</div>
        <div class="image-grid">
          ${shown.map(f => `
            <div class="image-card">
              <img src="/api/runs/${runId}/files/${encodeURIComponent(f.name)}" alt="${escapeHtml(f.name)}">
              <div class="image-caption">${escapeHtml(f.name)}</div>
            </div>
          `).join("")}
        </div>`;
    }

    async function renderCompleted(run) {
      const summary = await api(`/api/runs/${run.id}/summary`);
      const cards = summary.cards.map(c => `
        <div class="card">
          <div class="card-label">${displayText(c.label)}</div>
          <div class="card-value">${fmt(c.value)}</div>
          <div class="card-unit">${t(c.unit)}</div>
        </div>`).join("");
      const shares = Object.entries(summary.series.shares || {}).map(([name, data]) => ({ name, data }));
      const files = renderFileGroups(summary.files || [], run.id);
      const images = renderImageGallery(summary.files || [], run.id);

      document.getElementById("content").className = "";
      document.getElementById("content").innerHTML = `
        <div class="section-title">${t("Run Details")}</div>
        <div class="details-grid">${requestDetails(summary, run)}</div>
        <div class="section-title">${t("Summary Indicators")}</div>
        <div class="cards">${cards}</div>
        <div class="charts">
          ${lineChart(t("Total Sales"), [{ name: "sales_total", data: summary.series.sales_total }], t("vehicles"))}
          ${lineChart(t("Battery Demand"), [{ name: "vehicle_GWh", data: summary.series.vehicle_gwh }], "GWh")}
          ${lineChart(t("Certified CO2e"), [{ name: "vehicle_co2e_Mg", data: summary.series.vehicle_co2e_mg }], "Mg")}
          ${lineChart(t("Market Share Fraction"), shares, t("fraction"))}
        </div>
        ${images}
        <div class="section-title">${t("Output Files")}</div>
        <div class="files">
          <div class="file-row"><span>${t("Output File")}</span><span>${t("Type")}</span><span>${t("Size")}</span></div>
          ${files}
        </div>`;
    }

    async function renderSelected() {
      if (!state.selected) {
        document.getElementById("content").className = "empty";
        document.getElementById("content").textContent = t("Waiting for a scenario run");
        return;
      }
      const run = await api(`/api/runs/${state.selected}`);
      const log = await fetch(`/api/runs/${state.selected}/log`).then(r => r.text()).catch(() => "");
      if (run.status === "completed") {
        await renderCompleted(run);
      } else {
        renderPending(run, log);
      }
      applyLanguage();
    }

    async function refresh() {
      state.runs = await api("/api/runs");
      if (state.selected && !state.runs.some(r => r.id === state.selected)) {
        state.selected = null;
      }
      if (!state.selected && state.runs.length) state.selected = state.runs[0].id;
      renderRunList();
      await renderSelected();
      const running = state.runs.some(r => r.status === "running");
      document.getElementById("runButton").disabled = running;
    }

    async function selectRun(id) {
      state.selected = id;
      renderRunList();
      await renderSelected();
    }

    document.getElementById("scenarioForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      document.getElementById("runButton").disabled = true;
      try {
        const run = await api("/api/runs", {
          method: "POST",
          body: formPayload()
        });
        state.selected = run.id;
        await refresh();
      } catch (err) {
        document.getElementById("content").className = "";
        document.getElementById("content").innerHTML = `
          <div class="cards">
            <div class="card"><div class="card-label">${t("Run Error")}</div><div class="card-value" style="font-size:16px">${t("Failed")}</div><div class="card-unit">${t("request was not started")}</div></div>
          </div>
          <div class="logbox">${escapeHtml(err.message || String(err))}</div>`;
        document.getElementById("runButton").disabled = false;
        applyLanguage();
      }
    });

    document.getElementById("refreshButton").addEventListener("click", refresh);
    document.getElementById("langToggle").addEventListener("click", async () => {
      state.lang = state.lang === "zh" ? "en" : "zh";
      localStorage.setItem("cnCarbonWebLang", state.lang);
      renderRunList();
      await renderSelected();
      applyLanguage();
    });
    document.querySelectorAll("select").forEach(select => select.addEventListener("change", syncUploadFields));
    syncUploadFields();
    state.timer = setInterval(refresh, 4000);
    applyLanguage();
    refresh().catch(err => {
      document.getElementById("serverState").textContent = err.message;
    });
  </script>
</body>
</html>
"""


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _jsonable(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


def _send_json(handler: BaseHTTPRequestHandler, data, status=HTTPStatus.OK):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _send_text(handler: BaseHTTPRequestHandler, text: str, status=HTTPStatus.OK, content_type="text/plain; charset=utf-8"):
    body = text.encode("utf-8", errors="replace")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _run_dir(run_id: str) -> Path:
    return RUNS_DIR / run_id


def _safe_upload_name(filename: str) -> str:
    name = Path(filename or "upload.csv").name
    clean = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name)
    if not clean.lower().endswith(".csv"):
        clean += ".csv"
    return clean[:120]


def _tail_text(path: Path, limit: int = 48000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    data = path.read_bytes()[-limit:]
    return data.decode("utf-8", errors="replace")


def _relative_label(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.name


def _latest_model_log(run_dir: Path) -> Path | None:
    outputs_dir = run_dir / "outputs"
    candidates = []
    if outputs_dir.exists():
        candidates.extend(outputs_dir.rglob("o2log*.txt"))
    candidates.extend(
        path for path in run_dir.rglob("o2log*.txt") if not outputs_dir.exists() or outputs_dir not in path.parents
    )
    candidates = [path for path in candidates if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _output_files(run_dir: Path) -> list[dict]:
    outputs_dir = run_dir / "outputs"
    if not outputs_dir.exists():
        return []
    files = []
    for path in sorted(outputs_dir.rglob("*")):
        if not path.is_file():
            continue
        relative_name = path.relative_to(outputs_dir).as_posix()
        phase = "Pass 0 - consolidated automaker policy projection outputs" if relative_name.startswith("consolidate_1/") else "Pass 1 - by-automaker policy projection outputs"
        files.append(
            {
                "name": relative_name,
                "size": path.stat().st_size,
                "mtime": path.stat().st_mtime,
                "kind": path.suffix.lower().lstrip(".") or "file",
                "phase": phase,
            }
        )
    return files


def _parse_post_payload(handler: BaseHTTPRequestHandler, run_dir: Path) -> dict:
    content_type = handler.headers.get("Content-Type", "")
    length = int(handler.headers.get("Content-Length", "0"))

    if content_type.startswith("multipart/form-data"):
        form = cgi.FieldStorage(
            fp=handler.rfile,
            headers=handler.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
                "CONTENT_LENGTH": str(length),
            },
            keep_blank_values=True,
        )
        payload = {"uploaded_files": {}}
        upload_dir = run_dir / "uploads"
        for key in form.keys():
            item = form[key]
            items = item if isinstance(item, list) else [item]
            for part in items:
                if getattr(part, "filename", None):
                    if not part.filename:
                        continue
                    filename = _safe_upload_name(part.filename)
                    upload_dir.mkdir(parents=True, exist_ok=True)
                    dst = upload_dir / f"{key}_{filename}"
                    with dst.open("wb") as f:
                        data = part.file.read()
                        if isinstance(data, str):
                            data = data.encode("utf-8")
                        f.write(data)
                    payload["uploaded_files"][key] = str(dst)
                    payload[f"{key}_original_name"] = part.filename
                else:
                    value = part.value
                    if isinstance(value, bytes):
                        value = value.decode("utf-8", errors="replace")
                    payload[key] = value
        return payload

    if content_type.startswith("application/json"):
        return json.loads(handler.rfile.read(length).decode("utf-8") or "{}")

    body = handler.rfile.read(length).decode("utf-8", errors="replace")
    return json.loads(body or "{}")


def _run_status(run_id: str) -> dict:
    run_dir = _run_dir(run_id)
    request_path = run_dir / "request.json"
    status_path = run_dir / "status.json"
    request = _read_json(request_path, {})
    status = _read_json(status_path, {"id": run_id, "status": "failed", "message": "Incomplete run record"})
    status["id"] = run_id
    status["session_name"] = request.get("session_name", run_id)
    with LOCK:
        process = PROCESSES.get(run_id)
    if process and process.poll() is None:
        status["status"] = "running"
    elif status.get("status") in {"queued", "running"}:
        status["status"] = "failed"
        status["message"] = "Simulation process is no longer running"
    return status


def _list_runs() -> list[dict]:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    runs = []
    now = time.time()
    for path in RUNS_DIR.iterdir():
        if path.is_dir():
            request_path = path / "request.json"
            status_path = path / "status.json"
            if not request_path.exists() and not status_path.exists():
                try:
                    age_seconds = now - path.stat().st_mtime
                except OSError:
                    age_seconds = 0
                if age_seconds > 30:
                    shutil.rmtree(path, ignore_errors=True)
                continue
            runs.append(_run_status(path.name))
    runs.sort(key=lambda r: r.get("started_at") or 0, reverse=True)
    return runs


def _start_run(payload: dict, run_id: str, run_dir: Path) -> dict:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    payload = _jsonable(payload)
    _write_json(run_dir / "request.json", payload)
    _write_json(
        run_dir / "status.json",
        {"id": run_id, "status": "queued", "started_at": time.time(), "ended_at": None, "message": "Waiting for simulation process to start"},
    )

    log_file = open(run_dir / "run.log", "w", encoding="utf-8", errors="replace")
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("MPLBACKEND", "Agg")
    process = subprocess.Popen(
        [sys.executable, str(RUNNER), run_id, str(run_dir / "request.json")],
        cwd=str(ROOT_DIR),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=env,
        text=True,
    )
    with LOCK:
        PROCESSES[run_id] = process

    def waiter():
        try:
            process.wait()
        finally:
            log_file.close()
            with LOCK:
                PROCESSES.pop(run_id, None)

    threading.Thread(target=waiter, daemon=True).start()
    return _run_status(run_id)


class OmegaWebHandler(BaseHTTPRequestHandler):
    server_version = "CNCarbonPolicyWeb/0.1"

    def log_message(self, format, *args):
        print("[%s] %s" % (self.log_date_time_string(), format % args), flush=True)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        try:
            if path == "/":
                _send_text(self, INDEX_HTML, content_type="text/html; charset=utf-8")
                return
            if path == "/api/runs":
                _send_json(self, _list_runs())
                return
            if path.startswith("/api/runs/"):
                self._handle_run_get(path)
                return
            _send_text(self, "Not found", HTTPStatus.NOT_FOUND)
        except Exception as exc:
            _send_text(self, str(exc), HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.rstrip("/") != "/api/runs":
            _send_text(self, "Not found", HTTPStatus.NOT_FOUND)
            return
        try:
            RUNS_DIR.mkdir(parents=True, exist_ok=True)
            run_id = time.strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
            run_dir = _run_dir(run_id)
            run_dir.mkdir(parents=True, exist_ok=False)
            payload = _parse_post_payload(self, run_dir)
            run = _start_run(payload, run_id, run_dir)
            _send_json(self, run, HTTPStatus.CREATED)
        except Exception as exc:
            if "run_dir" in locals() and run_dir.exists() and not any(run_dir.iterdir()):
                shutil.rmtree(run_dir, ignore_errors=True)
            _send_text(self, str(exc), HTTPStatus.BAD_REQUEST)

    def _handle_run_get(self, path: str):
        parts = [unquote(p) for p in path.split("/") if p]
        if len(parts) < 3:
            _send_text(self, "Not found", HTTPStatus.NOT_FOUND)
            return
        run_id = parts[2]
        run_dir = _run_dir(run_id)
        if not run_dir.exists():
            _send_text(self, "Run not found", HTTPStatus.NOT_FOUND)
            return

        if len(parts) == 3:
            _send_json(self, _run_status(run_id))
            return

        action = parts[3]
        if action == "summary":
            summary = _read_json(run_dir / "summary.json", None)
            if summary is None:
                _send_text(self, "Summary not available", HTTPStatus.NOT_FOUND)
            else:
                summary["files"] = _output_files(run_dir)
                _send_json(self, summary)
            return
        if action == "log":
            model_log = _latest_model_log(run_dir)
            if model_log is not None:
                label = _relative_label(model_log, run_dir)
                text = f"Showing model progress log: {label}\n\n{_tail_text(model_log)}"
            else:
                log_path = run_dir / "run.log"
                text = ""
                if log_path.exists():
                    text = f"Showing process stdout/stderr log: run.log\n\n{_tail_text(log_path)}"
            _send_text(self, text)
            return
        if action == "files" and len(parts) == 5:
            filename = parts[4]
            file_path = (run_dir / "outputs" / filename).resolve()
            outputs_dir = (run_dir / "outputs").resolve()
            if outputs_dir not in file_path.parents or not file_path.is_file():
                _send_text(self, "File not found", HTTPStatus.NOT_FOUND)
                return
            content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(file_path.stat().st_size))
            disposition = "inline" if content_type.startswith("image/") else "attachment"
            fallback_name = file_path.name.encode("ascii", errors="ignore").decode("ascii") or f"output.{file_path.suffix.lstrip('.') or 'file'}"
            self.send_header("Content-Disposition", f"{disposition}; filename=\"{fallback_name}\"; filename*=UTF-8''{quote(file_path.name)}")
            self.end_headers()
            with file_path.open("rb") as f:
                while True:
                    chunk = f.read(1024 * 512)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
            return

        _send_text(self, "Not found", HTTPStatus.NOT_FOUND)


def main() -> int:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), OmegaWebHandler)
    print(f"Carbon emission policy web app running at http://{HOST}:{PORT}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
