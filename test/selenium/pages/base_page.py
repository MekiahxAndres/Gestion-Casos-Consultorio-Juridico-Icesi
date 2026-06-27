from __future__ import annotations

import unicodedata

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from test.selenium.config import BASE_URL, TIMEOUT


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value or "")
    without_marks = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return " ".join(without_marks.lower().split())


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, TIMEOUT)

    def open(self, path: str = "/"):
        if path.startswith("http"):
            self.driver.get(path)
        else:
            self.driver.get(f"{BASE_URL}{path}")

    def find(self, locator: tuple[str, str]):
        return self.wait.until(EC.presence_of_element_located(locator))

    def visible(self, locator: tuple[str, str]):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def clickable(self, locator: tuple[str, str]):
        return self.wait.until(EC.element_to_be_clickable(locator))

    def click(self, locator: tuple[str, str]):
        self.clickable(locator).click()

    def type_text(self, locator: tuple[str, str], text: str):
        element = self.visible(locator)
        element.clear()
        element.send_keys(text)

    def body_text(self) -> str:
        last_error = None
        for _ in range(3):
            try:
                return self.find((By.TAG_NAME, "body")).text
            except StaleElementReferenceException as exc:
                last_error = exc
        raise last_error

    def normalized_body(self) -> str:
        return normalize_text(self.body_text())

    def has_text(self, expected: str) -> bool:
        return normalize_text(expected) in self.normalized_body()

    def assert_text(self, expected: str):
        assert self.has_text(expected), f"No se encontro el texto esperado: {expected}"

    def assert_any_text(self, expected_values: list[str]):
        body = self.normalized_body()
        normalized_values = [normalize_text(value) for value in expected_values]
        assert any(value in body for value in normalized_values), (
            f"No se encontro ninguno de estos textos: {expected_values}"
        )

    def assert_no_server_error(self):
        body = self.normalized_body()
        assert "server error" not in body
        assert "error 500" not in body
        assert "traceback" not in body
