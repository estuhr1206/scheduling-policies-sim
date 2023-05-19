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
DROPS_FILE_NAME = 'drops_record.csv'
DEALLOCATIONS_FILE_NAME = 'core_deallocations.csv'

"""
  we want to have four plots
  1. arrivals (histogram?)
  2. completions (histogram) (probably just pull arrival times from csv and add corresponding system time for each task)
  3. number of tasks in system (shouldn't have to be a histogram) but, should pull from task times and from drops
  4. drops  (can probably mimic what I already have in place)

  issue: arrival times aren't overidden for dropped tasks. Fixed this, but an issue for previously collected data

  Workaround:
  time is stamped on the drops csv
  maybe just approach like normal with the task times and exclude all values with negative in any column
  and then plot over time on same graph, the points from the drops file.
  actually, concatenating probably makes more sense. 

  should I be doing histograms?
  Would require items to be put into bins.
"""

def analyze_sim_run(run_name, arr, plus_minus):
    if not os.path.exists('deallocations_pdfs'):
        os.makedirs('deallocations_pdfs')
    pdf_name = "{}.pdf".format(run_name)
    pdf_path = 'deallocations_pdfs/' + pdf_name
    pdf = matplotlib.backends.backend_pdf.PdfPages(pdf_path)
    """
        FILE READ
    """
    credits_file = RESULTS_SUBDIR_NAME.format(run_name) + CREDITS_FILE_NAME
    task_file = RESULTS_SUBDIR_NAME.format(run_name) + TASK_FILE_NAME
    drops_file = RESULTS_SUBDIR_NAME.format(run_name) + DROPS_FILE_NAME
    deallocations_file = RESULTS_SUBDIR_NAME.format(run_name) + DEALLOCATIONS_FILE_NAME
    core_file = RESULTS_SUBDIR_NAME.format(run_name) + CORES_FILE_NAME
    throughput_file = RESULTS_SUBDIR_NAME.format(run_name) + THROUGHPUT_FILE_NAME

    df = pandas.read_csv(credits_file)
    Data = df[['Time', 'Total Credits']]
    credits_data = np.array(Data)

    df = pandas.read_csv(throughput_file)
    Data = df[['Time', 'Throughput']]
    throughput_data = np.array(Data)

    df = pandas.read_csv(core_file)
    Data = df[['Time', 'Queues']]
    core_data = np.array(Data)

    df = pandas.read_csv(deallocations_file)
    Data = df[['Time', 'System Tasks']]
    deallocation_data = np.array(Data, dtype=np.int64)

    df = pandas.read_csv(drops_file)
    Data = df[['Time', 'C Dropped', 'System Tasks']]
    drops_data = np.array(Data, dtype=np.int64)
    drops_data_credits = drops_data[:,:2]
    drops_data_system_tasks = drops_data[:,[0,2]]


    df = pandas.read_csv(task_file)
    # total queue length = number of tasks across all queues = system tasks
    Data = df[['Arrival Time', 'Time in System', 'Total Queue Length']]
    Data = Data.replace(to_replace='None', value=np.nan).dropna()
    # a = np.array(Data)
    # b = a[(a >= 0).all(axis=1)]
    task_data = np.array(Data, dtype=np.int64)
    completions = np.sum(task_data[:,:2], axis=1)

    arrivals = task_data[:,0]
    total_arrivals = np.concatenate([arrivals, drops_data[:,0]])

    system_data = task_data[:,[0,2]]
    total_system_data = np.concatenate([system_data, drops_data_system_tasks])
    # a[a[:, 1].argsort()]
    total_system_data = total_system_data[total_system_data[:,0].argsort()]

    # add on drop times as arrival times
    del task_data
    del df
    del Data
    del system_data
    del arrivals
    del drops_data_system_tasks

    rasterize = True
    """ 
        PLOTTING
    """

    fig, (plt1, plt2, plt3, plt4, plt5, plt6, plt7) = plt.subplots(7, 1, figsize=(20,32))
    # TODO this can be something better
    fig.suptitle(run_name, fontsize=22, y=0.90)
    x_range = [0, 100000]
    # x_range = [59300, 59600]
    # for every us? Is that granular enough
    # took ~ 6 minutes to plot with 100,000 bins
    # took < 1 min for 10,000 bins
    num_bins = 10000
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

    plt1.hist(total_arrivals/1000, num_bins, rasterized=rasterize)        

    plt1.set_xlabel('Time (us)', fontsize=18)
    plt1.set_ylabel('# Task Arrivals', fontsize=18)
    # plt1.legend(fontsize=18)


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

    plt2.hist(completions/1000, num_bins, rasterized=rasterize)

    plt2.set_xlabel('Time (us)', fontsize=18)
    plt2.set_ylabel('# Task Completions', fontsize=18)
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

            
    plt3.plot(total_system_data[:,0]/1000, total_system_data[:,1], rasterized=rasterize)

    plt3.set_xlabel('Arrival Time (microseconds)', fontsize=18)
    plt3.set_ylabel('# Tasks in System', fontsize=18)

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

            
    plt4.scatter(drops_data[:,0]/1000, drops_data[:,1], rasterized=rasterize)

    plt4.set_xlabel('Time (microseconds)', fontsize=18)
    plt4.set_ylabel('# Dropped Credits', fontsize=18)


    """
    PLOT 5
    """
    plt5.tick_params(axis='both', which='major', labelsize=18)

    plt5.axis(xmin=x_range[0], xmax=x_range[1])
    #plt5.axis(ymin=0, ymax=25)
    plt5.grid(which='major', color='black', linewidth=1.0)
    plt5.grid(which='minor', color='grey', linewidth=0.2)
    plt5.minorticks_on()

            
    plt5.plot(core_data[:,0]/1000, core_data[:,1], rasterized=rasterize)

    plt5.set_xlabel('Arrival Time (us)', fontsize=18)
    plt5.set_ylabel('number of cores', fontsize=18)


    """
    PLOT 6
    """
    plt6.tick_params(axis='both', which='major', labelsize=18)

    plt6.axis(xmin=x_range[0], xmax=x_range[1])
    #plt6.axis(ymin=0, ymax=28)
    plt6.grid(which='major', color='black', linewidth=1.0)
    plt6.grid(which='minor', color='grey', linewidth=0.2)
    plt6.minorticks_on()
    # plt.ylim(ymin=0)

            
    plt6.plot(throughput_data[:,0]/1000, throughput_data[:,1], rasterized=rasterize)

    plt6.set_xlabel('Time (microseconds)', fontsize=18)
    plt6.set_ylabel('Throughput per second', fontsize=18)

    """
        PLOT 7
    """
    plt7.tick_params(axis='both', which='major', labelsize=18)

    plt7.axis(xmin=x_range[0], xmax=x_range[1])
    # plt7.axis(ymin=0, ymax=28)
    plt7.grid(which='major', color='black', linewidth=1.0)
    plt7.grid(which='minor', color='grey', linewidth=0.2)
    plt7.minorticks_on()
    # plt.ylim(ymin=0)

    plt7.plot(credits_data[:, 0] / 1000, credits_data[:, 1], rasterized=rasterize)

    plt7.set_xlabel('Time (microseconds)', fontsize=18)
    plt7.set_ylabel('Credit Pool', fontsize=18)



    # file_name = run_name + 'time_series.png'
    # plt.savefig(file_name)
    # TODO
    # pdf.savefig(fig)
    # plt.close(fig)
    pdf.savefig(fig)
    # repeat the below for however many closeups are wanted
    for xcenter in arr:
        xcenter_int = int(xcenter)
        print("plotting xrange: {}".format(xcenter_int))
        curr_min = xcenter_int - plus_minus
        curr_max = xcenter_int + plus_minus
        for curr_plot in [plt1, plt2, plt3, plt4, plt5, plt6, plt7]:
            curr_plot.axis(xmin=curr_min, xmax=curr_max)
        pdf.savefig(fig)
    pdf.close()
    plt.clf()
    plt.close()

