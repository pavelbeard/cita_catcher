import logging
from email import message
import sys

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
)

from citabot_actions import (
    WithData,
    run_polling_with_predata,
    show_tasks,
)
from citabot_utils.constants import LVL1_ROUTES, get_token
from citabot_utils.types import Provinces

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(token: str):
    bot = ApplicationBuilder().token(token=token).build()
    cities = "|".join(c.name for c in Provinces)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", WithData.ask_city)],
        states={
            LVL1_ROUTES: [
                CallbackQueryHandler(run_polling_with_predata, pattern=rf"^{cities}$")
            ],
        },
        fallbacks=[CommandHandler("start", WithData.ask_city)],
    )

    bot.add_handler(CommandHandler("show_tasks", show_tasks))
    bot.add_handler(conv_handler)
    bot.run_polling()


if __name__ == "__main__":
    try:
        sys.argv[1] == "--debug"
        debug = True
    except IndexError:
        debug = False

    token = get_token(debug=debug)

    if not token:
        message = "CITA_CATCHER_BOT token is not set and change it environment variables"
        logger.error(message)
        raise ValueError(message)

    main(token=token)
