This is the model documentation of the initial model version 0 of the Joshua Tree case study

# Model structure

This is an agent-based model. Each agent represents on organism of Joshua Tree, which can exist in one of jour life stages:

1. SEED (Age 0 - 3)
2. SEEDLING (Age 1 - 2)
3. JUVENILE (Age 3 - 30)
4. ADULT (Age > 30)

Each agent so far has an attribute `age` (see above).

The agents are organised on a grid. Note that agends are not explicit in space within each grid cells and do not move. Each gridcell can be occupied by multiple agents. Grid cell are explicit in space and interact with their neighbouring cells.

# Model structure

We have two main classes: `JoshuaTreeAgent` and `Vegetation`. Every model step (year), the `Vegetation` object steps forward and activates all agents (`Vegetation.step()`). Then each agent takes a step (`JoshuaTreeAgent.step()`).

## The `Vegetation.step()` function

The `Vegetation` class represent the landscape level and is found in `vegetation.py`. Each year, the `Vegetation` checks if a mast flowering year has occured the previous year. If no, it determines if a mast flowering event will occur in the current year, with `JOTR_MAST_YEAR_PROB`. Then we proceed to the agent level.

## The `JoshuaTreeAgent.step()` function

The central model function is the `JoshuaTreeAgent.step()` function within `joshua_tree_agent.py`. It is executed for each agent each model step and consists of the following steps:

1.  Check if the agent is alive. If the agent is dead, proceed to the next agent
2.  Check in which grid cell the agent lives
3.  Check if the agent is a `SEED` or a tree (`SEEDLING`, `JUVENILE` or `ADULT`).

    a. If the agent is a `SEED`

    - Convert to `SEEDLING` with germination probability $p_G$, remain `SEED` otherwise
    - If not germinate, kill with $p = 0.5$. This represent depletion of seeds by rodents and other biotic factors

    b. If agent is a tree

    - Calculate survival probabilty $p_S$ for life stage
    - Kill agent with probability $(1 - p_S)$

4.  Increment age by one
5.  Update life stages based on age as specified above. Note that age classes for Seeds and Seedlings do overlap, here the life stage is determined by germination process
6.  If agent is an `ADULT` tree and we are in a mast flowering event, disperse seeds with a flowering probability $p_F$. Number of seeds is drawn from a Poisson distribution with expected value $\lamba$

# Parametrization

The `step()` function is somewhat ecosystem-agnostic. Parametrization of the Joshua Tree model happens in the `transitions.py` file. `transitions.py` contains a section of global parameters at the top and functions below

## Parameters

@mzomer This is something where you could fill in the blanks to document these values

| **Parameter**                    | **Current value** | **Sources, Justification**                                   |
| -------------------------------- | ----------------- | ------------------------------------------------------------ |
| `JOTR_JUVENILE_AGE`              | 3                 |                                                              |
| `JOTR_REPRODUCTIVE_AGE`          | 30                |                                                              |
| `JOTR_SEED_DISPERSAL_DISTANCE`   | 30                |                                                              |
| `JOTR_SEEDS_EXPECTED_VALUE_MAST` | 4000              |                                                              |
| `JOTR_MAST_YEAR_PROB`            | 0.2               |                                                              |
| `JOTR_AGENT_FLOWERING_PROB`      | 0.8               |                                                              |
| `JOTR_SEED_MAX_AGE`              | 2                 |                                                              |
| `JOTR_BASE_GERMINATION_RATE`     | 0.004             |                                                              |
| `JOTR_BASE_SURVIVAL_SEEDLING`    | $(.45 + .31)/2$   | calculate mean of year 1 and year to from Esque et al (2015) |
| `JOTR_BASE_SURVIVAL_JUVENILE`    | 0.975             | mortality of 2.5% each year (Esque et al, 2015)              |
| `JOTR_BASE_SURVIVAL_ADULT`       | 0.97              |                                                              |

## Functions

_Most functions at this point are pretty self-explanatory, so I won't explain them any further_

- `get_jotr_number_seeds(expected_value)`: Draws number of seeds to be dispersed from a Poisson distribution
