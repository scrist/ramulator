import subprocess
import argparse
import os

import pandas as pd
import random
import seaborn as sns
import matplotlib.pyplot as plt

# policies = ["FCFS", "FRFCFS", "FRFCFS_Cap", "FRFCFS_PriorHit", "ATLAS", "BLISS"]
policy = "FCFS"

# Traces categorized into memory intensity on a scale of 3-0
# This is done by calculating: DRAM Request Inst / Total CPU Inst
# Metric used for memory intensity: % DRAM Requests
#   3: 8.46% - 3.17%
#   2: 2.25% - 1.40%
#   1: 0.89% - 0.14%
#   0: 0.09% - 0.01%        
traces = {
        "bzip2": [1, "./cputraces/401.bzip2"],
        "gcc": [0,"./cputraces/403.gcc"],
        "mcf": [3,"./cputraces/429.mcf"],
        "milc": [2,"./cputraces/433.milc"],
        "zeusmp": [3,"./cputraces/434.zeusmp"],
        "gromacs": [1,"./cputraces/435.gromacs"],
        "cactusADM": [1,"./cputraces/436.cactusADM"],
        "leslie3d": [2,"./cputraces/437.leslie3d"],
        "namd": [0,"./cputraces/444.namd"],
        "gobmk": [0,"./cputraces/445.gobmk"],
        "dealII": [0,"./cputraces/447.dealII"],
        "soplex": [3,"./cputraces/450.soplex"],
        "hmmer": [1,"./cputraces/456.hmmer"],
        "sjeng": [0,"./cputraces/458.sjeng"],
        "GemsFDTD": [3,"./cputraces/459.GemsFDTD"],
        "libquantum": [3,"./cputraces/462.libquantum"],
        "h264ref": [1,"./cputraces/464.h264ref"],
        "lbm": [3,"./cputraces/470.lbm"],
        "omnetpp": [2,"./cputraces/471.omnetpp"],
        "astar": [1,"./cputraces/473.astar"],
        "wrf": [0,"./cputraces/481.wrf"],
        "sphinx3": [2,"./cputraces/482.sphinx3"],
        "xalancbmk": [2, "./cputraces/483.xalancbmk"]
     }




workloads = [
    ["mcf","zeusmp","namd","dealII"],               # H H L L
    ["libquantum","xalancbmk","cactusADM","gobmk"], # H MH ML L
    ["sjeng","gobmk","namd","wrf"],                 # L L L L
    ["mcf","soplex","GemsFDTD","lbm"]              # H H H H
    ]

#workloads = [['leslie3d','sjeng','libquantum','astar']] #high compute workloads
#workloads = [['leslie3d', 'lbm'], ['GemsFDTD', 'gcc'], ['omnetpp', 'xalancbmk'], ['milc', 'gcc'], ['dealII', 'omnetpp'], ['soplex', 'xalancbmk'], ['astar', 'leslie3d'], ['sjeng', 'sphinx3'], ['leslie3d', 'hmmer'], ['hmmer', 'sjeng'], ['gcc', 'cactusADM'], ['cactusADM', 'soplex'], ['sjeng', 'soplex'], ['cactusADM', 'bzip2'], ['wrf', 'dealII'], ['lbm', 'mcf'], ['libquantum', 'gromacs'], ['namd', 'soplex'], ['wrf', 'cactusADM'], ['omnetpp', 'gobmk'], ['leslie3d', 'soplex'], ['dealII', 'libquantum'], ['libquantum', 'zeusmp']]
sim_type = "mult"

"""
for key in traces:
    wl = []
    wl.append(key)
    wl.append(key)
    workloads.append(wl)
"""
# def buildWorkload():
#     for i in range(0,23):
#         wl = []
#         trace1 = random.choice(list(traces.keys()))
#         trace2 = random.choice(list(traces.keys()))
#     while trace2==trace1:
#         trace2 = random.choice(list(traces.keys()))
#     wl.append(trace1)
#     wl.append(trace2)
#     workloads.append(wl)

def buildWorkload():
    workloads = []
    wl = []
    for key in traces:
        wl.append(key)
    # plus a tasty lick to even out the 24 core system
    wl.append("hmmer")
    workloads.append(wl)
    return workloads

#csv_file = f"./results/{policy}_2test.csv"




def stat_path(sim_type, name):
    return f"./stats/{sim_type}/{policy}/{name}.stats"

def csv_path():
    # TODO: CHANGE
    return f"./results/{policy}.csv" # change to {policy}_all 

def get_stat(stat, path):
    with open(path) as f:
        for line in f:
            rows = line.split()
            if rows[0] == stat:
                return float(rows[1])

def run_ramulator(trace, stat_path):
    
    command = ["./ramulator", "./configs/DDR4-config.cfg",
                              "--mode=cpu",
                              "--stats", stat_path,
                            ]
    command.extend(trace)
    command = " ".join(command)
    #print(command)
    os.system(command)


