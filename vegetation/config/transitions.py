from vegetation.config.stages import LifeStage

JOTR_JUVENILE_AGE = 3
JOTR_REPRODUCTIVE_AGE = 30
JOTR_SEED_DISPERSAL_DISTANCE = 30

# TODO: Refactor to be more like a config
# Issue URL: https://github.com/SchmidtDSE/mesa_abm_poc/issues/14
# This is a temporary solution to get the transition rates to be
# valid for the JOTR model, but this doesn't scale well - we need this
# to probably be more abstract and use a config for at least our initial


def get_jotr_germination_rate():
    rate = 0.8
    return rate


def get_jotr_survival_rate(life_stage):
    if life_stage == LifeStage.SEEDLING:
        rate = 0.55
    if life_stage == LifeStage.JUVENILE:
        rate = 0.8
    if life_stage == LifeStage.ADULT:
        rate = 0.97
    return rate


def get_jotr_adult_poisson_lambda():
    return 10
