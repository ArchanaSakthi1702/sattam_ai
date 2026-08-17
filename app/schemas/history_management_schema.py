from dataclasses import dataclass

@dataclass
class ChatHistoryConfig:
    history_token_budget: int
    summary_trigger_tokens: int
    max_summary_input_tokens: int
