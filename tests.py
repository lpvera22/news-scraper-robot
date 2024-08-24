import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from tasks import NewsScraper
from datetime import datetime, timedelta 
class TestNewsScraper(unittest.TestCase):

    @patch('tasks.Selenium')
    @patch('tasks.os.makedirs')
    def setUp(self, mock_makedirs, mock_selenium):
        # Set up a mock for Selenium and file directory creation
        self.mock_browser = mock_selenium.return_value
        self.scraper = NewsScraper('climate change', 'news', 3)

    def test_init(self):
        # Test the initialization of the NewsScraper
        self.assertEqual(self.scraper.search_phrase, 'climate change')
        self.assertEqual(self.scraper.news_category, 'news')
        self.assertEqual(self.scraper.number_of_months, 3)
        self.assertTrue(isinstance(self.scraper.articles, list))

    @patch('tasks.NewsScraper.open_browser')
    @patch('tasks.NewsScraper.extract_news_articles')
    @patch('tasks.NewsScraper.save_to_excel')
    @patch('tasks.NewsScraper.close_browser')
    def test_run(self, mock_close_browser, mock_save_to_excel, mock_extract_news_articles, mock_open_browser):
        # Test the run method
        self.scraper.run()
        mock_open_browser.assert_called_once()
        mock_extract_news_articles.assert_called_once()
        mock_save_to_excel.assert_called_once()
        mock_close_browser.assert_called_once()

    def test_open_browser(self):
        # Test the open_browser method
        self.scraper.open_browser()
        self.mock_browser.open_available_browser.assert_called_once()

    

    def test_extract_news_articles(self):
        # Mock the elements returned by find_elements
        mock_card_1 = MagicMock()
        mock_card_2 = MagicMock()
        self.mock_browser.find_elements.return_value = [mock_card_1, mock_card_2]

        # Mock the interactions within each article card
        self.mock_browser.get_text.side_effect = [
            'Title 1', 'Source 1', '1 day ago', 'Description 1',  # Article 1
            'Title 2', 'Source 2', '2 days ago', 'Description 2'   # Article 2
        ]

        # First calls to get_element_attribute are for the article links, the second ones are for image URLs
        self.mock_browser.get_element_attribute.side_effect = [
            'https://example.com/article1',  # Article 1 link
            'https://example.com/article2',  # Article 2 link
            'https://example.com/image1.jpg',  # Article 1 image
            'https://example.com/image2.jpg'   # Article 2 image
        ]

        # Mock the date parsing
        self.scraper.parse_date = MagicMock(side_effect=[
            datetime.now() - timedelta(days=1),  # Article 1 date
            datetime.now() - timedelta(days=2)   # Article 2 date
        ])

        # Mock the download_image method to return the expected image URL
        self.scraper.download_image = MagicMock(side_effect=[
            'https://example.com/image1.jpg',  # Article 1 image filename
            'https://example.com/image2.jpg'   # Article 2 image filename
        ])

        # Run the method under test
        self.scraper.extract_news_articles()

        # Verify the expected number of articles were added
        self.assertEqual(len(self.scraper.articles), 2)

        # Check the contents of the first article
        article_1 = self.scraper.articles[0]
        self.assertEqual(article_1['title'], 'Title 1')
        self.assertEqual(article_1['description'], 'Description 1')
        self.assertEqual(article_1['image_filename'], 'https://example.com/image1.jpg')

        # Check the contents of the second article
        article_2 = self.scraper.articles[1]
        self.assertEqual(article_2['title'], 'Title 2')
        self.assertEqual(article_2['description'], 'Description 2')
        self.assertEqual(article_2['image_filename'], 'https://example.com/image2.jpg')

    def test_get_article(self):
        # Test the get_article method
        mock_card = MagicMock()
        self.mock_browser.get_text.side_effect = ['Some Title', 'Some Source', '5 days ago', 'Description']
        self.mock_browser.get_element_attribute.side_effect = ['https://example.com', 'https://example.com/image.jpg']
        
        article = self.scraper.get_article(mock_card)
        self.assertEqual(article['title'], 'Some Title')
        self.assertEqual(article['description'], 'Description')
        self.assertEqual(article['clear_link'], 'https://example.com')

    def test_parse_date(self):
        # Test parsing various date strings
        self.assertIsInstance(self.scraper.parse_date('5 hours ago'), datetime)
        self.assertIsInstance(self.scraper.parse_date('2 days ago'), datetime)
        self.assertIsInstance(self.scraper.parse_date('1 week ago'), datetime)
        self.assertIsInstance(self.scraper.parse_date('3 months ago'), datetime)
        self.assertIsInstance(self.scraper.parse_date('2023-01-01'), datetime)

    def test_count_phrase_in_text(self):
        # Test counting occurrences of a phrase in text
        count = self.scraper.count_phrase_in_text('climate change', 'Climate change is real', 'Climate change effects are visible.')
        self.assertEqual(count, 2)

    def test_contains_monetary_value(self):
        # Test detection of monetary values in text
        contains = self.scraper.contains_monetary_value('The cost is $100.', 'There is no mention of dollars.')
        self.assertTrue(contains)

        contains = self.scraper.contains_monetary_value('No cost mentioned here.', 'Still no mention.')
        self.assertFalse(contains)

    


if __name__ == '__main__':
    unittest.main()
