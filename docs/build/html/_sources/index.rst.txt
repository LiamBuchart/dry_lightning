.. DryLightningForecast1.0 documentation master file, created by
   sphinx-quickstart on Mon Apr 20 15:28:18 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Dry Lightning Prediction
========================

Welcome to the Dry Lightning Prediction documentation. This site contains forecast maps, verification plots, and detailed process descriptions.

Interactive Forecast Map
-------------------------

.. raw:: html

    <style>
        .forecast-container { margin: 20px 0; }
        .forecast-image { width: 100%; max-width: 600px; border: 2px solid #ddd; border-radius: 5px; margin: 15px auto; display: block; height: auto; }
        .forecast-grid { display: flex; flex-direction: column; gap: 20px; margin: 20px 0; align-items: center; }
        .forecast-item { text-align: center; width: 100%; }
        .forecast-title { font-weight: bold; margin-bottom: 10px; color: #333; font-size: 16px; }
        .valid-period { background: #f8f9fa; padding: 10px; border-radius: 5px; margin: 15px 0; font-size: 14px; }
        .yesterday-section { margin-top: 40px; padding-top: 20px; border-top: 2px solid #eee; }
    </style>

    <div class="valid-period">
        <strong>Current Valid Periods:</strong><br>
        D0: April 21, 2026 00 UTC to April 22, 2026 00 UTC<br>
        D1: April 22, 2026 00 UTC to April 23, 2026 00 UTC
    </div>

    <div class="forecast-grid">
        <div class="forecast-item">
            <div class="forecast-title">D0 Forecast (Current Day)</div>
            <img src="../FORECAST/MAPS/d0_2026-04-21_lightning_forecast_points.png" alt="D0 Forecast Map" class="forecast-image"
                 onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
            <p style="display: none; color: #666; font-style: italic; margin: 20px 0;">
                D0 forecast image not available yet.</p>
        </div>
        <div class="forecast-item">
            <div class="forecast-title">D1 Forecast (Next Day)</div>
            <img src="../FORECAST/MAPS/d1_2026-04-21_lightning_forecast_points.png" alt="D1 Forecast Map" class="forecast-image"
                 onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
            <p style="display: none; color: #666; font-style: italic; margin: 20px 0;">
                D1 forecast image not available yet.</p>
        </div>
        <div class="forecast-item">
            <div class="forecast-title">Yesterday's D1 Forecast (April 20, 2026)</div>
            <p style="margin: 5px 0; font-size: 13px; color: #666;">This was yesterday's forecast for today (April 21, 2026).</p>
            <img src="../FORECAST/MAPS/d1_2026-04-20_lightning_forecast_points.png" alt="Yesterday's D1 Forecast" class="forecast-image"
                 onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
            <p style="display: none; color: #666; font-style: italic; margin: 20px 0;">
                Yesterday's forecast image not available yet.</p>
        </div>
    </div>

Project Overview
================

Dry Lightning Definition
------------------------

Dry lightning is defined as:

- Any lightning occurrence within 10km of the station
- With less than 2.5mm of rain from 12UTC on the day of the lightning to 12UTC the following day

Data Sources
------------

**Lightning Data**: Canadian Lightning Detection Network (CLDN) stored at CWFIS

**Forecast Data**: Environment and Climate Change Canada (ECCC) - RDPS/HRDPS

**Precipitation**: Surface observation network stored at CWFIS

Training
--------

Training takes place using sounding launch data from every site in Canada. Surface, upper air observations, and lightning strikes are gathered for the years 2017-2025.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   process
   validation
   technical

Quick Links
-----------

- `GitHub Repository <https://github.com/LiamBuchart/dry_lightning>`_
- Latest Forecast
- Recent Verifications

