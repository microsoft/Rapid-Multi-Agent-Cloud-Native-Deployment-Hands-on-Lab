import pytest

from backend.app.a2a_client import parse_agent_json
from backend.app.models import SocialPost


def test_parse_agent_json_accepts_fenced_json() -> None:
    result = parse_agent_json(
        '```json\n{"caption":"A bright day.","hashtags":["#one","#two","#three"],"visual_hook":"sun over city"}\n```',
        SocialPost,
    )
    assert result.hashtags == ["#one", "#two", "#three"]


def test_parse_agent_json_rejects_invalid_payload() -> None:
    with pytest.raises(ValueError):
        parse_agent_json('{"caption":"missing fields"}', SocialPost)

