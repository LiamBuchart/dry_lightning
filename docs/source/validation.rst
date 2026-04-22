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

Contunuing to refine definitions and they may change on short notice. 

Validation Scripts
------------------

- ``validate_d0.py`` - Verification for the d0 forecast.
- ``validate_d1.py`` - Verification for the d1 forecast.
- ``plot_validate.py`` - Visualization of verification results. Create and store base stats. 

Recent Validation Results
--------------------------

.. image:: ../VALIDATE/temp/latest_validation.png
   :alt: Latest validation plot
   :align: center