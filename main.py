from agent.main import Agent
from config.settings.conf import settings



if __name__ == "__main__":
    ai = Agent(model=settings.MODEL, user_name="Lili")
    ai.chat()
    