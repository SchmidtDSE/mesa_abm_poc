This is the model documentation of the initial model version 0 of the Joshua Tree case study

# Model structure

This is an agent-based model. Each agent represents on organism of Joshua Tree, which can exist in one of four life stages:

1. SEED (Age 0 - 3)
2. SEEDLING (Age 1 - 2)
3. JUVENILE (Age 3 - 30)
4. ADULT (Age > 30)

Each agent so far has an attribute `age` (see above).

The agents are organised on a grid. Note that agents are not explicit in space within each grid cells and do not move. Each gridcell can be occupied by multiple agents. Grid cells are explicit in space and interact with their neighbouring cells.

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
6.  If agent is an `ADULT` tree and we are in a mast flowering event, disperse seeds with a flowering probability $p_F$. Number of seeds is drawn from a Poisson distribution with expected value $\lambda$

# Parametrization

The `step()` function is somewhat ecosystem-agnostic. Parametrization of the Joshua Tree model happens in the `transitions.py` file. `transitions.py` contains a section of global parameters at the top and functions below

## Parameters

## Functions

_Most functions at this point are pretty self-explanatory, so I won't explain them any further_

- `get_jotr_number_seeds(expected_value)`: Draws number of seeds to be dispersed from a Poisson distribution

## Citations

Borchert, Mark I., and Lesley A. DeFalco. “Yucca Brevifolia Fruit Production, Predispersal Seed Predation, and Fruit Removal by Rodents during Two Years of Contrasting Reproduction.” American Journal of Botany 103, no. 5 (May 2016): 830–36. https://doi.org/10.3732/ajb.1500516.

DeFalco, L. A., Esque, T. C., Scoles-Sciulla, S. J., & Rodgers, J. (2010). Desert wildfire and severe drought diminish survivorship of the long-lived Joshua tree (Yucca brevifolia; Agavaceae). American Journal of Botany, 97(2), 243–250. https://doi.org/10.3732/ajb.0900032

Esque, Todd C., Philip A. Medica, Daniel F. Shryock, Lesley A. DeFalco, Robert H. Webb, and Richard B. Hunter. “Direct and Indirect Effects of Environmental Variability on Growth and Survivorship of Pre‐reproductive Joshua Trees, Yucca Brevifolia Engelm. (Agavaceae).” American Journal of Botany 102, no. 1 (January 2015): 85–91. https://doi.org/10.3732/ajb.1400257.

Reynolds, M. Bryant J., Lesley A. DeFalco, and Todd C. Esque. “Short Seed Longevity, Variable Germination Conditions, and Infrequent Establishment Events Provide a Narrow Window for Yucca Brevifolia (Agavaceae) Recruitment.” American Journal of Botany 99, no. 10 (October 2012): 1647–54. https://doi.org/10.3732/ajb.1200099.

St. Clair, S. B., & Hoines, J. (2018). Reproductive ecology and stand structure of Joshua tree forests across climate gradients of the Mojave Desert. PLOS ONE, 13(2), e0193248. https://doi.org/10.1371/journal.pone.0193248

U.S. Fish and Wildlife Service. 2023. Species Status Assessment Report for the Joshua tree
(Yucca brevifolia). Version 2.0, February 2023. U.S. Fish and Wildlife Service, Pacific
Southwest Region, Sacramento, California. xii + 177 pp.

Vander Wall, Stephen B., Todd Esque, Dustin Haines, Megan Garnett, and Ben A. Waitman. “Joshua Tree (Yucca Brevifolia) Seeds Are Dispersed by Seed-Caching Rodents.” Ecoscience 13, no. 4 (December 2006): 539–43. https://doi.org/10.2980/1195-6860(2006)13[539:JTYBSA]2.0.CO;2.
