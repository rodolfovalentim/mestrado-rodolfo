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

    sns.set(font_scale=1.5, rc={'text.usetex' : True})
    sns.set_style("whitegrid") 

    ax = sns.boxplot(x=df['Test'], y=df["Jitter(ms)"], showfliers=False)
    plt.savefig('./jitter.eps')
    plt.show()


def latency():
    # load the dataset 
    df = pd.read_csv("latency.csv", delimiter=';') 
   
    sns.set(font_scale=1.5, rc={'text.usetex' : True})
    sns.set_style("whitegrid") 

    ax = sns.boxplot(x=df['Test'], y=df["Latency(ms)"], showfliers=False)
    # plt.savefig('./latency.eps')
    plt.show()
    
    
def throughput():
    # load the dataset 
    df = pd.read_csv("throughput.csv", delimiter=';') 
    # display 5 rows of dataset 

    sns.set_style("whitegrid") 
    ax = sns.boxplot(x=df['Test'], y=df["Bandwidth(Mbits/sec)"], showfliers=False)
    # plt.savefig('./thoughput.eps')
    plt.show()
    
    
    
# jitter()
# latency()
throughput()
