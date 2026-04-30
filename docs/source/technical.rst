Technical Documentation
=======================

Code Structure
--------------

- **FORECAST/**: Forecast model storage and daily forecast generation
- **PROCESS/**: Data processing and model training
- **DOWNLOAD/**: Data acquisition and preprocessing
- **VALIDATE/**: Model verification scripts
- **UTILS/**: Utility functions and data handling
- **CLIM_DATA/**: Climatological data - depreciated

Key Modules
-----------

See source code documentation for detailed API information.

Updates
-------

As of April 29, 2026 the forecast bin definitions have changed. 
The previous bins were weighted means of the 50th and 80th percentile.
The new bins are weighted means of the 65th and 90th percentile.
The previous forecast was "hot" and forecasted dry lightning too frequently. 