def get_xcenters(run_name, buffer):
    deallocations_file = RESULTS_SUBDIR_NAME.format(run_name) + DEALLOCATIONS_FILE_NAME
    df = pandas.read_csv(deallocations_file)
    Data = df[['Time', 'Available Queues']]
    deallocation_data = np.array(Data)
    # print(deallocation_data.shape)
    last_time = -2*buffer
    time_stamps = []
    for i in range(deallocation_data.shape[0]):
        # should be sufficient conditions to see a dropped core, and still skip succssive drops
        if deallocation_data[i][0] - buffer > last_time and deallocation_data[i][1] == 31:
            last_time = deallocation_data[i][0]
            time_stamps.append(int(last_time / 1000))
    return time_stamps

def main():
    # ex. python3 path/deallocations_analysis.py nrgserver_23-04-05 500
    plus_minus = int(sys.argv[2])
    # put into nanoseconds
    buffer = (plus_minus - 100) * 1000
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

    for sim_name in sim_list:
        # analyze_sim_run(sim_name.strip(), get_xcenters(sim_name.strip(), buffer), plus_minus)
        centers = [0, 25000, 26000, 27000, 50000, 75000, 100000]
        analyze_sim_run(sim_name.strip(), centers, plus_minus)
        print("Simulation {} analysis complete".format(sim_name))

    print("All analysis complete")

if __name__ == "__main__":
    main()