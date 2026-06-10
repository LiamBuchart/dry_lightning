Verification 
============

Model Validation
----------------

Verification plots and validation metrics are generated to assess model performance. Verification takes place on ~650 weather stations across Canada in conjunction with the Canadian Lightning Detection Network flash data.

- Daily validation (D0)
- 1-day forecast validation (D1)
- Comparison against observed CLDN data

Statistics include: Accuracy, the Hideki Skill Score, and the Hanssen-Kuipers Discimnant value.
Accuracy is based on a three category view of the forecast:
The Considerable bin is only a hit if dry lightning occurs. The Moderate is allowed to be a hit when lightning with wetting rain occurs. Finally, no lightning is permitted in the Low forecast bin. 

Continuing to refine definitions and they may change on short notice.

Overall Verification Values
---------------------------

These metrics are an average of the daily metrics from all model runs over each forecast day (d0 and d1). They are updated with each model run.

.. csv-table:: Statistics
   :file: ./static/cat_validation_mean_stats.csv
   :header: "Forecast Day", "ACC", "HSS", "HK"
   :widths: 15, 10, 10, 10
   :align: center

Recent Validation Plots
--------------------------

.. image:: ./static/hist.png
   :alt: Latest distribution plot
   :align: center
**Observed and Forecast Distributions for D0 and D1 Forecasts**

.. image:: ./static/cat_full_season.png
   :alt: Latest validation plot
   :align: center
**Daily validation metrics for the fire season**

Plots and tables are updated daily near 11am MDT. 
I also plan to add a daily updated lightning strike count plot to this page so account for trends in stike numbers versus model performance. 

Validation Scripts
------------------

- ``d0_allstn_validate.py`` - Verification for the d0 forecast.
- ``d1_allstn_validate.py`` - Verification for the d1 forecast.
- ``png_plot_validate.py`` - Visualization of verification results. Create and store base stats. 
