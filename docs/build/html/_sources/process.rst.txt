Forecast Process
================

The dry lightning forecast is generated using statistical and machine learning methods. Namely, this is a Linear Discriminant Ananlysis (LDA) model combined with a Random Forest Model. 
Numerous convective and atmospheric values/indices are fed into the model to predict the probability of lightning occurrence. This model is heavily based on that of [2] Rorig et al. (2007) and [3] Wickramasinghe et al. (2024). 
These variables are: 
    - Convective Available Potential Energy (CAPE)
    - Lifted Index (LI)
    - K-Index
    - Total Totals Index
    - The 500hPa-850hPa temperature difference
    - the dewpoint depression at 850hPa
    - the dewpoint depression at 700hPa
    - the Sweat Index
    - the Lifting Condensation Level (LCL)

Dry lightning (defined on the home page) is a categorical variable. I also defined another variable, moist lightning (lightning occurring with wetting rains), in order to get a more complete definition of the dry lightning probability. The LDA-RF model calculated proabilities for both dry and moist lightning (as well as a no-lightning category). The displayed forecast is based on the dry lightning probability only.

Beginning in 2018, sounding data from every location in Canada, and those within 200km of the Canadian border were downloaded. Additionally, precipitation observation from coincident stations and lightning strike data within 10km of each station were also stored.
A different model is trained for each ecozone in Canada. The data is determined by which sounding launch locations reside in each ecozone or sit within a 200km buffer. Probabilites are then assigned to each model grid cell that sits in an ecozone based on the variable gather from raw model output. No surface variables were selected due to lower confidence in these values in complex terrain. 

Finally, the proabilities are binned into three categories:
- Low: the lowest 65% of probabilities
- Moderate: the next 25% of probabilities
- Considerable: the top 10% of probabilities

This is defined in `./PROCESS/station_lightning_lda.py`.

Domain
------

The forecast domain covers the ecozones of Canada shown in the map below.
Each ecozone is uniquely colored. Red dots indicate sounding launch locations. This is where training data is grabbed. 

.. image:: ./static/ecozones_sounding_stations_map.png
   :alt: Forecast Domain Map
   :align: center
   :width: 600px

Daily Forecast Workflow
-----------------------

1. **Data Acquisition**: Daily 12 UTC RDPS/HRDPS analysis data is retrieved
2. **Index Calculation**: All required indices for LDA and Random Forest models are calculated on the full grid
3. **Masking by Ecozone**: Weather data is masked by ecozone for model-specific fitting
4. **Probability Calculation**: Dry lightning probability is calculated for all grid cells based on the LDA-RF model for each ecozone
5. **Classification**: Output is assigned as one of:
   
   - "Low"
   - "Moderate"
   - "Considerable"

   based on the nationwide binning thresholds. 
6. **Map Generation**: The forecast map is generated and saved as a .tif, and .png files. Only the .png files are displayed online for now. 



I follow the definitions provided by Avalanche Canada for their risk communication.

Ecozone-Based Binning
---------------------

Low is defined as the lowest 50% of probabilities, Moderate is defined as the next 30% of probabilities, and Considerable is defined as the top 20% of probabilities. 
This binning is done separately for each ecozone to account for regional differences in dry lightning occurrence.
We then define the nationwide bins by taking a weighted mean of each ecozone's bin thresholds. Weights are the number of lightning stikes that occurred in the training datasets during the 2018-2025 training period. However these were only stikes that occurred within the 10km radius of each sounding location. Thus, ecozones with more stations that have more lightning are more heavily favoured to have some dry lightning occurrence.

Training
--------

A unique model was trained for each ecozone using data from 2018-2025. Teh training dataset was a straitifed random sample consisting of 80% of the data and ensureing that 80% of both dry and moist lightning strikes days were included. 
Data for each ecoxzone consisted of sound launch data within each ecozone as well as a 200km buffer. This was necessary as some ecozones (Taiga Cordillera) had no stations within it. Additionally, the 200km buffer had sufficiently similar weather and convection rates to warrant inclusion to increase the training dataset size. An sample map for Pacific Maritime ecozone is shown below. 

.. image:: ./static/Pacific_Maritime.png
   :width: 600px
   :align: center

Future Enhancements
-------------------

Extension to general lightning prediction using a combination of dry and moist lightning probabilies. However, I would like to limit some of the variables being used in the LDA-RF model for this sort of prediction.

I would also like to convert the maps to an interactive format. But I am lazy at the moment. Please reach out to me if you would like a closer look. 