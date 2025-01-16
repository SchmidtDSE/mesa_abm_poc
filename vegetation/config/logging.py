# logging.py

import logging
import json
from enum import Enum, auto
from typing import Dict, Optional


class AgentEventType(Enum):
    ON_CREATE = "on_create"
    ON_STEP = "on_step"
    ON_DEATH = "on_death"
    ON_TRANSITION = "on_transition"
    ON_DISPERSE = "on_disperse"


class SimEventType(Enum):
    ON_START = "on_start"
    ON_STEP = "on_step"
    ON_END = "on_end"


tst_json = {
    "JoshuaTreeAgent": {
        "on_create": "{indent}🌱 Agent {id} created at ({x}, {y})",
        "on_death": "{indent}💀 Agent {id} died (survival {survival_rate:.2f})",
        "on_transition": "{indent}🔄 Agent {id} promoted to {new_stage}",
    },
    "Vegetation": {
        "on_start": "🌵 Simulation started (maximum number of steps: {num_steps})",
        "on_step": "🕰️ Time passes. It is the year {year}"},
}


class LogConfig:
    _instance = None

    @classmethod
    def initialize(cls, config_path):
        instance = cls()
        instance.load_config(config_path)
        return instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._templates = {}

        return cls._instance

    def load_config(self, config_path: str):
        with open(config_path, "r") as f:
            self._templates.update(json.load(f))

    def update_template(self, agent_type: str, event_type: str, template: str):
        if agent_type not in self._templates:
            self._templates[agent_type] = {}
        self._templates[agent_type][event_type] = template

    def get_template(self, agent_type: str, event_type: str) -> Optional[str]:
        return self._templates.get(agent_type, {}).get(event_type)


class AgentLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.config = LogConfig()
            cls._instance._setup_logger()
        return cls._instance

   def _setup_logger(self):
        self.logger = logging.getLogger("agent_logger")
        self.logger.setLevel(logging.INFO)

        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def log_agent_event(
        self,
        agent,
        event_type: AgentEventType,
        context: Dict = None
    ):
        template = self.config.get_template(agent.__class__.__name__, event_type.value)

        if not agent.log_level:
            return

        if template and context:
            message = template.format(**context)
            self.logger.log(agent.log_level, message)

class SimLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.config = LogConfig()
            cls._instance._setup_logger()
        return cls._instance

   def _setup_logger(self):
        self.logger = logging.getLogger("sim_logger")
        self.logger.setLevel(logging.INFO)

        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.config = LogConfig()
            cls._instance._setup_logger()
        return cls._instance

    def log_sim_event(
        self, sim, event_type: SimEventType, context: Dict = None, level=logging.INFO
    ):
        template = self.config.get_template(sim.__class__.__name__, event_type.value)
        if template and context:
            message = template.format(**context)
            self.logger.log(level, message)