def run_simulation_alone():
    cpu_cycles_alone = {}
    cpu_ints_alone = {}
    ipc_alone = {}

    for key in traces:
        nameAll = f"{key}_all"

        # TODO: CHANGE
        path = stat_path("alone", key) 
        print(traces[key][1])

        try:
            run_ramulator([traces[key][1]],path)
        except AssertionError:
            print("Simulation error")
            continue
        cpu_cycles_alone[key] = get_stat("ramulator.cpu_cycles",path)
        cpu_ints_alone[key] = get_stat(f"ramulator.cpu_instructions_core_{0}",path)
        #ipc_alone[key] = cpu_ints_alone[key] / cpu_cycles_alone[key]
        #print(f"IPC alone: {ipc_alone[key]}\n")


def run_simulation(workloads):
    data_ms_ws = []


    for testNum, workload in enumerate(workloads):

        trace_files = []
        total_ints = 0
        total_cycs = 0
        name = ""
        max_slowdown = -1
        min_speedup = 2
        print(f"Configuring simulation #{testNum}")
        
        for c in workload:
            trace_files.append(traces[c][1])
            name += f"{c}_"
        name = name[:-1]
        name2 = "all"
        
        # TODO: CHANGE
        mult_path = stat_path("mult",name)

        
        run_ramulator(trace_files,mult_path)


        #Calculate per workload values
        for coreid, c in enumerate(workload):
            #prelim calculations using single core sims
            nameAll = f"{c}_all"
            
            # TODO CHANGE name if simulation is different 
            alone_path = stat_path("alone",c)

            # 
            cpu_cycles_shared = get_stat(f"ramulator.record_cycs_core_{coreid}",mult_path)
            cpu_cycles_alone = get_stat("ramulator.cpu_cycles",alone_path)

            slowdown = cpu_cycles_shared / cpu_cycles_alone
            if (slowdown > max_slowdown):
                max_slowdown = slowdown
                max_slowdown_workload = c

            cpu_ints_alone = get_stat(f"ramulator.cpu_instructions_core_{0}",alone_path)
            ipc_alone = cpu_ints_alone / cpu_cycles_alone

            cpu_inst_shared = get_stat(f"ramulator.record_insts_core_{coreid}",mult_path)
            total_ints += cpu_inst_shared
            try: 
                ipc_shared = cpu_inst_shared / cpu_cycles_shared
            except ZeroDivisionError:
                ipc_shared = 0

            weighted_speedup = ipc_shared / ipc_alone
            if (weighted_speedup < min_speedup):
                min_speedup = weighted_speedup
                min_ws_work = c

            print(f"Slowdown of {c}: {slowdown}")
            print(f"Weighted Speedup of {c}: {weighted_speedup}\n")
            data_ms_ws.append([testNum, policy, c, slowdown, weighted_speedup])

        total_cycs = get_stat("ramulator.cpu_cycles",mult_path)
        total_ipc = total_ints / total_cycs

        print(f"Min Weighted Speedup from {min_ws_work}: {min_speedup}")
        print(f"Max Slowdown from {max_slowdown_workload}: {max_slowdown}")
        print(f"Instruction Throughput: {total_ipc}\n")
        #data.append([testNum, policy, max_slowdown_workload, round(max_slowdown, 2)]) #originally contained both workloads

    print(f"Writing data to: {csv_path()}")
    df1 = pd.DataFrame(data_ms_ws, columns=["Test Num", "Policy","Workload","Slowdown","Weighted Speedup"])
    df1.to_csv(csv_path())
    #df = pd.DataFrame(data, columns=["policy", "workload", "max_slowdown"])
    #df.to_csv(csv_file, index=False)
    #return df

#def testPath(path):
    

def plot(df, name, label, save):
    sns.set_theme()
    sns.set_style("whitegrid")
    sns.set_context("paper")
    g = sns.catplot(x="workload", y=name, hue="policy", data=df, kind="bar")
    g.set_axis_labels("", label)
    g.legend.set_title(None)
    g.set_xticklabels(rotation=40, ha="right", fontsize=7)
    g.tight_layout()
    if save:
        """
        file = open("incimg.txt","r")
        count = int(file.read())
        file.close()
        count += 1
        name = name + str(count)
        file.open("incimg","w")
        file.write(str(count))
        file.close()
        """
        plt.savefig(f"img/{name}.pdf", format="pdf")
    else:
        plt.show()

def main():
    #just in case you forget to build
    os.system("make -j8")

    print(f"\nPolicy: {policy}")
    
    parser = argparse.ArgumentParser(description='Simulate and plot scheduling policies.')
    parser.add_argument('--sim', const=True, default=False, help="Run simulation", nargs="?")
    parser.add_argument('--save', const=True, default=False, help="Save plots as pdf", nargs="?")

    args = parser.parse_args()
    do_simulation = args.sim
    do_save = args.save
    do_save = True
    do_alone_simulation = True
    do_simulation = False
    sim_all = False
    # try:
    #     df  = pd.read_csv(csv_file)
    # except FileNotFoundError:
    #     do_simulation = True
    if do_alone_simulation:
        df = run_simulation_alone()

    if do_simulation:
        if sim_all:
            all = buildWorkload()
            print(f"Workloads Generated: {all}\n")
            run_simulation(all)
        else:
            run_simulation(workloads)

    # plot(df, "inst_throughput", "Instruction Throughput", do_save)
    
    #plot(df, "max_slowdown", "Max. Slowdown", do_save)

if __name__ == "__main__":
    main()
