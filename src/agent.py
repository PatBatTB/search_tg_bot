import os
import openai
import langgraph
import agent_tools

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.rate_limiters import InMemoryRateLimiter

from pydantic import SecretStr


_system_prompt = """
## **РОЛЬ**: 
Ты полезный ассистент-исследователь, помогающий пользователю с поиском в интернете.

## **ЗАДАЧА**: 
Производи поиск релевантной и достоверной информации по запросу пользователя.
Сравнивай информацию, полученную из разных источников и давай пользователю полезный ответ по запросу.
Старайся искать конкретные варианты ответа на вопрос, избегай обобщенных рекомендаций.
Все фактические ответы должны сопровождаться ссылкой на источник в формате markdown.

## **ПРОЦЕСС РАБОТЫ**:
1. Анализируй вопрос пользователя и формируй подходящие поисковые запросы.
2. Если в вопросе пользователя фигурирует какой-то относительное указание времени и нужно его сопоставить с текущей датой - используй инструмент `current_datetime` для получения текущей даты.
3. Ищи информацию инструментом `DDG_web_search`
4. Анализируй полученную информацию для формирования ответа пользователю
5. Для подтверждения факта дополняй информацию дополнительной выгрузкой - используй инструмент `read_page` для получения дополнительной информации.
6. На основании всей полученной информации составь релевантный ответ пользователю.

**ДОСТУПНЫЕ ИНСТРУМЕНТЫ**:
    - `DDG_web_search`: инструмент для поиска информации в интернете.
    - `current_datetime`: инструмент для получения текущей даты и времени.
    - `read_page`: инструмент для чтения содержимого web-страниц
"""

class ReactAgent:
    def __init__(self):
        _rate_limiter = InMemoryRateLimiter(
            requests_per_second=1,
            check_every_n_seconds=0.1,
            max_bucket_size=10
        )
        _chat_model = ChatOpenAI(
            model=os.environ["OPENAI_MODEL"],
            temperature=0.2,
            base_url=os.environ["OPENAI_BASE_URL"],
            api_key=SecretStr(os.environ["OPENAI_API_KEY"]),
            timeout=60,
            rate_limiter=_rate_limiter,
            max_tokens=6000
        )
        # _azure_chat_model = AzureAIOpenAIApiChatModel(
        #     model="openai/gpt-5-chat",
        #     temperature=0.2,
        #     base_url=os.environ["OPENAI_BASE_URL"],
        #     api_key=SecretStr(os.environ["OPENAI_API_KEY"]),
        #     timeout=60
        # )
        self._agent = create_agent(
            model=_chat_model,
            tools=[
                agent_tools.ddg_tool,
                agent_tools.current_datetime,
                agent_tools.read_page
            ],
            system_prompt=_system_prompt,
        )

    def invoke(self, message_text: str):
        user_message = HumanMessage(content=message_text)
        config: RunnableConfig = {
                "recursion_limit": 20,
                "configurable": {
                    "thread_id": "default"
                }
            }
        try:
            response = self._agent.invoke(
                input={"messages": [user_message]},
                config=config
            )
            response_text = response["messages"][-1].content
        except openai.APIStatusError as e:
            response_text = e.body
        except langgraph.errors.GraphRecursionError as e:
            response_text = e
        except openai.APITimeoutError as e:
            response_text = e.message
        return response_text

