from simulation import Simulation, RESULTS_DIR, META_LOG_FILE, CONFIG_LOG_DIR, SINGLE_THREAD_SIM_NAME_FORMAT, \
    MULTI_THREAD_SIM_NAME_FORMAT
from sim_config import SimConfig

import sys
import os
from datetime import datetime
import multiprocessing
import json
import pathlib


class SimProcess(multiprocessing.Process):
    def __init__(self, thread_id, name, configuration, sim_dir_path):
        multiprocessing.Process.__init__(self)
        self.thread_id = thread_id
        self.name = name
        self.config = configuration
        self.sim_path = sim_dir_path

    def run(self):
        print("Starting " + self.name)
        simulation = Simulation(self.config, self.sim_path)
        simulation.run()
        simulation.save_stats()
        print("Exiting " + self.name)


if __name__ == "__main__":
    time = datetime.now().strftime("%y-%m-%d_%H:%M:%S")

    loads = list(range(50, 150, 10))
    threads = []
    cores = None
    targets = None
    RTTs = None
    credits_list = None
    description = ""

    path_to_sim = os.path.relpath(pathlib.Path(__file__).resolve().parents[1], start=os.curdir)

    if os.path.isfile(sys.argv[1]):
        cfg_json_fp = open(sys.argv[1], "r")
        cfg_json = cfg_json_fp.read()
        cfg_json_fp.close()

    if "-varycores" in sys.argv:
        cores = [4, 8, 12, 16, 17, 18, 19, 20, 21, 22, 23, 24, 28, 32] #list(range(4, 36, 4))
        sys.argv.remove("-varycores")
        if "-varytarget" in sys.argv or "-varyRTT" in sys.argv or "-varycredits" in sys.argv:
            print("can't have multiple vary options enabled")
            exit(1)

    if "-varytarget" in sys.argv:
        targets = [5000, 8000, 10000, 12000, 15000]
        sys.argv.remove("-varytarget")
        if "-varyRTT" in sys.argv or "-varycredits" in sys.argv:
            print("can't have varyRTT and varytarget both enabled")
            exit(1)

    if "-varyRTT" in sys.argv:
        RTTs = [5000, 10000, 15000, 20000, 25000, 30000, 35000, 40000]
        sys.argv.remove("-varyRTT")
        if "-varycredits" in sys.argv:
            print("can't have multiple vary options enabled")
            exit(1)

    if "-varycredits" in sys.argv:
        credits_list = [0, 50, 100, 150, 175, 200, 225, 250]
        sys.argv.remove("-varycredits")

    if len(sys.argv) > 2:
        name = SINGLE_THREAD_SIM_NAME_FORMAT.format(os.uname().nodename, time)
        if not os.path.isdir(RESULTS_DIR.format(path_to_sim)):
            os.makedirs(RESULTS_DIR.format(path_to_sim))
        meta_log = open(META_LOG_FILE.format(path_to_sim), "a")
        meta_log.write("{}: {}\n".format(name, sys.argv[2]))
        meta_log.close()
        description = sys.argv[2]


    if cores is not None:
        for i, core_num in enumerate(cores):
            name = MULTI_THREAD_SIM_NAME_FORMAT.format(os.uname().nodename, time, i)

            if os.path.isfile(sys.argv[1]):
                cfg = json.loads(cfg_json, object_hook=SimConfig.decode_object)
                if cfg.reallocation_replay:
                    name_parts = cfg.reallocation_record.split("_", 1)
                    cfg.reallocation_record = MULTI_THREAD_SIM_NAME_FORMAT.format(name_parts[0], name_parts[1], i)
                cfg.num_threads = core_num
                if cfg.num_queues != 1:
                    cfg.num_queues = core_num
                cfg.mapping = list(range(core_num))
                cfg.set_ws_permutation()
                cfg.name = name
                cfg.description = description
                cfg.progress_bar = (i == 0) and cfg.progress_bar

            else:
                print("Missing or invalid argument")
                exit(1)

            threads.append(SimProcess(i, name, cfg, path_to_sim))
    elif targets is not None:
        for i, target in enumerate(targets):
            name = MULTI_THREAD_SIM_NAME_FORMAT.format(os.uname().nodename, time, i)

            if os.path.isfile(sys.argv[1]):
                cfg = json.loads(cfg_json, object_hook=SimConfig.decode_object)
                if cfg.reallocation_replay:
                    name_parts = cfg.reallocation_record.split("_", 1)
                    cfg.reallocation_record = MULTI_THREAD_SIM_NAME_FORMAT.format(name_parts[0], name_parts[1], i)
                cfg.BREAKWATER_TARGET_DELAY = target
                cfg.name = name
                cfg.progress_bar = (i == 0) and cfg.progress_bar
                cfg.description = description

            else:
                print("Missing or invalid argument")
                exit(1)

            threads.append(SimProcess(i, name, cfg, path_to_sim))

    elif RTTs is not None:
        for i, RTT in enumerate(RTTs):
            name = MULTI_THREAD_SIM_NAME_FORMAT.format(os.uname().nodename, time, i)

            if os.path.isfile(sys.argv[1]):
                cfg = json.loads(cfg_json, object_hook=SimConfig.decode_object)
                if cfg.reallocation_replay:
                    name_parts = cfg.reallocation_record.split("_", 1)
                    cfg.reallocation_record = MULTI_THREAD_SIM_NAME_FORMAT.format(name_parts[0], name_parts[1], i)
                cfg.RTT = RTT
                cfg.name = name
                cfg.progress_bar = (i == 0) and cfg.progress_bar
                cfg.description = description

            else:
                print("Missing or invalid argument")
                exit(1)

            threads.append(SimProcess(i, name, cfg, path_to_sim))
    elif credits_list is not None:
        for i, credit_num in enumerate(credits_list):
            name = MULTI_THREAD_SIM_NAME_FORMAT.format(os.uname().nodename, time, i)

            if os.path.isfile(sys.argv[1]):
                cfg = json.loads(cfg_json, object_hook=SimConfig.decode_object)
                if cfg.reallocation_replay:
                    name_parts = cfg.reallocation_record.split("_", 1)
                    cfg.reallocation_record = MULTI_THREAD_SIM_NAME_FORMAT.format(name_parts[0], name_parts[1], i)
                cfg.SERVER_INITIAL_CREDITS = credit_num
                cfg.name = name
                cfg.progress_bar = (i == 0) and cfg.progress_bar
                cfg.description = description

            else:
                print("Missing or invalid argument")
                exit(1)

            threads.append(SimProcess(i, name, cfg, path_to_sim))
    else:
        for i, load in enumerate(loads):
            name = MULTI_THREAD_SIM_NAME_FORMAT.format(os.uname().nodename, time, i)

            if os.path.isfile(sys.argv[1]):
                cfg = json.loads(cfg_json, object_hook=SimConfig.decode_object)
                if cfg.reallocation_replay:
                    name_parts = cfg.reallocation_record.split("_", 1)
                    cfg.reallocation_record = MULTI_THREAD_SIM_NAME_FORMAT.format(name_parts[0], name_parts[1], i)
                cfg.avg_system_load = load / 100
                cfg.name = name
                cfg.progress_bar = (i == 0) and cfg.progress_bar
                cfg.description = description

            else:
                print("Missing or invalid argument")
                exit(1)

            threads.append(SimProcess(i, name, cfg, path_to_sim))

    threads.reverse()
    for thread in threads:
        thread.start()

    if not(os.path.isdir(CONFIG_LOG_DIR.format(path_to_sim))):
        os.makedirs(CONFIG_LOG_DIR.format(path_to_sim))
    config_record = open(
        CONFIG_LOG_DIR.format(path_to_sim) + SINGLE_THREAD_SIM_NAME_FORMAT.format(os.uname().nodename, time) + ".json",
        "w")
    config_record.write(cfg_json)
    config_record.close()
