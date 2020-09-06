import os
import logging

logging.basicConfig(filename='log.txt',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

if os.path.isfile('.env'):
    from dotenv import load_dotenv
    load_dotenv('.env')

from app import create_bot

bot = create_bot(os.getenv('REDDIT_CHAT_URL'))

if __name__ == '__main__':
    bot.run()
