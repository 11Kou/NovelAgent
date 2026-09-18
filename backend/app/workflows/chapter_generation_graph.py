from langgraph.graph import END, START, StateGraph

from app.retrieval.assembler import PromptAssembler
from app.retrieval.dynamic_retriever import DynamicRetriever
from app.retrieval.static_retriever import StaticRetriever
from app.retrieval.vector_retriever import VectorRetriever
from app.workflows.workflow_state import ChapterGenerationState


def build_chapter_generation_graph(
    *,
    static_retriever: StaticRetriever,
    dynamic_retriever: DynamicRetriever,
    vector_retriever: VectorRetriever,
    assembler: PromptAssembler,
    writing_agent,
):
    graph = StateGraph(ChapterGenerationState)

    def retrieve_static_context(state: ChapterGenerationState) -> dict:
        return {"static_context": static_retriever.retrieve(state["story_id"])}

    def retrieve_dynamic_context(state: ChapterGenerationState) -> dict:
        chapter_event = state["chapter_event"]
        entity_ids = chapter_event.involved_entities
        return {
            "entity_ids": entity_ids,
            "dynamic_context": dynamic_retriever.retrieve(state["story_id"], entity_ids),
        }

    def retrieve_vector_context(state: ChapterGenerationState) -> dict:
        chapter_event = state["chapter_event"]
        return {
            "related_history": vector_retriever.retrieve(
                story_id=state["story_id"],
                query=chapter_event.event_description,
                top_k=5,
            )
        }

    def assemble_prompt(state: ChapterGenerationState) -> dict:
        return {
            "assembled_prompt": assembler.assemble(
                static_context=state["static_context"],
                dynamic_context=state["dynamic_context"],
                related_history=state["related_history"],
                chapter_event=state["chapter_event"],
            )
        }

    def write_chapter(state: ChapterGenerationState) -> dict:
        return {
            "content": writing_agent.write_chapter(
                state["assembled_prompt"],
                state.get("rewrite_note", ""),
            )
        }

    graph.add_node("retrieve_static_context", retrieve_static_context)
    graph.add_node("retrieve_dynamic_context", retrieve_dynamic_context)
    graph.add_node("retrieve_vector_context", retrieve_vector_context)
    graph.add_node("assemble_prompt", assemble_prompt)
    graph.add_node("write_chapter", write_chapter)

    graph.add_edge(START, "retrieve_static_context")
    graph.add_edge("retrieve_static_context", "retrieve_dynamic_context")
    graph.add_edge("retrieve_dynamic_context", "retrieve_vector_context")
    graph.add_edge("retrieve_vector_context", "assemble_prompt")
    graph.add_edge("assemble_prompt", "write_chapter")
    graph.add_edge("write_chapter", END)

    return graph.compile()

