import logging
from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files
from RPA.Robocorp.WorkItems import WorkItems
import re
from datetime import datetime, timedelta
from dateutil import parser
import dateutil.relativedelta
from time import sleep
import requests
import os
from mimetypes import guess_extension
from robocorp.tasks import task

class NewsScraper:
    def __init__(self, search_phrase, news_category, number_of_months):
        self.search_phrase = search_phrase
        self.news_category = news_category
        self.number_of_months = number_of_months
        self.browser = Selenium()
        self.articles = []
        self.download_dir = "output/images"
        os.makedirs(self.download_dir, exist_ok=True)
    
    def run(self):
        try:
            self.open_browser()
            self.extract_news_articles()
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            self.save_to_excel()
            self.close_browser()
    
    def open_browser(self):
        template = 'https://news.search.yahoo.com/search?p={}&fr2=category:{}'
        url = template.format(self.search_phrase, self.news_category)
        self.browser.open_available_browser(url)
    
    def extract_news_articles(self):
        current_time = datetime.now()
        page_count = 0
        while True:
            sleep(2)  # Allow the page to load
            
            try:
                cards = self.browser.find_elements("xpath://div[contains(@class, 'NewsArticle')]")
                
                for card in cards:
                    article = self.get_article(card)
                    link = article["clear_link"]
                    posted_date = article["date"]

                    if link not in [a['clear_link'] for a in self.articles] and posted_date and (current_time - posted_date).days <= 30 * self.number_of_months:
                        self.articles.append(article)
                
                # Save progress periodically every 2 pages
                if page_count > 0 and page_count % 2 == 0:
                    self.save_to_excel(auto_save=True)

                page_count += 1
                
                next_button = self.browser.find_element("xpath=//a[contains(@class, 'next')]")
                next_url = self.browser.get_element_attribute(next_button, "href")
                self.browser.go_to(next_url)
            except Exception:
                break
    
    def get_article(self, card):
        headline = self.browser.get_text(self.browser.find_element("xpath=.//h4[contains(@class, 's-title')]", card))
        source = self.browser.get_text(self.browser.find_element("xpath=.//span[contains(@class, 's-source')]", card))
        posted_text = self.browser.get_text(self.browser.find_element("xpath=.//span[contains(@class, 's-time')]", card))
        posted = posted_text.replace('.', '').strip()
        posted_date = self.parse_date(posted)
        description = self.browser.get_text(self.browser.find_element("xpath=.//p[contains(@class, 's-desc')]", card)).strip()
        
        raw_link = self.browser.get_element_attribute(self.browser.find_element("xpath=.//a", card), "href")
        unquoted_link = requests.utils.unquote(raw_link)
        
        pattern = re.compile(r'RU=(.+)\/RK')
        match = re.search(pattern, unquoted_link)
        clear_link = match.group(1) if match else unquoted_link
        
        try:
            image_element = self.browser.find_element("xpath=.//img", card)
            image_url = self.browser.get_element_attribute(image_element, "src")
            logging.info(f"Image URL found: {image_url}")
            image_filename = self.download_image(image_url)
        except Exception:
            image_filename = "No image"
        
        phrase_count = self.count_phrase_in_text(self.search_phrase, headline, description)
        contains_money = self.contains_monetary_value(headline, description)
        
        article = {
            "title": headline,
            "date": posted_date,
            "description": description,
            "image_filename": image_filename,
            "count_search_phrase": phrase_count,
            "contains_money": contains_money,
            "clear_link": clear_link
        }
        return article
    
    def parse_date(self, date_str):
        current_time = datetime.now()
        try:
            if "hour" in date_str:
                hours_ago = int(re.search(r"(\d+)", date_str).group())
                parsed_date = current_time - timedelta(hours=hours_ago)
            elif "day" in date_str:
                days_ago = int(re.search(r"(\d+)", date_str).group())
                parsed_date = current_time - timedelta(days=days_ago)
            elif "week" in date_str:
                weeks_ago = int(re.search(r"(\d+)", date_str).group())
                parsed_date = current_time - timedelta(weeks=weeks_ago)
            elif "month" in date_str:
                months_ago = int(re.search(r"(\d+)", date_str).group())
                parsed_date = current_time - dateutil.relativedelta.relativedelta(months=months_ago)
            elif "year" in date_str:
                years_ago = int(re.search(r"(\d+)", date_str).group())
                parsed_date = current_time - dateutil.relativedelta.relativedelta(years=years_ago)
            else:
                parsed_date = parser.parse(date_str)
            return parsed_date
        except Exception:
            return None
    
    def count_phrase_in_text(self, phrase, title, description):
        phrase_lower = phrase.lower()
        count = title.lower().count(phrase_lower) + description.lower().count(phrase_lower)
        return count
    
    def contains_monetary_value(self, title, description):
        money_pattern = r"\$\d+(\.\d{1,2})?|\d+ (USD|dollars)"
        contains = bool(re.search(money_pattern, title) or re.search(money_pattern, description))
        return contains
    
    def download_image(self, url):
        if not url:
            return "No image"
        
        try:
            # Generate a valid file name from the URL
            file_name = os.path.join(self.download_dir, url.split("/")[-1])
            
            # Ensure the file name has an extension
            if not os.path.splitext(file_name)[1]:
                response = requests.head(url)
                content_type = response.headers.get('Content-Type', '')
                extension = guess_extension(content_type.split(';')[0].strip()) or '.jpg'
                file_name += extension
            
            # Ensure the file name is unique
            if os.path.exists(file_name):
                base, ext = os.path.splitext(file_name)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                file_name = f"{base}_{counter}{ext}"
            
            # Download the image using requests
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(file_name, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                return file_name
            else:
                return "No image"
        except Exception:
            return "No image"
    
    def save_to_excel(self, auto_save=False):
        excel = Files()
        try:
            excel.create_workbook("output/news_data.xlsx")
            excel.create_worksheet("News Data")
            header = ["Title", "Date", "Description", "Image Filename", "Count Search Phrase", "Contains Money"]
            data = [header] + [
                [
                    article["title"],
                    article["date"].strftime("%Y-%m-%d") if article["date"] else "",
                    article["description"],
                    article["image_filename"],
                    article["count_search_phrase"],
                    article["contains_money"]
                ]
                for article in self.articles
            ]
            excel.append_rows_to_worksheet(data, "News Data")
            excel.save_workbook()
        except Exception as e:
            raise
    
    def close_browser(self):
        try:
            self.browser.close_all_browsers()
        except Exception:
            pass


class NewsRobot:
    def __init__(self):
        self.work_item = WorkItems()
    
    def run(self):
        search_phrase, news_category, number_of_months = self.get_work_item_data()
        scraper = NewsScraper(search_phrase, news_category, number_of_months)
        scraper.run()
        self.complete_work_item()
    
    def get_work_item_data(self):
        try:
            self.work_item.get_input_work_item()
            search_phrase = self.work_item.get_work_item_variable("search_phrase")
            news_category = self.work_item.get_work_item_variable("news_category")
            number_of_months = int(self.work_item.get_work_item_variable("number_of_months", default=1))
        except Exception:
            search_phrase = "climate change"
            news_category = "news"
            number_of_months = 1
        return search_phrase, news_category, number_of_months
    
    def complete_work_item(self):
        try:
            self.work_item.complete_work_item()
        except Exception:
            pass


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Task function for Robocorp
@task
def robot_spare_bin_python():
    robot = NewsRobot()
    robot.run()
