## Logging Configuration

Logging is configurable within the simulation using the following workflow.


#### Logging Pattern

First, find a reasonable location to trigger a log event - this should be associated with a particular model 'event', whether it occurs to the `agent` or to the `sim` itself. For eg, the `sim` will 'experience' a step, and during that step, each `agent` will make a step - but we likely want to log different things at the time of an agent step and a sim step.

Accordingly, at the top of `vegetation/config/logging.py`, we define a events as:

```

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

```

We will use these later on to determine the format, flavor, and logging level of the log message we issue when the given event occurs. 

#### JSON Configuration

For each particular logging event defined, we have a representative key / value entry within `vegetation/config/logging_config.json`. For eg, for the event `AgentEventType.ON_SURVIVE`, we have defined:

```json
{
    "agent": {
        "JoshuaTreeAgent": {
            "on_survive": "{STD_INDENT}💪 Agent {agent.unique_id} survived! ({agent.life_stage} w/ survival rate {survival_rate:.2f})",
        ...
    },
    "sim": ...
}
```

Note that in this example we added `...` to signify the rest of the json config for the other event types, for clarity. 

There are a couple of conventions we assume (logic defined by `vegetation/config/logging.py`). These log strings will be passed to `string.format` with some custom logic - any variables defined within curly braces will be obtained in one of two ways:

- First, if they are a single variable name with no `.` within the variable (for eg `survival_rate`), the logger will expect to be passed this variable within a keyword argument defined in `context` dict (more on that below).

- If the variable contains a `.` - for eg `agent.life_stage`, this will be assumed to be obtained from within the agent method where the logging is triggered. The logging event has access to the agent object by default, so these don't need to be passed in `context` - but they do need to exist as a valid attribute within the `agent` class (for example, `agent.life_stage` must be valid and existing).

    - _For now, this only works one level deep and doesn't support execution - for eg, `agent.indices.min_index` or `agent.indices[0]` or `int(agent.life_stage)` or similar will not work. We could investigate this if it seems useful_, though.

#### Triggering a Log

The agent(s) and simulation both have their own loggers - `agent_logger` and `sim_logger`, respectively. These can be accessed at any point to issue a log event according to the event type passed along, as follows:

```
self.agent_logger.log_agent_event(
    self,
    AgentEventType.ON_SURVIVE,
    context={"survival_rate": survival_rate},
)
```

Using this method call, the `agent_logger` will grab the appropriate log method defined in `logging_config.json`, according to the log event type (here `AgentEventType.ON_SURVIVE`), and pass along the agent itself (here, `self`, since this method is triggered from within the agent class method `on_step`) and any additional context necessary (here `survival_rate`, since this is ephemeral and not stored by the agent - but do we want to log it, so we pass it for just this log event).

