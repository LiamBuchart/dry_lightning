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
        .valid-period { background: var(--color-background-secondary); padding: 14px; border-left: 4px solid var(--color-brand-primary); border-radius: 5px; margin: 20px 0; font-size: 14px; }
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

Map Interpretation
^^^^^^^^^^^^^^^^^^

By default the forecast region with be Grey, Yellow, or Orange. The light grey is the base map and is outside of the forecast region.

- Grey: "Low" probability of dry lightning
- Yellow: "Moderate" probability of dry lightning
- Orange: "Considerable" probability of dry lightning

Assume that "Low" is a null forecast for dry lightning, or any lightning occurrence. "Moderate" can be interpreted as a low likelihood of dry lightning. "Considerable" is the highest forecast category. Some lightning occurrence or at minimal instability is expected.

Maps
^^^^
Click on map to enlarge. Updated daily around 10:00 MT. 

.. image:: ./static/d1.png
   :width: 600px
   :align: center
**D1 Forecast Map**

.. image:: ./static/d0.png
   :align: center
   :width: 600px
**D0 Forecast Map**

.. image:: ./static/d1_yesterday.png
   :class: with-border
   :align: center
   :width: 600px
**Yesterday's D1 Forecast Map**

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

Training takes place using sounding launch data from every site in Canada. Surface, upper air observations, and lightning strikes are gathered for the years 2018-2025.

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



