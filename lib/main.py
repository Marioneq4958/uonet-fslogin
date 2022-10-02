import requests
from bs4 import BeautifulSoup
import re

DEFAULT_SYMBOL: str = "default"

class UonetFSLogin:
    def __init__(self, username: str, password: str, scheme: str, host: str, symbols: str):
        self.username = username
        self.password = password
        self.scheme = scheme
        self.symbols = symbols
        self.host = host
        self.session = requests.Session()

    def get_login_endpoint_url(self, symbol: str = DEFAULT_SYMBOL) -> str:
        return f"{self.scheme}://uonetplus.{self.host}/{symbol}/LoginEndpoint.aspx"

    def get_hidden_inputs(self, form) -> dict:
        hidden_inputs: dict = {}
        hidden_input_tags: list = form.select('input[type="hidden"]')
        for hidden_input_tag in hidden_input_tags:
            hidden_inputs[hidden_input_tag["name"]] = hidden_input_tag["value"]
        return hidden_inputs

    def get_credentials_inputs(self, form):
        try:
            if form.select_one('input[type="text"]'):
                username_input: str = form.select_one('input[type="text"]')["name"]
            else:
                username_input: str = form.select_one('input[type="email"]')["name"]
            password_input: str = form.select_one('input[type="password"]')["name"]
        except:
            raise Exception("Failed searching credentials inputs")
        return username_input, password_input

    def get_form_data(self):
        try:
            response = self.session.get(self.get_login_endpoint_url(DEFAULT_SYMBOL))
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

    def log_in(self):
        sessions = {}
        credentials_response = self.send_credentials()
        soup = BeautifulSoup(credentials_response.text, "html.parser")
        if soup.select(".ErrorMessage, #ErrorTextLabel, #loginArea #errorText"):
            raise Exception("Username or password is incorrect")

        form = soup.select_one('form[name="hiddenform"]')
        cert: dict[str, str] = self.get_hidden_inputs(soup.select_one('form'))
        symbols: list[str] = self.extract_symbols(cert["wresult"])
        for symbol in self.symbols:
            symbols.append(symbol)
        try:
            symbols.remove(DEFAULT_SYMBOL)
        except:
            pass
        for symbol in symbols:
            url: str = form["action"].replace(DEFAULT_SYMBOL, symbol)
            cert_response = self.send_cert(cert, url)
            soup = BeautifulSoup(cert_response.text, "html.parser")
            second_form = soup.select_one('form[name="hiddenform"]')
            print(cert_response.text)
            if not "nie został zarejestrowany" in cert_response.text:
                if second_form:
                    second_cert: dict[str, str] = self.get_hidden_inputs(second_form)
                    url: str = second_form["action"].replace(self.symbol, symbol)
                    cert_response = self.send_cert(second_cert, url)
                if not "Brak uprawnień" in cert_response.text:
                    sessions[symbol] = self.session.cookies.get_dict()
        return sessions

    def send_cert(self, cert: dict, url: str):
        try:
            response = self.session.post(url=url, data=cert)
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

    def log_out(self, symbol: str, session_cookies: dict[str, str]):
        try:
            self.session.get(
                url=self.get_login_endpoint_url(self.get_login_endpoint_url(symbol)),
                params={"logout": "true"},
                cookies=session_cookies,
            )
        except:
            raise Exception("Failed sending request to log-out")