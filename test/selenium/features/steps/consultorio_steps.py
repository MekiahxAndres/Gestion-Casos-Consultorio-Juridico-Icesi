from __future__ import annotations

from behave import given, then, when

from test.selenium.config import BASE_URL, credentials_for
from test.selenium.pages.base_page import BasePage
from test.selenium.pages.login_page import LoginPage
from test.selenium.pages.navigation_page import NavigationPage


def base_page(context) -> BasePage:
    return BasePage(context.driver)


def login_page(context) -> LoginPage:
    return LoginPage(context.driver)


def nav_page(context) -> NavigationPage:
    return NavigationPage(context.driver)


@given("que abro la aplicacion desplegada")
def step_open_deployed_app(context):
    login_page(context).open_login()


@given('inicio sesion como "{role}"')
def step_login_as_role(context, role):
    credentials = credentials_for(role)
    login_page(context).login(credentials["document"], credentials["password"])
    base_page(context).assert_no_server_error()


@when('ingreso credenciales invalidas con documento "{document}" y clave "{password}"')
def step_invalid_credentials(context, document, password):
    login_page(context).login(document, password)


@when('abro la ruta "{path}"')
def step_open_path(context, path):
    nav_page(context).open(path)


@when('abro directamente "{path}"')
def step_open_direct_path(context, path):
    nav_page(context).open(path)


@when('selecciono el acceso "{text}"')
def step_click_access(context, text):
    nav_page(context).click_link_by_text(text)


@then('debo ver el login institucional')
def step_assert_login(context):
    login_page(context).assert_login_loaded()


@then("debo permanecer en el login con mensaje de error")
def step_assert_invalid_login(context):
    nav_page(context).assert_current_url_contains("/login/")
    login_page(context).assert_invalid_credentials_message()


@then('debo ver el texto "{text}"')
def step_assert_text(context, text):
    base_page(context).assert_text(text)


@then("debo ver estos textos")
def step_assert_table_texts(context):
    expected_values = [row["texto"] for row in context.table]
    for text in expected_values:
        base_page(context).assert_text(text)


@then("debo ver alguno de estos textos")
def step_assert_any_table_texts(context):
    expected_values = [row["texto"] for row in context.table]
    base_page(context).assert_any_text(expected_values)


@then('la url debe contener "{path}"')
def step_assert_url_contains(context, path):
    nav_page(context).assert_current_url_contains(path)


@then("la pagina no debe mostrar error de servidor")
def step_no_server_error(context):
    base_page(context).assert_no_server_error()


@then('guardo evidencia con nombre "{name}"')
def step_save_named_screenshot(context, name):
    safe_name = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in name)
    path = context.screenshot_dir / f"{safe_name}.png"
    context.driver.save_screenshot(str(path))


@then("debo estar autenticado en el sistema")
def step_assert_authenticated(context):
    assert "/login/" not in context.driver.current_url, (
        f"El usuario no salio del login. URL actual: {context.driver.current_url}"
    )
    base_page(context).assert_no_server_error()


@then("debo estar en el despliegue final")
def step_assert_base_url(context):
    assert context.driver.current_url.startswith(BASE_URL), context.driver.current_url
