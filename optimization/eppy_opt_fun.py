"""
functions that actually adjust the idf using eppy 
take in an idf, and output an edited idf 
"""

from eppy import *
from ladybug import analysisperiod as ap
from collections import OrderedDict


class eppy_opt_functions():

    def perc_change_val(self, pc, xo):
        "given percent change pc, and xo, calc x_new, xn"
        xn = (xo*pc)/100 + xo
        xn_real = max(0, xn)
        return xn_real

    def perc_change_arr(self, pc_arr, xo):
        "given array of percent changes pc_arr, and xo, calc x_new_arr, xn_arr"
        xn_arr = [self.perc_change_val(pc, xo) for pc in pc_arr]
        return xn_arr

    def change_window_shgc(self, idf0, pc):
        window_mat = [s  for s in idf0.idfobjects["WindowMaterial:SimpleGlazingSystem"] if s.Name == "Thornton Window Material 1"][0]
        # get current value 
        curr_val = window_mat.Solar_Heat_Gain_Coefficient 
        print(curr_val)
        # calculate new values 
        new_val = self.perc_change_val(pc, curr_val)
        # adjust the idf 
        window_mat.Solar_Heat_Gain_Coefficient = new_val
        # return the idf
        print([s  for s in idf0.idfobjects["WindowMaterial:SimpleGlazingSystem"] if s.Name == "Thornton Window Material 1"][0])
        return (idf0, new_val)