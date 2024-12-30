import logging
import sys

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
)

from citabot_actions import (
    WithData,
    clear_all_tasks,
    clear_task,
    run_polling_with_predata,
    show_tasks,
)
from citabot_utils.constants import LVL0_ROUTES, LVL1_ROUTES, LVL2_ROUTES, get_token
from citabot_utils.types import Provinces

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(token: str):
    bot = ApplicationBuilder().token(token=token).build()
    cities = "|".join(c.name for c in Provinces)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", WithData.choose_city)],
        states={
            LVL0_ROUTES: [
                CallbackQueryHandler(run_polling_with_predata, pattern=rf"^{cities}$"),
            ],
            LVL1_ROUTES: [
                CallbackQueryHandler(show_tasks, pattern="show_tasks"),
                CallbackQueryHandler(clear_all_tasks, pattern="clear_all_tasks"),
            ],
            LVL2_ROUTES: [
                CallbackQueryHandler(clear_task, pattern=rf"^{cities}$"),
            ]
        },
        fallbacks=[CommandHandler("start", WithData.choose_city)],
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
        message = (
            "CITA_CATCHER_BOT token is not set and change it environment variables"
        )
        logger.error(message)
        raise ValueError(message)

    main(token=token)
