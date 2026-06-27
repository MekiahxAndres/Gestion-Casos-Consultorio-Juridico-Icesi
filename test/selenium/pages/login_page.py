from __future__ import annotations

from selenium.webdriver.common.by import By

from test.selenium.pages.base_page import BasePage


class LoginPage(BasePage):
    DOCUMENT_INPUT = (By.NAME, "document_number")
    PASSWORD_INPUT = (By.NAME, "password")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")

    def open_login(self):
        self.open("/login/")
        self.visible(self.DOCUMENT_INPUT)

    def login(self, document: str, password: str):
        self.open_login()
        self.type_text(self.DOCUMENT_INPUT, document)
        self.type_text(self.PASSWORD_INPUT, password)
        self.click(self.SUBMIT_BUTTON)

    def assert_login_loaded(self):
        self.assert_any_text(["Inicia sesion", "Inicia sesión"])
        self.visible(self.DOCUMENT_INPUT)
        self.visible(self.PASSWORD_INPUT)

    def assert_invalid_credentials_message(self):
        self.assert_any_text([
            "Documento o contraseña incorrectos",
            "Documento o contrasena incorrectos",
            "Credenciales invalidas",
            "incorrectos",
        ])
