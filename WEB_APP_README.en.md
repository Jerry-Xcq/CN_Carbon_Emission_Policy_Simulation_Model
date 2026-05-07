# CN OMEGA Web App

This document explains how to use and publish the local web front end for the China-localized OMEGA scenario model. The front end provides scenario configuration, run submission, log review, summary visualization, and output-file browsing.

Chinese version: [WEB_APP_README.md](WEB_APP_README.md)

## Release Scope

Recommended files to publish for the local web front end:

- `web_app.py`: local web server and browser interface implemented with the Python standard library.
- `omega_web_runner.py`: one-scenario runner. Each submitted scenario starts an isolated Python process that calls the local `omega_model.omega.run_omega()`.
- `WEB_APP_README.md`: Chinese setup and operating instructions.
- `WEB_APP_README.en.md`: English setup and operating instructions.

## Start the App

Run the service from the repository root:

```powershell
python web_app.py
```

Open the app in a browser:

```text
http://127.0.0.1:8765
```

Stop the service by pressing `Ctrl+C` in the terminal running `python web_app.py`.

## LAN or Server Access

By default, the app listens only on `127.0.0.1`. To allow access from the same local network or through a reverse proxy, set the host explicitly:

```powershell
$env:OMEGA_WEB_HOST="0.0.0.0"
$env:OMEGA_WEB_PORT="8765"
python web_app.py
```

Then open the app with the machine IP address or server domain, for example:

```text
http://<machine-ip>:8765
```

Security note: this prototype has no login system. Anyone who can access the URL can submit a model run on the host machine. Before public deployment, place it behind a controlled network, VPN, or authenticated reverse proxy.

## Interface

- The left panel configures scenario parameters, policy inputs, one-run CSV uploads, and run history.
- The right panel shows key metrics, trend charts, model logs, and output files.
- The emissions-standard selector supports the baseline `ghg_standards-cm_cn.csv` and stricter `ghg_standards-cm_cn_strict.csv` inputs.
- Policy/input uploads are applied only to the current run. Uploaded files are stored under that run's `uploads/` directory and do not overwrite `omega_model/test_inputs`.
- Integrated input categories include emissions standards, NEV credit requirements, upstream-emissions methods, required sales-share constraints, production constraints, and subsidy/price modifications.
- Advanced numeric controls include battery-capacity-limit years, battery-capacity limits, and the second-pass production-constraint switch.

## Run Outputs

Each run creates a directory such as:

```text
web_runs/20260427_203000_ab12cd34/
```

The directory contains:

- `request.json`: scenario parameters submitted by the page.
- `status.json`: run status.
- `run.log`: model-process console output.
- `summary.json`: summary data used by the web page.
- `uploads/`: input files uploaded for this run.
- `outputs/`: OMEGA output files, including `_summary_results.csv`, charts, and detailed CSV files.

`web_runs/` contains local runtime artifacts and should not be committed to the public repository.

## Dependencies

The web service itself uses only the Python standard library. Model-execution dependencies are determined by the user's local `omega_model/` environment.

Use the same Python environment that has already been validated for `omega_model`, for example:

```powershell
python --version
python web_app.py
```

## Prototype Status

This is a local research prototype. It wraps an existing model in a browser interface for non-code users. The model still runs locally, is not uploaded to an external service, and does not require internet access.

To start it in the background on Windows, use the current directory rather than a machine-specific absolute path:

```powershell
Start-Process -FilePath python -ArgumentList 'web_app.py' -WorkingDirectory (Get-Location) -WindowStyle Hidden
```

Foreground execution is recommended during debugging because logs and failures are easier to inspect.
