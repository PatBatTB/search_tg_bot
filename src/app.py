import dotenv
import os
import asyncio
from agent import ReactAgent
from tg_bot import SearchBot

UI = "bot"

def init_arize_phoenix():
    from openinference.instrumentation.langchain import LangChainInstrumentor
    from phoenix.otel import register

    tracer_provider = register(
        project_name="react-agent",
        endpoint="http://localhost:6006/v1/traces",
        batch=True,
        set_global_tracer_provider=False
    )
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

def bot_chat(agent: ReactAgent):
    bot_token = os.environ["TG_BOT_TOKEN"]
    proxy = os.environ["PROXY"]
    bot = SearchBot(bot_token, agent, proxy)
    try:
        asyncio.run(bot.start())
    finally:
        bot.stop()

def console_chat(agent: ReactAgent):
    print("Привет! Чем могу помочь?")
    while (request := input("> ")) and request.lower() not in ("выход", "exit", "quit"):
        response = agent.invoke(request)
        print(f"AI: {response}")
    print("До встречи.")

if __name__ == '__main__':
    dotenv.load_dotenv()
    if os.environ["PHOENIX_TELEMETRY"].casefold() == "true": init_arize_phoenix()
    agent = ReactAgent()

    match UI:
        case "bot":
            bot_chat(agent)
        case "console":
            console_chat(agent)
        case _:
            print("unknown mode. Exit")







