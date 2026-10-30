import json
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.api.game_routes import get_game_service, get_library_service
from app.config.settings import Settings
from app.main import app
from app.schemas.game import SceneDraft, WorldBook
from app.services.game_service import GameService
from app.services.library_service import LibraryService
from app.services.model_clients import ModelClientError
from app.services.worldbook import import_worldbook, select_lore
from app.storage.game_models import GameConfiguration, GameSession, GameTurn


class FakeGameLLM:
    def __init__(self):
        self.calls = []
        self.fail = False

    def generate_json(self, messages, schema, **kwargs):
        assert schema is SceneDraft
        context = json.loads(messages[-1]["content"])
        self.calls.append(context)
        if self.fail:
            raise ModelClientError("测试生成失败")
        return SceneDraft(
            title="雾港的信", content=f"你站在钟表铺里。{context['本次行动']}",
            choices=["检查信封", "观察钟表"],
            state=[{"label": "位置", "value": "钟表铺"}],
            summary=f"{context['累计记忆']}你在钟表铺发现了一封信。",
        )


@pytest.fixture
def game_api():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    llm = FakeGameLLM()

    def override() -> Generator[GameService, None, None]:
        with Session(engine) as session:
            yield GameService(session, Settings(), llm_client=llm)

    app.dependency_overrides[get_game_service] = override
    def override_library():
        with Session(engine) as session:
            yield LibraryService(session)

    app.dependency_overrides[get_library_service] = override_library
    try:
        yield TestClient(app), llm, engine
    finally:
        app.dependency_overrides.pop(get_game_service, None)
        app.dependency_overrides.pop(get_library_service, None)
        engine.dispose()


def create_payload(request_id="create-1"):
    return {
        "request_id": request_id, "title": "雾港来信", "persona": "旧物修复师林舟",
        "opening": "走进钟表铺", "worldbook": {
            "name": "雾港", "entries": [{"title": "规则", "content": "旧物可以保存记忆。"}],
        },
    }


def test_game_create_play_restore_deduplicate_and_isolate(game_api):
    client, llm, engine = game_api
    created = client.post("/api/games", json=create_payload())
    assert created.status_code == 200
    first = created.json()
    assert first["version"] == 1
    assert first["turns"][0]["action"] == ""
    assert first["state"] == [{"label": "位置", "value": "钟表铺"}]
    assert client.post("/api/games", json=create_payload()).json() == first
    assert len(llm.calls) == 1

    action = {"request_id": "action-1", "expected_version": 1, "action": "检查信封"}
    response = client.post(f"/api/games/{first['id']}/actions", json=action)
    assert response.status_code == 200
    played = response.json()
    assert played["version"] == 2
    assert played["turns"][-1]["action"] == "检查信封"
    assert llm.calls[-1]["累计记忆"] == first["summary"]
    assert llm.calls[-1]["当前状态"] == first["state"]
    assert "旧物可以保存记忆" in llm.calls[-1]["世界书"]
    assert client.get(f"/api/games/{first['id']}").json() == played
    assert client.post(f"/api/games/{first['id']}/actions", json=action).json() == played
    assert len(llm.calls) == 2

    stale = client.post(f"/api/games/{first['id']}/actions", json={**action, "request_id": "action-stale"})
    assert stale.status_code == 409
    assert len(llm.calls) == 2
    second = client.post("/api/games", json=create_payload("create-2")).json()
    assert second["id"] != first["id"]
    assert second["version"] == 1
    assert len(second["turns"]) == 1
    assert len(client.get("/api/games").json()) == 2
    with Session(engine) as session:
        assert len(session.exec(select(GameTurn)).all()) == 3


def test_generation_failure_does_not_save_partial_game_or_turn(game_api):
    client, llm, engine = game_api
    llm.fail = True
    assert client.post("/api/games", json=create_payload()).status_code == 502
    assert client.get("/api/games").json() == []
    llm.fail = False
    game = client.post("/api/games", json=create_payload()).json()
    llm.fail = True
    response = client.post(f"/api/games/{game['id']}/actions", json={
        "request_id": "retry-me", "expected_version": 1, "action": "检查信封",
    })
    assert response.status_code == 502
    assert client.get(f"/api/games/{game['id']}").json() == game
    with Session(engine) as session:
        assert len(session.exec(select(GameSession)).all()) == 1
        assert len(session.exec(select(GameTurn)).all()) == 1
    llm.fail = False
    assert client.post(f"/api/games/{game['id']}/actions", json={
        "request_id": "retry-me", "expected_version": 1, "action": "检查信封",
    }).json()["version"] == 2


