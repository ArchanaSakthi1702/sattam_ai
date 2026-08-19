from enum import StrEnum


class AgentStatus(StrEnum):
    COMPLETED = "completed"
    NEEDS_INPUT = "needs_input"
    MAX_ITERATIONS = "max_iterations"


class EventType(StrEnum):
    FINAL = "final"
    STATUS = "status"
    TOOL_STARTED = "tool_started"
    TOOL_COMPLETED = "tool_completed"
    NEEDS_INPUT = "needs_input"


class ToolExecutionStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"