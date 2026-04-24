Forecast Process
================

Daily Forecast Workflow
-----------------------

1. **Data Acquisition**: Daily 12 UTC RDPS/HRDPS analysis data is retrieved
2. **Index Calculation**: All required indices for LDA and Random Forest models are calculated on the full grid
3. **Masking by Ecozone**: Weather data is masked by ecozone for model-specific fitting
4. **Probability Calculation**: Dry lightning probability is calculated for all grid cells
5. **Classification**: Output is assigned as one of:
   
   - "Low"
   - "Moderate"
   - "Considerable"

I follow the definitions provided by Avalanche Canada for their risk communication.

Ecozone-Based Binning
---------------------

Low is defined as the lowest 50% of probabilities, Moderate is defined as the next 30% of probabilities, and Considerable is defined as the top 20% of probabilities. 
This binning is done separately for each ecozone to account for regional differences in dry lightning occurrence.
We then define the nationwide bins by taking a weighted mean of each ecozone's bin thresholds. Weights are the number of lightning stikes that occurred in the trainin dataset.

Future Enhancements
-------------------

Extension to general lightning prediction using the same model framework, incorporating probability of lightning with wetting rains.

I would also like to convert the maps to an interactive format. But I am lazy at the moment. Please reach out to me if you would like a closer look. 