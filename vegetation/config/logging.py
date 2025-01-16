# logging.py

import logging
import json
import string
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


STD_FORMATTERS = {"STD_INDENT": "    "}


class FallbackFormatter(string.Formatter):
    def get_field(self, field_name, args, kwargs):
        # Check if field_name contains dots (e.g., 'agent.unique_id')
        if "." in field_name:
            obj_name, attr = field_name.split(".", 1)
            try:
                # First check context dictionary
                if obj_name in kwargs:
                    obj = kwargs[obj_name]
                    # Try getting nested attribute
                    for part in attr.split("."):
                        obj = getattr(obj, part)
                    return obj, field_name
            except (KeyError, AttributeError):
                # If not in context, check if object itself is passed
                if hasattr(kwargs.get("_obj"), obj_name):
                    obj = getattr(kwargs["_obj"], obj_name)
                    # Try getting nested attribute
                    for part in attr.split("."):
                        obj = getattr(obj, part)
                    return obj, field_name

        # Default lookup in kwargs
        try:
            return super().get_field(field_name, args, kwargs)
        except (KeyError, AttributeError) as e:
            raise ValueError(
                f"Could not find {field_name} in context or object attributes"
            ) from e


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
    _fallback_formatter = FallbackFormatter()

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

    def log_agent_event(self, agent, event_type: AgentEventType, context: Dict = None):
        template = self.config.get_template(agent.__class__.__name__, event_type.value)

        if not agent.log_level:
            return

        if template and context:
            context = context or {}
            context["_obj"] = agent
            context.update(STD_FORMATTERS)
            message = self._fallback_formatter.format(template, **context)
            self.logger.log(agent.log_level, message)


class SimLogger:
    _instance = None
    _fallback_formatter = FallbackFormatter()

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

    def log_sim_event(
        self, sim, event_type: SimEventType, context: Dict = None, level=logging.INFO
    ):
        template = self.config.get_template(sim.__class__.__name__, event_type.value)

        if template and context:
            context = context or {}
            context["_obj"] = sim
            context.update(STD_FORMATTERS)
            message = self._fallback_formatter.format(template, **context)
            self.logger.log(sim.log_level, message)
