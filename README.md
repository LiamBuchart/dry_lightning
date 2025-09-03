# Dry Lightning Prediction


## Dry lightning criteria:
- Any lightning occurrence.
- < 2.5mm of rain within a day of the lightning stroke.

### Lightning Data
All lightning data comes from the Canadian Lightning Detection Network (CLDN), daata which is stored at CWFIS.

All products are interpolated to a common lat/lon grid. 
Lightning is binned to +/- half the distance between grid center points. 

### Precipitation
All forecast data comes from Environment and Climate Change Canada

Precipitaiton data comes the RDPA, the High Resolution Deterministic Precipitation Analysis (HRDPA). This is used to initialize the RDPS forecast model. This is the ECCC best guess for precipitation which used various data sources to give a nation-wise look at the 24-hr preciptiation total.

### Climatology
Strictly speaking climatology is not the correct word. However, several year's worth of CLDN and RDPA data are compared to find dry lightning occurence. These dates and time are then used to constuct mean weather patterns for these days in comparison to the mean over the entire duration of data acquisition.

