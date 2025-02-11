This is the model documentation of the initial model version 0 of the Joshua Tree case study

# Model structure

This is an agent-based model. Each agent represents on organism of Joshua Tree, which can exist in one of jour life stages:

1. SEED (Age 0 - 3)
2. SEEDLING (Age 1 - 2)
3. JUVENILE (Age 3 - 30)
4. ADULT (Age > 30)

Each agent so far has an attribute `age` (see above) as well as an attribute `flowering` (see below)

The agents are organised on a grid. Note that agends are not explicit in space within each grid cells and do not move. Each gridcell can be occupied by multiple agents. Grid cell are explicit in space and interact with their neighbouring cells.

# The `step()` function

The central model function us the `step()` function within `joshua_tree_agent.py`. A model step represents a year and the `step()` function is executed for each agent each model step. It consits of the following steps:

1. Check if the agent is alive. If the agent is dead, proceed to the next agent
2. Check in which grid cell the agent lives
3. Check if the agent is a `SEED` or a tree (`SEEDLING`, `JUVENILE` or `ADULT`).
   a. If the agent is a `SEED` - Convert to `SEEDLING` with germination probability $p_G, remain `SEED` otherwise
    b. If agent is a tree
        - Calculate survival probabilty $p_S$ for life stage - Kill agent with probability $(1 - p_S)$

# Parametrization

The `step()` function is ecosystem-agnostic. Parametrization of the Joshua Tree model happens in the `transitions.py` file.

## Parameters

## Functions
