import requests

from datetime import datetime, timezone, timedelta

from langchain_community.tools import DuckDuckGoSearchResults
from langchain.tools import tool
from bs4 import BeautifulSoup


ddg_tool = DuckDuckGoSearchResults(
    name="DDG_web_search",
    description="Инструмент для поиска информации в интернете",
    num_results=5,
    output_format="json"
)


@tool
def current_datetime():
    """Получает текущую дату и время"""
    return datetime.now(
        tz=timezone(
            offset=timedelta(hours=3)
        )
    )

@tool
def read_page(url: str) -> str:
    """Извлекает читаемый текст одной веб-страницы по ее URL.
    Используйте это, когда фрагмента результата поиска недостаточно."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator='\n', strip=True)
        return text[:2000]
    except Exception as e:
            return f"Не удалось загрузить страницу: {e}"