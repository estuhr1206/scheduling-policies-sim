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

def analyze_sim_run(run_name, pdf):
    """
        FILE READ
    """

    queues = 'Queues'
    threads = 'Threads'
    item = queues

    core_data = None
    credit_data = None
    task_data = None
    throughput_data = None

    credit_file = RESULTS_SUBDIR_NAME.format(run_name) + CREDITS_FILE_NAME
    core_file = RESULTS_SUBDIR_NAME.format(run_name) + CORES_FILE_NAME
    task_file = RESULTS_SUBDIR_NAME.format(run_name) + TASK_FILE_NAME
    throughput_file = RESULTS_SUBDIR_NAME.format(run_name) + THROUGHPUT_FILE_NAME

    df = pandas.read_csv(credit_file)
    Data = df[['Time', 'Total Credits']]
    credit_data = np.array(Data)

    df = pandas.read_csv(core_file)
    Data = df[['Time', item]]
    core_data = np.array(Data)

    df = pandas.read_csv(throughput_file)
    Data = df[['Time', 'Throughput']]
    throughput_data = np.array(Data)

    df = pandas.read_csv(task_file)
    Data = df[['Arrival Time', 'Time in System']]
    #Data['Time in System'] = pandas.to_numeric(Data['Time in System'])
    a = np.array(Data)
    b = a[(a >= 0).all(axis=1)]
    task_data = np.array(b)

    del a
    del b
    del df
    del Data

    rasterize = True

    """ 
        PLOTTING
    """
    
    fig, (plt1, plt2, plt3, plt4) = plt.subplots(4, 1, figsize=(20,20))
    fig.suptitle(run_name, fontsize=22, y=0.90)
    x_range = [0, 100000]
    """
    PLOT 1
    """
    plt1.tick_params(axis='both', which='major', labelsize=18)

    plt1.axis(xmin=x_range[0], xmax=x_range[1])
    # plt1.axis(ymin=50, ymax=101)
    plt1.grid(which='major', color='black', linewidth=1.0)
    plt1.grid(which='minor', color='grey', linewidth=0.2)
    plt1.minorticks_on()
    # plt.ylim(ymin=0)

            
    plt1.plot(credit_data[:,0]/1000, credit_data[:,1], label='none', rasterized=rasterize)

    plt1.set_xlabel('Time', fontsize=18)
    plt1.set_ylabel('Total Credit Pool', fontsize=18)
    plt1.legend(fontsize=18)


    """
    PLOT 2
    """
    plt2.tick_params(axis='both', which='major', labelsize=18)

    plt2.axis(xmin=x_range[0], xmax=x_range[1])
    #plt2.axis(ymin=16, ymax=34)
    plt2.grid(which='major', color='black', linewidth=1.0)
    plt2.grid(which='minor', color='grey', linewidth=0.2)
    plt2.minorticks_on()
    # plt.ylim(ymin=0)

            
    plt2.plot(core_data[:,0]/1000, core_data[:,1], rasterized=rasterize)

    plt2.set_xlabel('Time (microseconds)', fontsize=18)
    plt2.set_ylabel('Cores Allocated', fontsize=18)
    #plt2.legend(fontsize=18)


    """
    PLOT 3
    """
    plt3.tick_params(axis='both', which='major', labelsize=18)

    plt3.axis(xmin=x_range[0], xmax=x_range[1])
    #plt3.axis(ymin=0, ymax=25)
    plt3.grid(which='major', color='black', linewidth=1.0)
    plt3.grid(which='minor', color='grey', linewidth=0.2)
    plt3.minorticks_on()
    # plt.ylim(ymin=0)

            
    plt3.scatter(task_data[:,0]/1000, task_data[:,1]/1000, alpha = 0.2, rasterized=rasterize)

    plt3.set_xlabel('Arrival Time (microseconds)', fontsize=18)
    plt3.set_ylabel('latency (microseconds)', fontsize=18)

    """
    PLOT 4
    """
    plt4.tick_params(axis='both', which='major', labelsize=18)

    plt4.axis(xmin=x_range[0], xmax=x_range[1])
    #plt4.axis(ymin=0, ymax=28)
    plt4.grid(which='major', color='black', linewidth=1.0)
    plt4.grid(which='minor', color='grey', linewidth=0.2)
    plt4.minorticks_on()
    # plt.ylim(ymin=0)

            
    plt4.plot(throughput_data[:,0]/1000, throughput_data[:,1], rasterized=rasterize)

    plt4.set_xlabel('Time (microseconds)', fontsize=18)
    plt4.set_ylabel('Throughput per second', fontsize=18)

    # file_name = run_name + 'time_series.png'
    # plt.savefig(file_name)
    pdf.savefig(fig)
    plt.close(fig)

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
    pdf = None
    if len(sys.argv) > 2:
        csv_name = None
        for x in os.listdir():
            if x.endswith(".csv"):
                # should grab just the filename, not .csv
                csv_name = os.path.splitext(x)[0]
                break
        if csv_name == None:
            csv_name = 'time_series_plots'
        pdf = matplotlib.backends.backend_pdf.PdfPages("{}.pdf".format(csv_name))
    else:
        pdf = matplotlib.backends.backend_pdf.PdfPages("time_series_plots.pdf")

    for sim_name in sim_list:
        analyze_sim_run(sim_name.strip(), pdf)
        print("Simulation {} analysis complete".format(sim_name))
    pdf.close()

if __name__ == "__main__":
    main()