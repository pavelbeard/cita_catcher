import asyncio
import json
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from citabot_actions.reducer_types import ProvinceAction
from citabot_actions.store import interval_store, province_store
from citabot_utils.constants import COUNTRIES, LVL1_ROUTES
from citabot_utils.types import Data, Provinces, Task, Tramites
from citabot_watcher import Watcher
from reducer.types import ActionType

start_keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(text="Start", callback_data="choose_city"),
            InlineKeyboardButton(
                text="Clear all tasks", callback_data="clear_all_tasks"
            ),
        ]
    ]
)

city_keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                text=Provinces.Alicante.name, callback_data=Provinces.Alicante.name
            ),
            InlineKeyboardButton(
                text=Provinces.Murcia.name, callback_data=Provinces.Murcia.name
            ),
        ]
    ]
)

country_chunks = [COUNTRIES[i : i + 5] for i in range(0, len(COUNTRIES), 5)]

countries_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=country, callback_data=country) for country in chunk]
        for chunk in country_chunks
    ]
)


def find(iterable, predicate):
    return next((item for item in iterable if predicate(item)), None)


async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass


async def clear_all_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass


async def run_polling_with_predata(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    try:
        with open("data.json", "r") as f:
            data = json.load(f)

            data = Data(**data)
            await update.effective_message.reply_text("Bot started!")
            await WithData.run_polling_with_data(
                update=update,
                nie=data.doc_value,
                nameSurname=data.name,
                yearOfBirth=data.year_of_birth,
                country=data.country,
            )
    except FileNotFoundError:
        await update.effective_message.reply_text(
            "data.json not found. Please, create it"
        )


async def clear_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    for task in asyncio.all_tasks():
        if task.get("catch_cita"):
            task["catch_cita"].cancel()

            break
    if user_id in task:
        task = task.pop(user_id)
        task.cancel()
        await update.effective_message.reply_text("Task cleared")

    else:
        await update.effective_message.reply_text("No task found")


async def run_polling(
    update: Update,
    data: Task,
):
    while True:
        try:
            for province in data.provinces:
                logging.info("Watching your province {}.".format(province))
                result = await Watcher().watch_citas(
                    province,
                    data.nie,
                    data.nameSurname,
                    data.yearOfBirth,
                    data.country,
                    data.tramite,
                )

                found = bool(result.get("found"))
                ref = result.get("ref")
                message = result.get("message")

                if found and ref:
                    await update.effective_message.reply_text(
                        f"found: {found}, message: {message}"
                    )
                    await update.effective_message.reply_text(
                        "Quick reference for request cita: {}".format(ref)
                    )
                    return

                logging.info(f"Waiting for retry {interval_store.state()} seconds")
                await asyncio.sleep(interval_store.state())

        except KeyboardInterrupt:
            logging.info("Polling interrupted")
            break

        except Exception:
            logging.error("Error while running polling", exc_info=True)
            break


class WithData:
    @staticmethod
    async def ask_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(
            "Choose city", reply_markup=city_keyboard
        )

        return LVL1_ROUTES

    @staticmethod
    async def run_polling_with_data(
        update: Update,
        nie: str,
        nameSurname: str,
        yearOfBirth: str,
        country: str,
        province: str = "",
    ):
        query = update.callback_query
        await query.answer()

        province = query.data

        province_store.dispatch(
            ActionType(type=ProvinceAction.ADD_PROVINCE, payload=province)
        )

        task = Task(
            tramite=Tramites.RENOVACION.value,
            nie=nie,
            nameSurname=nameSurname,
            yearOfBirth=yearOfBirth,
            country=country,
            provinces=province_store.state(),
        )

        catch_cita = find(
            asyncio.tasks.all_tasks(), lambda x: x.get_name() == "catch_cita"
        )
        try:
            if catch_cita:
                catch_cita.cancel()

                asyncio.create_task(
                    run_polling(update=update, data=task), name="catch_cita"
                )
            else:
                asyncio.create_task(
                    run_polling(update=update, data=task), name="catch_cita"
                )

        except KeyboardInterrupt:
            logging.info("Polling interrupted")

        except Exception:
            logging.error("Error while running polling", exc_info=True)
