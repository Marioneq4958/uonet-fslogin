import requests
from bs4 import BeautifulSoup
import re

class FSLogin():
    def __init__(self, scheme: str, symbol: str, host: str):
        self.scheme = scheme
        self.symbol = symbol
        self.host = host
        self.session = requests.Session()

    def get_login_endpoint_url(self, symbol: str = "Default") -> str:
        return f"{self.scheme}://uonetplus.{self.host}/{symbol}/LoginEndpoint.aspx"

    def get_hidden_inputs(self, form) -> dict:
        hidden_inputs: dict = {}
        hidden_input_tags: list = form.select('input[type="hidden"]')
        for hidden_input_tag in hidden_input_tags:
            hidden_inputs[hidden_input_tag["name"]] = hidden_input_tag["value"]
        return hidden_inputs

    def get_credentials_inputs(self, form):
        if form.select_one('input[type="text"]'):
            username_input: str = form.select_one('input[type="text"]')["name"]
        else:
            username_input: str = form.select_one('input[type="email"]')["name"]
        password_input: str = form.select_one('input[type="password"]')["name"]
        return username_input, password_input

    def get_form_data(self, username: str, password: str):
        try:
            response = self.session.get(self.get_login_endpoint_url(self.symbol))
        except:
            raise Exception("Failed fetching login page")
        soup = BeautifulSoup(response.text, "html.parser")
        form = soup.select_one("form")
        data = self.get_hidden_inputs(form)
        username_input, password_input = self.get_credentials_inputs(form)
        data[username_input] = username
        data[password_input] = password
        url = response.url
        return data, url

    def send_credentials(self, data: dict, url: str):
        try:
            response = self.session.post(url=url, data=data)
        except:
            raise Exception("Failed sending credentials")
        return response

    def login(self, username: str, password: str) -> dict:
        data, url = self.get_form_data(username, password)
        credentials_response = self.send_credentials(data, url)
        soup = BeautifulSoup(credentials_response.text, "html.parser")
        if soup.select(".ErrorMessage, #ErrorTextLabel, #loginArea #errorText"):
            raise Exception("Username or password is incorrect")
        certificate = self.get_hidden_inputs(soup.select_one("form"))
        symbols: list = self.extract_symbols(certificate["wresult"])
        if not self.symbol in symbols:
            symbols.append(self.symbol)
        sessions: dict = {}
        for symbol in symbols:
            certificate_response = self.send_certificate(certificate, symbol)
            if not "nie został zarejestrowany" in certificate_response.text and not "Brak uprawnień" in certificate_response.text:
                sessions[symbol] = self.session.cookies.get_dict()
        return sessions

    def send_certificate(self, certificate: dict, symbol: str = "Default") -> requests.models.Response:
        try:
            response = self.session.post(url=self.get_login_endpoint_url(symbol), data=certificate)
        except:
            raise Exception("Failed sending certificate")
        return response

    def extract_symbols(self, wresult: str) -> list[str]:
        # drobotk/vulcan-sdk-py <3
        try:
            soup = BeautifulSoup(wresult.replace(":", ""), "lxml")
            tags: list = soup.select(
                'samlAttribute[AttributeName$="Instance"] samlAttributeValue'
            )
            symbols: list[str] = [tag.text.strip() for tag in tags]
            symbols = [s for s in symbols if re.compile(r"[a-zA-Z0-9]*").fullmatch(s)]
        except:
            raise Exception("Failed extracting symbols")
        return symbols

    def log_out(self, session_cookies: dict, symbol = None):
        try:
            self.session.get(
                url=self.get_login_endpoint_url(self.get_login_endpoint_url(symbol)),
                params={"logout": "true"},
                cookies=session_cookies,
            )
        except:
            raise Exception("Failed sending request to log-out")