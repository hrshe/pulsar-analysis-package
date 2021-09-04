import sys

import numpy as np
from itertools import islice


fname = sys.argv[1]
with open(f"{fname}.spec", 'r') as spec_file:
    for i in range(10):
        dyn_spec = np.genfromtxt(islice(spec_file, 10000), dtype=float)
        with open(f"{fname}_small.spec", "ab") as file:
            np.savetxt(file, dyn_spec, fmt='%1.3f')
            print("saved...", str(i))