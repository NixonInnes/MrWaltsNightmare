from .bot import RedditChatBot
from .commands import HelpCommand, InfoCommand, RecommendationsCommand, \
    NewsCommand, CallsCommand, PutsCommand, SleepCommand


def create_bot(url):
    bot = RedditChatBot(url)

    bot.register_command(HelpCommand)
    bot.register_command(SleepCommand)
    bot.register_command(InfoCommand)
    bot.register_command(RecommendationsCommand)
    bot.register_command(NewsCommand)
    bot.register_command(CallsCommand)
    bot.register_command(PutsCommand)

    return bot