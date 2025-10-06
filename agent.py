from __future__ import annotations
from typing import Dict, Any, List
from pydantic import BaseModel
import os


# Optional: dùng OpenAI function calling nếu có API key
def _check_openai_available():
    return bool(os.getenv("OPENAI_API_KEY"))


def _get_openai_client():
    """Lazy initialization of OpenAI client"""
    if not hasattr(_get_openai_client, 'client'):
        from openai import OpenAI
        _get_openai_client.client = OpenAI()
    return _get_openai_client.client


def _get_openai_model():
    """Get OpenAI model name"""
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class Registry(BaseModel):
    tools: Dict[str, Any] = {}

    def register(self, tool):
        self.tools[tool.spec.name] = tool

    def list_openai_functions(self):
        # chuyển schema pydantic -> JSON schema theo OpenAI tool format
        fns = []
        for t in self.tools.values():
            schema = t.spec.args_schema.model_json_schema()
            fns.append({
                "type": "function",
                "function": {
                    "name": t.spec.name,
                    "description": t.spec.description,
                    "parameters": schema,
                },
            })
        return fns


class SingleAgent:
    def __init__(self, registry: Registry):
        self.r = registry

    def plan_and_act(self, user_msg: str) -> str:
        if _check_openai_available():
            return self._openai_function_calling(user_msg)
        else:
            return "❌ **Lỗi: Thiếu OpenAI API Key**\n\n" + \
                   "Để sử dụng agent này, bạn cần:\n" + \
                   "1. Tạo file `.env` trong thư mục dự án\n" + \
                   "2. Thêm dòng: `OPENAI_API_KEY=your_api_key_here`\n" + \
                   "3. Khởi động lại ứng dụng\n\n" + \
                   "**Lưu ý:** Agent này được thiết kế để sử dụng OpenAI Function Calling để hiểu và xử lý các yêu cầu tự nhiên. " + \
                   "Không có API key, agent không thể hoạt động đúng cách."


    def _openai_function_calling(self, user_msg: str) -> str:
        # gửi list tools cho model để nó quyết định
        tools = self.r.list_openai_functions()
        messages = [
            {"role": "system", "content": "You are a helpful assistant that executes actions immediately without asking for confirmation. When users request to add, update, or delete employees, execute the action directly and report the result."},
            {"role": "user", "content": user_msg}
        ]
        client = _get_openai_client()
        model = _get_openai_model()
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        choice = resp.choices[0]
        msg = choice.message
        if msg.tool_calls:
            # chỉ demo 1 step tool call
            call = msg.tool_calls[0]
            name = call.function.name
            import json
            args = json.loads(call.function.arguments or "{}")
            
            tool = self.r.tools[name]
            result = tool(**args)
            messages.append(msg)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "name": name,
                "content": str(result),
            })
            final = client.chat.completions.create(model=model, messages=messages)
            return final.choices[0].message.content
        else:
            return msg.content

