import os
from dotenv import load_dotenv
from agent import Registry, SingleAgent
from tools import rag_tool_factory, weather_tool_factory, db_tool_factory


load_dotenv()


reg = Registry()
reg.register(rag_tool_factory())
reg.register(weather_tool_factory(os.getenv("WEATHER_API_BASE", "https://api.open-meteo.com/v1/forecast")))
reg.register(db_tool_factory("data.db"))


agent = SingleAgent(reg)


print("Single‑Agent demo. Ví dụ câu hỏi:")
print("- Thời tiết hôm nay ở Đà Nẵng?")
print("- Cho tôi biết tổng số khách hàng trong DB.")
print("- Tóm tắt kiến thức về … (RAG)")


while True:
    try:
        q = input("\nYou> ")
        if q.strip().lower() in {"quit", "exit"}:
            break
        ans = agent.plan_and_act(q)
        print("Agent>", ans)
    except KeyboardInterrupt:
        break
