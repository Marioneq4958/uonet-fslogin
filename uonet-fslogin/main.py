from typing import Union
from bs4 import BeautifulSoup
import re
import aiohttp
from uonet_fslogin.errors import *
from uonet_fslogin.utils import *
from logging import getLogger
import logging

DEFAULT_SYMBOL: str = "default"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s | %(message)s"
)
class UonetFSLogin:
    def __init__(self, scheme: str, host: str):
        self.scheme = scheme
        self.host = host
        self.session = aiohttp.ClientSession()
        self._log = getLogger(__name__)

    async def send_request(self, url: str, method: str, data: dict = None, **kwargs) -> tuple[str, str]:
        try:
            async with self.session.request(method=method, url=url, data=data, **kwargs) as response:
                for r in response.history:
                    self._log.debug(f"[{r.status}] {r.method} {r.url}")
                self._log.debug(f"[{response.status}] {response.method} {response.url}")

                text: str = await response.text()
                return text, response.url, response.status
        except:
            raise FailedRequestException()

    async def get_login_form_data(self, username: str, password: str, default_symbol: str) -> tuple[
        dict[str, str], str]:
        text, url, status = await self.send_request(get_login_endpoint_url(self.scheme, self.host, default_symbol), "GET")
        bs = BeautifulSoup(text, "html.parser")
        login_form = bs.select_one("form")
        data: dict[str, str] = get_hidden_inputs(login_form)
        username_input, password_input = get_credentials_inputs(login_form)
        prefix = get_login_prefix(text)
        data[username_input["name"]] = rf"{prefix}\{username}" if prefix else username
        data[password_input["name"]] = password
        return data, url

    async def log_in(self, username: str, password: str, default_symbol: str = DEFAULT_SYMBOL,
                     symbols: list[str] = []) -> tuple[dict, dict]:
        sessions: dict[str, dict[str, str]] = {}
        data, url = await self.get_login_form_data(username, password, default_symbol)
        text, url, status = await self.send_request(url, "POST", data)
        check_errors(text)
        bs = BeautifulSoup(text, "html.parser")
        form = bs.select_one('form[name="hiddenform"]')
        cert_data: dict[str, str] = get_hidden_inputs(bs.select_one('form'))
        user_data: dict = get_attributes_from_cert(cert_data["wresult"])
        try:
            for symbol in user_data["symbols"]:
                symbols.append(symbol)
        except:
            pass
        try:
            symbols.remove(DEFAULT_SYMBOL)
        except:
            pass
        for symbol in symbols:
            url: str = form["action"].replace(default_symbol, symbol)
            text, url, status = await self.send_request(url, "POST", cert_data)
            if status != 200:
                continue
            try:
                check_errors(text)
            except:
                continue
            bs = BeautifulSoup(text, "html.parser")
            if bs.select_one('form[name="hiddenform"]'):
                form = bs.select_one('form[name="hiddenform"]')
                cert_data: dict[str, str] = get_hidden_inputs(
                    form)
                url: str = second_form["action"].replace(
                    default_symbol, symbol)
                text, url, status = await self.send_request(url, "POST", cert_data)
                if status != 200:
                    continue
                try:
                    check_errors(text)
                except:
                    continue
            cookies: dict[str, str] = {}
            for cookie in self.session.cookie_jar:
                cookies[cookie.key] = cookie.value
            sessions[symbol] = cookies
        return sessions, user_data

    async def log_out(self, sessions: dict[str, dict[str, str]]):
        if sessions:
            await self.send_request(get_login_endpoint_url(self.scheme, self.host, sessions[0]), "GET", cookies=sessions[sessions[0]])

    async def close(self):
        await self.session.close()
