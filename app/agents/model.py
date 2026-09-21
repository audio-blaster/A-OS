from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class Agent:

    name: str
    goal: str

    id: str = field(
        default_factory=lambda: str(uuid4())
    )

    description: str = ""

    capabilities: list = field(
        default_factory=list
    )

    knowledge_sources: list = field(
        default_factory=list
    )

    channels: list = field(
        default_factory=list
    )

    configuration: dict = field(
        default_factory=dict
    )

    status: str = "DRAFT"

    version: str = "1.0"

    owner_id: str | None = None

    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    updated_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )