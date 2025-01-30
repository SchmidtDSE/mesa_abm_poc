from vegetation.config.stages import LifeStage

JOTR_JUVENILE_AGE = 3
JOTR_REPRODUCTIVE_AGE = 30
JOTR_SEED_DISPERSAL_DISTANCE = 30

# TODO: Refactor to be more like a config
# Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/14
# This is a temporary solution to get the transition rates to be
# valid for the JOTR model, but this doesn't scale well - we need this
# to probably be more abstract and use a config for at least our initial

def get_jotr_seeds_expected_value():
    ''' expected value for seeds per tree, will then be drawn from a Poisson distribution in model.py''' 
    return 100

def get_jotr_dispersal_rate() -> float:
    '''caching of seeds'''
    rate = 0.95*0.84 #(van der Wall, 2006)
    return rate

def get_jotr_germination_rate(age) -> float:
    ''' germination of cached seeds'''
    if age > 3:
        rate = 0
    else:
        rate = 0.004 #including the effects of rodents and climate (van der Wall, 2006)
    return rate



def get_jotr_survival_rate(life_stage):
    if life_stage == LifeStage.SEEDLING:
        rate = (0.45 + 0.31)/2 #calculate mean of year 1 and year to from Esque et al (2015)
    if life_stage == LifeStage.JUVENILE:
        rate = (1 - 0.025) #mortality of 2.5% each year (Esque et al, 2015)
    if life_stage == LifeStage.ADULT:
        rate = 0.97
    return rate



