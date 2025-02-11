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
   a. If the agent is a `SEED`
   - Convert to `SEEDLING` with germination probability $p_G, remain `SEED` otherwise
     b. If agent is a tree
   - Calculate survival probabilty $p_S$ for life stage
   - Kill agent with probability $(1 - p_S)$
4. Increment age by one
5. Update life stages based on age as specified above. Note that age classes for Seeds and Seedlings do overlap, here the life stage is determined by germination process
6. If agent is an `ADULT` tree that has not flowered the year before (`flowering == 0`), disperse seeds with a flowering probabily $p_F$.

# Parametrization

The `step()` function is somewhat ecosystem-agnostic. Parametrization of the Joshua Tree model happens in the `transitions.py` file. `transitions.py` contains a section of global parameters at the top and functions below

## Parameters

@mzomer This is something where you could fill in the blanks to document these values

| **Parameter**                      | **Current value**      | **Sources, Justification**                                   |
| ---------------------------------- | ---------------------- | ------------------------------------------------------------ |
| `JOTR_JUVENILE_AGE`                | 3                      |                                                              |
| `JOTR_REPRODUCTIVE_AGE`            | 30                     |                                                              |
| `JOTR_SEED_DISPERSAL_DISTANCE`     | 30                     |                                                              |
| `JOTR_SEEDS_EXPECTED_VALUE_MAST`   | 4000                   |                                                              |
| `JOTR_SEEDS_EXPECTED_VALUE_NORMAL` | 40                     |                                                              |
| `JOTR_MAST_YEAR_PROB`              | 0.2                    |                                                              |
| `JOTR_SEED_MAX_AGE`                | 2                      |                                                              |
| `JOTR_BASE_GERMINATION_RATE`       | 0.004                  |                                                              |
| `JOTR_BASE_SURVIVAL_SEEDLING`      | $ \frac{.45 + .31}{2}$ | calculate mean of year 1 and year to from Esque et al (2015) |
| `JOTR_BASE_SURVIVAL_JUVENILE`      | 0.975                  | mortality of 2.5% each year (Esque et al, 2015)              |
| `JOTR_BASE_SURVIVAL_ADULT`         | 0.97                   |                                                              |

## Functions

_At this point I feel these functions are self-explanatory, so I won't explain them any further_
