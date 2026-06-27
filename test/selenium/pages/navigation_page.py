from __future__ import annotations

from selenium.webdriver.common.by import By

from test.selenium.pages.base_page import BasePage


class NavigationPage(BasePage):
    def open_path_and_assert(self, path: str, expected_texts: list[str]):
        self.open(path)
        self.assert_no_server_error()
        self.assert_any_text(expected_texts)

    def click_link_by_text(self, text: str):
        locator = (
            By.XPATH,
            f"//a[contains(normalize-space(.), '{text}')] | //button[contains(normalize-space(.), '{text}')]",
        )
        self.click(locator)

    def assert_current_url_contains(self, expected: str):
        assert expected in self.driver.current_url, (
            f"La URL actual '{self.driver.current_url}' no contiene '{expected}'"
        )
