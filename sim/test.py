import os
import pathlib
import sys
import json

from sim_config import SimConfig

if __name__ == "__main__":

    path_to_sim = os.path.relpath(pathlib.Path(__file__).resolve().parents[1], start=os.curdir)
    run_name = "test"

    if os.path.isfile(sys.argv[1]):
        cfg_json = open(sys.argv[1], "r")
        cfg = json.load(cfg_json, object_hook=SimConfig.decode_object)
        cfg.name = run_name
        cfg_json.close()

    print(cfg.breakwater_enabled)
    print(cfg.RTT)
    print(cfg.NUM_CLIENTS)
