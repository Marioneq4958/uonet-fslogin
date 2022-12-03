import logging
import aiohttp
from bs4 import BeautifulSoup
from uonet_fslogin.errors import FailedRequestException, NotRegisteredException, \
    NoPermissionsException
from uonet_fslogin.utils import get_login_endpoint_url, check_errors, get_login_prefix, \
    get_credentials_inputs, get_hidden_inputs, get_attributes_from_cert

DEFAULT_SYMBOL: str = "default"


class UonetFSLogin:
    """Includes functions for user login and logout"""

    def __init__(self, scheme: str, host: str):
        self.scheme = scheme
        self.host = host
        self.session = aiohttp.ClientSession()
        self._log = logging.getLogger(__name__)

    async def _send_request(self, url: str, method: str, data: dict = None, **kwargs) -> tuple[
        str, str]:
        try:
            async with self.session.request(method=method, url=url, data=data,
                                            **kwargs) as response:
                for res in response.history:
                    self._log.debug("[%s] %s %s", res.status, res.method, res.url)
                self._log.debug("[%s] %s %s", response.status, response.method, response.url)

                text: str = await response.text()
                return text, response.url, response.status
        except ValueError as exc:
            raise FailedRequestException() from exc

    async def _get_login_form_data(self, username: str, password: str, default_symbol: str) -> \
    tuple[dict[str, str], str]:
        text, url, status = await self._send_request(
            get_login_endpoint_url(self.scheme, self.host, default_symbol),
            "GET")
        soup = BeautifulSoup(text, "html.parser")
        login_form = soup.select_one("form")
        data: dict[str, str] = get_hidden_inputs(login_form)
        username_input, password_input = get_credentials_inputs(login_form)
        prefix = get_login_prefix(text)
        data[username_input["name"]] = rf"{prefix}\{username}" if prefix else username
        data[password_input["name"]] = password
        return data, url

    async def log_in(self, username: str, password: str, default_symbol: str = DEFAULT_SYMBOL,
                     symbols: list[str] = None) -> tuple[dict, dict]:
        """User login"""
        sessions: dict[str, dict[str, str]] = {}
        data, url = await self._get_login_form_data(username, password, default_symbol)
        text, url, status = await self._send_request(url, "POST", data)
        check_errors(text)
        soup = BeautifulSoup(text, "html.parser")
        form = soup.select_one('form[name="hiddenform"]')
        cert_data: dict[str, str] = get_hidden_inputs(soup.select_one('form'))
        user_data: dict = get_attributes_from_cert(cert_data["wresult"])
        if not symbols:
            symbols = []
        if "symbols" in user_data:
            for symbol in user_data["symbols"]:
                symbols.append(symbol)
        if DEFAULT_SYMBOL in symbols:
            symbols.remove(DEFAULT_SYMBOL)
        for symbol in symbols:
            url: str = form["action"].replace(default_symbol, symbol)
            text, url, status = await self._send_request(url, "POST", cert_data)
            if status != 200:
                continue
            try:
                check_errors(text)
            except NotRegisteredException:
                continue
            except NoPermissionsException:
                continue
            soup = BeautifulSoup(text, "html.parser")
            if soup.select_one('form[name="hiddenform"]'):
                form = soup.select_one('form[name="hiddenform"]')
                cert_data: dict[str, str] = get_hidden_inputs(
                    form)
                url: str = form["action"].replace(
                    default_symbol, symbol)
                text, url, status = await self._send_request(url, "POST", cert_data)
                if status != 200:
                    continue
                try:
                    check_errors(text)
                except NotRegisteredException:
                    continue
                except NoPermissionsException:
                    continue
            cookies: dict[str, str] = {}
            for cookie in self.session.cookie_jar:
                cookies[cookie.key] = cookie.value
            sessions[symbol] = cookies
        return sessions, user_data

    async def log_out(self, sessions: dict[str, dict[str, str]]) -> None:
        """User logout"""
        if sessions:
            await self._send_request(get_login_endpoint_url(self.scheme, self.host, sessions[0]),
                                     "GET",
                                     cookies=sessions[sessions[0]])

    async def close(self) -> None:
        await self.session.close()
