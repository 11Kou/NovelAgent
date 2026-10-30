import json
from pathlib import Path

from app.schemas.game import LoreEntry, WorldBook


def import_worldbook(content: str, filename: str) -> WorldBook:
    text = content.lstrip("\ufeff").strip()
    if not text:
        raise ValueError("世界书内容不能为空。")
    name = Path(filename).stem[:120] or "世界书"
    is_json = filename.lower().endswith(".json") or text.startswith(("{", "["))
    if not is_json:
        return WorldBook(name=name, entries=[LoreEntry(title=name, content=text)])
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("JSON 格式不正确，请检查世界书文件。") from exc
    if not isinstance(data, (dict, list)):
        raise ValueError("世界书 JSON 必须是对象或条目数组。")
    if isinstance(data, dict) and isinstance(data.get("data"), dict):
        data = data["data"]
    if isinstance(data, dict) and "entries" not in data and "character_book" in data:
        data = data["character_book"]
    if isinstance(data, dict):
        name = str(data.get("name") or data.get("title") or name)[:120]
        entries = data.get("entries")
        if entries is None:
            # Accept the project's original story settings export as a fixed setting.
            if "worldview" in data or "premise" in data:
                return WorldBook(name=name, entries=[LoreEntry(content=json.dumps(data, ensure_ascii=False))])
            raise ValueError("没有找到 entries 条目；支持酒馆世界书、角色卡 character_book 或文本文件。")
    else:
        entries = data
    if isinstance(entries, dict):
        entries = list(entries.values())
    if not isinstance(entries, list) or len(entries) > 500:
        raise ValueError("entries 必须是数组或对象，且最多包含 500 个条目。")
    normalized = []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("content"), str):
            raise ValueError("每个世界书条目必须包含字符串 content。")
        if not entry["content"].strip():
            continue
        keys = entry.get("keys", entry.get("key", []))
        if isinstance(keys, str):
            keys = [key.strip() for key in keys.split(",") if key.strip()]
        if not isinstance(keys, list) or any(not isinstance(key, str) for key in keys):
            raise ValueError("条目关键词必须是字符串数组。")
        normalized.append(LoreEntry(
            title=str(entry.get("title") or entry.get("comment") or entry.get("name") or "设定")[:200],
            content=entry["content"],
            keys=keys,
            constant=bool(entry.get("constant", not keys)),
            enabled=bool(entry.get("enabled", not entry.get("disable", False))),
        ))
    return WorldBook(name=name, entries=normalized)


def select_lore(book: WorldBook, query: str, budget: int = 18000) -> str:
    query = query.casefold()
    selected = []
    for entry in book.entries:
        if not entry.enabled:
            continue
        if entry.constant or not entry.keys or any(key.casefold() in query for key in entry.keys if key):
            selected.append(f"【{entry.title}】\n{entry.content}")
    # Do not silently truncate rules or cut an entry in the middle.
    result = "\n\n".join(selected)
    if len(result) > budget:
        raise ValueError("当前触发的世界书条目超过 18000 字符，请精简常驻设定，或为条目设置关键词。")
    return result or "本回合没有触发额外世界书条目。"
