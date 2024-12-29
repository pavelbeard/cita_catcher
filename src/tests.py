import time
from unittest import TestCase

import helium
from fake_useragent import UserAgent

from citabot_actions.reducer import interval_reducer, province_reducer
from citabot_actions.reducer_types import IntervalAction, ProvinceAction
from reducer import create_store
from reducer.types import ActionType


class TestHeliumCustomDriver(TestCase):
    def doCleanups(self):
        helium.kill_browser()

        return super().doCleanups()

    def test_set_get_driver(self):
        from selenium.webdriver.chrome.webdriver import WebDriver as Chrome

        helium.set_driver(Chrome())

        driver = helium.get_driver()
        assert driver is not None

        print(driver)

    def test_clickable(self):
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.chrome.service import Service as ChromeService
        from selenium.webdriver.chrome.webdriver import WebDriver as Chrome
        from webdriver_manager.chrome import ChromeDriverManager

        # DISABLE DETECTION
        options = ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--incognito")
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation", "enable-logging"]
        )

        # USER AGENT
        user_agent = UserAgent()
        rand_ua = user_agent.random

        options.add_argument(f"user-agent={rand_ua}")

        # SERVICE

        service = ChromeService(ChromeDriverManager().install())

        helium.set_driver(
            Chrome(
                service=service,
                options=options,
            )
        )

        driver = helium.get_driver()

        driver.get("https://icp.administracionelectronica.gob.es/icpplus/index.html/")

        helium.wait_until(lambda x: helium.S("title"))

        helium.select("PROVINCIAS DISPONIBLES", "Alicante")

        helium.click(helium.Button("Aceptar"))

        time.sleep(5)


class TestReducer(TestCase):
    def test_create_store(self):
        from citabot_utils.types import Intervals

        interval_store = create_store(interval_reducer, init_arg=Intervals.I_1M.value)
        assert interval_store.state() == Intervals.I_1M.value

        # change interval
        interval_store.dispatch(
            ActionType(
                type=IntervalAction.CHANGE_INTERVAL, payload=Intervals.I_3M.value
            )
        )

        # state is old
        assert interval_store.state() == Intervals.I_3M.value

        province_store = create_store(province_reducer, init_arg=set())
        assert province_store.state() == set()

        # add province
        province_store.dispatch(
            ActionType(type=ProvinceAction.ADD_PROVINCE, payload="Murcia")
        )

        assert province_store.state() == {"Murcia"}

        # add province
        province_store.dispatch(
            ActionType(type=ProvinceAction.ADD_PROVINCE, payload="Alicante")
        )

        assert province_store.state() == {"Murcia", "Alicante"}
