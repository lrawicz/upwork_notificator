from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from dotenv import load_dotenv
import os
import undetected_chromedriver as uc
#from webdriver_manager.chrome import ChromeDriverManager
import json
import requests
import hashlib
load_dotenv()
driver_folder = os.getenv("DRIVER_FOLDER")
firefox_profile = os.getenv("FIREFOX_PROFILE")
firefox_driver = os.getenv("DRIVER_FOLDER") + "firefox"
search_tags = os.getenv("SEARCH_TAGS").split("-") 
url = os.getenv("URL")

webhook_url = "https://hooks.slack.com/services/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" #os.getenv("WEBHOOK_URL_DEV")
def main_firefox():
        options = webdriver.FirefoxOptions()
        executable_path="/home/lrawicz/Desktop/develop/code/freelance/upwork/upwork-api/drivers/geckodriver-v0.33.0"
        driver = webdriver.Firefox(executable_path=executable_path, options=options)
        driver.get('https://google.com')
        time.sleep(20)


def send_msg(dict):
    if dict == {}:
        dict = {"title":"Pikachu","link":"www.google.com","time_and_cash":"ayer","search":"Excel"}
    

    payload = { 
        "text": f"{dict['title']}",
        "blocks": [
            { "type": "section","text": {"type": "mrkdwn","text": 
                f"<{dict['link']}|*{dict['title']}*> - Filtred by: {dict['search']}"}},
            {"type": "context","elements": 
                [{"type": "mrkdwn","text": f"{dict['time_and_cash']}"}]
            },
            {"type": "divider"}
        ]
        }
    json_payload = json.dumps(payload)
    response = requests.post(webhook_url, data=json_payload)

    if response.status_code == 200:
        print("Mensaje enviado exitosamente a Slack.")
    else:
        print(f"Error al enviar el mensaje a Slack. Código de respuesta: {response.status_code}")

def main_uc2():
    options = uc.ChromeOptions()
    profile_path= r"user-data-dir=/home/lrawicz/.config/google-chrome"
    profile = f"{profile_path}/Profile 5"
    #options.user_data_dir = r"user-data-dir=/home/lrawicz/.config/google-chrome/Profile 5"
    options.add_argument(f"user-data-dir={profile}")  
    #options.add_argument(r"user-data-dir=Default")  
     
    # --profile-directory=Default
    with uc.Chrome(options = options , version_main = 113) as driver:
        driver.get('https://yahoo.com')
        time.sleep(10000)
def main_uc():
    #options = webdriver.ChromeOptions()
    options = uc.ChromeOptions()
    options.user_data_dir = r"user-data-dir=/home/lrawicz/.config/google-chrome/Profile 5" 
    options.add_argument(r"user-data-dir=/home/lrawicz/.config/google-chrome")  
    #options.add_argument(r"profile-directory=Profile 5")
    #executable_path="/home/lrawicz/Desktop/develop/code/freelance/upwork/upwork-api/drivers/chromedriver"
    #driver = webdriver.Chrome(executable_path=executable_path, options=options)
    
    
    with uc.Chrome(options = options , version_main = 113) as driver:
        driver.get('https://www.upwork.com/ab/account-security/login')
        input("waiting for login.... ")
        saved_searchs = driver.find_elements(By.CSS_SELECTOR,"*[data-test='select-saved-search']")
        searchs = [{"title": search.text, "link":search.get_attribute("href") } for search in saved_searchs]
        id_arr = []
        while 1:

            for search in searchs:
                if search["title"] not in ["excel vba", "google sheets", "excel macros"]:
                    continue
                driver.get(search["link"])
                
                time.sleep(1)
                for iteration in range (0,10):
                    driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight*{iteration/10});")
                    time.sleep(10/1000)
                job_tile_list = driver.find_elements(By.CSS_SELECTOR,"*[data-test='job-tile-list']")[0]
                jobs = job_tile_list.find_elements(By.TAG_NAME, "section")

                for job in jobs:
                    
                    text_arr= job.text.split("\n")
                    for item_to_remove in ["FEATURED","Applied" ]: 
                        if item_to_remove in text_arr:
                            text_arr.remove(item_to_remove)
                    
                    title = text_arr[0]
                    time_and_cash = text_arr[3]
                    description  = "".join(text_arr[4:])
                    link =job.find_elements(By.TAG_NAME,"h3")[0].find_elements(By.TAG_NAME,"a")[0].get_attribute("href")

                    job_dict = {
                        "id": hashlib.sha256(f"{title}-{description}".encode('utf-8')).hexdigest(),
                        "title":title,
                        "search":search["title"], 
                        "desc": description, 
                        "link":link, 
                        "time_and_cash":time_and_cash
                        }
                    if  job_dict["id"] in id_arr  or (job_dict["time_and_cash"].split("Posted")[1].strip().split(" ")[1].split("s")[0] not in ["minute","hour"]):
                        continue

                    #if job_dict["time_and_cash"].split("Posted")[1].split(" ")
                    if len(id_arr) > (10*3):
                        id_arr.pop(0)
                    id_arr.append(job_dict["id"])
                    send_msg(job_dict)
                    #hash_str = str(abs(hash(f"{title}-{description}")))

                    #    with open(f"DB/{hash_str}.json", "w") as archivo:
                    #        json.dump(new_dict, archivo, indent=2)
                    #        send_msg(new_dict)
                time.sleep(5)
        #   first_time = False
if (__name__ == "__main__"):
    main_uc2()
    #send_msg({})