from matplotlib import pyplot as plt 

from sys import argv
from itertools import islice
import re

FILE = None 
WINDOW = 1

if len(argv) < 2:
    raise ValueError("Missing datasum file for tracking")
FILE = argv[1]    

finders = {
    'bindings took ' : [],
    'priority took ' : [],
    'firing took ' : []
}

for line in open(FILE, "r").readlines():
    for finds in finders.keys():
        if finds in line:
            grabber = re.compile(f"{finds}([0-9\\.]*)s")
            for time in grabber.findall(line):
                finders[finds].append(float(time) * 1000)

def mean(data, window):
        return sum(data) / window

def rolling_mean(data, window):
    return [
        mean(data[i-window:i], window) if i >= window else None
        for i 
        in range(len(data))
    ]

def make_plot(data, title, ax=0, fig=None, size=(15,5)):
    if fig is None:
        fig = plt.figure(figsize=size)
        fig.suptitle("Timing data from simulation")
        
        axes = fig.subplots(1,3, sharey="all",)
        for axe in axes:
            axe.set_xlabel("sim steps")  
            axe.set_ylabel("response time (ms)")
            axe.set_ylim(bottom=0, top=2000)
            axe.grid(True)
        
    ax = fig.axes[ax]
    ax.plot(
        range(len(data)),
        data,
    )
    ax.set_title(title)
    ax.set_ylim()
    return fig

fig = None
ax=0
for finds in finders.keys():
    finders[finds] = rolling_mean(finders[finds], WINDOW)
    fig = make_plot(finders[finds], finds, fig=fig, ax=ax)
    ax += 1

fig.tight_layout()
fig.savefig(
    f"{FILE.split(".")[0]}.png",
    transparent=True
)

