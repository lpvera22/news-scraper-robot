import logging
from typing import Tuple

from RPA.Robocorp.WorkItems import WorkItems

from src.news_scraper import NewsScraper


class NewsRobot:
    def __init__(self):
        '''
        Initialize the NewsRobot, which manages the work items and the scraping process.
        '''
        self.work_item: WorkItems = WorkItems()
        logging.info('NewsRobot initialized')

    def run(self) -> None:
        '''
        Execute the news scraping task using the configured work items.
        '''
        logging.info('Running the NewsRobot')
        search_phrase, news_category, number_of_months = self.get_work_item_data()
        scraper = NewsScraper(search_phrase, news_category, number_of_months)
        scraper.run()
        self.complete_work_item()

    def get_work_item_data(self) -> Tuple[str, str, int]:
        '''
        Retrieve the input data from work items.
        '''
        logging.info('Getting work item data')
        try:
            self.work_item.get_input_work_item()
            search_phrase: str = self.work_item.get_work_item_variable('search_phrase')
            news_category: str = self.work_item.get_work_item_variable('news_category')
            number_of_months: int = int(self.work_item.get_work_item_variable('number_of_months', default=1))
            logging.info('Work item data retrieved: %s, %s, %d', search_phrase, news_category, number_of_months)
        except Exception as e:
            logging.error('An error occurred while getting work item data: %s', e)
            search_phrase, news_category, number_of_months = 'climate change', 'news', 1
        return search_phrase, news_category, number_of_months

    def complete_work_item(self) -> None:
        '''
        Mark the work item as completed.
        '''
        logging.info('Completing work item')
        try:
            self.work_item.complete_work_item()
            logging.info('Work item completed successfully')
        except Exception as e:
            logging.error('An error occurred while completing work item: %s', e)
