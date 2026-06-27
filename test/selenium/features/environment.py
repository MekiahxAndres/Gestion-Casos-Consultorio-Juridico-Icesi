from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from test.selenium.config import HEADLESS, REQUIRED_TAGS, SCREENSHOT_DIR, has_credentials


def before_all(context):
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    options = Options()
    options.add_argument("--window-size=1440,1000")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    if HEADLESS:
        options.add_argument("--headless=new")

    context.driver = webdriver.Chrome(options=options)
    context.driver.implicitly_wait(2)
    context.screenshot_dir = SCREENSHOT_DIR


def before_scenario(context, scenario):
    for tag in scenario.effective_tags:
        required_role = REQUIRED_TAGS.get(tag)
        if required_role and not has_credentials(required_role):
            scenario.skip(
                f"Faltan credenciales para rol {required_role}. "
                "Configurar variables CJ_* antes de ejecutar."
            )


def after_scenario(context, scenario):
    if scenario.status.name.lower() != "failed":
        return

    safe_name = "".join(
        char if char.isalnum() or char in ("-", "_") else "_"
        for char in scenario.name.lower()
    )[:90]
    status = scenario.status.name.lower()
    screenshot_path = context.screenshot_dir / f"{status}_{safe_name}.png"
    context.driver.save_screenshot(str(screenshot_path))


def after_all(context):
    context.driver.quit()
