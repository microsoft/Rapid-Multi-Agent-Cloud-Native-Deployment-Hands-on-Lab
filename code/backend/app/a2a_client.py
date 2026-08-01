import json
import re
from typing import TypeVar

import httpx
from a2a.client import A2ACardResolver
from agent_framework.a2a import A2AAgent
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def parse_agent_json(text: str, model: type[T]) -> T:
    cleaned = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    if fenced:
        cleaned = fenced.group(1)
    try:
        return model.model_validate(json.loads(cleaned))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(f"Agent returned invalid {model.__name__} JSON") from exc


async def run_remote_agent(url: str, payload: dict, model: type[T]) -> T:
    async with httpx.AsyncClient(timeout=120.0) as http_client:
        resolver = A2ACardResolver(httpx_client=http_client, base_url=url)
        card = await resolver.get_agent_card()
        agent = A2AAgent(
            name=card.name,
            description=card.description,
            agent_card=card,
            url=url,
            http_client=http_client,
            timeout=120.0,
        )
        response = await agent.run(json.dumps(payload, ensure_ascii=False))
    return parse_agent_json(response.text, model)
