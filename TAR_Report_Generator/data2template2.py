import pandas as pd
from urllib.request import urlopen
from selenium import webdriver
from bs4 import BeautifulSoup
import requests
from PIL import Image
from webdriver_manager.chrome import ChromeDriverManager

def getTectonicIntensityInformation(source_data, dest_file_pic, dest_file_text, index):
    """
    README: This function is used to obtain the earthquake tectonic and intensity information from USGS website.
        It reads the website link from the standardized USGS csv data file, 
        and "inspect" the website to download the relevant information.
        The intensity map is saved as picture, and the tectonic information is saved as text files.
    
    source_data: csv data file (and directory).
    dest_file_pic: intensity information output file name (and directory). *.jpg recommended.
    dest_file_text: tectonic information output file name (and directory). *.txt recommended.
    index: the index of event to be processed in the csv file (starting at 0).
    
    In order to inspect pages, we need selenium, which could be downloaded at 
    https://selenium-python.readthedocs.io/installation.html#downloading-python-bindings-for-selenium
    We used Chrome version, which could automatically open Chrome
    After downloading, run it, and fill in below the executable_path, which is
    /Users/lichenglong/Downloads/chromedriver in my case
    If the code fails, try one more time.
    """

    df = pd.read_csv(source_data)
    url = df.iloc[index]['url']
    url_intensity = url+"/shakemap/intensity"
    url_tectonic = url+"/region-info"

    # intensity image
    url_image = ""
    print("is \n\n\n\n\n\n\n " + str(url)) 
    while (url_image == ""):
        driver = webdriver.Chrome(ChromeDriverManager(version="93.0.4577.15").install())
        driver.get(url_intensity)
        content_element = driver.find_element_by_class_name('ng-star-inserted')
        content_html = content_element.get_attribute("innerHTML")

        soup = BeautifulSoup(content_html, "html.parser")
        a_tags = soup.find_all("a", href=True)


        for a in a_tags:
            if (a['href'][-4:] == ".jpg"):
                url_image = a['href']
                break

        #driver.close()

    img = Image.open(urlopen(url_image))
    img.save(dest_file_pic)

    # tectonic information
    driver.get(url_tectonic)
    content_element = driver.find_element_by_class_name('ng-star-inserted')
    content_html = content_element.get_attribute("innerHTML")
    soup = BeautifulSoup(content_html, "html.parser")
    p_tags = soup.find_all("p")

    text = open(dest_file_text, "a");
    retText = "" 
    
    for p in p_tags:
        text.write(p.getText())
        
        retText += p.getText() 
    text.close()
    
    return retText 
    #driver.close()

#process("data/earthquakes_log.csv", "intensity.jpg", "record.txt", 0);