from langgraph.graph import END, START, StateGraph

from app.workflows.workflow_state import ChapterConfirmationState


def build_chapter_confirmation_graph(*, dynamic_store, memory_service):
    graph = StateGraph(ChapterConfirmationState)

    def save_chapter(state: ChapterConfirmationState) -> dict:
        chapter_event = state["chapter_event"]
        chapter = dynamic_store.save_chapter(
            story_id=state["story_id"],
            chapter_index=chapter_event.chapter_index,
            title=chapter_event.title,
            event_description=chapter_event.event_description,
            content=state["content"],
        )
        return {"chapter": chapter}

    def extract_and_save_memory(state: ChapterConfirmationState) -> dict:
        chapter = state["chapter"]
        memory = memory_service.extract_and_save(
            story_id=state["story_id"],
            chapter_id=chapter.id,
            chapter_index=chapter.chapter_index,
            chapter_event=chapter.event_description,
            chapter_content=chapter.content,
        )
        return {"memory": memory}

    graph.add_node("save_chapter", save_chapter)
    graph.add_node("extract_and_save_memory", extract_and_save_memory)

    graph.add_edge(START, "save_chapter")
    graph.add_edge("save_chapter", "extract_and_save_memory")
    graph.add_edge("extract_and_save_memory", END)

    return graph.compile()

