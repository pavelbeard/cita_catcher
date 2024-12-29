import asyncio
import logging
import platform
import random
from functools import wraps

import distro
from fake_useragent import UserAgent
from helium import S, get_driver, kill_browser, set_driver, wait_until
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver as Chrome
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import OperationSystemManager

from citabot_actions.reducer_types import IntervalAction
from citabot_actions.store import interval_store
from citabot_utils.exceptions import RequestRejected, TooManyRequests
from citabot_utils.types import Intervals
from reducer import ActionType


def find(iterable, predicate):
    return next((item for item in iterable if predicate(item)), None)


def get_os():
    os_info = distro.lsb_release_info()

    if os_info.get("distributor_id") is None:
        os_info["distributor_id"] = platform.system()

    if os_info.get("codename") is None:
        os_info["codename"] = ""

    return {
        "distributor_id": os_info.get("distributor_id"),
        "codename": os_info.get("codename"),
    }


def random_number(start=4.9, end=10.0):
    # between start=4.9 and end=10.0 seconds by default
    return random.uniform(start, end)


async def implicitly_wait(seconds=0):
    if seconds == 0:
        seconds = random_number(start=2, end=3)
    logging.info(f"Implicitly wait {seconds} seconds")
    await asyncio.sleep(seconds)


async def implicitly_random_wait(start=2, end=3):
    seconds = random_number(start=start, end=end)
    logging.info(f"Implicitly wait {seconds} seconds")
    await asyncio.sleep(seconds)


class driver_context:
    def __init__(self, headless=False, proxy=False):
        self.driver = None
        self.headless = headless
        self.proxy = proxy

    def _build_driver(self):
        if self.driver is None:
            if platform.machine() in ["arm64", "aarch64"]:
                ##### LINUX AARCH64 #####
                if (
                    get_os()["distributor_id"] == "Ubuntu"
                    and get_os()["codename"] == "bionic"
                ):
                    service = ChromeService(executable_path="/usr/bin/chromedriver")
                ##### MACOS ARM64 #####
                elif get_os()["distributor_id"] == "Darwin":
                    manager = ChromeDriverManager(
                        os_system_manager=OperationSystemManager(os_type="mac-arm64")
                    )
                    service = ChromeService(manager.install())
            elif platform.machine() in ["x86_64", "amd64"]:
                ##### LINUX X86_64 #####
                manager = ChromeDriverManager(
                    os_system_manager=OperationSystemManager(os_type="linux-x86_64")
                )
                service = ChromeService(manager.install())

            options = ChromeOptions()

            # HEADLESS MODE
            if self.headless:
                options.add_argument("--headless")
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-setuid-sandbox")

            # ROTATE PROXY
            if self.proxy:
                with open("proxies", "r") as f:
                    proxies = f.read().splitlines()

                proxy = random.choice(proxies)
                options.add_argument("--proxy-server={}".format(proxy))

            # DISABLE DETECTION
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--incognito")
            options.add_experimental_option("useAutomationExtension", False)
            options.add_experimental_option(
                "excludeSwitches", ["enable-automation", "enable-logging"]
            )

            # USER AGENT
            user_agent = UserAgent()
            random_user_agent = user_agent.random

            options.add_argument(f"user-agent={random_user_agent}")

            driver = Chrome(
                service=service,
                options=options,
            )

            driver.maximize_window()

            return driver

    def __enter__(self):
        try:
            driver = self._build_driver()
            set_driver(driver)
            return get_driver()
        except Exception:
            logging.error("Error while building driver", exc_info=True)

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            kill_browser()
        except Exception:
            logging.error("Error while killing browser", exc_info=True)


def driver_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            await implicitly_random_wait(start=1.5, end=3.7)

            try:
                wait_until(lambda x: S("Too Many Requests").exists)
                raise TooManyRequests("Too many requests")

            except Exception:
                pass

            try:
                wait_until(
                    lambda x: S(
                        "The requested URL was rejected. Please consult with your administrador."
                    ).exists
                )
                raise RequestRejected("Request rejected")
            except Exception:
                pass

            return await func(*args, **kwargs)

        except NoSuchElementException:
            logging.error("[500] NoSuchElementException", exc_info=True)

        except TimeoutException:
            logging.error("[500] TimeoutException", exc_info=True)

        except WebDriverException:
            logging.error("[500] WebDriverException", exc_info=True)

        except TooManyRequests:
            logging.error("[500] Too many requests")
            interval_store.dispatch(
                ActionType(type=IntervalAction.ADD_TIME, payload=Intervals.I_3M.value)
            )
            raise

        except RequestRejected:
            logging.error("[500] Request rejected")
            interval_store.dispatch(
                ActionType(
                    type=IntervalAction.SET_INTERVAL, payload=Intervals.I_3M.value
                )
            )
            raise

        except Exception:
            logging.error("[500] Exception", exc_info=True)
            raise

    return wrapper
