import os
from logging import getLogger
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait


class RedditChatBot:
    MESSAGE_CLASS = '_3Gy8WZD53wWAE41lr57by3'
    USER_CLASS = 'pqdGGYoXaBuzfPrYLoqaM'
    TEXTBOX_XPATH = '/html/body/div[1]/div/main/div[2]/div/form/textarea'
    SLEEP_TIME = 5

    def __init__(self, channel_url):
        self.logger = getLogger(self.__class__.__name__)
        self.channel_url = channel_url
        self.commands = {}
        self.textbox = None
        self.ignored_users = []

        options = webdriver.FirefoxOptions()
        options.headless = True
        self.driver = webdriver.Firefox(options=options)

    def _get_message_element(self, driver):
        element = driver.find_elements_by_class_name(self.MESSAGE_CLASS)
        if element:
            return element
        return False

    def _get_user_element(self, driver):
        element = driver.find_elements_by_class_name(self.USER_CLASS)
        if element:
            return element
        return False

    def login(self):
        self.logger.info(f'Logging in to channel: {self.channel_url}')
        self.driver.get(self.channel_url)
        sleep(5)
        self.driver.find_element_by_id("loginUsername").send_keys(os.getenv('REDDIT_USERNAME'))
        self.driver.find_element_by_id("loginPassword").send_keys(os.getenv('REDDIT_PASSWORD'))
        self.driver.find_element_by_id("loginPassword").send_keys(Keys.RETURN)
        sleep(10)
        self.textbox = self.get_textbox()

    def get_msgs(self):
        return WebDriverWait(self.driver, 1).until(self._get_message_element)

    def get_users(self):
        return WebDriverWait(self.driver, 1).until(self._get_user_element)

    def get_last_msg(self):
        messages = self.get_msgs()
        return messages[-1].text

    def get_last_user(self):
        users = self.get_users()
        return users[-1].text

    def get_textbox(self):
        return self.driver.find_element_by_xpath(self.TEXTBOX_XPATH)

    def send_msg(self, msg):
        self.textbox.send_keys(msg)
        self.textbox.send_keys(Keys.RETURN)

    def send_error(self):
        self.textbox.send_keys('Woops! Something went wrong :(')
        self.textbox.send_keys(Keys.RETURN)

    def parse_msg(self, *args):
        if args[0] in self.commands:
            if len(args) > 1:
                self.commands[args[0]](*args[1:])
            else:
                self.commands[args[0]]()

    def register_command(self, BotCommand):
        command = BotCommand(self)
        self.commands[command.keyword] = command

    def run(self):
        self.logger.info(f'Starting {self.__class__.__name__}...')
        self.login()
        while True:
            try:
                msg = self.get_last_msg()
                user = self.get_last_user()
                if msg.startswith('!') and user not in self.ignored_users:
                    self.parse_msg(*msg[1:].split())
                    sleep(self.SLEEP_TIME)
                else:
                    sleep(0.1)
            except KeyboardInterrupt:
                self.logger.info('Exiting!')
                self.driver.quit()
                break

    def __del__(self):
        self.driver.quit()
