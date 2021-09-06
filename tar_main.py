from earthquake_data import *
from data2template import *
from data2template2 import *
from website2text import *
from data2template4 import *
from earthquakeReport import EarthquakeReport
from FineTunedBertModule import FineTunedBertModule
from summarize import *

def format_rupture_time(ruptureTime):
    indexCheck = ruptureTime.find(" ")
    ruptureTime = ruptureTime[:indexCheck] + "_" + ruptureTime[indexCheck + 1:]

    ruptureTime = ruptureTime.replace("/", "-")

    return ruptureTime


def get_data_for_earthquake(earthquakeLog):
    retDict = dict()

    retDict["ruptureTime"] = earthquakeLog[3]
    retDict["city"] = earthquakeLog[1]

    return retDict


def initialize_report_directory(ruptureTimeForPath, city):
    workingPath = os.path.join(os.getcwd(), "reports", ruptureTimeForPath + "_" + city)

    if (not os.path.isdir(workingPath)):
        os.mkdir(workingPath)
        os.mkdir(workingPath + "/overviewData")
        os.mkdir(workingPath + "/predictions")

    return workingPath


def get_sentences_from_news(workingPath, newsArticles):
    sentencesList = []

    urlLinks = (newsArticles["url"]).to_numpy()

    for j in range(0, len(urlLinks)):
        get_content(sentencesList, urlLinks[j], workingPath + "/overviewData/article.txt")

    return sentencesList


def get_sections_dictionary(predictions_df, resilienceSummaryText):
    buildingsText = get_summary(predictions_df, "buildings", 0.2)
    resilienceText = get_summary(predictions_df, "resilience", 0.2) + "\n\n" + resilienceSummaryText
    infrastructureText = get_summary(predictions_df, "infrastructure", 0.2)

    sectionsDictionary = {"Buildings": buildingsText,
                          "Infrastructure": infrastructureText,
                          "Resilience": resilienceText}

    return sectionsDictionary

def generate_reports_for_earthquakes(earthquakeLogs):
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
    earthquakeDataCollector = EarthquakeDataCollector()
    earthquakeDataCollector.runDailyUpdate()

    earthquakeLogs = pd.read_csv("data/earthquakes_log.csv")

    generate_reports_for_earthquakes(earthquakeLogs)

if __name__ == '__main__':
    #runDataUpdate()
    earthquakes_log = pd.read_csv("data/earthquakes_log.csv")

    generate_reports_for_earthquakes(earthquakes_log)