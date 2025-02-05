from pydantic import BaseModel


class LocalResponseObjectiveConfig(BaseModel):
    rolling_message_window: int = 5
    base: float = 0.55
