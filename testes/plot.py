import glob
import math

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator
from mpl_toolkits.axes_grid1.inset_locator import mark_inset, zoomed_inset_axes


def jitter():
    # load the dataset
    df = pd.read_csv("jitter.csv", delimiter=';')

    groups = df.groupby(['Test'])
    print("Mean", groups.mean())
    print("std", groups.std())

    sns.set_style("darkgrid")
    plt.figure(figsize=(6, 5))

    plt.rcParams['font.family'] = "serif"
    ax = sns.boxplot(x=df['Test'], y=df["Jitter(ms)"],
                     showfliers=False,  palette="Set2", notch=True)

    ax.set_xlabel("Cenário",fontsize=15)
    ax.set_ylabel("Jitter (ms)",fontsize=15)
    ax.tick_params(labelsize=12)

    ax.set(xlabel='Cenário', ylabel='Jitter (ms)')
    plt.savefig('./jitter.eps')
    plt.show()


def latency():
    # load the dataset
    df = pd.read_csv("latency.csv", delimiter=';')

    groups = df.groupby(['Test'])
    print("Mean", groups.mean())
    print("std", groups.std())

    sns.set_style("darkgrid")
    plt.figure(figsize=(6, 5))
    
    plt.rcParams['font.family'] = "serif"
    ax = sns.boxplot(x=df['Test'], y=df["Latency(ms)"],
                     showfliers=False,  palette="Set2", notch=True)

    ax.set_xlabel("Cenário",fontsize=15)
    ax.set_ylabel("Latência (ms)",fontsize=15)
    ax.tick_params(labelsize=12)

    plt.savefig('./latency.eps')
    plt.show()


def throughput():
    # load the dataset
    df = pd.read_csv("throughput.csv", delimiter=';')
    # display 5 rows of dataset

    groups = df.groupby(['Cenário'])
    print("Mean", groups.mean())
    print("std", groups.std())
    print(groups)
    sns.set_style("darkgrid")
    plt.figure(figsize=(6, 5))
    plt.rcParams['font.family'] = "serif"
    ax = sns.boxplot(
        x=df['Cenário'], y=df["Bandwidth(Mbits/sec)"], palette="Set2", showfliers=False, notch=True)

    ax.set_xlabel("Cenário",fontsize=15)
    ax.set_ylabel("Vazão Máxima (Mbits/seg)",fontsize=15)
    ax.tick_params(labelsize=12)

    plt.savefig('./thoughput.eps')
    plt.show()


def line_throughput():
    # load the dataset
    df = pd.read_csv("throughput.csv", delimiter=';')
    # display 5 rows of dataset
    sns.set_style("darkgrid")
    plt.figure(figsize=(10, 4))
    plt.rcParams['font.family'] = "serif"
    ax = sns.lineplot(x=df["Amostra"], y=df["Bandwidth(Mbits/sec)"], palette="Set2",
                      hue=df["Cenário"], style=df["Cenário"], markers=True, dashes=False)

    ax.set_xlabel("Nº Amostra",fontsize=15)
    ax.set_ylabel("Vazão Máxima (Mbits/seg)",fontsize=15)
    ax.tick_params(labelsize=12)

    plt.savefig('./line_thoughput.eps')
    plt.show()

 
jitter()
latency()
throughput()
line_throughput()
