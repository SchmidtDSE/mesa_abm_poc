import logging
import json
import string
from enum import Enum, auto
from typing import Dict, Optional


class AgentEventType(Enum):
    ON_CREATE = "on_create"
    ON_STEP = "on_step"
    ON_SURVIVE = "on_survive"
    ON_DEATH = "on_death"
    ON_TRANSITION = "on_transition"
    ON_DISPERSE = "on_disperse"


class SimEventType(Enum):
    ON_START = "on_start"
    ON_STEP = "on_step"
    ON_END = "on_end"
    ON_MANAGE = "on_manage"


STD_FORMATTERS = {
    "STD_INDENT": "    ",
    "WIDE_INDENT": "        ",
    "VERY_WIDE_INDENT": "            ",
}


class FallbackFormatter(string.Formatter):
    def get_field(self, field_name, args, kwargs):

        try:
            # Check if field_name contains dots (e.g., 'agent.unique_id')
            if "." in field_name:
                obj_name, attr = field_name.split(".", 1)
                assert obj_name in ["agent", "sim"], f"Invalid object name: {obj_name}"
                if hasattr(kwargs.get(obj_name), attr):
                    attr_value = getattr(kwargs[obj_name], attr)
                    return attr_value, field_name
                else:
                    raise AttributeError(
                        f"Could not find {attr} in {obj_name}'s attributes"
                    )
            else:
                return super().get_field(field_name, args, kwargs)
        except (KeyError, AttributeError) as e:
            raise ValueError(
                f"Could not find {field_name} in context or agent's attributes"
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
            cls._instance._agent_templates = {}
            cls._instance._sim_templates = {}
        return cls._instance

    def load_config(self, config_path: str):
        with open(config_path, "r") as f:
            log_config_dict = json.load(f)
            if "agent" in log_config_dict:
                self._agent_templates = log_config_dict["agent"]
            if "sim" in log_config_dict:
                self._sim_templates = log_config_dict["sim"]

    def update_agent_template(self, agent_type: str, event_type: str, template: str):
        if agent_type not in self._templates:
            self._agent_templates[agent_type] = {}
        self._agent_templates[agent_type][event_type] = template

    def update_sim_template(self, sim_type: str, event_type: str, template: str):
        if sim_type not in self._templates:
            self._sim_templates[sim_type] = {}
        self._sim_templates[sim_type][event_type] = template

    def get_agent_template(self, agent_type: str, event_type: str) -> Optional[str]:
        return self._agent_templates.get(agent_type, {}).get(event_type)

    def get_sim_template(self, sim_type: str, event_type: str) -> Optional[str]:
        return self._sim_templates.get(sim_type, {}).get(event_type)


# TODO: Figure out if AgentLogger and SimLogger need to be different classes
# Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/32
# It might make sense to do these in one class


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
        self.logger.propagate = False

        if not self.logger.handlers:
            ch = logging.StreamHandler()
            formatter = logging.Formatter("%(message)s")
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def log_agent_event(self, agent, event_type: AgentEventType, context: Dict = None):

        if not agent.log_level:
            return

        if context is None:
            context = {}

        template = self.config.get_agent_template(
            agent.__class__.__name__, event_type.value
        )

        if template:
            context["agent"] = agent
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
        self.logger.propagate = False

        if not self.logger.handlers:
            ch = logging.StreamHandler()
            formatter = logging.Formatter("%(message)s")
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def log_sim_event(
        self, sim, event_type: SimEventType, context: Dict = None, level=logging.INFO
    ):

        if not sim.log_level:
            return

        if context is None:
            context = {}

        template = self.config.get_sim_template(
            sim.__class__.__name__, event_type.value
        )

        if template:
            context["sim"] = sim
            context.update(STD_FORMATTERS)
            message = self._fallback_formatter.format(template, **context)
            self.logger.log(sim.log_level, message)
