.. DryLightningForecast1.0 documentation master file, created by
   sphinx-quickstart on Mon Apr 20 15:28:18 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

==============================
Dry Lightning Forecast
==============================

Welcome to the Dry Lightning Forecast viewer and documentation. This site contains forecast maps, verification plots, and a detailed process descriptions along with information on datasource and model construction.

Interactive Forecast Map
^^^^^^^^^^^^^^^^^^^^^^^^^

.. raw:: html

    <style>
        .forecast-container { margin: 20px 0; }
        .forecast-image { width: 100%; max-width: 800px; border: 1px solid var(--color-border); border-radius: 8px; margin: 15px auto; display: block; height: auto; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .forecast-grid { display: flex; flex-direction: column; gap: 24px; margin: 24px 0; align-items: center; }
        .forecast-item { text-align: center; width: 100%; background: var(--color-background-secondary); padding: 20px; border-radius: 8px; }
        .forecast-title { font-weight: 600; margin-bottom: 12px; color: var(--color-foreground-primary); font-size: 17px; }
        .valid-period { background: var(--color-background-secondary); padding: 14px; border-left: 4px solid var(--color-brand-primary); border-radius: 5px; margin: 20px 0; font-size: 14px; }
        .yesterday-section { margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--color-border); }
    </style>

    <div class="valid-period">
        <strong>Current Valid Periods:</strong><br>
        <span id="valid-periods">Loading...</span>
    </div>

    <script>
        function formatDate(date) {
            const months = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December'];
            return months[date.getMonth()] + ' ' + date.getDate() + ', ' + date.getFullYear();
        }

        function updateValidPeriods() {
            const now = new Date();
            const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);
            const dayAfterTomorrow = new Date(tomorrow);
            dayAfterTomorrow.setDate(dayAfterTomorrow.getDate() + 1);

            const d0Start = formatDate(today) + ' - 12 UTC';
            const d0End = formatDate(tomorrow) + ' - 12 UTC';
            const d1Start = formatDate(tomorrow) + ' - 12 UTC';
            const d1End = formatDate(dayAfterTomorrow) + ' - 12 UTC';

            document.getElementById('valid-periods').innerHTML =
                'D0: ' + d0Start + ' to ' + d0End + '<br>' +
                'D1: ' + d1Start + ' to ' + d1End;
        }

        // Update immediately and then every hour
        updateValidPeriods();
    </script>

    <div class="forecast-grid">
        <div class="forecast-item">
            <div class="forecast-title">D0 Forecast</div>
            <img src="_static/d0.png" alt="D0 Forecast Map" class="forecast-image"
                 onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
            <p style="display: none; color: #666; font-style: italic; margin: 20px 0;">
                D0 forecast image not available yet.</p>
        </div>
        <div class="forecast-item">
            <div class="forecast-title">D1 Forecast</div>
            <img src="_static/d1.png" alt="D1 Forecast Map" class="forecast-image"
                 onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
            <p style="display: none; color: #666; font-style: italic; margin: 20px 0;">
                D1 forecast image not available yet.</p>
        </div>
        <div class="forecast-item">
            <div class="forecast-title">Yesterday's D1 Forecast</div>
            <p style="margin: 5px 0; font-size: 13px; color: #666;">.</p>
            <img src="_static/d1_yesterday.png" alt="Yesterday's D1 Forecast" class="forecast-image"
                 onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
            <p style="display: none; color: #666; font-style: italic; margin: 20px 0;">
                Yesterday's D1 forecast image not available yet.</p>
        </div>
    </div>

Project Overview
^^^^^^^^^^^^^^^^^

Dry Lightning Definition
""""""""""""""""""""""""

- Any lightning occurrence within 10km of the station
- With less than 2.5mm of rain from 12UTC on the day of the lightning to 12UTC the following day

Data Sources
""""""""""""

**Lightning Data**: Canadian Lightning Detection Network (CLDN) stored at CWFIS

**Forecast Data**: Environment and Climate Change Canada (ECCC) - RDPS/HRDPS 12 UTC Analyses

**Precipitation**: Surface observation network stored at CWFIS

Training
""""""""

Training takes place using sounding launch data from every site in Canada. Surface, upper air observations, and lightning strikes are gathered for the years 2017-2025.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   process
   validation
   technical
   references

Quick Links
""""""""""""

- `GitHub Repository <https://github.com/LiamBuchart/dry_lightning>`_
- Recent Verifications
- References



