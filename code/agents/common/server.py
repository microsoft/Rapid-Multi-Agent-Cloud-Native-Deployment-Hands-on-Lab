import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any

from a2a.helpers import new_task_from_user_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import AgentCapabilities, AgentInterface, Part, TaskState
from agent_framework.github import GitHubCopilotAgent
from agent_framework_hosting import AgentState
from agent_framework_hosting_a2a import AgentA2AAdapter
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

logger = logging.getLogger(__name__)


class CopilotAgentExecutor(AgentExecutor):
    def __init__(self, adapter: AgentA2AAdapter[Any]) -> None:
        self.adapter = adapter

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.context_id is None:
            raise ValueError("A2A context id is required")
        updater = TaskUpdater(event_queue, context.task_id or "", context.context_id)
        await updater.cancel()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.message is None or context.context_id is None:
            raise ValueError("A2A message and context id are required")

        task = context.current_task
        if task is None:
            task = new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, context.context_id)
        await updater.submit()
        try:
            await updater.start_work()
            run = self.adapter.a2a_to_run(context.message, stream=True)
            agent = await self.adapter.state.get_target()
            session_id = f"a2a:{context.tenant}:{context.context_id}"
            session = await self.adapter.state.get_or_create_session(session_id)
            stream = agent.run(
                run["messages"],
                session=session,
                options=run["options"],
                stream=True,
            )
            default_artifact_id = uuid.uuid4().hex
            streamed_artifact_ids: set[str] = set()
            async for update in stream:
                parts = self.adapter.a2a_from_run(update)
                if parts:
                    artifact_id = update.message_id or default_artifact_id
                    await updater.add_artifact(
                        parts=parts,
                        artifact_id=artifact_id,
                        append=True if artifact_id in streamed_artifact_ids else None,
                    )
                    streamed_artifact_ids.add(artifact_id)

            final_response = await stream.get_final_response()
            if not streamed_artifact_ids:
                parts = self.adapter.a2a_from_run(final_response)
                if parts:
                    await updater.update_status(
                        state=TaskState.TASK_STATE_WORKING,
                        message=updater.new_agent_message(parts),
                    )
            await self.adapter.state.set_session(session_id, session)
            await updater.complete()
        except asyncio.CancelledError:
            await updater.update_status(state=TaskState.TASK_STATE_CANCELED)
        except Exception:
            logger.exception("A2A agent execution failed")
            await updater.update_status(
                state=TaskState.TASK_STATE_FAILED,
                message=updater.new_agent_message([Part(text="Agent execution failed.")]),
            )


def create_a2a_app(
    *,
    name: str,
    description: str,
    instructions: str,
    default_port: int,
) -> Starlette:
    agent = GitHubCopilotAgent(
        name=name,
        description=description,
        instructions=instructions,
    )
    state = AgentState(agent)
    public_url = os.getenv("AGENT_PUBLIC_URL", f"http://localhost:{default_port}/")
    adapter = AgentA2AAdapter(
        state,
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=True),
        supported_interfaces=[AgentInterface(url=public_url, protocol_binding="JSONRPC")],
    )
    card = asyncio.run(adapter.get_card())
    handler = DefaultRequestHandler(
        agent_executor=CopilotAgentExecutor(adapter),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )

    async def health(_: Any) -> JSONResponse:
        return JSONResponse({"status": "ok", "agent": name})

    @asynccontextmanager
    async def lifespan(_: Starlette):
        await agent.__aenter__()
        try:
            yield
        finally:
            await agent.__aexit__(None, None, None)

    return Starlette(
        routes=[
            Route("/health", health),
            *create_agent_card_routes(card),
            *create_jsonrpc_routes(handler, "/"),
        ],
        lifespan=lifespan,
    )
