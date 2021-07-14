import argparse
import os

import pandas as pd
import random
import matplotlib.pyplot as plt

policies = ["FRFCFS", "FRFCFS_Cap", "FRFCFS_PriorHit"]
policy = "FRFCFS"
traces = {
        "bzip2": "./cputraces/401.bzip2",
        "gcc": "./cputraces/403.gcc",
        "mcf": "./cputraces/429.mcf",
        "milc": "./cputraces/433.milc",
        "zeusmp": "./cputraces/434.zeusmp",
        "gromacs": "./cputraces/435.gromacs",
        "cactusADM": "./cputraces/436.cactusADM",
        "leslie3d": "./cputraces/437.leslie3d",
        "namd": "./cputraces/444.namd",
        "gobmk": "./cputraces/445.gobmk",
        "dealII": "./cputraces/447.dealII",
        "soplex": "./cputraces/450.soplex",
        "hmmer": "./cputraces/456.hmmer",
        "sjeng": "./cputraces/458.sjeng",
        "GemsFDTD": "./cputraces/459.GemsFDTD",
        "libquantum": "./cputraces/462.libquantum",
        "h264ref": "./cputraces/464.h264ref",
        "lbm": "./cputraces/470.lbm",
        "omnetpp": "./cputraces/471.omnetpp",
        "astar": "./cputraces/473.astar",
        "wrf": "./cputraces/481.wrf",
        "sphinx3": "./cputraces/482.sphinx3",
        "xalancbmk": "./cputraces/483.xalancbmk"
     }
     
mult_workloads = [
    ["mcf","zeusmp","namd","dealII"],               # H H L L
    ["libquantum","xalancbmk","cactusADM","gobmk"], # H MH ML L
    ["sjeng","gobmk","namd","wrf"],                 # L L L L
    ["mcf","soplex","GemsFDTD","lbm"]              # H H H H
    ]

sim_type = "alone"
stat_file = "plot.stats"
csv_file = f"./results/dram_stats.csv"

def stat_path(sim_type, name):
    return f"./stats/{sim_type}/{policy}/{name}.stats"


def get_stat(stat, path):
    with open(path) as f:
        for line in f:
            rows = line.split()
            if rows[0] == stat:
                return float(rows[1])

def csv_path(type):
    # TODO: CHANGE
    return f"./results/{policy}_{type}_ipc.csv" # change to {policy}_all 

def buildWorkload():
    workloads = []
    wl = []
    for key in traces:
        wl.append(key)
    # plus a tasty lick to even out the 24 core system
    wl.append("hmmer")
    workloads.append(wl)
    return workloads
"""
data to collect:
    read_requests
    write_requests
    incoming_requests
    cpu_instructions_core_{0} (number of total CPU intructions)

    #req_queue_length_avg_0 #not yet
    

    row_hits_channel_0_core
    row_misses_channel_0_core
    read_latency_avg_0     #not yet

    in_queue_read_req_num_avg
    in_queue_write_req_num_avg

    read_transaction_bytes_0
    write_transaction_bytes_0

    dram_cycles
"""
def extract_init_stats():
    data = []


    for key in traces:
        path = stat_path("alone", key) 
        print(f"Reading from: {path}")

        # read_requests = get_stat("ramulator.read_requests",path)
        # write_requests = get_stat("ramulator.write_requests",path)
        # incoming_requests = get_stat("ramulator.incoming_requests",path)
        # cpu_instructions = get_stat(f"ramulator.record_insts_core_0",path)
        #data.append([key, read_requests, write_requests, incoming_requests, cpu_instructions])


        row_hits = get_stat("ramulator.row_hits_channel_0_core",path)
        row_misses = get_stat("ramulator.row_misses_channel_0_core",path)
        read_latency_avg = get_stat("ramulator.read_latency_avg_0",path)
        avg_read_req_q = get_stat("ramulator.in_queue_read_req_num_avg",path)
        avg_write_req_q = get_stat("ramulator.in_queue_write_req_num_avg",path)
        read_bytes = get_stat("ramulator.read_transaction_bytes_0",path)
        write_bytes = get_stat("ramulator.write_transaction_bytes_0",path)
        dram_cycs = get_stat("ramulator.dram_cycles",path)

        data.append([key, row_hits, row_misses, read_latency_avg, avg_read_req_q,avg_write_req_q, read_bytes,write_bytes,dram_cycs])

    df = pd.DataFrame(data, columns=["workload", "row_hits", "row_misses", "read_latency_avg","avg_read_req_q","avg_write_req_q","read_bytes","write_bytes","dram_cycs"])
    print(f"Saving to file: {csv_file}")
    df.to_csv(csv_file, index=False)
    return df

def get_mult_stats(type):

    if type=="all":
        workloads = buildWorkload()
        num_cores =  24
        total_ints = num_cores * 10000000
    elif type =="mult":
        workloads = mult_workloads
        num_cores = 4
        total_ints = num_cores * 200000000
   
    data_ipc = []

    for testNum, workload in enumerate(workloads):

        trace_files = []
        total_cycs = 0
        name = ""
        print(f"Getting data from {policy} sim: {workload}\n")

        if type=="all":
            name = "all"

        elif type =="mult":
            for c in workload:
                trace_files.append(traces[c][1])
                name += f"{c}_"
            name = name[:-1]
        
        
        # TODO: CHANGE
        mult_path = stat_path("mult",name)


        total_cycs = get_stat("ramulator.cpu_cycles",mult_path)
        total_ipc = total_ints / total_cycs

        data_ipc.append([testNum, policy, total_ipc])
        print(f"Instruction Throughput: {total_ipc}\n")
        #data.append([testNum, policy, max_slowdown_workload, round(max_slowdown, 2)]) #originally contained both workloads

    print(f"Writing data to: {csv_path(type)}")
    df1 = pd.DataFrame(data_ipc, columns=["Test Num", "Policy","Total IPC"])
    df1.to_csv(csv_path(type))

def main():

    parser = argparse.ArgumentParser(description='Simulate and plot scheduling policies.')
    parser.add_argument('--sim', const=True, default=False, help="Run simulation", nargs="?")
    parser.add_argument('--save', const=True, default=False, help="Save plots as pdf", nargs="?")

    print("Starting to extract stats.\n")
    extract_init_stats()
    # get_mult_stats("mult")
    # get_mult_stats("all")
    print("Extraction complete.\n")
    

if __name__ == "__main__":
    main()
