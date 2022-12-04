import re
from bs4 import BeautifulSoup
from uonet_fslogin.errors import InvalidLoginFormException, NotRegisteredException, \
    NoPermissionsException, IncorrectCredentialsException

NOT_REGISTERED_ERROR_TEXT: str = "nie został zarejestrowany"
NO_PERMISSIONS_ERROR_TEXT: str = "Brak uprawnień"

INCORRECT_CREDENTIALS_ERROR_TAGS: str = ".ErrorMessage, #ErrorTextLabel, #loginArea #errorText"

ATTRIBUTES: dict[str, str] = {
    "name": "username",
    "emailaddress": "primary_email",
    "SecondaryEmail": "secondary_email",
    "PESEL": "pesel",
    "givenname": "name",
    "surname": "last_name",
    "SessionID": "session_id",
    "authtype": "auth_type",
    "UserInstance": "symbols",
    "UPN": "upn",
    "ImmutableID": "immutable_id",
    "accountauthorization": "account_authorization",
    "daystochange": "days_to_change_password"
}


def get_login_endpoint_url(scheme: str, host: str, symbol: str) -> str:
    return f"{scheme}://uonetplus.{host}/{symbol}/LoginEndpoint.aspx"


def check_errors(text: str):
    if NOT_REGISTERED_ERROR_TEXT in text:
        raise NotRegisteredException()
    if NO_PERMISSIONS_ERROR_TEXT in text:
        raise NoPermissionsException()

    soup = BeautifulSoup(text, "html.parser")
    if soup.select(INCORRECT_CREDENTIALS_ERROR_TAGS):
        raise IncorrectCredentialsException()


def get_login_prefix(text: str) -> str:
    login_prefix: str = re.compile(
        r"var userNameValue = '([A-Z]+?)\\\\' \+ userName\.value;").search(text)
    return login_prefix


def get_credentials_inputs(form) -> tuple[str, str]:
    username_input: str = form.select_one(
        'input[type="text"], input[type="email"]')
    password_input: str = form.select_one(
        'input[type="password"]')
    if not username_input or not password_input:
        raise InvalidLoginFormException()
    return username_input, password_input


def get_hidden_inputs(form) -> dict[str, str]:
    hidden_inputs: dict[str, str] = {}
    hidden_input_tags: list = form.select('input[type="hidden"]')
    for hidden_input_tag in hidden_input_tags:
        hidden_inputs[hidden_input_tag["name"]] = hidden_input_tag["value"]
    return hidden_inputs


def get_attributes_from_cert(wresult: str) -> dict:
    # drobotk/vulcan-sdk-py <3
    attributes: dict[str, str | list[str]] = {}
    soup = BeautifulSoup(wresult.replace(":", ""), "html.parser")
    attribute_tags: list = soup.select(
        "samlAttributeStatement samlAttribute"
    )
    for attribute_tag in attribute_tags:
        if attribute_tag["attributename"] in ATTRIBUTES:
            name = ATTRIBUTES[attribute_tag["attributename"]]
        else:
            name = attribute_tag["attributename"]
        attribute_value_tags: list = attribute_tag.select(
            "samlattributevalue")
        attribute_values: list = []
        for attribute_value_tag in attribute_value_tags:
            attribute_values.append(attribute_value_tag.text)
        if len(attribute_values) > 1:
            attributes[name] = attribute_values
        else:
            attributes[name] = attribute_values[0]
    return attributes
