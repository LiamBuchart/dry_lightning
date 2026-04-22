## Process

Daily 12 UTC RDPS ( or HRDPS) analysis data is pulled in. From here all indices required by the Linear Discriminant Analysis and Random Forest Model are calcaulted on the full grid. 

Next, weather data is masked by each ecozone so that the corresponding data can be fit for the correct model. Once the dry lightning probability is calculated for all weather grid cells. An output of "More Likely", "Less Likely", or "Highly Improbable" is assigned to each grid cell. The bins are defined by the ecozone statistical model for each region. A probability of say 25% in one ecozone may be in the "Less Likely" category for one region, and not in another. 

## Future Updates

Hoping to use the same model for general lightning prediction. I am already calculating the probability of lightning with wetting rains. So will be a simple additions of the two probabilities. 