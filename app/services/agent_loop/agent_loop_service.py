import logging
import asyncio
import json
from app.agents.tool_executor import ToolExecutor
from app.helpers.openai_client import client
from app.agents.tools import TOOLS
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

class AgentLoopService:

    MAX_ITERATIONS = 4

    @staticmethod
    async def run(
        *,
        conversation: list,
        db,
        user,
        session,
    ):
        logger.info(
            "Agent loop started session_id=%s",
            session.id,
        )
        events = []

        input_tokens = 0
        output_tokens = 0
        total_tokens = 0

        logger.info("===== AGENT CONVERSATION =====")

        for i, item in enumerate(conversation):
            logger.info(
                "[%s] role=%r content=%r",
                i,
                item.get("role"),
                str(item.get("content"))[:300],
            )

        logger.info(
            json.dumps(
                conversation,
                indent=2,
                default=str,
            )
        )
        response = await client.responses.create(
            model=settings.DEPLOYMENT_NAME,
            input=conversation,
            tools=TOOLS,
        )

        input_tokens += response.usage.input_tokens
        output_tokens += response.usage.output_tokens
        total_tokens += response.usage.total_tokens

        for iteration in range(
            AgentLoopService.MAX_ITERATIONS
        ):

            logger.info(
                "Agent iteration=%s session_id=%s",
                iteration + 1,
                session.id,
            )

            tool_calls = [
                item
                for item in response.output
                if getattr(item, "type", None)
                == "function_call"
            ]

            logger.info(
                "Detected %d tool call(s) session_id=%s",
                len(tool_calls),
                session.id,
            )

            # ---------------------------------------------
            # Final Answer
            # ---------------------------------------------

            if not tool_calls:

                logger.info(
                    "Agent produced final answer "
                    "session_id=%s iteration=%s",
                    session.id,
                    iteration + 1,
                )

                return {
                    "status": "completed",
                    "answer": response.output_text,
                    "data": {},
                    "events": events,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                }

            tool_outputs = []

            for tool_call in tool_calls:

                logger.info(
                    "Tool requested: %s session_id=%s",
                    tool_call.name,
                    session.id,
                )

                try:

                    arguments = json.loads(
                        tool_call.arguments or "{}"
                    )

                except json.JSONDecodeError:

                    logger.exception(
                        "Invalid tool arguments "
                        "tool=%s session_id=%s",
                        tool_call.name,
                        session.id,
                    )

                    arguments = {}

                events.append({
                                    "type": "tool_started",
                                    "tool_name": tool_call.name,
                                    "arguments": arguments,
                                })

                tool_result = await ToolExecutor.execute(
                    tool_name=tool_call.name,
                    arguments=arguments,
                    db=db,
                    user=user,
                    session=session,
                )

                events.append({
                    "type": "tool_completed",
                    "tool_name": tool_call.name,
                    "result": tool_result,
                })

                logger.info(
                    "Tool result: %s",
                    tool_result,
                )

                status = tool_result.get("status")

                # ---------------------------------------------
                # Tool needs more information
                # ---------------------------------------------

                if status == "needs_input":

                    events.append({
                        "type": "needs_input",
                        "tool_name": tool_call.name,
                        "result": tool_result,
                    })

                    return {
                        "status": "needs_input",
                        "answer": tool_result.get("message"),
                        "data": tool_result.get(
                            "data",
                            {},
                        ),
                        "events": events,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": total_tokens,
                    }

                tool_outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": json.dumps(
                            tool_result,
                            default=str,
                        ),
                    }
                )

            response = await client.responses.create(
                model=settings.DEPLOYMENT_NAME,
                previous_response_id=response.id,
                input=tool_outputs,
                tools=TOOLS,
            )

            input_tokens += response.usage.input_tokens
            output_tokens += response.usage.output_tokens
            total_tokens += response.usage.total_tokens

        logger.warning(
            "Maximum agent iterations reached "
            "session_id=%s",
            session.id,
        )

        return {
            "status": "max_iterations",
            "answer": (
                response.output_text
                if response.output_text
                else "Maximum agent iterations reached."
            ),
            "data": {},
            "events": events,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        }