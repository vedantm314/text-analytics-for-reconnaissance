
# TAR Software Package Repository

Code combining preprocessing, data collection, training and inference to generate automated disaster reports.

## Key Files 
* tar_main.py - File that consolidates relevant functions to produce a report 
* date2template* - Files that do different collectiong/processing of USGIS data to be added to the briefings 
* classifiers.py - Calls classifiers (regression, SVN, GAN, CNN) and runs a majority vote to determine the final classification for sentences according to 4 categories (buildings, infrastructure, resilience, other) 
* resilience_curve.py - Generates resilience curves, and calculates t0 and t1 (to calculate recovery time for disaster) 
* config.ini - Set of parameters to control briefing generation
* data - Folder containing log of earthquakes, tweets and news articles

## Usage
**Generating a report**

To generate a report, run 
``` python3 tar_main.py ```.

This would iterate through earthquakes listed in the earthquake log and output a report to the "reports" directory. 

**Generating a resilience curve** 

To do this, call the ```generateResilience``` function in resilience_curve.py. It takes the following parameters - 

* ruptureTime - Reference time to when the earthquake happened (e.g. 2021-02-24 02:05:59)
* twitterFile - CSV with tweets for earthquake
* keywords - keywords to filter tweets by


An example call would be ```generateResilience("2021-02-24 02:05:59", "data/tweets/ArgentinaTweets.csv", ["electricity", "lights"])```