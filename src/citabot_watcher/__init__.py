import logging

from helium import wait_until, write, select, click, Button, S
from selenium.webdriver.chrome.webdriver import WebDriver as Chrome

from citabot_utils.main import driver_context, driver_decorator
from citabot_utils.types import Provinces

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Watcher:
    def _if_solicitar_cita_exists(self, province: Provinces):
        try:
            wait_until(lambda x: S("#btnConsultar").exists)
            return True
        except Exception:
            return False

    def _if_salir_exists(self, province: Provinces):
        try:
            wait_until(Button("Salir").exists)
            return True
        except Exception:
            return False

    def if_aceptar_exists(self, province: Provinces):
        try:
            wait_until(Button("Aceptar").exists)
            return True
        except Exception:
            return False

    @driver_decorator
    async def _open_extranjeria(self, driver: Chrome) -> None:
        driver.get("https://icp.administracionelectronica.gob.es/icpplus/index.html/")
        logger.info("[1/6] Extranjeria page loaded")

    @driver_decorator
    async def _select_province(self, driver: Chrome, province: Provinces) -> None:
        wait_until(lambda x: S("PROVINCIAS DISPONIBLES").exists)
        select("PROVINCIAS DISPONIBLES", province)

        click(Button("Aceptar"))
        logger.info("[2/6] City accepted")

    @driver_decorator
    async def _accept_cookie(self, driver: Chrome) -> None:
        try:
            wait_until(lambda: S("#cookie_action_close_header").exists)
            click(S("#cookie_action_close_header"))

            # driver.delete_all_cookies()
            # driver.execute_script("window.localStorage.clear();")
            # driver.execute_script("window.sessionStorage.clear();")

            logger.info("[3/6] Cookie accepted")
        except Exception:
            logger.info("[3/6] Cookies not accepted")
            raise

    @driver_decorator
    async def _select_tramite(self, driver: Chrome, tramite: str) -> None:
        wait_until(lambda x: S("TRÁMITES POLICÍA NACIONAL").exists)
        select("TRÁMITES POLICÍA NACIONAL", tramite)

        wait_until(Button("Aceptar").exists)

        click(Button("Aceptar"))

        logger.info("[4/6] Tramite selected")

    @driver_decorator
    async def _interchange_page(self, driver: Chrome) -> None:
        wait_until(Button("Entrar").exists)

        click("Entrar")

        logger.info("[5/6] Page passed")

    @driver_decorator
    async def _personal_data(
        self, driver: Chrome, nie: str, nameSurname: str, yearOfBirth: str, country: str
    ) -> None:
        wait_until(lambda x: S(lambda x: "#txtIdCitado").exists)

        write(nie, into="N.I.E.")
        write(nameSurname, into="Nombre y apellidos")
        write(yearOfBirth, into="Año de nacimiento")

        select("País de nacionalidad", country)

        click(Button("Aceptar"))

        logger.info("[6/6] Data send")
        logger.info("[Step 2 1/2] Cita requested")

    @driver_decorator
    async def _check_accessability(self, driver: Chrome, province: Provinces) -> dict:
        if self._if_salir_exists(province=province):
            return {
                "found": False,
                "message": f"Cita for {province} has not found... 😔",
            }

        if self.if_aceptar_exists(province=province):
            return {
                "found": False,
                "message": f"Cita for {province} has not found... 😔",
            }

        if self._if_solicitar_cita_exists(province=province):
            return {
                "found": True,
                "message": f"Cita for {province} has found 🥳",
                "ref": "https://icp.administracionelectronica.gob.es/icpco/citar?p={}/acInfo?{}={}/".format(
                    province.value, "tramiteGrupo[1]", "4067"
                ),
            }

    async def watch_citas(
        self, province, nie, nameSurname, yearOfBirth, country, tramite
    ):
        try:
            ##################

            with driver_context(headless=False, proxy=False) as driver:
                await self._open_extranjeria(driver=driver)
                await self._select_province(driver=driver, province=province)
                await self._accept_cookie(driver=driver)
                await self._select_tramite(driver=driver, tramite=tramite)
                await self._interchange_page(driver=driver)
                await self._personal_data(
                    driver=driver,
                    nie=nie,
                    nameSurname=nameSurname,
                    yearOfBirth=yearOfBirth,
                    country=country,
                )
                result = await self._check_accessability(
                    driver=driver, province=province
                )

                if result:
                    return result

                else:
                    return {
                        "found": False,
                        "message": "Something went wrong... 😔",
                    }

        except Exception as e:
            logger.error(f"[Exception]: {e}")
            return {"found": False, "message": str(e)}
