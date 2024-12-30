import asyncio
import json
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from citabot_actions.reducer_types import ProvinceAction
from citabot_actions.store import interval_store, province_store
from citabot_utils.constants import COUNTRIES, LVL0_ROUTES, LVL1_ROUTES, LVL2_ROUTES
from citabot_utils.main import find
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

keyboard_lvl1 = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(text="Show tasks", callback_data="show_tasks"),
            InlineKeyboardButton(text="Clear task", callback_data="clear_task"),
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


async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    tasks = asyncio.tasks.all_tasks()
    found_tasks = []
    for province in province_store.state():
        province_task = find(tasks, lambda x: x.get_name() == province)
        if province_task:
            found_tasks.append(province)

    if len(found_tasks) == 0:
        await update.effective_message.reply_text("No tasks found")
        return LVL1_ROUTES

    await update.effective_message.reply_text(
        "Press the province for clear task. Task for provinces:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=province.capitalize(), callback_data=province
                    )
                    for province in found_tasks
                ]
            ]
        ),
    )

    return LVL2_ROUTES


async def clear_all_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    for province in province_store.state():
        province_task = find(
            asyncio.tasks.all_tasks(), lambda x: x.get_name() == province
        )

        if province_task:
            province_task.cancel()

    await update.effective_message.reply_text("All tasks cleared")

    return ConversationHandler.END


async def clear_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    province = query.data
    province_task = find(asyncio.tasks.all_tasks(), lambda x: x.get_name() == province)

    if province_task:
        province_task.cancel()
        await update.effective_message.reply_text(
            "Task for {} cleared".format(province)
        )
    else:
        await update.effective_message.reply_text(
            "No task for {} found".format(province)
        )

    return ConversationHandler.END


async def run_polling_with_predata(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()

    try:
        with open("data.json", "r") as f:
            data = json.load(f)

            data = Data(**data)
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

    return LVL1_ROUTES


async def run_polling(
    update: Update,
    data: Task,
):
    while True:
        try:
            logging.info("Watching your province {}.".format(data.province))
            result = await Watcher().watch_citas(
                data.province,
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
            elif not found:
                logging.info(f"[Unsuccessful] Message: {message}")

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
    async def choose_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(
            "Choose city", reply_markup=city_keyboard
        )

        return LVL0_ROUTES

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
            province=province,
        )

        province_task = find(
            asyncio.tasks.all_tasks(), lambda x: x.get_name() == province
        )

        try:
            if not province_task:
                asyncio.create_task(
                    run_polling(update=update, data=task), name=province
                )
                await update.effective_message.reply_text(
                    "Bot started for {}!".format(province), reply_markup=keyboard_lvl1
                )
            else:
                await update.effective_message.reply_text(
                    f"Task for {province} already exists"
                )

        except KeyboardInterrupt:
            logging.info("Polling interrupted")

        except Exception:
            logging.error("Error while running polling", exc_info=True)
