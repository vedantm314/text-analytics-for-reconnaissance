# -*- coding: utf-8 -*-
import os
import re
import csv
import pandas
import calendar
import pytz
import pandas as pd
import requests
import numpy as np
import cv2
import pytesseract 
import time

from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import tz
from tzwhere import tzwhere
from urllib.request import urlopen
from selenium import webdriver
from PIL import Image
from webdriver_manager.chrome import ChromeDriverManager


def generateSummary(source_data, dest_file, index):
    """
    README: This function is used to process the earthquake basic information from csv file 
        into sentences, and save to a file. The csv file is the standardized file downloaded from the USGS website.
    
    source_data: csv data file (and directory).
    dest_file: output file name (and directory). *.txt recommended.
    index: the index of event to be processed in the csv file (starting at 0).
    """

    df = pd.read_csv(source_data)  

    utctime = df.iloc[index]['rupture_time']
    utctime = utctime.replace("/", "-") 
    longitude = df.iloc[index]['longitude']
    latitude = df.iloc[index]['latitude']

    # UTC to local time (daylight save is also considered)
    tzwherev = tzwhere.tzwhere()
    timezone_str = tzwherev.tzNameAt(latitude, longitude) # Seville coordinates
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz(timezone_str)
    utc = datetime.strptime(utctime, '%Y-%m-%d %H:%M:%S')
    utc = utc.replace(tzinfo=from_zone)
    localtime = utc.astimezone(to_zone)

    result = "On {} {}, {}, at approximately {}:{} local time, ".format(calendar.month_name[localtime.month], localtime.day, localtime.year, localtime.hour, localtime.minute); 
    result += "a magnitude {} earthquake, with a depth of {} km, ".format(df.iloc[index]['magnitude'], df.iloc[index]['depth']);
    location = df.iloc[index]['place'];
    location = re.split('km | | of', location);
    direction = {"E": "East", "W": "West", "S": "South", "N": "North", "SE": "Southeast", "SW": "Southwest", "NE": "Northeast", "NW": "Northwest", "ESE": "East-Southeast", "WSW": "West-Southwest", "ENE": "East-Northeast", "WNW": "West-Northwest", "SSE": "South-Southeast", "SSW": "South-Southwest", "NNE": "North-Northeast", "NNW": "North-Northwest"}
    city = "";
    for i in range(3, len(location)):
        city += location[i] + " ";
    city = city[:-1];
    (location) = list(filter(None, location))
    print(direction)
    print(location)
    result += "struck {} km {} of {}. ".format(location[0], direction[location[1]], city);
    if (float(latitude) > 0):
        latitudeNS = "N";
    else:
        latitudeNS = "S";
    if (float(longitude) > 0):
        longitudeEW = "E";
    else:
        longitudeEW = "W";
    result += "The coordinate of epicenter of the earthquake was {}°{}, {}°{}.".format(abs(float(latitude)), latitudeNS, abs(float(longitude)), longitudeEW);
    result += "\n";
    text = open(dest_file, "a");
    text.write(result);
    text.close();
    
    return result

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
    print(str(url)) 
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

def get_imagelink(url):
    """
    README: This function is used to output the image links to get the fatalities and economic losses
        estimations (PAGER) graphs for the earthquake in the url.
        This function uses selenium webdrive, therefore, the executable_path also needs to be configured.
        This is a helper function.

    url: the url of the earthquake PAGER estimation page.
    RETURN: a list of two strings, each one is the image link for estimated fatalities/economic losses
    """

    url_image1 = ""
    url_image2 = ""

    while (url_image2 == ""):
        url_image1 = ""

        driver = webdriver.Chrome(ChromeDriverManager(version="93.0.4577.15").install())
        driver.get(url)

        time.sleep(3)
        
        content_element = driver.find_element_by_class_name('ng-star-inserted')
        content_html = content_element.get_attribute("innerHTML")

        soup = BeautifulSoup(content_html, "html.parser")
        a_tags = soup.find_all("img")

        for a in a_tags:
            if (a['src'][-4:] == ".png"):
                if (url_image1 == ""):
                    url_image1 = a['src']
                else:
                    url_image2 = a['src']
                    break

        driver.close()

    return [url_image1, url_image2]

