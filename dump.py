import requests
import json
import datetime
import os
import logging
from bs4 import BeautifulSoup

# First step: Images
# Second step: METADATA
# Third step: Front end?

FIRST_EDITION_IMAGE_ID = "1282_01_1867_0001_0001_18769495"
BASE_PATH = "F:\\_dump" # Without leading "\\"!

s_field = ''
cookies = ''
log = ''

config = {}


def main():

    global s_field, cookies, log

    LOG_FILE_NAME = os.path.basename(__file__).replace(".py",".log")
    LOGGER_NAME = os.path.basename(__file__).replace(".py","")

    fh = logging.FileHandler(LOG_FILE_NAME)
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s]: %(message)s')
    fh.setFormatter(formatter)
    log = logging.getLogger(LOGGER_NAME)
    logging.basicConfig(format='%(asctime)s - [%(levelname)s]: %(message)s')
    log.setLevel(logging.DEBUG)
    log.addHandler(fh)

    s_field, cookies = download_session_fields()


    current_edition_id = FIRST_EDITION_IMAGE_ID

    while current_edition_id != "HAPPY 2006":
        edition_details = get_edition_details(current_edition_id)
        log.info(f"Downloading edition {edition_details['edition_number']} from year {get_year_from_edition_date(edition_details['edition_date'])}")
        pages = get_pages(current_edition_id)
        for page in pages:
            log.info(f"Page {page['number']}")
            download_image(page['number'], page['thumbnailId'], edition_details)
            download_metadata(current_edition_id, edition_details)
        
        log.info("---------")
        current_edition_id = get_next_edition(edition_details['edition_date'])
  
    log.info("Done downloading")


def get_next_edition(last_edition_date):

    # Input: last_edition_date => Full date of last download edition
    # Output: next_edition_id => The id of the next edition ready to be used in the download URL

    r = requests.get(f"http://www.archiviolastampa.it/index2.php?option=com_lastampa&task=issue&no_html=1&type=neighbors&headboard=01&date={last_edition_date}")
    if r.status_code != 200:
        log.critical(f"[-] get_next_edition: Failed with status code {r.status_code}")
        raise Exception(f"[-] get_next_edition: Failed with status code {r.status_code}")

    r_json = json.loads(r.content)
    next_edition_id = r_json['nextIssueId']

    if next_edition_id is None:
        # No next_edition_id? This must be the last one, 31/12/2005!
        return "HAPPY 2006"
    else:
        return next_edition_id

    return


def get_edition_details(image_id):    

    # Returns "edition_id" and "edition_date"
    # edition_date is used to check for neighbours (previous and next edition) useful for looping.
    # You can use a random image_id, page does not matter, start with FIRST_EDITION_IMAGE_ID and then loop with neighbours!

    # Input: image_id => The image_id that you are currently trying to download
    # Output: edition_number => The edition number (duh)
    # Output: edition_date => The edition date (duh)

    r = requests.get(f"http://www.archiviolastampa.it/index2.php?option=com_lastampa&task=issue&no_html=1&type=info&issueid={image_id}")

    if r.status_code != 200:
        log.critical(f"[-] get_edition_details: Failed with status code {r.status_code}")
        raise Exception(f"[-] get_edition_details: Failed with status code {r.status_code}")

    r_json = json.loads(r.content)

    return {"edition_number": r_json['uscita'], "edition_date": r_json['data_uscita']}

