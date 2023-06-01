import numpy as np
import sys
import os
import json

import matplotlib.pyplot as plt
import math
import pandas

import matplotlib.backends.backend_pdf


#RESULTS_DIR_NAME = "results/"
RESULTS_SUBDIR_NAME = "sim_{}/"
THREAD_RUN_FORMAT = "{}_t{}"
TASK_FILE_NAME = "task_times.csv"
CREDITS_FILE_NAME = "credit_pool.csv"
CORES_FILE_NAME = "cores_over_time.csv"
THROUGHPUT_FILE_NAME = "throughput_over_time.csv"

BREAKWATER_INFO_FILE_NAME = 'breakwater_info.csv'

def read_files(run_name):
    """
        FILE READ
    """
    breakwater_info_file = RESULTS_SUBDIR_NAME.format(run_name) + BREAKWATER_INFO_FILE_NAME
    df = pandas.read_csv(breakwater_info_file)
    Data = df[['Dropped Tasks', 'Timed Out Tasks']]
    breakwater_data = np.array(Data)
    return breakwater_data

def analyze_sim_run(breakwater_data, new_filename):
    # figure1=plt.figure(figsize=(7,6))
    fig, (plt1, plt2) = plt.subplots(1, 2, figsize=(20,8))

    RTTs = np.arange(5, 41, 5)

    """
    PLOT 1
    """
    plt1.tick_params(axis='both', which='major', labelsize=18)

    plt1.grid(which='major', color='black', linewidth=1.0)
    plt1.grid(which='minor', color='grey', linewidth=0.2)
    plt1.minorticks_on()
    # plt.ylim(ymin=0)

    # drops        
    plt1.plot(RTTs, breakwater_data[:,0], marker = 'x', color = 'blue')

    plt1.set_xlabel('RTTs(microsecond)', fontsize=18)
    plt1.set_ylabel('Number of Dropped Tasks', fontsize=18)
    # plt1.legend(fontsize=18)


    """
    PLOT 2
    """
    plt2.tick_params(axis='both', which='major', labelsize=18)

    plt2.grid(which='major', color='black', linewidth=1.0)
    plt2.grid(which='minor', color='grey', linewidth=0.2)
    plt2.minorticks_on()
    # plt.ylim(ymin=0)



    # timeouts          
    plt2.plot(RTTs, breakwater_data[:,1], marker = 'x', color = 'blue')


    plt2.set_xlabel('RTTs (microsecond)', fontsize=18)
    plt2.set_ylabel('Number of Timed Out Tasks', fontsize=18)
    # plt2.legend(fontsize=18)

    plt.savefig(new_filename)

def main():
    sim_list = []
    name = sys.argv[1].strip()

    # File with list of sim names
    if os.path.isfile("./" + name):
        sim_list_file = open(name)
        sim_list = sim_list_file.readlines()
        sim_list_file.close()

    # Name of one run
    elif os.path.isdir(RESULTS_SUBDIR_NAME.format(name)):
        sim_list.append(name)

    # Name of multiple runs (different threads)
    elif os.path.isdir(RESULTS_SUBDIR_NAME.format(THREAD_RUN_FORMAT.format(name, 0))):
        i = 0
        while os.path.isdir(RESULTS_SUBDIR_NAME.format(THREAD_RUN_FORMAT.format(name, i))):
            sim_list.append(THREAD_RUN_FORMAT.format(name, i))
            i += 1
    else:
        print("File or directory not found")

    new_filename = None
    if len(sys.argv) > 2:
        new_filename = None
        for x in os.listdir():
            if x.endswith(".csv"):
                # should grab just the filename, not .csv
                new_filename = os.path.splitext(x)[0]
                break
        if new_filename == None:
            new_filename = 'breakwater_info'
    else:
        new_filename = 'breakwater_info'
    breakwater_data_total = np.zeros((8,2))
    for i, sim_name in enumerate(sim_list):
        breakwater_data_total[i] = (read_files(sim_name.strip()))
        print("Simulation {} analysis complete".format(sim_name))
    analyze_sim_run(breakwater_data_total, new_filename)
    if "-outfile" in sys.argv:
        pandas.DataFrame(breakwater_data_total, columns=['Dropped Tasks', 'Timed Out Tasks'], dtype=int).to_csv(new_filename + '.csv')


if __name__ == "__main__":
    main()