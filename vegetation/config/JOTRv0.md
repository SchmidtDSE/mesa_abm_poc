This is the model documentation of the initial model version 0 of the Joshua Tree case study

# Model structure

This is an agent-based model. Each agent represents on organism of Joshua Tree, which can exist in one of four life stages:

1. SEED (Age 0 - 3)
2. SEEDLING (Age 1 - 2)
3. JUVENILE (Age 3 - 30)
4. ADULT (Age > 30)

Each agent so far has an attribute `age` (see above) as well as an attribute `flowering` (see below)

The agents are organised on a grid. Note that agents are not explicit in space within each grid cells and do not move. Each gridcell can be occupied by multiple agents. Grid cells are explicit in space and interact with their neighbouring cells.

# The `step()` function

The central model function is the `step()` function within `joshua_tree_agent.py`. A model step represents a year and the `step()` function is executed for each agent each model step. It consits of the following steps:

1.  Check if the agent is alive. If the agent is dead, proceed to the next agent
2.  Check in which grid cell the agent lives
3.  Check if the agent is a `SEED` or a tree (`SEEDLING`, `JUVENILE` or `ADULT`).

    a. If the agent is a `SEED`

    - Convert to `SEEDLING` with germination probability $p_G$, remain `SEED` otherwise

    b. If agent is a tree

    - Calculate survival probabilty $p_S$ for life stage
    - Kill agent with probability $(1 - p_S)$

4.  Increment age by one
5.  Update life stages based on age as specified above. Note that age classes for Seeds and Seedlings do overlap, here the life stage is determined by germination process
6.  If agent is an `ADULT` tree that has not flowered the year before (`flowering == 0`), disperse seeds with a flowering probabily $p_F$. Numer of seeds is drawn from a Poisson distribution

# Parametrization

The `step()` function is somewhat ecosystem-agnostic. Parametrization of the Joshua Tree model happens in the `transitions.py` file. `transitions.py` contains a section of global parameters at the top and functions below

## Parameters


| **Parameter**                    | **Current value** | **Sources, Justification**                                   |
| -------------------------------- | ----------------- | ------------------------------------------------------------ |
| `JOTR_JUVENILE_AGE`              | 3                 | U.S. Fish and Wildlife Service, 2023 (page 11), Input by Todd Esque (2015, 2022, pers comm.)|
| `JOTR_REPRODUCTIVE_AGE`          | 30                | U.S. Fish and Wildlife Service, 2023 (page 11), Input by Todd Esque (2015, 2022, pers comm.)|
| `JOTR_SEED_DISPERSAL_DISTANCE`   | 30                | mean maximum dispersal distance was 30.0 ± 16.8 m (Vander Wall et al., 2006, page 541)|
|  secondary dispersal distance    | 10                | transport distance between primary and secondary caches averaged 6-13 m (Vander Wall et al., 2006, page 541)|
| `JOTR_SEEDS_EXPECTED_VALUE_MAST` | 4000              |High flowering year 2013 with 80% trees in bloom. calculate mean number of seeds/tree from two sites in JTNP (4703.5, St. Clair & Hoines, 2018), and calculate predispersal moth predation (19.5% in same year, but different site, Borchert & Defalco 2016 ). In non-mast years, large possibility that all seeds are foraged by rodents (Borchert and DeFalco 2016, p. 833). Trees need at least 1 - 2 years between flowering events to replenish resources (U.S. Fish and Wildlife Service, 2023, page 13: Borchert and DeFalco 2016, p. 831; Smith 2022, pers. comm.)|
| `JOTR_MAST_YEAR_PROB`            | 0.2               | 2 large flowering events each decade (Borchert & Defalco 2016, page 831)|
| `JOTR_SEED_MAX_AGE`              | 3                 |(Reynolds et al. 2012, page 1651)|
|  soil seed viability             | 0.05 yr 1, 0.25 yr 2, 0.003 yr 3 | twelve months in the soil reduced germination to 50-68%, and it dropped to less than 1-3% after 40 mo in the soil (Reynolds et al. 2012, page 1651)|
|  seeds removed by rodents        | 0.95              | 95% of seeds harvested by rodents (Vander Wall et al., 2006, page 541)|
|  seeds cached by rodents         | 0.85              | 84.1 ± 13.1% of removed seeds (range 67.7 to 97.5%) stored in caches (Vander Wall et al., 2006, page 541)|
| `JOTR_BASE_GERMINATION_RATE`     | 0.004             | 0.4% cached seeds germinated, includes the effects of climate and rodent foraging (Vander Wall et al., 2006, page 539, 541)|
| `JOTR_BASE_SURVIVAL_SEEDLING`    | $(.45 + .31)/2$   | calculate mean of year 1 and year to from Esque et al (2015, page 87)|
| `JOTR_BASE_SURVIVAL_JUVENILE`    | 0.975             | mortality of 2.5% each year (Esque et al, 2015, page 87)|
| `JOTR_BASE_SURVIVAL_ADULT`       | 0.97              | estimated survivorship unburned adult plants over 4 years ~90-100%, precipitation deficits reduced surivval in 5th year to ~ 80%, DeFalco et al, 2010, page 247)|

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
