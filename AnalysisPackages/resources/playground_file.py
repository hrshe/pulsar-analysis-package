import numpy as np

"""
Purpose of this file is to execute rough patches of code... Not to be included in final project
"""

old = np.array([22.067273068000002, 22.637951762999997, 22.783322316999993, 25.94358726600001, 31.06037999, 29.223290632000015])
new = np.array([9.291042568, 10.794996157, 10.486564659999999, 9.832394484999998, 10.807567624, 9.974830566000001])

print(np.mean(old)/np.mean(new))