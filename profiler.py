import pstats 
from pstats import SortKey
from sys import argv 

file = argv[1]

prof = pstats.Stats(file)

prof.strip_dirs().sort_stats(-1).print_stats()

print("*************************")

prof.sort_stats(SortKey.CUMULATIVE).print_stats(.2)

print("*************************")

prof.sort_stats(SortKey.TIME, SortKey.CUMULATIVE).print_stats(.2)

print("*************************")

prof.print_callers(.2)