def get_pages(url_id):

    # Gets the page list for current edition
    # Input: url_id => The correctly formatted id (like "FIRST_EDITION_IMAGE_ID")
    # Output: pageList => a JSON formatted page list that contains a "number" (page number) and a "thumbnailId" (formatted id like "FIRST_EDITION_IMAGE_ID")

    r = requests.get(f"http://www.archiviolastampa.it/load.php?url=/item/getPagesInfo.do?id={url_id}&s={s_field}", headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0'}, cookies=cookies)
    if r.status_code != 200:
        log.critical(f"[-] get_pages: Failed with status code {r.status_code}")
        raise Exception(f"[-] get_pages: Failed with status code {r.status_code}")

    r_json = json.loads(r.content)

    return r_json['pageList']

def download_image(page_number, image_id, edition_details):

    # Downloads the chosen page in jpg

    # Input: page_number => The page number (padded with zeros to reach 4 digits)
    # Input: image_id => The full formatted id (like "FIRST_EDITION_IMAGE_ID")
    # Input: edition_details => Array from "get_edition_details()", used for edition year and edition number.
    # Output: NONE. Just saves the file.

    global BASE_PATH

    image_url = f"http://www.archiviolastampa.it/load.php?url=/downloadContent.do?id={image_id}&s={s_field}"
    r = requests.get(image_url, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0'}, cookies=cookies)

    if r.status_code != 200:
        log.critical(f"[-] download_image: Failed with status code {r.status_code}")
        raise Exception(f"[-] download_image: Failed with status code {r.status_code}")

    edition_year = get_year_from_edition_date(edition_details['edition_date'])
    edition_number = edition_details['edition_number']

    download_path = f"{BASE_PATH}\\{edition_year}\\{edition_number}\\{page_number}.jpg"
    # Create path if does not exist!
    os.makedirs(os.path.dirname(download_path), exist_ok=True)

    open(download_path, 'wb').write(r.content)

    return

def get_year_from_edition_date(edition_date):

    # Strips 4 digit year from the edition date (YYYY-MM-DD HH:mm:ss).

    # Input: edition_date => Date in YYYY-MM-DD HH:mm:ss format.
    # Output: 4 digit year

    # year = datetime.datetime.strptime(edition_details['edition_date'], "%Y-%m-%d %H:%M:%S'").strftime("%Y")
    # HACK: I'm sorry, one day I will do this the proper way. I tried but I just can't, it's late...
    year = edition_date[0:4]

    return year

def download_session_fields():

    # HACK: This is just a random page to load and get the s_field and cookies
    placeholder_page = "http://www.archiviolastampa.it/component/option,com_lastampa/task,search/mod,libera/action,viewer/Itemid,3/page,1/articleid,0251_01_2005_0352_0001_1857676/anews,true/"
    r = requests.get(placeholder_page, headers={"Cache-Control": "no-cache", "Pragma": "no-cache"})

    if r.status_code != 200:
        log.critical(f"[-] download_session_fields: Failed with status code {r.status_code}")
        raise Exception(f"[-] download_session_fields: Failed with status code {r.status_code}")

    soup = BeautifulSoup(r.content, features="lxml")
    s_field = soup.find("input", {"name":"t"})['value']

    cookies = requests.utils.dict_from_cookiejar(r.cookies)

    log.debug(f"Current s_field: {s_field}")
    log.debug(f"Current cookies: {cookies}")

    return (s_field, cookies)

def download_metadata(image_id, edition_details):

    # Downloads metadata (titles, descriptions, bounding boxes ids, ocr confidence)

    log.info("Downloading metadata JSON")

    split_id = image_id.split('_')
    if (len(split_id) > 5):
        split_id = split_id[0:5]
        image_id = '_'.join(split_id)

    url = f"http://www.archiviolastampa.it/load.php?url=/search/select/?wt=json&q=pageID:{image_id}&s={s_field}"
    r = requests.get(url, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0'}, cookies=cookies)

    if r.status_code != 200:
        log.critical(f"[-] download_metadata: Failed with status code {r.status_code}")
        raise Exception(f"[-] download_metadata: Failed with status code {r.status_code}")

    edition_year = get_year_from_edition_date(edition_details['edition_date'])
    edition_number = edition_details['edition_number']

    download_path = f"{BASE_PATH}\\{edition_year}\\{edition_number}\\metadata\\metadata.json"
    # Create path if does not exist!
    os.makedirs(os.path.dirname(download_path), exist_ok=True)

    r_json = json.loads(r.content)
    # Let's dump some pretty JSON instead of the ugly thing we get with the request
    open(download_path, 'w').write(json.dumps(r_json, sort_keys=True, indent=4))

    docs = r_json['response']['docs']

    for doc in docs:
        download_bounding_boxes(image_id, edition_details, doc['id'])

    return

def download_bounding_boxes(image_id, edition_details, metadata_id):

    # Downloads info about bounding boxes (coordinates, text)

    log.info("Downloading bounding boxes JSON")

    image_id_full = image_id + "_" + metadata_id
    url = f"http://www.archiviolastampa.it/load.php?url=/item/getmetadata.do?articleid={image_id_full}&query=&s={s_field}"
    r = requests.get(url, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0'}, cookies=cookies)

    if r.status_code != 200:
        log.critical(f"[-] download_bounding_boxes: Failed with status code {r.status_code}")
        raise Exception(f"[-] download_bounding_boxes: Failed with status code {r.status_code}")

    edition_year = get_year_from_edition_date(edition_details['edition_date'])
    edition_number = edition_details['edition_number']

    r_json = json.loads(r.content)

    download_path = f"{BASE_PATH}\\{edition_year}\\{edition_number}\\metadata\\bb\\{metadata_id}.json"
    # Create path if does not exist!
    os.makedirs(os.path.dirname(download_path), exist_ok=True)
    # Let's dump some pretty JSON instead of the ugly thing we get with the request
    open(download_path, 'w').write(json.dumps(r_json, sort_keys=True, indent=4))

    return

if __name__ == '__main__':
    main()