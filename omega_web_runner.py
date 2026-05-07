"""
Run one OMEGA scenario for the local web app.

This script is intentionally isolated from the web server process.  The OMEGA
model uses module globals during a run, so each web run gets its own Python
process and output directory.
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
OMEGA_DIR = ROOT_DIR / "omega_model"


def _json_safe(value):
    try:
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        return str(value)
    except Exception:
        return None


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_name(value: str, fallback: str) -> str:
    value = (value or "").strip()
    value = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", value, flags=re.UNICODE).strip("_")
    return value[:60] or fallback


def _float(payload: dict, key: str, default: float, min_value: float | None = None, max_value: float | None = None) -> float:
    try:
        value = float(payload.get(key, default))
    except (TypeError, ValueError):
        value = default
    if min_value is not None:
        value = max(min_value, value)
    if max_value is not None:
        value = min(max_value, value)
    return value


def _int(payload: dict, key: str, default: int, min_value: int | None = None, max_value: int | None = None) -> int:
    try:
        value = int(payload.get(key, default))
    except (TypeError, ValueError):
        value = default
    if min_value is not None:
        value = max(min_value, value)
    if max_value is not None:
        value = min(max_value, value)
    return value


def _bool(payload: dict, key: str, default: bool = False) -> bool:
    value = payload.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _number_list(payload: dict, key: str, default: list, cast=float) -> list:
    value = payload.get(key, default)
    if isinstance(value, list):
        raw_values = value
    elif isinstance(value, str):
        raw_values = [v.strip() for v in value.replace(";", ",").split(",") if v.strip()]
    else:
        return default
    try:
        return [cast(v) for v in raw_values]
    except (TypeError, ValueError):
        return default


def _uploaded_file(payload: dict, field_name: str) -> str | None:
    uploaded = payload.get("uploaded_files", {})
    if isinstance(uploaded, dict):
        path = uploaded.get(field_name)
        if path and Path(path).exists():
            return str(Path(path).resolve())
    return None


def _series(rows: list[dict], column: str, decimals: int | None = None) -> list[dict]:
    data = []
    for row in rows:
        if column not in row or row[column] == "":
            continue
        try:
            value = float(row[column])
        except (TypeError, ValueError):
            continue
        if decimals is not None:
            value = round(value, decimals)
        data.append({"year": int(float(row["calendar_year"])), "value": value})
    return data


def _final_value(rows: list[dict], column: str, scale: float = 1.0, decimals: int = 2):
    values = _series(rows, column)
    if not values:
        return None
    return round(values[-1]["value"] / scale, decimals)


def _build_summary(summary_csv: Path, output_dir: Path, request_payload: dict) -> dict:
    with summary_csv.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    columns = list(rows[0].keys()) if rows else []
    market_share_columns = [c for c in columns if c.startswith("abs_share_frac_")]

    preferred_shares = [
        "abs_share_frac_BEV",
        "abs_share_frac_PHEV",
        "abs_share_frac_ICE",
        "abs_share_frac_car",
        "abs_share_frac_truck",
    ]
    share_columns = [c for c in preferred_shares if c in columns]
    if len(share_columns) < 3:
        share_columns.extend([c for c in market_share_columns if c not in share_columns][: 6 - len(share_columns)])

    series = {
        "sales_total": _series(rows, "sales_total", 0),
        "vehicle_gwh": _series(rows, "vehicle_GWh", 2),
        "vehicle_co2e_mg": _series(rows, "vehicle_co2e_Mg", 0),
        "average_vehicle_cost": _series(rows, "average_vehicle_cost", 0),
        "total_vehicle_cost_billions": _series(rows, "total_vehicle_cost_billions", 3),
        "shares": {c.replace("abs_share_frac_", ""): _series(rows, c, 4) for c in share_columns},
    }

    cards = [
        {
            "label": "Final-Year Sales",
            "value": _final_value(rows, "sales_total", scale=1_000_000, decimals=2),
            "unit": "million vehicles",
        },
        {
            "label": "Final-Year Battery Demand",
            "value": _final_value(rows, "vehicle_GWh", decimals=1),
            "unit": "GWh",
        },
        {
            "label": "Final-Year Certified Carbon Emissions",
            "value": _final_value(rows, "vehicle_co2e_Mg", scale=1_000_000, decimals=2),
            "unit": "million Mg",
        },
        {
            "label": "Final-Year Average Manufacturing Cost",
            "value": _final_value(rows, "average_vehicle_cost", decimals=0),
            "unit": "USD / vehicle",
        },
    ]

    output_files = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file():
            relative_name = path.relative_to(output_dir).as_posix()
            phase = "Pass 0 - consolidated automaker policy projection outputs" if relative_name.startswith("consolidate_1/") else "Pass 1 - by-automaker policy projection outputs"
            output_files.append(
                {
                    "name": relative_name,
                    "size": path.stat().st_size,
                    "mtime": path.stat().st_mtime,
                    "kind": path.suffix.lower().lstrip(".") or "file",
                    "phase": phase,
                }
            )

    return {
        "request": request_payload,
        "summary_csv": summary_csv.relative_to(output_dir).as_posix(),
        "rows": rows,
        "columns": columns,
        "cards": cards,
        "series": series,
        "files": output_files,
    }


def _apply_settings(settings, payload: dict, run_id: str, run_dir: Path):
    session_name = _safe_name(payload.get("session_name", ""), "Carbon_Policy_Scenario")
    settings.session_name = session_name
    settings.session_unique_name = f"{session_name}_{run_id}"
    output_dir = run_dir / "outputs"
    settings.output_folder_base = str(output_dir) + os.sep
    settings.output_folder = settings.output_folder_base

    settings.analysis_final_year = _int(payload, "analysis_final_year", settings.analysis_final_year, 2026, 2040)
    settings.credit_market_efficiency = _float(payload, "credit_market_efficiency", settings.credit_market_efficiency, 0.0, 1.0)
    settings.consumer_pricing_multiplier_max = _float(
        payload, "consumer_pricing_multiplier_max", settings.consumer_pricing_multiplier_max, 1.0, 2.0
    )
    settings.consumer_pricing_multiplier_min = 0.9999999996 / settings.consumer_pricing_multiplier_max
    settings.producer_market_category_ramp_limit = _float(
        payload, "producer_market_category_ramp_limit", settings.producer_market_category_ramp_limit, 0.01, 1.0
    )
    settings.new_vehicle_price_elasticity_of_demand = _float(
        payload, "new_vehicle_price_elasticity_of_demand", settings.new_vehicle_price_elasticity_of_demand, -5.0, 0.0
    )
    settings.bev_range_mi = _int(payload, "bev_range_mi", settings.bev_range_mi, 100, 800)
    settings.phev_range_mi = _int(payload, "phev_range_mi", settings.phev_range_mi, 20, 250)
    settings.multiprocessing = _bool(payload, "multiprocessing", False)
    settings.second_pass_production_constraints = _bool(payload, "second_pass_production_constraints", settings.second_pass_production_constraints)
    settings.verbose = False
    settings.verbose_console_modules = []

    policy_preset = payload.get("policy_preset", "baseline")
    if policy_preset == "upload":
        uploaded = _uploaded_file(payload, "policy_targets_upload")
        if uploaded:
            settings.policy_targets_file = uploaded
    elif policy_preset == "strict":
        strict_targets = OMEGA_DIR / "test_inputs" / "ghg_standards-cm_cn_strict.csv"
        if strict_targets.exists():
            settings.policy_targets_file = str(strict_targets)

    if payload.get("nev_preset") == "upload":
        uploaded = _uploaded_file(payload, "nev_requirements_upload")
        if uploaded:
            settings.nev_requirements_file = uploaded

    if payload.get("upstream_preset", "zero") == "upload":
        uploaded = _uploaded_file(payload, "fuel_upstream_methods_upload")
        if uploaded:
            settings.fuel_upstream_methods_file = uploaded

    required_sales_share_preset = payload.get("required_sales_share_preset", "noacc")
    if required_sales_share_preset == "upload":
        uploaded = _uploaded_file(payload, "required_sales_share_upload")
        if uploaded:
            settings.required_sales_share_file = uploaded
    elif required_sales_share_preset == "floor_user":
        file_path = OMEGA_DIR / "test_inputs" / "required_sales_share_body_style_BEV_PHEV_floor_user_20251226.csv"
        if file_path.exists():
            settings.required_sales_share_file = str(file_path)

    production_constraints_preset = payload.get("production_constraints_preset", "cn_ice")
    if production_constraints_preset == "upload":
        uploaded = _uploaded_file(payload, "production_constraints_upload")
        if uploaded:
            settings.production_constraints_file = uploaded
    elif production_constraints_preset == "general":
        file_path = OMEGA_DIR / "test_inputs" / "production_constraints-body_style_20221130.csv"
        if file_path.exists():
            settings.production_constraints_file = str(file_path)

    if payload.get("price_modifications_preset", "default") == "upload":
        uploaded = _uploaded_file(payload, "vehicle_price_modifications_upload")
        if uploaded:
            settings.vehicle_price_modifications_file = uploaded

    battery_years = _number_list(payload, "battery_GWh_limit_years", settings.battery_GWh_limit_years, int)
    battery_limits = _number_list(payload, "battery_GWh_limit", settings.battery_GWh_limit, float)
    if len(battery_years) == len(battery_limits) and battery_years:
        settings.battery_GWh_limit_years = battery_years
        settings.battery_GWh_limit = battery_limits

    return output_dir


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python omega_web_runner.py <run_id> <request_json>", file=sys.stderr)
        return 2

    run_id = sys.argv[1]
    request_path = Path(sys.argv[2]).resolve()
    run_dir = request_path.parent
    status_path = run_dir / "status.json"

    os.environ.setdefault("MPLBACKEND", "Agg")
    sys.path.insert(0, str(ROOT_DIR))
    sys.path.insert(0, str(OMEGA_DIR))

    payload = json.loads(request_path.read_text(encoding="utf-8"))
    started = time.time()
    _write_json(
        status_path,
        {
            "id": run_id,
            "status": "running",
            "started_at": started,
            "ended_at": None,
            "message": "Simulation running",
        },
    )

    try:
        from omega_model import OMEGASessionSettings
        from omega_model.omega import run_omega

        settings = OMEGASessionSettings()
        output_dir = _apply_settings(settings, payload, run_id, run_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        run_omega(settings, standalone_run=True)

        summary_files = sorted(output_dir.rglob("*_summary_results.csv"), key=lambda p: p.stat().st_mtime)
        if not summary_files:
            raise RuntimeError("Simulation finished, but no *_summary_results.csv file was found. Please review run.log and the simulation logs.")

        summary = _build_summary(summary_files[-1], output_dir, payload)
        _write_json(run_dir / "summary.json", summary)

        _write_json(
            status_path,
            {
                "id": run_id,
                "status": "completed",
                "started_at": started,
                "ended_at": time.time(),
                "message": "Simulation completed",
                "output_dir": str(output_dir),
                "summary_csv": summary_files[-1].name,
            },
        )
        return 0
    except Exception as exc:
        _write_json(
            status_path,
            {
                "id": run_id,
                "status": "failed",
                "started_at": started,
                "ended_at": time.time(),
                "message": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        print(traceback.format_exc(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
