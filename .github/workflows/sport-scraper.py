import time
import string
import gspread
from bs4 import BeautifulSoup
from selenium import webdriver
import selenium.common.exceptions
from oauth2client.service_account import ServiceAccountCredentials
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


all_data = []


class Scraper:
    def __init__(self, scraper_id, service, n=0, m=0):
        self.options = webdriver.ChromeOptions()
        # self.options.page_load_strategy = 'eager'
        self.options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument("--start-maximized")
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_prefs = dict()
        self.options.experimental_options["prefs"] = self.chrome_prefs
        self.chrome_prefs["profile.default_content_settings"] = {
            "images": 2}
        self.chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}
        self.service = service
        self.driver = webdriver.Chrome(service=self.service, options=self.options)

        self.scraper_id = scraper_id
        self.local_listing_id = 0

        self.n = n
        self.m = m

        print('\n[+] Browser session initialized!')

    def scrape_data(self):
        print('\t-> Getting "https://www.livesportsontv.com/"...')
        self.driver.get('https://www.livesportsontv.com/')
        time.sleep(5)

        page_body = self.driver.find_element(By.TAG_NAME, 'body')

        print('\t-> Reaching all sports events...')
        for stroke in range(100):
            page_body.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.05)

        html_content = self.driver.page_source

        print('\n[+] Browser session finalized!')
        self.driver.quit()

        soup = BeautifulSoup(html_content, 'html.parser')

        elements = soup.find_all(["a", "div"])

        event_date_div = None
        sports_event_div = None
        league_name = None
        event_counter = 0

        print(f'\n[+] Parsing through {len(elements)} elements...')
        for element in elements:
            if elements.index(element) % 1000 == 0:
                print(f'\t-> Approx. {len(elements) - elements.index(element)} elements left')

            try:
                if element.name == "div" and "date-events__sport-header-date" in element.get("class", [])[0]:
                    event_date_div = element

                elif event_date_div and element.name == "div" and 'date-events__sport-header-title' in element.get("class", [])[0]:
                    sports_event_div = element

                elif sports_event_div and element.name == "a" and "league" in element.get("href", []):
                    league_name = element.text.strip('>')

                elif element.name == "div" and element.get("class", [])[0] == 'event':
                    event_name = ''
                    home_team = element.find("div", class_="event__participant event__participant--home").text

                    try:
                        away_team = element.find("div", class_="event__participant event__participant--away").text

                    except:
                        event_name = home_team
                        home_team = ''
                        away_team = ''

                    event_time = element.find("div", class_="event__info--time").text

                    event_channels_holder = element.find("ul", class_="event__tags")

                    event_channels = event_channels_holder.find_all("span", class_="channel-text")

                    channels = []
                    for channel in event_channels:
                        channels.append(channel.text)

                    channels_string = ", ".join(channels)

                    all_data.append([home_team,
                                     away_team,
                                     event_name,
                                     event_time,
                                     channels_string,
                                     sports_event_div.text,
                                     league_name,
                                     event_date_div.text,
                                     event_counter])

                    event_counter += 1

            except IndexError:
                continue


print('===== SCRAPING OPERATION =====')
scraper = Scraper(0, Service('chromedriver.exe'))
scraper.scrape_data()
print('\n[+] Scraping finalized!')

print('\n------------------------------------------------------------------------\n')


print('===== UPLOADING OPERATION =====')
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('scraper-396615-5f864a78d08c.json', scope)
client = gspread.authorize(creds)

spreadsheet = client.open('ThporthToday')
print('\n[+] Sheet Name - "ThporthToday"')

worksheets = spreadsheet.worksheets()

for worksheet in worksheets:
    try:
        spreadsheet.del_worksheet(worksheet)
    except gspread.exceptions.APIError:
        worksheet_zero = spreadsheet.get_worksheet(0)
        worksheet_zero.clear()

        cell_format = {
            "textFormat": {"bold": True},
            "horizontalAlignment": "CENTER"
        }

        worksheet.update("A1:G1", [['Home Team', 'Away team', 'Event', 'Time', 'Channel', 'League', 'Sport']])

        worksheet.format("A1:G1", cell_format)

        time.sleep(1.5)
        pass

print('\n[+] Data Uploading...')
date_modifier = 0
row_counter = 2
old_date = ''
for sport_event in all_data:
    if all_data.index(sport_event) == 0:
        worksheet_zero = spreadsheet.get_worksheet(0)
        worksheet_zero.update_title(sport_event[-2])
    try:
        worksheet = spreadsheet.worksheet(sport_event[-2])
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sport_event[-2], rows="1000", cols="20")

        cell_format = {
            "textFormat": {"bold": True},
            "horizontalAlignment": "CENTER"
        }

        worksheet.update("A1:G1", [['Home Team', 'Away team', 'Event', 'Time', 'Channel', 'League', 'Sport']])

        worksheet.format("A1:G1", cell_format)

        time.sleep(1.5)

    if sport_event[-2] != old_date:
        row_counter = 2
        date_modifier = all_data.index(sport_event)

    event_index = all_data.index(sport_event) - date_modifier + 2

    print(f'\t-> Uploading to Sheet "{sport_event[-2]}" | Row "{row_counter}"...')

    cell_range = f"A{event_index}:G{event_index}"
    worksheet.update(cell_range, [sport_event[:-2]])

    time.sleep(0.75)

    old_date = sport_event[-2]
    row_counter += 1

print(f'\n[+] {len(all_data)} events uploaded successfully!')
