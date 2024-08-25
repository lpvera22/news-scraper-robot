import logging

from robocorp.tasks import task

from src.news_robot import NewsRobot

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@task
def robot_spare_bin_python():
    '''
    Main task function to run the news scraping robot.
    '''
    logging.info('Starting robot task')
    robot = NewsRobot()
    robot.run()
    logging.info('Robot task completed')
