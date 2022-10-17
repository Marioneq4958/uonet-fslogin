import requests
from bs4 import BeautifulSoup
import re

DEFAULT_SYMBOL: str = "default"
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

class UonetFSLogin:
    def __init__(
            self, username: str, password: str, scheme: str, host: str, symbols: list[str],
            default_symbol: str = DEFAULT_SYMBOL):
        self.username = username
        self.password = password
        self.scheme = scheme
        self.symbols = symbols
        self.default_symbol = default_symbol
        self.host = host
        self.session = requests.Session()

    def get_login_endpoint_url(self, symbol: str) -> str:
        return f"{self.scheme}://uonetplus.{self.host}/{symbol if symbol else self.default_symbol}/LoginEndpoint.aspx"

    def get_hidden_inputs(self, form) -> dict:
        hidden_inputs: dict = {}
        hidden_input_tags: list = form.select('input[type="hidden"]')
        for hidden_input_tag in hidden_input_tags:
            hidden_inputs[hidden_input_tag["name"]] = hidden_input_tag["value"]
        return hidden_inputs

    def get_credentials_inputs(self, form) -> tuple[str, str]:
        try:
            if form.select_one('input[type="text"]'):
                username_input: str = form.select_one('input[type="text"]')["name"]
            else:
                username_input: str = form.select_one('input[type="email"]')["name"]
            password_input: str = form.select_one('input[type="password"]')["name"]
        except:
            raise Exception("Failed searching credentials inputs")
        return username_input, password_input

    def get_form_data(self) -> tuple[dict, str]:
        try:
            response = self.session.get(self.get_login_endpoint_url(self.default_symbol))
        except:
            raise Exception("Failed fetching login page")
        soup = BeautifulSoup(response.text, "html.parser")
        form = soup.select_one("form")
        data = self.get_hidden_inputs(form)
        username_input, password_input = self.get_credentials_inputs(form)
        data[username_input] = self.username
        data[password_input] = self.password
        url = response.url
        return data, url

    def send_credentials(self):
        data, url = self.get_form_data()
        try:
            response = self.session.post(url=url, data=data)
        except:
            raise Exception("Failed sending credentials")
        return response

    def log_in(self) -> tuple[dict, dict]:
        sessions: dict = {}
        credentials_response = self.send_credentials()
        soup = BeautifulSoup(credentials_response.text, "html.parser")
        if soup.select(".ErrorMessage, #ErrorTextLabel, #loginArea #errorText"):
            raise Exception("Username or password is incorrect")

        form = soup.select_one('form[name="hiddenform"]')
        cert: dict[str, str] = self.get_hidden_inputs(soup.select_one('form'))
        user_data: dict = self.get_attributes_from_cert(cert["wresult"])
        try:
            symbols: list[str] = user_data["symbols"]
        except:
            symbols: list[str] = []
        for symbol in self.symbols:
            symbols.append(symbol)
        try:
            symbols.remove(DEFAULT_SYMBOL)
        except:
            pass
        for symbol in symbols:
            url: str = form["action"].replace(self.default_symbol, symbol)
            cert_response = self.send_cert(cert, url)
            soup = BeautifulSoup(cert_response.text, "html.parser")
            second_form = soup.select_one('form[name="hiddenform"]')
            if not "nie został zarejestrowany" in cert_response.text:
                if second_form:
                    second_cert: dict[str, str] = self.get_hidden_inputs(second_form)
                    url: str = second_form["action"].replace(self.default_symbol, symbol)
                    cert_response = self.send_cert(second_cert, url)
                if not "Brak uprawnień" in cert_response.text:
                    sessions[symbol] = self.session.cookies.get_dict()
        return (sessions, user_data)

    def send_cert(self, cert: dict, url: str):
        try:
            response = self.session.post(url=url, data=cert)
        except:
            raise Exception("Failed sending certificate")
        return response

    def get_attributes_from_cert(self, wresult: str) -> dict:
        # drobotk/vulcan-sdk-py <3
        attributes: dict = {}
        try:
            soup = BeautifulSoup(wresult.replace(":", ""), "lxml")
            attribute_tags: list = soup.select(
                "samlAttributeStatement samlAttribute"
            )
            for attribute_tag in attribute_tags:
                try:
                    name = ATTRIBUTES[attribute_tag["attributename"]]
                except:
                    name = attribute_tag["attributename"]
                attribute_value_tags: list = attribute_tag.select("samlattributevalue")
                attribute_values: list = []
                for attribute_value_tag in attribute_value_tags:
                    attribute_values.append(attribute_value_tag.text)
                if len(attribute_values) > 1:
                    attributes[name] = attribute_values
                else:
                    attributes[name] = attribute_values[0]
            return attributes
        except:
            raise Exception("Failed getting attributes from cert")

    def log_out(self, sessions: dict):
        for symbol in sessions:
            try:
                self.session.get(
                    url=self.get_login_endpoint_url(self.get_login_endpoint_url(symbol)),
                    params={"logout": "true"},
                    cookies=sessions[symbol],
                )
            except:
                raise Exception("Failed sending request to log-out")
