import textract

from nltk import sent_tokenize
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
from webdriver_manager.chrome import ChromeDriverManager


# Download ntlk
# nltk.download()

def get_content(sentencesList, website, dest_file=""):
    """
    README: This function is used to copy text (html type <p>) into an output file. 
        If failed, no text will be copied.

    website: the website to grab information.
    dest_file: output file name (and directory). *.txt recommended. Note that new text 
        will be appended behind the old text. If not specified, the text will be printed
        (not recommend).

    In order to split the sentences, package nltk is used herein.
        nltk needs to be downloaded first by using "nltk.download()".
    """
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(ChromeDriverManager(version="93.0.4577.15").install(), chrome_options=chrome_options)

    driver.get(website)
    content_element = driver.find_element_by_tag_name("div")
    content_html = content_element.get_attribute("innerHTML")
    soup = BeautifulSoup(content_html, "html.parser")
    p_tags = soup.find_all("p")

    if (dest_file != ""):
        text = open(dest_file, "w")
        for p in p_tags:
            sentences = sent_tokenize(p.getText())

            for i in range(len(sentences)):
                if(len(sentences[i].split(" ")) > 1): 
                    sentencesList.append(sentences[i]) 

                text.write(sentences[i]) 
                text.write("\n")
        text.close()
    else:
        for p in p_tags:
            sentences = sent_tokenize(p.getText())
            for i in range(len(sentences)):
                print(sentences[i])

    driver.close()
        
def read_pdf(filename):
    """
    README: This function is used to read texts from a PDF file into a list of strings.
        Each string in the list is one row of text.
        This is a helper function.

    filename: the file name of *.pdf file (and directory).
    RETURN: a list of strings
    """

    """
    pdfFileObj = open(filename,'rb')  
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    pdfReader.numPages
    pageObj = pdfReader.getPage(3)
    text = pageObj.extractText()
    if (text == ""):
    """
    text = textract.process(filename, method='tesseract', language='eng')
    return str(text).split('\\n')

def steer(source_file, dest_file):
    """
    README: This function is used to read texts from websites referenced in STEER earthquake briefings.
        This function calls read_pdf to locate and extract the websites inside the PDF, 
        then it iterates over websites by calling get_content to obtain the texts.

    source_file: PDF file name (and directory).
    dest_file: output file name (and directory).
    """
    lines = read_pdf(source_file)
    i = 0
    while (i < len(lines)):
        index = lines[i].find("eference") #reference
        if (index != -1):
            break
        i += 1
    while (i < len(lines)):
        #print(i)
        index = lines[i].find("http")
        if (index == -1):
            i += 1
            continue
        url = lines[i][index:]
        url_found = False
        try:
            req = requests.get(url)
        except:
            i += 1
            continue
        if (str(req) == "<Response [200]>"):
            url_found = True
        else:
            url += lines[i+1]
            try:
                req = requests.get(url)
            except:
                i += 1
                continue
            if (str(req) == "<Response [200]>"):
                url_found = True
                
        if (not url_found):
            url = lines[i][index:]
            url.replace(" ", "")
            try:
                req = requests.get(url)
            except:
                i += 1
                continue
            if (str(req) == "<Response [200]>"):
                url_found = True
            else:
                url += lines[i+1]
                url.replace(" ", "")
                try:
                    req = requests.get(url)
                except:
                    i += 1
                    continue
                if (str(req) == "<Response [200]>"):
                    url_found = True
        if (not url_found):
            url = lines[i][index:]
            url.replace(" ", ".")
            try:
                req = requests.get(url)
            except:
                i += 1
                continue
            if (str(req) == "<Response [200]>"):
                url_found = True
            else:
                url += lines[i+1]
                url.replace(" ", ".")
                try:
                    req = requests.get(url)
                except:
                    i += 1
                    continue
                if (str(req) == "<Response [200]>"):
                    url_found = True
                    
        if (not url_found):
            i += 1
            continue
        get_content(url, dest_file)
        i += 1
        
#get_content("https://www.reuters.com/article/us-argentina-quake/magnitude-68-quake-strikes-san-juan-province-argentina-gfz-idUSKBN29O077", "article.txt") 