def test_missing_game_and_invalid_input(game_api):
    client, _, _ = game_api
    assert client.get("/api/games/999").status_code == 404
    assert client.post("/api/games", json={**create_payload(), "persona": "  "}).status_code == 422
    for content in ["{broken", '{"entries":42}', '{"entries":[{"content":12}]}', 'null']:
        response = client.post("/api/worldbooks/import", json={"filename": "bad.json", "content": content})
        assert response.status_code == 422


def test_worldbook_formats_and_activation():
    data = {"name": "雾港", "entries": {
        "0": {"comment": "规则", "content": "旧物保存记忆", "constant": True, "key": []},
        "1": {"comment": "秘密码头", "content": "码头夜间关闭", "key": ["码头"]},
        "2": {"content": "禁用资料", "constant": True, "disable": True},
    }}
    book = import_worldbook(json.dumps(data), "lore.json")
    assert book.name == "雾港"
    assert book.entries[1].keys == ["码头"]
    assert "码头夜间关闭" not in select_lore(book, "检查信封")
    assert "码头夜间关闭" in select_lore(book, "前往码头")
    assert "禁用资料" not in select_lore(book, "码头")
    card = import_worldbook(json.dumps({"character_book": data}), "character.json")
    assert card == book
    assert import_worldbook("\ufeff海上有一座岛", "岛屿.txt").entries[0].content == "海上有一座岛"
    assert import_worldbook('{"title":"故事","worldview":"海岛"}', "story.json").name == "故事"
    with pytest.raises(ValueError, match="18000"):
        select_lore(WorldBook(entries=[{"content": "字" * 18001}]), "开场")


def test_late_concurrent_update_does_not_overwrite_newer_state(game_api):
    client, llm, engine = game_api
    game = client.post("/api/games", json=create_payload()).json()
    generate = llm.generate_json

    def racing_generate(*args, **kwargs):
        draft = generate(*args, **kwargs)
        with Session(engine) as other:
            saved = other.get(GameSession, game["id"])
            saved.version = 2
            saved.summary = "其他页面已经更新"
            other.add(saved)
            other.commit()
        return draft

    llm.generate_json = racing_generate
    response = client.post(f"/api/games/{game['id']}/actions", json={
        "request_id": "race", "expected_version": 1, "action": "检查信封",
    })
    assert response.status_code == 409
    restored = client.get(f"/api/games/{game['id']}").json()
    assert restored["summary"] == "其他页面已经更新"
    assert len(restored["turns"]) == 1


def test_library_templates_are_independent_from_story_copies(game_api):
    client, llm, _ = game_api
    saved_book = client.post("/api/library/worldbooks", json=create_payload()["worldbook"]).json()
    saved_card = client.post("/api/library/characters", json={
        "name": "阿远", "description": "码头邮差", "personality": "谨慎", "goal": "送完最后一封信",
    }).json()
    assert len(client.get("/api/library/worldbooks").json()) == 1
    assert len(client.get("/api/library/characters").json()) == 1
    created = client.post("/api/games", json={
        **create_payload(), "worldbook": saved_book["book"],
        "characters": [{"card": saved_card["card"], "role": "npc"}],
    }).json()
    assert llm.calls[-1]["人设卡"][0]["name"] == "阿远"
    edited_card = {**saved_card["card"], "personality": "勇敢"}
    assert client.put(f"/api/library/characters/{saved_card['id']}", json=edited_card).status_code == 200
    assert client.put(f"/api/library/worldbooks/{saved_book['id']}", json={
        "name": "新版世界", "entries": [{"content": "新的世界规则"}],
    }).status_code == 200
    restored = client.get(f"/api/games/{created['id']}").json()
    assert restored["worldbook"]["name"] == "雾港"
    assert restored["characters"][0]["card"]["personality"] == "谨慎"
    assert client.put("/api/library/worldbooks/999", json=saved_book["book"]).status_code == 404
    assert client.put("/api/library/characters/999", json=edited_card).status_code == 404


def test_mid_story_settings_apply_on_next_turn_without_rewriting_history(game_api):
    client, llm, _ = game_api
    created = client.post("/api/games", json=create_payload()).json()
    settings = {
        "expected_version": 1, "expected_settings_revision": 0,
        "persona": created["persona"], "style": "悬疑",
        "worldbook": {"name": "雾港", "entries": [*created["worldbook"]["entries"], {"content": "邮局每天清晨开门"}]},
        "characters": [{"role": "npc", "card": {"name": "阿远", "description": "码头邮差"}}],
    }
    response = client.put(f"/api/games/{created['id']}/settings", json=settings)
    assert response.status_code == 200
    updated = response.json()
    assert updated["version"] == 1
    assert updated["settings_revision"] == 1
    assert updated["turns"] == created["turns"]
    assert updated["summary"] == created["summary"]
    assert updated["state"] == created["state"]
    assert len(llm.calls) == 1
    assert client.put(f"/api/games/{created['id']}/settings", json=settings).status_code == 409
    action = {"request_id": "next", "expected_version": 1, "action": "寻找阿远"}
    assert client.post(f"/api/games/{created['id']}/actions", json=action).status_code == 409
    response = client.post(f"/api/games/{created['id']}/actions", json={**action, "expected_settings_revision": 1})
    assert response.status_code == 200
    assert response.json()["version"] == 2
    assert "邮局每天清晨开门" in llm.calls[-1]["世界书"]
    assert llm.calls[-1]["人设卡"][0]["description"] == "码头邮差"


