from earthquake_data import *
from usgsModule import *
from website2text import *
from earthquakeReport import EarthquakeReport
from FineTunedBertModule import FineTunedBertModule
from summarize import *

def format_rupture_time(ruptureTime):
    """
    README: Helper function for formatting rupture time as a string to be used in directory name
    
    ruptureTime: Rupture time of earthquake
    """
    
    indexCheck = ruptureTime.find(" ")
    ruptureTime = ruptureTime[:indexCheck] + "_" + ruptureTime[indexCheck + 1:]

    ruptureTime = ruptureTime.replace("/", "-")

    return ruptureTime


def get_data_for_earthquake(earthquakeLog):
    """
    README: Helper function retrieving time and city for earthquakes 
    
    earthquakeLog: Dataframe of earthquakes and associated metadata 
    """
    
    retDict = dict()

    retDict["ruptureTime"] = earthquakeLog[3]
    retDict["city"] = earthquakeLog[1]

    return retDict


def initialize_report_directory(ruptureTimeForPath, city):
    """
    README: Does some initial setup for a report. Given a rupture time and city, it creates a directory that is where all relevant files/data would be stored for that specific earthquake
    
    ruptureTimeForPath: The date of the earthquake
    city: The city of the earthquake
    
    """
    workingPath = os.path.join(os.getcwd(), "reports", ruptureTimeForPath + "_" + city)

    if (not os.path.isdir(workingPath)):
        os.mkdir(workingPath)
        os.mkdir(workingPath + "/overviewData")
        os.mkdir(workingPath + "/predictions")

    return workingPath


def get_sentences_from_news(workingPath, newsArticles):
    """
    README: Runs content retrieval for news articles 
    
    workingPath: Path to create files storing sentences
    newsArticles: Dataframe containing news article links
    """
    
    sentencesList = []

    urlLinks = (newsArticles["url"]).to_numpy()

    for j in range(0, len(urlLinks)):
        get_content(sentencesList, urlLinks[j], workingPath + "/overviewData/article.txt")

    return sentencesList


def get_sections_dictionary(predictions_df, resilienceSummaryText):
    """
    README: Summarizes sentences corresponding to each section (Buildings, Infrastructure, Resilience) and returns them in a dictionary 
    
    predictions_df: A dataframe of predictions from the fine-tuned BERT with a sentence and its predicted label
    resilienceSummaryText: A separate summary text directly retrieved from USGS Pager
    """
    
    buildingsText = get_summary(predictions_df, "buildings", 0.2)
    resilienceText = get_summary(predictions_df, "resilience", 0.2) + "\n\n" + resilienceSummaryText
    infrastructureText = get_summary(predictions_df, "infrastructure", 0.2)

    sectionsDictionary = {"Buildings": buildingsText,
                          "Infrastructure": infrastructureText,
                          "Resilience": resilienceText}

    return sectionsDictionary

def generate_reports_for_earthquakes(earthquakeLogs):
    """
    README: This function takes all earthquakes that are still to be logged and brings together different components (getting summaries, getting news article content, running the fine-tuned BERT model on news sentences, etc.) and outputs a generated report for each of these earthquakes 
    
    earthquakeLogs: Dataframe with earthquakes and associated metadata
    """
    
    earthquakeLogs = earthquakeLogs.to_numpy()

    for x in range(0, len(earthquakeLogs)):
        # add 7 days check only then generate report
        earthquakeData = get_data_for_earthquake(earthquakeLogs[x])
   
        ruptureTime = earthquakeData["ruptureTime"]
        city = earthquakeData["city"]

        ruptureTimeForPath = ruptureTime[:ruptureTime.find(" ")]

        workingPath = initialize_report_directory(ruptureTimeForPath, city)

        pager = earthquakeLogs[x][11] + "/pager"

        initialSummary = generateSummary("data/earthquakes_log.csv", workingPath + "/overviewData/record.txt", (x))

        tectonicSummary = getTectonicIntensityInformation("data/earthquakes_log.csv", workingPath + "/overviewData/intensity.jpg",
                                                          workingPath + "/overviewData/record.txt", x)
        resultText = generate_estimation(pager, workingPath + "/overviewData/1.png", workingPath + "/overviewData/2.png", workingPath + "/overviewData/1.txt")

        newsArticles = pd.read_csv("data/news/" + ruptureTime[: ruptureTime.find(" ")] + "_" + city + "_earthquake.csv")

        sentences = get_sentences_from_news(workingPath, newsArticles)
        print("Got news")
        
        df_sentences = pd.DataFrame(sentences)
        df_sentences.to_csv(workingPath + "/sentences.csv")
        
        fineTunedModel = FineTunedBertModule()

        predictions_df = fineTunedModel.get_predictions(sentences)
        predictions_df.to_csv(workingPath + "/predictions/predictions.csv")

        sectionsDictionary = get_sections_dictionary(predictions_df, resultText)

        report = EarthquakeReport(workingPath)

        report.set_title(city, ruptureTime)
        report.add_hazard_description(initialSummary, tectonicSummary)

        report.add_sections(sectionsDictionary)

        report.add_picture(workingPath + "/overviewData/1.png", 4, 2)
        report.add_picture(workingPath + "/overviewData/2.png", 4, 2)

        report.save()

def runDataUpdate():
    """
    README: This function runs scripts in the earthquakeData.py file that is responsible for the initial querying of USGS, Twitter and the NewsAPI. This would be the part of the program that determines if there were any earthquakes to be recorded for the day, and if so retreive tweets and links to news articles to store in CSV files in the /data/ directory
    """
    
    earthquakeDataCollector = EarthquakeDataCollector()
    earthquakeDataCollector.runDailyUpdate()

    earthquakeLogs = pd.read_csv("data/earthquakes_log.csv")

    generate_reports_for_earthquakes(earthquakeLogs)

if __name__ == '__main__':
    runDataUpdate()
    earthquakes_log = pd.read_csv("data/earthquakes_log.csv")

    generate_reports_for_earthquakes(earthquakes_log)
