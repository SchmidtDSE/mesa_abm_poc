from functools import partial
from multiprocessing import Pool
from typing import Any, Iterable, Mapping
import dill  # More robust than pickle for class serialization
import tqdm

from mesa.batchrunner import _make_model_kwargs, _collect_data
from mesa import Model


def batch_run_serialized(
    model_cls: type[Model],
    parameters: Mapping[str, Any | Iterable[Any]],
    number_processes: int | None = 1,
    iterations: int = 1,
    data_collection_period: int = -1,
    max_steps: int = 1000,
    display_progress: bool = True,
) -> list[dict[str, Any]]:
    """Batch run a mesa model with a set of parameter values."""

    # Serialize the model class state
    model_cls_serialized = dill.dumps(model_cls)

    runs_list = []
    run_id = 0
    for iteration in range(iterations):
        for kwargs in _make_model_kwargs(parameters):
            runs_list.append((run_id, iteration, kwargs))
            run_id += 1

    process_func = partial(
        _model_run_func,
        model_cls_serialized,  # Pass serialized class instead of class directly
        max_steps=max_steps,
        data_collection_period=data_collection_period,
    )

    results: list[dict[str, Any]] = []

    with tqdm(total=len(runs_list), disable=not display_progress) as pbar:
        if number_processes == 1:
            # For single process, use original class
            process_func = partial(
                _model_run_func,
                model_cls,
                max_steps=max_steps,
                data_collection_period=data_collection_period,
            )
            for run in runs_list:
                data = process_func(run)
                results.extend(data)
                pbar.update()
        else:
            with Pool(number_processes) as p:
                for data in p.imap_unordered(process_func, runs_list):
                    results.extend(data)
                    pbar.update()

    return results


# Modify _model_run_func to handle serialized class
def _model_run_func(
    model_cls_or_serialized, run_data, max_steps, data_collection_period
):
    run_id, iteration, kwargs = run_data

    # Deserialize if necessary
    if isinstance(model_cls_or_serialized, bytes):
        model_cls = dill.loads(model_cls_or_serialized)
    else:
        model_cls = model_cls_or_serialized

    model = model_cls(**kwargs)

    while model.running and model.steps <= max_steps:
        model.step()

    data = []
    steps = list(range(0, model.steps, data_collection_period))
    if not steps or steps[-1] != model.steps - 1:
        steps.append(model.steps - 1)

    for step in steps:
        model_data, all_agents_data = _collect_data(model, step)

        # If there are agent_reporters, then create an entry for each agent
        if all_agents_data:
            stepdata = [
                {
                    "RunId": run_id,
                    "iteration": iteration,
                    "Step": step,
                    **kwargs,
                    **model_data,
                    **agent_data,
                }
                for agent_data in all_agents_data
            ]
        # If there is only model data, then create a single entry for the step
        else:
            stepdata = [
                {
                    "RunId": run_id,
                    "iteration": iteration,
                    "Step": step,
                    **kwargs,
                    **model_data,
                }
            ]
        data.extend(stepdata)

    return data
