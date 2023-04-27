import numpy as np
import sys
import os
import json

import matplotlib.pyplot as plt
import math
import pandas

import matplotlib.backends.backend_pdf

# RESULTS_DIR_NAME = "results/"
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


def analyze_sim_run(current_dir, pdf, arr, plus_minus):
    """
        FILE READ
    """

    # task_file = RESULTS_SUBDIR_NAME.format(run_name) + TASK_FILE_NAME
    # drops_file = RESULTS_SUBDIR_NAME.format(run_name) + DROPS_FILE_NAME
    # deallocations_file = RESULTS_SUBDIR_NAME.format(run_name) + DEALLOCATIONS_FILE_NAME
    # core_file = RESULTS_SUBDIR_NAME.format(run_name) + CORES_FILE_NAME

    task_file = TASK_FILE_NAME
    drops_file = DROPS_FILE_NAME
    deallocations_file = DEALLOCATIONS_FILE_NAME
    core_file = CORES_FILE_NAME
    throughput_file = THROUGHPUT_FILE_NAME

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
    drops_data_credits = drops_data[:, :2]
    drops_data_system_tasks = drops_data[:, [0, 2]]

    df = pandas.read_csv(task_file)
    # total queue length = number of tasks across all queues = system tasks
    Data = df[['Arrival Time', 'Time in System', 'Total Queue Length']]
    Data = Data.replace(to_replace='None', value=np.nan).dropna()
    # a = np.array(Data)
    # b = a[(a >= 0).all(axis=1)]
    task_data = np.array(Data, dtype=np.int64)
    completions = np.sum(task_data[:, :2], axis=1)

    arrivals = task_data[:, 0]
    total_arrivals = np.concatenate([arrivals, drops_data[:, 0]])

    system_data = task_data[:, [0, 2]]
    total_system_data = np.concatenate([system_data, drops_data_system_tasks])
    # a[a[:, 1].argsort()]
    total_system_data = total_system_data[total_system_data[:, 0].argsort()]

    # add on drop times as arrival times
    # del task_data
    # del df
    # del Data
    # del system_data
    # del arrivals
    # del drops_data
    # del drops_data_system_tasks

    rasterize = True
    """ 
        PLOTTING
    """

    fig, (plt1, plt2, plt3, plt4, plt5, plt6) = plt.subplots(6, 1, figsize=(20, 26))
    # TODO this can be something better
    fig.suptitle(current_dir, fontsize=22, y=0.90)
    x_range = [0, 100000]
    # x_range = [59300, 59600]
    # for every us? Is that granular enough
    # took ~ 6 minutes to plot with 100,000 bins
    # took < 1 min for 10,000 bins
    num_bins = 100000
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

    plt1.hist(total_arrivals / 1000, num_bins, rasterized=rasterize)

    plt1.set_xlabel('Time (us)', fontsize=18)
    plt1.set_ylabel('# Task Arrivals', fontsize=18)
    # plt1.legend(fontsize=18)

    """
    PLOT 2
    """
    plt2.tick_params(axis='both', which='major', labelsize=18)

    plt2.axis(xmin=x_range[0], xmax=x_range[1])
    # plt2.axis(ymin=16, ymax=34)
    plt2.grid(which='major', color='black', linewidth=1.0)
    plt2.grid(which='minor', color='grey', linewidth=0.2)
    plt2.minorticks_on()
    # plt.ylim(ymin=0)

    plt2.hist(completions / 1000, num_bins, rasterized=rasterize)

    plt2.set_xlabel('Time (us)', fontsize=18)
    plt2.set_ylabel('# Task Completions', fontsize=18)
    # plt2.legend(fontsize=18)

    """
    PLOT 3
    """
    plt3.tick_params(axis='both', which='major', labelsize=18)

    plt3.axis(xmin=x_range[0], xmax=x_range[1])
    # plt3.axis(ymin=0, ymax=25)
    plt3.grid(which='major', color='black', linewidth=1.0)
    plt3.grid(which='minor', color='grey', linewidth=0.2)
    plt3.minorticks_on()
    # plt.ylim(ymin=0)

    plt3.plot(total_system_data[:, 0] / 1000, total_system_data[:, 1], rasterized=rasterize)

    plt3.set_xlabel('Arrival Time (microseconds)', fontsize=18)
    plt3.set_ylabel('# Tasks in System', fontsize=18)

    """
    PLOT 4
    """
    plt4.tick_params(axis='both', which='major', labelsize=18)

    plt4.axis(xmin=x_range[0], xmax=x_range[1])
    # plt4.axis(ymin=0, ymax=28)
    plt4.grid(which='major', color='black', linewidth=1.0)
    plt4.grid(which='minor', color='grey', linewidth=0.2)
    plt4.minorticks_on()
    # plt.ylim(ymin=0)

    plt4.scatter(drops_data[:, 0] / 1000, drops_data[:, 1], rasterized=rasterize)

    plt4.set_xlabel('Time (microseconds)', fontsize=18)
    plt4.set_ylabel('# Dropped Credits', fontsize=18)

    """
    PLOT 5
    """
    plt5.tick_params(axis='both', which='major', labelsize=18)

    plt5.axis(xmin=x_range[0], xmax=x_range[1])
    # plt5.axis(ymin=0, ymax=25)
    plt5.grid(which='major', color='black', linewidth=1.0)
    plt5.grid(which='minor', color='grey', linewidth=0.2)
    plt5.minorticks_on()

    plt5.plot(core_data[:, 0] / 1000, core_data[:, 1], rasterized=rasterize)

    plt5.set_xlabel('Arrival Time (us)', fontsize=18)
    plt5.set_ylabel('number of cores', fontsize=18)

    """
    PLOT 6
    """
    plt6.tick_params(axis='both', which='major', labelsize=18)

    plt6.axis(xmin=x_range[0], xmax=x_range[1])
    # plt6.axis(ymin=0, ymax=28)
    plt6.grid(which='major', color='black', linewidth=1.0)
    plt6.grid(which='minor', color='grey', linewidth=0.2)
    plt6.minorticks_on()
    # plt.ylim(ymin=0)

    plt6.plot(throughput_data[:, 0] / 1000, throughput_data[:, 1], rasterized=rasterize)

    plt6.set_xlabel('Time (microseconds)', fontsize=18)
    plt6.set_ylabel('Throughput per second', fontsize=18)

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
        for curr_plot in [plt1, plt2, plt3, plt4, plt5, plt6]:
            curr_plot.axis(xmin=curr_min, xmax=curr_max)
        pdf.savefig(fig)


def main():
    plus_minus = int(sys.argv[1])
    arr = sys.argv[2:]
    print("x ranges to inspect (will view -{} and + {} us)".format(plus_minus, plus_minus))
    print(arr)

    current_dir = os.getcwd()
    thread_num = current_dir[-1]
    name = 'deallocations_analysis_plots_t{}'.format(thread_num)
    pdf = matplotlib.backends.backend_pdf.PdfPages("{}.pdf".format(name))
    page_name = os.path.basename(os.path.normpath(current_dir))
    analyze_sim_run(page_name, pdf, arr, plus_minus)
    print("Simulation analysis complete")
    pdf.close()


if __name__ == "__main__":
    main()