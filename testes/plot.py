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

    sns.set_style("whitegrid") 
    plt.figure(figsize=(5,5))

    ax = sns.boxplot(x=df['Test'], y=df["Jitter(ms)"], showfliers=False,  palette="Set2", notch=True)
    ax.set(xlabel='Cenário', ylabel='Jitter (ms)')
    plt.savefig('./jitter.eps')
    plt.show()


def latency():
    # load the dataset 
    df = pd.read_csv("latency.csv", delimiter=';') 
    
    sns.set_style("whitegrid") 
    plt.figure(figsize=(5,5))

    ax = sns.boxplot(x=df['Test'], y=df["Latency(ms)"], showfliers=False,  palette="Set2", notch=True)
    ax.set(xlabel='Cenário', ylabel='Latência (ms)')
    plt.savefig('./latency.eps')
    plt.show()
    
    
def throughput():
    # load the dataset 
    df = pd.read_csv("throughput.csv", delimiter=';') 
    # display 5 rows of dataset 

    sns.set_style("whitegrid") 
    plt.figure(figsize=(5,5))
    ax = sns.boxplot(x=df['Test'], y=df["Bandwidth(Mbits/sec)"], showfliers=False,  palette="Set2", notch=True)
    ax.set(xlabel='Cenário', ylabel='Largura de Banda (ms)')
    # ax.set(ylim=(700, 1024))
    plt.savefig('./thoughput.eps')
    plt.show()
    
    
    
jitter()
latency()
throughput()
