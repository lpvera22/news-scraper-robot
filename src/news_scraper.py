import logging
import os
import re
from datetime import datetime, timedelta
from mimetypes import guess_extension
from time import sleep
from typing import List, Optional, Tuple

import requests
import dateutil.relativedelta
from dateutil import parser
from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files
from RPA.Robocorp.WorkItems import WorkItems
from robocorp.tasks import task
class NewsScraper:
    def __init__(self, search_phrase: str, news_category: str, number_of_months: int):
        '''
        Initialize the NewsScraper with search phrase, news category, and the number of months to look back.
        '''
        self.search_phrase: str = search_phrase
        self.news_category: str = news_category
        self.number_of_months: int = number_of_months
        self.browser: Selenium = Selenium()
        self.articles: List[dict] = []
        self.download_dir: str = 'images'
        os.makedirs(self.download_dir, exist_ok=True)
        logging.info('NewsScraper initialized')

    def run(self) -> None:
        '''
        Run the news scraping process: open browser, extract articles, and save results.
        '''
        try:
            logging.info('Running the NewsScraper')
            self.open_browser()
            self.extract_news_articles()
        except Exception as e:
            logging.error('An error occurred during the run: %s', e)
        finally:
            logging.info('Saving to Excel and closing the browser')
            self.save_to_excel()
            self.close_browser()

    def open_browser(self) -> None:
        '''
        Open the browser in headless mode and navigate to the search results page.
        '''
        logging.info('Opening browser')
        template = 'https://news.search.yahoo.com/search?p={}&fr2=category:{}'
        url: str = template.format(self.search_phrase, self.news_category)
        logging.info('Opening URL: %s', url)

        options = {
            'arguments': ['--headless', '--disable-gpu', '--no-sandbox']
        }
        self.browser.open_available_browser(url, options=options)
        logging.info('Browser opened in headless mode')

    def check_and_handle_consent_page(self) -> None:
        '''
        Check if a consent page is displayed and handle it by clicking the consent button.
        '''
        try:
            consent_button_xpath: str = "//*[@id='consent-page']/div/div/div/form/div[2]/div[2]/button[1]"
            if self.browser.is_element_visible(consent_button_xpath):
                logging.info('Consent page detected. Clicking the consent button.')
                self.browser.click_element(consent_button_xpath)
                sleep(2)  # Wait to ensure the action is completed
            else:
                logging.info('Consent page not detected.')
        except Exception as e:
            logging.error('An error occurred while handling the consent page: %s', e)

    def extract_news_articles(self) -> None:
        '''
        Extract news articles from the search results, save HTML content, and check for the next page.
        '''
        logging.info('Starting to extract news articles')
        current_time: datetime = datetime.now()
        page_count: int = 0

        # Check and handle the consent page at the start
        self.check_and_handle_consent_page()

        while True:
            sleep(2)  # Allow the page to load
            logging.info('Processing page %d', page_count + 1)

            try:
                cards: List = self.browser.find_elements("xpath://div[contains(@class, 'NewsArticle')]")
                logging.info('Found %d articles on the page', len(cards))

                for card in cards:
                    article: Optional[dict] = self.get_article(card)
                    if article:
                        link: str = article['clear_link']
                        posted_date: Optional[datetime] = article['date']

                        if link not in [a['clear_link'] for a in self.articles] and posted_date and (current_time - posted_date).days <= 30 * self.number_of_months:
                            logging.info('Adding article: %s', article['title'])
                            self.articles.append(article)

                # Save progress periodically every 2 pages
                if page_count > 0 and page_count % 2 == 0:
                    logging.info('Saving progress after %d pages', page_count)
                    self.save_to_excel(auto_save=True)

                page_count += 1

                next_button = self.browser.find_element("xpath=//a[contains(@class, 'next')]")
                next_url: str = self.browser.get_element_attribute(next_button, 'href')
                logging.info('Moving to next page: %s', next_url)
                self.browser.go_to(next_url)

                # Check for the consent page on each navigation
                self.check_and_handle_consent_page()

            except Exception as e:
                logging.error('An error occurred while extracting articles: %s', e)
                break

            self.save_to_excel(auto_save=True)

    def get_article(self, card) -> Optional[dict]:
        '''
        Extract details from a news article card element.
        '''
        logging.info('Extracting article details')
        try:
            headline: str = self.browser.get_text(self.browser.find_element("xpath=.//h4[contains(@class, 's-title')]", card))
            source: str = self.browser.get_text(self.browser.find_element("xpath=.//span[contains(@class, 's-source')]", card))
            posted_text: str = self.browser.get_text(self.browser.find_element("xpath=.//span[contains(@class, 's-time')]", card))
            posted_date: Optional[datetime] = self.parse_date(posted_text.replace('.', '').strip())
            description: str = self.browser.get_text(self.browser.find_element("xpath=.//p[contains(@class, 's-desc')]", card)).strip()

            raw_link: str = self.browser.get_element_attribute(self.browser.find_element("xpath=.//a", card), 'href')
            unquoted_link: str = requests.utils.unquote(raw_link)

            clear_link_match = re.search(r'RU=(.+)\/RK', unquoted_link)
            clear_link: str = clear_link_match.group(1) if clear_link_match else unquoted_link

            image_url: str = self.browser.get_element_attribute(self.browser.find_element("xpath=.//img", card), 'src')
            image_filename: str = self.download_image(image_url)

            phrase_count: int = self.count_phrase_in_text(self.search_phrase, headline, description)
            contains_money: bool = self.contains_monetary_value(headline, description)

            article: dict = {
                'title': headline,
                'date': posted_date,
                'description': description,
                'image_filename': image_filename,
                'count_search_phrase': phrase_count,
                'contains_money': contains_money,
                'clear_link': clear_link
            }
            logging.info('Article extracted: %s', headline)
            return article

        except Exception as e:
            logging.error('An error occurred while extracting article details: %s', e)
            return None

    def parse_date(self, date_str: str) -> Optional[datetime]:
        '''
        Parse a date string into a datetime object.
        '''
        logging.info('Parsing date: %s', date_str)
        current_time: datetime = datetime.now()
        try:
            if 'hour' in date_str:
                return current_time - timedelta(hours=int(re.search(r'(\d+)', date_str).group()))
            elif 'day' in date_str:
                return current_time - timedelta(days=int(re.search(r'(\d+)', date_str).group()))
            elif 'week' in date_str:
                return current_time - timedelta(weeks=int(re.search(r'(\d+)', date_str).group()))
            elif 'month' in date_str:
                return current_time - dateutil.relativedelta.relativedelta(months=int(re.search(r'(\d+)', date_str).group()))
            elif 'year' in date_str:
                return current_time - dateutil.relativedelta.relativedelta(years=int(re.search(r'(\d+)', date_str).group()))
            else:
                return parser.parse(date_str)
        except Exception as e:
            logging.error('An error occurred while parsing date: %s', e)
            return None

    def count_phrase_in_text(self, phrase: str, title: str, description: str) -> int:
        '''
        Count the occurrences of a search phrase in the title and description.
        '''
        logging.info('Counting occurrences of phrase "%s" in title and description', phrase)
        phrase_lower: str = phrase.lower()
        count: int = title.lower().count(phrase_lower) + description.lower().count(phrase_lower)
        logging.info('Phrase count: %d', count)
        return count

    def contains_monetary_value(self, title: str, description: str) -> bool:
        '''
        Check if the title or description contains any monetary values.
        '''
        logging.info('Checking for monetary values in title and description')
        money_pattern: str = r'\$\d+(\.\d{1,2})?|\d+ (USD|dollars)'
        contains: bool = bool(re.search(money_pattern, title) or re.search(money_pattern, description))
        logging.info('Contains monetary value: %s', contains)
        return contains

    def download_image(self, url: str) -> str:
        '''
        Download an image from the given URL.
        '''
        if not url:
            return 'No image'
        try:
            logging.info('Downloading image from URL: %s', url)
            file_name: str = os.path.join(self.download_dir, url.split('/')[-1])

            # Ensure the file name has an extension
            if not os.path.splitext(file_name)[1]:
                response = requests.head(url)
                content_type: str = response.headers.get('Content-Type', '')
                extension: str = guess_extension(content_type.split(';')[0].strip()) or '.jpg'
                file_name += extension

            # Ensure the file name is unique
            if os.path.exists(file_name):
                base, ext = os.path.splitext(file_name)
                counter: int = 1
                while os.path.exists(f'{base}_{counter}{ext}'):
                    counter += 1
                file_name = f'{base}_{counter}{ext}'

            # Download the image
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(file_name, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                logging.info('Image saved as: %s', file_name)
                return file_name
            else:
                logging.warning('Failed to download image, status code: %d', response.status_code)
                return 'No image'
        except Exception as e:
            logging.error('An error occurred while downloading image: %s', e)
            return 'No image'

    def save_to_excel(self, auto_save: bool = False) -> None:
        '''
        Save the extracted articles to an Excel file.
        '''
        logging.info('Saving articles to Excel')
        excel = Files()
        try:
            excel.create_workbook('output/news_data.xlsx')
            excel.create_worksheet('News Data')
            header: List[str] = ['Title', 'Date', 'Description', 'Image Filename', 'Count Search Phrase', 'Contains Money']
            data: List[List[str]] = [header] + [
                [
                    article['title'],
                    article['date'].strftime('%Y-%m-%d') if article['date'] else '',
                    article['description'],
                    article['image_filename'],
                    str(article['count_search_phrase']),
                    str(article['contains_money'])
                ]
                for article in self.articles if article is not None
            ]
            excel.append_rows_to_worksheet(data, 'News Data')
            excel.save_workbook()
            logging.info('Excel workbook saved successfully')
        except Exception as e:
            logging.error('An error occurred while saving to Excel: %s', e)
            raise

    def close_browser(self) -> None:
        '''
        Close all open browser instances.
        '''
        logging.info('Closing the browser')
        try:
            self.browser.close_all_browsers()
            logging.info('Browser closed successfully')
        except Exception as e:
            logging.error('An error occurred while closing the browser: %s', e)



