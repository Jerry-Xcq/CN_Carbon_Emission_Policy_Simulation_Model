# China Vehicle Carbon Emission Policy Simulation Platform

China Vehicle Carbon Emission Policy Simulation Platform is a China-focused vehicle policy simulation project designed to evaluate how regulatory pathways, market assumptions, and technology constraints may shape passenger-vehicle carbon-emission outcomes.

The public site introduces the project concept, workflow, deployment direction, and planned demonstration materials. It is intended as a collaboration-facing landing page for automakers, automotive data institutions, researchers, policy analysts, and potential project partners.

## Project Highlights

- China-localized policy simulation workflow for passenger-vehicle carbon-emission analysis
- Browser-based interaction design for scenario configuration and result review
- Support for policy inputs, model run tracking, summary metrics, logs, and output files in the full local application
- A deployment path from local research use to server-hosted access for broader collaboration

## Local Web App

This repository can include the local browser interface for configuring and running policy scenarios:

- `web_app.py` provides a standard-library Python web server and browser UI.
- `omega_web_runner.py` starts one isolated model process for each scenario run.
- `WEB_APP_README.md` and `WEB_APP_README.en.md` describe local setup and operation.

## Collaboration Focus

The project is designed to support:

- Automaker compliance and technology-pathway scenario analysis
- Automotive market and fleet data research
- Carbon-emission policy evaluation and sensitivity analysis
- Reproducible reporting workflows for policy briefs, research papers, and stakeholder workshops

## Contact

Xu Jiarui, PhD Student, College of Transportation, Tongji University, Email: 2410824@tongji.edu.cn  
Liu Haobing, Professor and Doctoral Supervisor, College of Transportation, Tongji University, Email: liuhaobing@tongji.edu.cn

## Public Preview

The GitHub Pages site introduces the project and demonstration workflow.

The GitHub Pages site is built from the `docs/` directory.
