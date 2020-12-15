import os
from pathlib import Path
import re

from yaml import load, FullLoader


def parse_value(val):
    env_variable_regex = re.compile(r"(\w*):\-([\w|\/\\.]*)")
    res = re.findall(env_variable_regex, val)

    env_var = res[0][0]
    env_value = res[0][1]
    return env_var, env_value


def load_conf(filepath):
    conf_values = load(Path(filepath).read_bytes(), Loader=FullLoader)
    for group_params in conf_values.values():
        for val in group_params.values():
            env_var, env_value = parse_value(val)
            if env_var not in os.environ.keys():
                os.environ[env_var] = env_value
    return


