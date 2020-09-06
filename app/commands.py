import os
import emoji
import datetime
import requests
from time import sleep
import yfinance as yf
import pandas as pd
from logging import getLogger
from azure.cognitiveservices.search.websearch import WebSearchClient
from msrest.authentication import CognitiveServicesCredentials


class BaseCommand:
    keyword = ''
    help_txt = ''

    def __init__(self, bot):
        self.bot = bot
        self.logger = getLogger(self.__class__.__name__)

    def __call__(self, *args):
        return self.run(*args)

    def run(self, *args):
        pass


class HelpCommand(BaseCommand):
    keyword = 'help'
    help_text = 'Show this help'

    def run(self, *args):
        msg = 'Bot commands:\n'
        for kw, command in self.bot.commands.items():
            if kw == 'help':
                continue
            msg += f'!{kw} - {command.help_txt}\n'
        self.bot.send_msg(msg)


class SleepCommand(BaseCommand):
    keyword = 'sleep'
    help_txt = 'Send me to sleep for a minute'

    def run(self, *args):
        self.bot.send_msg(emoji.emojize('Zzzz :sleeping:'))
        sleep(60)


class InfoCommand(BaseCommand):
    keyword = 'info'
    help_txt = 'Price information for a ticker, e.g. !info AAPL'

    def run(self, *args):
        symbol = args[0]
        ticker = yf.Ticker(symbol)

        try:
            info = ticker.info
            msg = f"[{info['symbol']}] {info['longName']}\n"\
                  f"Price: {info['ask']}\n"\
                  f"Day Range: {info['dayLow']} - {info['dayHigh']}"
        except ValueError:
            self.logger.debug(f'Unable to find ticker {symbol}')
            self.bot.send_msg(f'Sorry, I couldn\'t find {symbol}')
        except Exception as e:
            self.logger.error(e)
            self.bot.send_error()
        else:
            self.logger.debug(f'Got info on {symbol}')
            self.bot.send_msg(msg)


class RecommendationsCommand(BaseCommand):
    keyword = 'recom'
    help_txt = 'Analyst recommendations trend, e.g. !recom TSLA'

    def run(self, *args):
        symbol = args[0]

        try:
            r = requests.get('https://finnhub.io/api/v1/stock/recommendation',
                             params={'symbol': symbol,
                                     'token': os.getenv('FINNHUB_API')})
            df = pd.DataFrame(r.json())
            df = df.set_index('period').drop('symbol', axis=1).iloc[:4]
            for col in df.columns:
                df[col] = df[col].apply(str).str.pad(10, fillchar='_', side='both')
            msg = df.to_markdown()
        except Exception as e:
            self.logger.error(e)
            self.bot.send_msg(f'Sorry, I couldn\'t find any recommendations for {symbol}')
        else:
            self.logger.debug(f'Got recommendations on {symbol}')
            self.bot.send_msg(msg)


class NewsCommand(BaseCommand):
    keyword = 'news'
    help_txt = 'Headline articles on subject, e.g. !news US Economy'

    def __init__(self, *args):
        super().__init__(*args)
        self.client = WebSearchClient(endpoint=os.getenv('SEARCH_ENDPOINT'),
                                      credentials=CognitiveServicesCredentials(os.getenv('SEARCH_API')))

    def run(self, *args):
        query = ' '.join(args)
        articles = self.client.web.search(query=query,
                                          response_filter=['News'],
                                          freshness='Day')
        if articles.news is None:
            self.bot.send_msg(f'Sorry, I couldn\'t find any news on {query}')
        else:
            msg = ''
            for article in articles.news.value:
                title = article.name
                long_url = article.url
                #try:
                #    short_url = requests.get('https://cutt.ly/api/api.php',
                #                             params={'key': os.getenv('CUTTLYAPI'),
                #                                     'short': long_url}).json()['url']['shortLink']
                #    msg += f'{title} ({short_url})\n'
                #except Exception as e:
                #    self.logger.warning(f'Unable to get shortened URL for {long_url}')
                #    msg += f'{title}\n{long_url}\n'
                msg += f'▸ {title} ({long_url})\n'
            self.bot.send_msg(msg)


class CallsCommand(BaseCommand):
    keyword = 'calls'
    help_txt = 'Options chain for calls around strike, e.g. !calls TSLA 2020-09-11 420'

    def run(self, *args):
        if len(args) != 3:
            self.bot.send_msg('Sorry, I don\'t understand.\n'
                              'I need the symbol, date (YYYY-MM-DD) and strike')
        else:
            symbol, date, strike = args
            strike = float(strike)
            ticker = yf.Ticker(symbol)
            try:
                df = ticker.option_chain(date).calls[['strike', 'ask', 'bid',
                                                      'volume', 'impliedVolatility',
                                                      'inTheMoney']]
                df.rename(columns={'impliedVolatility': 'IV',
                                   'inTheMoney': 'ITM'},
                          inplace=True)
                if strike < df['strike'].iloc[0] or strike > df['strike'].iloc[-1]:
                    msg = f'I couldn\'t find any options at strike {strike}'
                else:
                    idx = df['strike'].sub(strike).abs().idxmin()
                    idx_min = abs(idx-2)
                    idx_max = idx+3 if idx+3 < len(df)-1 else len(df)-1
                    df = df.iloc[idx_min:idx_max]
                    msg = df.to_markdown(index=False)
            except Exception as e:
                self.logger.error(e)
                self.bot.send_error()
            else:
                self.bot.send_msg(msg)


class PutsCommand(BaseCommand):
    keyword = 'puts'
    help_txt = 'Options chain for puts around strike, e.g. !puts TSLA 2020-09-11 420'

    def run(self, *args):
        if len(args) != 3:
            self.bot.send_msg('Sorry, I don\'t understand.\n'
                              'I need the symbol, date (YYYY-MM-DD) and strike')
        else:
            symbol, date, strike = args
            strike = float(strike)
            ticker = yf.Ticker(symbol)
            try:
                df = ticker.option_chain(date).puts[['strike', 'ask', 'bid',
                                                      'volume', 'impliedVolatility',
                                                      'inTheMoney']]
                df.rename(columns={'impliedVolatility': 'IV',
                                   'inTheMoney': 'ITM'},
                          inplace=True)
                if strike < df['strike'].iloc[0] or strike > df['strike'].iloc[-1]:
                    msg = f'I couldn\'t find any options at strike {strike}'
                else:
                    idx = df['strike'].sub(strike).abs().idxmin()
                    idx_min = abs(idx-2)
                    idx_max = idx+3 if idx+3 < len(df)-1 else len(df)-1
                    df = df.iloc[idx_min:idx_max]
                    msg = df.to_markdown(index=False)
            except Exception as e:
                self.logger.error(e)
                self.bot.send_error()
            else:
                self.bot.send_msg(msg)