def test_character_card_import_includes_embedded_lore_and_validates_roles(game_api):
    client, llm, _ = game_api
    card_data = {"spec": "chara_card_v2", "data": {
        "name": "阿远", "description": "邮差", "personality": "谨慎", "scenario": "雾港",
        "first_mes": "你的信。", "mes_example": "<START>\n阿远：请签收。",
        "character_book": {"name": "邮差往事", "entries": [{"content": "阿远怕水", "constant": True}]},
    }}
    response = client.post("/api/characters/import", json={"filename": "card.json", "content": json.dumps(card_data)})
    assert response.status_code == 200
    card = response.json()
    assert card["worldbook"]["entries"][0]["content"] == "阿远怕水"
    assert card["first_mes"] == "你的信。"
    created = client.post("/api/games", json={**create_payload(), "characters": [
        {"card": card, "role": "npc"}, {"card": {"name": "林舟"}, "role": "player"},
        {"card": {"name": "未启用角色"}, "enabled": False},
    ]})
    assert created.status_code == 200
    assert len(llm.calls[-1]["人设卡"]) == 2
    assert "阿远怕水" in llm.calls[-1]["角色关联世界书"][0]["设定"]
    assert llm.calls[-1]["人设卡"][0]["first_mes"] == "你的信。"
    assert client.post(f"/api/games/{created.json()['id']}/actions", json={
        "request_id": "card-next", "expected_version": 1, "action": "询问邮路",
    }).status_code == 200
    assert "first_mes" not in llm.calls[-1]["人设卡"][0]
    invalid = client.post("/api/games", json={**create_payload("two-players"), "characters": [
        {"card": {"name": "甲"}, "role": "player"}, {"card": {"name": "乙"}, "role": "player"},
    ]})
    assert invalid.status_code == 422
    for content in ['{"data":null}', '{"name":"  "}', '[1]', '{bad']:
        assert client.post("/api/characters/import", json={"filename": "bad.json", "content": content}).status_code == 422
    assert client.post("/api/characters/import", json={"filename": "旅人.txt", "content": "一个喜欢旅行的修复师"}).json()["name"] == "旅人"


def test_legacy_save_can_add_settings_without_schema_migration(game_api):
    client, _, engine = game_api
    created = client.post("/api/games", json=create_payload()).json()
    with Session(engine) as session:
        session.delete(session.get(GameConfiguration, created["id"]))
        session.commit()
    legacy = client.get(f"/api/games/{created['id']}").json()
    assert legacy["characters"] == []
    assert legacy["settings_revision"] == 0
    response = client.put(f"/api/games/{created['id']}/settings", json={
        "expected_version": 1, "expected_settings_revision": 0, "worldbook": legacy["worldbook"],
        "persona": legacy["persona"], "characters": [{"card": {"name": "新人物"}}],
    })
    assert response.status_code == 200
    assert response.json()["characters"][0]["card"]["name"] == "新人物"


def test_settings_edit_during_generation_rejects_old_scene(game_api):
    client, llm, engine = game_api
    created = client.post("/api/games", json=create_payload()).json()
    generate = llm.generate_json

    def edit_during_generation(*args, **kwargs):
        draft = generate(*args, **kwargs)
        from app.schemas.game import GameSettingsUpdate
        with Session(engine) as session:
            GameService(session, Settings(), llm_client=llm).update_settings(created["id"], GameSettingsUpdate(
                expected_version=1, expected_settings_revision=0, worldbook=created["worldbook"],
                persona="新补充的玩家身份",
            ))
        return draft

    llm.generate_json = edit_during_generation
    response = client.post(f"/api/games/{created['id']}/actions", json={
        "request_id": "settings-race", "expected_version": 1, "action": "检查信封",
    })
    assert response.status_code == 409
    restored = client.get(f"/api/games/{created['id']}").json()
    assert restored["settings_revision"] == 1
    assert restored["persona"] == "新补充的玩家身份"
    assert restored["version"] == 1
    assert len(restored["turns"]) == 1
