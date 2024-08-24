# News Scraper Robot

This project is a Robocorp robot that automates the process of scraping news articles from Yahoo News based on a search phrase, news category, and time frame. The robot extracts key details from each news article, such as the headline, source, date, description, image, and whether the article contains any monetary values. The scraped data is saved in an Excel file.

## Features

- **Search and Scrape News Articles**: Automatically searches Yahoo News for articles based on a given search phrase and category.
- **Filter by Time Frame**: Only retrieves articles within a specified number of months.
- **Extract Key Information**: Captures the headline, source, publication date, description, and image URL from each article.
- **Image Downloading**: Downloads article images and saves them with appropriate file extensions.
- **Excel Report Generation**: Compiles the extracted data into an Excel file with the article details and image filenames.
- **Robocorp Cloud Integration**: Configured to run on Robocorp Cloud using GitHub integration.

## Installation

### Prerequisites

- [Python 3.x](https://www.python.org/downloads/)
- [Robocorp Lab](https://robocorp.com/docs/product-manuals/robocorp-lab)
- [Git](https://git-scm.com/)

### Clone the Repository

```bash
git clone https://github.com/yourusername/news-scraper-robot.git
cd news-scraper-robot
```
### Install Dependencies
```bash
conda env create -f conda.yaml
conda activate news-scraper-robot
```
### Configuration
The robot configuration is handled through a ```robot.yaml``` file and environment variables or work items passed from Robocorp Cloud.
### Work Items
The robot expects the following work item variables when run in Robocorp Cloud:

- search_phrase: The phrase to search for in Yahoo News.
- news_category: The category or section of the news (e.g., "World", "Technology").
- number_of_months: The number of months to filter articles by (e.g., 1 for the current month).

## Running the Robot
### Locally with Robocorp Lab
- Open the project in Robocorp Lab.
- Select the ```robot_spare_bin_python``` task.
- Run the robot.
### In Robocorp Cloud
- Create a robot in Robocorp Cloud and link it to this GitHub repository.
- Configure the work items with the necessary search parameters.
- Run the robot from Robocorp Cloud.
