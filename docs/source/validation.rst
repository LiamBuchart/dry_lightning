Verification 
============

Model Validation
----------------

Verification plots and validation metrics are generated to assess model performance.

- Daily validation (D0)
- 1-day forecast validation (D1)
- Comparison against observed CLDN data

Statistics include: Probability of Detection, False Alarm Ratio, Critical Success Index, the Hideki Skill Score, and Bias.
However, I have had difficulty in defining some of these metric in a three bin forecast that has only two outcomes. 

Continuing to refine definitions and they may change on short notice.

Overall Verification Values
---------------------------

These metrics are an average of the daily metrics from all model runs over each forecast day (d0 and d1). They are updated with each model run.

.. csv-table:: Statistics
   :file: ./static/validation_mean_stats.csv
   :header: "Forecast Day", "POD", "FAR", "CSI", "HSS", "Bias"
   :widths: 15, 10, 10, 10, 10, 10
   :align: center

Recent Validation Plots
--------------------------

.. image:: ./static/14_timeseries.png
   :alt: Latest validation plot
   :align: center
**Daily validation metrics for the last 14 days**

.. image:: ./static/90_timeseries.png
   :alt: Latest validation plot
   :align: center
**Daily validation metrics for the last 90 days**

Note that during early season these plots are likely to be the same since the model has not been running for 90 days. 
I also plan to add a daily updated lightning strike count plot to this page so account for trends in stike numbers versus model performance. 

Validation Scripts
------------------

- ``validate_d0.py`` - Verification for the d0 forecast.
- ``validate_d1.py`` - Verification for the d1 forecast.
- ``plot_validate.py`` - Visualization of verification results. Create and store base stats. 
