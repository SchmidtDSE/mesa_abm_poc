from collections.abc import Iterable, Mapping
from functools import partial
from multiprocessing import Pool
from typing import Any

from mesa.batchrunner import _collect_data, _make_model_kwargs
from mesa.model import Model
from tqdm.auto import tqdm


def jotr_batch_run(
    model_cls: type[Model],
    model_parameters: Mapping[str, Any | Iterable[Any]],
    # We still retain the Optional[int] because users may set it to None (i.e. use all CPUs)
    class_parameters_dict: dict[str, Any],
    number_processes: int | None = 1,
    iterations: int = 1,
    data_collection_period: int = -1,
    max_steps: int = 1000,
    display_progress: bool = True,
) -> list[dict[str, Any]]:
    """Batch run a mesa model with a set of parameter values.

    Args:
        model_cls (Type[Model]): The model class to batch-run
        parameters (Mapping[str, Union[Any, Iterable[Any]]]): Dictionary with model parameters over which to run the model. You can either pass single values or iterables.
        number_processes (int, optional): Number of processes used, by default 1. Set this to None if you want to use all CPUs.
        iterations (int, optional): Number of iterations for each parameter combination, by default 1
        data_collection_period (int, optional): Number of steps after which data gets collected, by default -1 (end of episode)
        max_steps (int, optional): Maximum number of model steps after which the model halts, by default 1000
        display_progress (bool, optional): Display batch run process, by default True

    Returns:
        List[Dict[str, Any]]

    Notes:
        batch_run assumes the model has a `datacollector` attribute that has a DataCollector object initialized.

    """
    runs_list = []
    run_id = 0
    for iteration in range(iterations):
        for kwargs in _make_model_kwargs(model_parameters):
            runs_list.append((run_id, iteration, kwargs))
            run_id += 1

    process_func = partial(
        _jotr_model_run_func,
        model_cls,
        class_parameters_dict,
        max_steps=max_steps,
        data_collection_period=data_collection_period,
    )

    results: list[dict[str, Any]] = []

    with tqdm(total=len(runs_list), disable=not display_progress) as pbar:
        if number_processes == 1:
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


def _jotr_model_run_func(
    vegetation_cls, class_parameters_dict, run_data, max_steps, data_collection_period
):
    run_id, iteration, kwargs = run_data

    # This is a hack to get the parallel pool to work with class level
    # attributes - at this point, it's a hack of a hack which was meant to
    # keep the vegetation run attributes seperate from higher level attributes that
    # don't affect the simulation. But this will be deprecated in the future.
    vegetation_cls.set_attribute_encodings(
        attribute_encodings=class_parameters_dict["attribute_encodings"]
    )
    vegetation_cls.set_aoi_bounds(aoi_bounds=class_parameters_dict["aoi_bounds"])
    vegetation_cls.set_cell_attributes_to_save(
        cell_attributes_to_save=class_parameters_dict["cell_attributes_to_save"]
    )

    vegetation = vegetation_cls(**kwargs)

    while vegetation.running and vegetation.steps <= max_steps:
        vegetation.step()

    data = []
    steps = list(range(0, vegetation.steps, data_collection_period))
    if not steps or steps[-1] != vegetation.steps - 1:
        steps.append(vegetation.steps - 1)

    for step in steps:
        vegetation_data, __all_agents_data = _collect_data(vegetation, step)

        # # If there are agent_reporters, then create an entry for each agent
        # if all_agents_data:
        #     stepdata = [
        #         {
        #             "RunId": run_id,
        #             "iteration": iteration,
        #             "Step": step,
        #             **kwargs,
        #             **vegetation_data,
        #             **agent_data,
        #         }
        #         for agent_data in all_agents_data
        #     ]
        # # If there is only vegetation data, then create a single entry for the step
        # else:
        stepdata = [
            {
                "RunId": run_id,
                "iteration": iteration,
                "Step": step,
                **kwargs,
                **vegetation_data,
            }
        ]
        data.extend(stepdata)

    return data
