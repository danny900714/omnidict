from bs4 import BeautifulSoup
from requests import Session


class ParseError(Exception):
    pass


def _parse_supported_target_languages(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    bilingual_list = soup.select_one("amp-state#stateSidebarDictBi ~ ul")
    semi_bilingual_list = soup.select_one("amp-state#stateSidebarDictBi ~ div:last-child")
    if not bilingual_list or not semi_bilingual_list:
        raise ParseError("Failed to parse supported target languages")

    target_languages = {}
    for list_element in [bilingual_list, semi_bilingual_list]:
        buttons = list_element.select('span[role="button"].hp')
        for button in buttons:
            code = button.attrs["data-dictcode"]
            if not isinstance(code, str):
                raise ParseError("Failed to parse supported target languages")
            name = button.text.removeprefix("English–")
            target_languages[code] = name

    return target_languages

def _parse_definition(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    entry_body = soup.select_one("div.entry-body")
    if entry_body is None:
        raise ParseError("Failed to parse definition")
    return str(entry_body)


class Client:
    def __init__(self):
        self.session = Session()
        self.session.headers.update({
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "dnt": "1",
            "priority": "u=0,i",
            "sec-ch-ua": '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "macOS",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        })

    def __del__(self):
        self.session.close()

    def fetch_supported_target_languages(self) -> dict[str, str]:
        response = self.session.get("https://dictionary.cambridge.org/")
        return _parse_supported_target_languages(response.text)

    def fetch_definition(self, dict_code: str, vocabulary: str) -> str:
        url = f"https://dictionary.cambridge.org/dictionary/{dict_code}/{vocabulary}"
        response = self.session.get(url)
        return _parse_definition(response.text)
