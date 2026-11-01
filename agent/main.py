from pathlib import Path

from docxtpl import DocxTemplate
from langchain_core.tools import tool
import requests
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph

import urllib
from config.prompts.ai_prompt import AIPrompt
from config.settings.conf import settings



class Agent:
    def __init__(self, model: str, user_name: str):
        self.model = model
        self.user_name = user_name
        self.agent = None

    def _llm(self):
        return ChatOpenAI(
            model=MODEL,
            base_url="https://sprutdock.ru/v1",
            api_key=settings.API_DEEP_KEY,
            temperature=0.9,
        )

    def _agent(self):
        self.agent = create_agent(
            model=self._llm(),
            tools=[self.get_weather, self.read_text_from_url],
            checkpointer=InMemorySaver(),
        )
        return self.agent

    def _user_config(self) -> dict[str, any]:
        return {"configurable": {"thread_id": "user1"}}

    @staticmethod
    @tool
    def get_weather(city: str) -> dict:
        """
        Получить текущую погоду в указанном городе.
        Args:
            city: Название города на английском или русском, например 'Moscow', "Москва" или 'London'.
        Получаем координаты годорда latitude и longitude возвращаем словарь вида
        {'time': '2026-10-31T18:30',
        'interval': 900,
        'temperature_2m': 7.7,
        'wind_speed_10m': 6.4,
        'relative_humidity_2m': 89}
        """
        # Для примера используем бесплатный геокодер Open-Meteo, 
        # чтобы получить координаты по названию города
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {"name": city, "language": "ru"}

        try:
            geo_response = requests.get(geo_url, params=geo_params, timeout=10)
            geo_data = geo_response.json()
            
            if not geo_data.get("results"):
                return f"Не удалось найти город '{city}'."
                
            lat = geo_data["results"][0]["latitude"]
            lon = geo_data["results"][0]["longitude"]
            
            # Теперь запрашиваем погоду по полученным координатам
            weather_url = "https://api.open-meteo.com/v1/forecast"
            weather_params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,wind_speed_10m,relative_humidity_2m", 
                "timezone": "auto"
            }
            weather_response = requests.get(weather_url, params=weather_params).json()["current"]
            return weather_response
            
        except Exception as e:
            return f"Ошибка при получении погоды: {e}"


    def _get_started(self) -> dict:
        response = self.agent.invoke(
            {"messages": [{"role": "user", "content": f"Меня зовут {self.user_name}"}]},
            config=self._user_config())
        print("Бот приветствует:", response["messages"][-1].content)  
        return response["messages"][-1].content

    def _answer(self, user_msg: str):
        agent_answer = self.agent.invoke(
            {"messages": [{"role": "user", "content": user_msg}]},
            config=self._user_config(),
        )
        return agent_answer["messages"][-1]   # возвращаем AIMessage, не строку

    @staticmethod
    @tool
    def read_text_from_url(url: str) -> str:
        """ПРочитать стихотворение Пушника
        """
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; quickstart-research/1.0)"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read()
        except urllib.error.URLError as e:
            return f"Fetch failed: {e}"
        text = raw.decode("utf-8", errors="replace")
        return text

    def chat(self):
        self.agent = self._agent()
        self._get_started()
        while True:
            user_msg = input("ты:".strip())
            if not user_msg:
                continue

            if user_msg.lower() in ("exit", "/exit"):
                print("Выход...")
                break

            answer = self._answer(user_msg=user_msg) # это словарь ai messages
            print("Бот:", answer.content)
            # usage = answer.usage_metadata or {}   
            # print("Токенов на ответ бота ушло:", usage.get("output_tokens", "н/д"))

