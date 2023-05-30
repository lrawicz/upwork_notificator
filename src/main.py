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
import logging



load_dotenv()

#LOGGING
#FORMAT = '%(asctime)s %(clientip)-15s %(user)-8s %(message)s'
#logging.basicConfig(format=FORMAT)
logger = logging.getLogger("upwork")
logger.setLevel(10)


driver_folder = os.getenv("DRIVER_FOLDER")
firefox_profile = os.getenv("FIREFOX_PROFILE")
firefox_driver = os.getenv("DRIVER_FOLDER") + "firefox"
#search_tags = os.getenv("SEARCH_TAGS").split("-") 
url = os.getenv("URL")

def main_firefox():
        options = webdriver.FirefoxOptions()
        executable_path="/home/lrawicz/Desktop/develop/code/freelance/upwork/upwork-api/drivers/geckodriver-v0.33.0"
        driver = webdriver.Firefox(executable_path=executable_path, options=options)
        driver.get('https://google.com')
        time.sleep(20)


def send_msg(dict,webhook_url):
    if dict == {}:
        dict = {"title":"Pikachu","link":"www.google.com","time_and_cash":"ayer","search":"Excel"}
    
    skills = ', '.join(dict["skills"])
    payload = { 
        "text": f"{dict['title']}",
        "blocks": [
            { "type": "section","text": {"type": "mrkdwn","text": 
                f"<{dict['link']}|*{dict['title']}*> "}},
            {"type": "context","elements": 
                [{"type": "mrkdwn","text": f"{dict['time_and_cash']}"}]
            },
            {"type": "context","elements":
                [{"type": "mrkdwn","text": f"*Skills*: {skills}"}]
            },
            {"type": "divider"}
        ]
        }
    json_payload = json.dumps(payload)
    response = requests.post(webhook_url, data=json_payload)

    if response.status_code != 200:
        print(f"Error al enviar el mensaje a Slack. Código de respuesta: {response.status_code}")
        print(f"Reason: {response.text}")

def main_uc2():
    options = uc.ChromeOptions()
    profile_path= r"/home/lrawicz/.config/google-chrome"
    #profile = f"{profile_path}/Profile 5"
    #options.user_data_dir = r"user-data-dir=/home/lrawicz/.config/google-chrome/Profile 5"
    options.add_argument(f"user-data-dir={profile_path}")
    options.add_argument("--headless")

    #options.add_argument(r"user-data-dir=Default")
    options.add_argument(r"profile-directory=Profile 5")
    # --profile-directory=Default
    with uc.Chrome(user_data_dir="".join([profile_path,"/","Profile 5"]), version_main = 113) as driver:
        driver.get('https://yahoo.com')
        time.sleep(10000)
def create_job_dict(job):
    title = job.find_elements(By.CSS_SELECTOR,"h3")
    description = job.find_elements(By.CSS_SELECTOR,"div[data-test='job-description-line-clamp']")
    time_and_cash = job.find_elements(By.CSS_SELECTOR,"div.mb-10>div>small")
    if len(title) == 0 or len(description) == 0 or len(time_and_cash) == 0:
        return False
    title = title[0].text
    description = description[0].text
    link =job.find_elements(By.TAG_NAME,"h3")[0].find_elements(By.TAG_NAME,"a")[0].get_attribute("href")
    time_and_cash = time_and_cash[0].text
    skills = job.find_elements(By.CSS_SELECTOR,"div.up-skill-wrapper>a.up-skill-badge")
    skills = [skill.text for skill in skills]
    job_dict = {
        "id":hashlib.sha256(f"{title}-{description}".encode('utf-8')).hexdigest(),
        "title":title,
        "desc": description, "link":link,
        "skills": skills,
        "time_and_cash":time_and_cash
        }
    return job_dict
def main_uc():

    # Open the file and load its |ontents
    with open("config.json", 'r') as file:
        slackConfig = json.load(file)
    dict_webhook = {filter_name:{"webhook":slackConfig[item]["webhook"], "category":item} for item in slackConfig for filter_name in slackConfig[item]["filters"]}


    #options = webdriver.ChromeOptions()
    options = uc.ChromeOptions()
    options.user_data_dir = r"user-data-dir=/home/lrawicz/.config/google-chrome/Profile 5" 
    options.add_argument(r"user-data-dir=/home/lrawicz/.config/google-chrome")  

    #options.add_argument("--headless")



    #options.add_argument(r"profile-directory=Profile 5")
    #executable_path="/home/lrawicz/Desktop/develop/code/freelance/upwork/upwork-api/drivers/chromedriver"
    #driver = webdriver.Chrome(executable_path=executable_path, options=options)
    
    
    with uc.Chrome(options = options , version_main = 113) as driver:
        driver.get('https://www.upwork.com/ab/account-security/login')
        time.sleep(2)
        login = driver.find_elements(By.CSS_SELECTOR,"button#login_google_submit")
        print("proceso de Login")
        logger.info("login...")
        if len(login) > 0:
            login[0].click()
            time.sleep(8)

        #input("waiting for login.... ")
        searchs = []
        while len(searchs) == 0:
            time.sleep(1)
            saved_searchs = driver.find_elements(By.CSS_SELECTOR,"*[data-test='select-saved-search']")
            searchs = [{"title": search.text, "link":search.get_attribute("href") } for search in saved_searchs]
            print("saved_searchs: ", len(saved_searchs))
        while 1:
            time.sleep(10)
            print("-- from the top")
            print("--------")
            for search in searchs:
                time.sleep(1)
                if search["title"] not in dict_webhook:
                    print(f"no se esta considerando {search['title']}")
                    continue
                search_category = dict_webhook[search["title"]]["category"]
                if not os.path.exists(f"DB/{search_category}"):
                    os.makedirs(f"DB/{search_category}")
                driver.get(search["link"]) #go to site
                time.sleep(1)
                #scroll down
                for iteration in range (0,10):
                    driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight*{iteration/10});")
                    time.sleep(10/1000)

                job_tile_list = driver.find_elements(By.CSS_SELECTOR,"*[data-test='job-tile-list']")
                if len(job_tile_list) == 0:
                    return False #mejorar el manejo de errores
                job_tile_list = job_tile_list[0]
                jobs = job_tile_list.find_elements(By.TAG_NAME, "section")
                new_jobs ={}
                for job in jobs:
                    job_dict = create_job_dict(job)
                    if (job_dict["time_and_cash"].split("Posted")[1].strip().split(" ")[1].split("s")[0] not in ["minute","hour"]):
                        continue
                    if os.path.exists(f"DB/{search_category}/{job_dict['id']}"):
                        continue
                    with open(f"DB/{search_category}/{job_dict['id']}","w"):
                        pass
                    new_jobs[job_dict['id']] = job_dict

                if len(new_jobs.keys()) == 0:
                    continue
                print(f"{search['title'].capitalize()} - Job founds: {len(new_jobs.keys())}")
                print("--------")

                for job_key in new_jobs:
                    send_msg(new_jobs[job_key],dict_webhook[search["title"]]["webhook"])

if (__name__ == "__main__"):
    while 1:
        main_uc()
        time.sleep(30)
    #send_msg({})