def generate_estimation(url, dest_file_pic1, dest_file_pic2, generate_text=True, dest_file_text="", print_text=False):
    """
    README: This function is used to save PAGER estimation images and (optional) generated text descriptions
        from the earthquake PAGER information url. 
        This function uses OpenCV tools and Tesseract to locate and extract text in images to 
        generate text descriptions.

    url: the url of the earthquake PAGER estimation page.
    dest_file_pic1: PAGER fatality estimation information output image name (and directory). *.png recommended.
    dest_file_pic2: PAGER econimic loss estimationinformation output image name (and directory). *.png recommended.
    dest_file_text: PAGER information output file name (and directory). Append to the original text in the file. *.txt recommended.
        if empty, then no output.
    generate_text: whether generate text apart from image. The purpose for this variable is,
        in case Tesseract below is not configured well, then only images are already enough
    print: whether to print out the text

    In order for this function to work, Tesseract is needed. The python module pytesseract is a python wrapper.
    Firstly, Tesseract needs to be installed by following the instruction: https://tesseract-ocr.github.io/tessdoc/Home.html
        (for example, I am using MacOS, so I used homebrew)
    Secondly, pytesseract needs to be installed like normal packages (e.g. pip install pytesseract)
    Thirdly, in Python, configure the path to Tesseract.
        In the official manual (in the link above) the path could be checked in terminal by following instructions in the link above (e.g., brew info tesseract for MacOS)
        HOWEVER, it does not work for my case. I found the path by using the following line in terminal: which tesseract
        The path could be configured by calling: pytesseract.pytesseract.tesseract_cmd = YOUR PATH
    """
    # configure the path to Tesseract
    '''
    def change_permissions_recursive(path, mode):
        for root, dirs, files in os.walk(path, topdown=False):
            for dir in [os.path.join(root,d) for d in dirs]:
                os.chmod(dir, mode)
            for file in [os.path.join(root, f) for f in files]:
                os.chmod(file, mode)
    #change_permissions_recursive('/usr/local/Cellar/tesseract/4.1.1', 0o741)
    #pytesseract.pytesseract.tesseract_cmd = "/usr/local/Cellar/tesseract/4.1.1/share"
    '''
    pytesseract.pytesseract.tesseract_cmd = "user/lichenglong/Downloads/tesseract-4.1.1"

    pytesseract.pytesseract.tesseract_cmd = "/Users/vedantmathur/Downloads/tesseract/tesseract"
    

    url_image1, url_image2 = get_imagelink(url)
    img = Image.open(urlopen(url_image1))
    img.save(dest_file_pic1)
    img = Image.open(urlopen(url_image2))
    img.save(dest_file_pic2)

    if (generate_text):
        image = cv2.imread(dest_file_pic1)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) 
        
        # Performing OTSU threshold 
        ret, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV) 
        
        # Specify structure shape and kernel size.  
        # Kernel size increases or decreases the area  
        # of the rectangle to be detected. 
        # A smaller value like (10, 10) will detect  
        # each word instead of a sentence. 
        rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (4, 4)) 
        
        # Appplying dilation on the threshold image 
        dilation = cv2.dilate(thresh1, rect_kernel, iterations = 1)  

        # Finding contours 
        contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE) 
        
        # Looping through the identified contours 
        # Then rectangular part is cropped and passed on 
        # to pytesseract for extracting text from it 
        # Extracted text is then written into the text file 

        result = np.zeros(7)
        for cnt in contours: 
            x, y, w, h = cv2.boundingRect(cnt) 
            
            if (w >= 60 or h >= 20):
                continue
                
            cropped = image[y - 2: y + h + 2, x - 2: x + w + 2]
            text = pytesseract.image_to_string(cropped)
            
            index = text.find('%')
            
            if (index == -1):
                continue
                
            value = int(text[:index])
            
            if (x > 565):
                result[6] = value
            elif (x > 496):
                result[5] = value
            elif (x > 427):
                result[4] = value
            elif (x > 358):
                result[3] = value
            elif (x > 289):
                result[2] = value
            elif (x > 220):
                result[1] = value
            else:
                result[0] = value

        fatality_result = "USGS PAGER tool estimated the fatalities to be"

        if (result[0] != 0):
            fatality_result += " smaller than 1 with a probability of {}%,".format(int(result[0]))
        if (result[1] != 0):
            fatality_result += " between 1 and 10 with a probability of {}%,".format(int(result[1]))
        if (result[2] != 0):
            fatality_result += " between 10 and 100 with a probability of {}%,".format(int(result[2]))
        if (result[3] != 0):
            fatality_result += " between 100 and 1,000 with a probability of {}%,".format(int(result[3]))
        if (result[4] != 0):
            fatality_result += " between 1,000 and 10,000 with a probability of {}%,".format(int(result[4]))
        if (result[5] != 0):
            fatality_result += " between 10,000 and 100,000 with a probability of {}%,".format(int(result[5]))
        if (result[6] != 0):
            fatality_result += " larger than 100,000 with a probability of {}%,".format(int(result[6]))

        fatality_result = fatality_result[:-1] + "."

        index = fatality_result.rfind(",") 
        if (index != -1):
            fatality_result = fatality_result[: index+2] + "and " + fatality_result[index+2:]

        if (np.sum(result) == 0):
            fatality_result = ""

        if (dest_file_text != ""):
            text = open(dest_file_text, "a")
            text.write(fatality_result)
            text.write("\n")
            text.close()
        if (print_text):
            print("fatality: \n")
            print(fatality_result)
            print("\n")

    

        image = cv2.imread(dest_file_pic2)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) 
        
        # Performing OTSU threshold 
        ret, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV) 
        
        # Specify structure shape and kernel size.  
        # Kernel size increases or decreases the area  
        # of the rectangle to be detected. 
        # A smaller value like (10, 10) will detect  
        # each word instead of a sentence. 
        rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (4, 4)) 
        
        # Appplying dilation on the threshold image 
        dilation = cv2.dilate(thresh1, rect_kernel, iterations = 1)  

        # Finding contours 
        contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE) 
        
        # Looping through the identified contours 
        # Then rectangular part is cropped and passed on 
        # to pytesseract for extracting text from it 
        # Extracted text is then written into the text file 

        result = np.zeros(7)
        for cnt in contours: 
            x, y, w, h = cv2.boundingRect(cnt) 
            
            if (w >= 60 or h >= 20):
                continue
                
            cropped = image[y - 2: y + h + 2, x - 2: x + w + 2]
            text = pytesseract.image_to_string(cropped)
            
            index = text.find('%')
            
            if (index == -1):
                continue
                
            value = int(text[:index])
            
            if (x > 565):
                result[6] = value
            elif (x > 496):
                result[5] = value
            elif (x > 427):
                result[4] = value
            elif (x > 358):
                result[3] = value
            elif (x > 289):
                result[2] = value
            elif (x > 220):
                result[1] = value
            else:
                result[0] = value

        loss_result = "Economic losses were expected to be"

        if (result[0] != 0):
            loss_result += " smaller than $1 million with a probability of {}%,".format(int(result[0]))
        if (result[1] != 0):
            loss_result += " between $1 million and $10 million with a probability of {}%,".format(int(result[1]))
        if (result[2] != 0):
            loss_result += " between $10 million and $100 million with a probability of {}%,".format(int(result[2]))
        if (result[3] != 0):
            loss_result += " between $100 million and $1,000 million with a probability of {}%,".format(int(result[3]))
        if (result[4] != 0):
            loss_result += " between $1,000 million and $10,000 million with a probability of {}%,".format(int(result[4]))
        if (result[5] != 0):
            loss_result += " between $10,000 million and $100,000 million with a probability of {}%,".format(int(result[5]))
        if (result[6] != 0):
            loss_result += " larger than $100,000 million with a probability of {}%,".format(int(result[6]))

        loss_result = loss_result[:-1] + "."

        index = loss_result.rfind(",") 
        if (index != -1):
            loss_result = loss_result[: index+2] + "and " + loss_result[index+2:]

        if (np.sum(result) == 0):
            loss_result = ""

        if (dest_file_text != ""):
            text = open(dest_file_text, "a")
            text.write(loss_result)
            text.write("\n")
            text.close()
        if (not print_text):
            print("loss: \n")
            print(loss_result)
            print("\n")
            
        return loss_result