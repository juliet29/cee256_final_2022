import numpy as np
import os
from eppy import *
from eppy.modeleditor import IDF
import pandas as pd
from ladybug.sql import SQLiteResult
from ladybug import analysisperiod as ap
from collections import OrderedDict
from eppy.results import fasthtml

class opt_functions():
    def __init__(self, root_idf):
        # set the idd
        iddfile = "/Applications/OpenStudioApplication-1.1.1/EnergyPlus/Energy+.idd"
        IDF.setiddname(iddfile)
        # get the epw
        self.epw = "/Users/julietnwagwuume-ezeoke/Documents/cee256_local/weather_files/CA_PALO-ALTO-AP_724937S_19.epw"

        self.root = os.getcwd()
        self.opt_models_dir = os.path.join(self.root,"opt_models")
        # TODO make this an input, class is specified by the root idf 
        self.root_idf_path = root_idf
        self.root_idf = IDF(self.root_idf_path, self.epw)
            
    # generate new idf 
    def new_idfs(self, opt_group_name, fun_key, pc_arr):
        # make a group folder
        group_folder = os.path.join(self.opt_models_dir, opt_group_name)
        os.makedirs(group_folder)
        # keep track of the values changed in the idf 
        new_vals = {}
        for ix, pc in enumerate(pc_arr):
            # make a folder for the specific run 
            # rename negatives 
            str_pc = str(pc)
            if str_pc[0] == "-":
                str_pc = str_pc.replace("-", "neg_")
            str_pc
            run_folder = os.path.join(group_folder, f"run_{str_pc}")
            os.makedirs(run_folder)
            # make a copy of an og idf
            idf0_path = os.path.join(run_folder, "opt.idf")
            self.root_idf.save(idf0_path)

            # initialize this new idf 
            idf0 = IDF(idf0_path, self.epw)

            # call function to modify the idf 
            idf_adjust_fun = self.get_epppy_change_fun(fun_key)
            idf0, new_val = idf_adjust_fun(idf0, pc)

            # save the idf here 
            idf0.save()
            # save the new vals
            new_vals[pc] = new_val
        print(group_folder)
        # save to csv in group folder 
        new_vals_df = pd.DataFrame.from_dict(new_vals, orient="index")
        new_vals_df.to_csv(os.path.join(group_folder, "values.csv"))
        return group_folder


    def get_sub_dirs(self, group_path):
        sub_dirs = [d for d in os.listdir(group_path) if os.path.isdir(os.path.join(group_path, d))]
        return sub_dirs

    # run idfs 
    def run_idfs(self, group_path):
        print(group_path)
        sub_dirs = self.get_sub_dirs(group_path)
        for sub_dir in sub_dirs:
            dir = os.path.join(group_path, sub_dir)
            print(sub_dir)
            idf_path = os.path.join(dir, "opt.idf")
            idf0 = IDF(idf_path, self.epw)
            idf0.run(output_directory = dir)


    def extract_data(self, group_path):
        "can execute after run_idfs to get the data"
        print(group_path)

        sub_dirs = self.get_sub_dirs(group_path)

        sub_dir_data = OrderedDict()
        for sub_dir in sub_dirs:
            dir = os.path.join(group_path, sub_dir)

            # energy 
            sql_path = os.path.join(dir, "eplusout.sql")
            sqld = SQLiteResult(sql_path)

            # costs 
            html_path = os.path.join(dir, "eplustbl.htm")
            filehandle = open(html_path, 'r') # get a file handle to the html file
            namedtable = fasthtml.tablebyname(filehandle, "Tariff Summary")
            table_rows = namedtable[1]

            data = OrderedDict({
                # energy kwh 
                "elect": sqld.data_collections_by_output_name("Electricity:Facility")[-1].total,
                "hot": sqld.data_collections_by_output_name("DistrictHeating:Facility")[-1].total,
                "chill": sqld.data_collections_by_output_name("DistrictCooling:Facility")[-1].total,
                # costs $
                "elect_c": [t for t in table_rows if t[0] == 'ELECTRICITY TARIFF'][0][-1],
                "hot_c": [t for t in table_rows if t[0] == 'DISTRICTHEATING TARIFF'][0][-1],
                "chill_c": [t for t in table_rows if t[0] == 'DISTRICTCOOLING TARIFF'][0][-1],
            })
            data["total"] = data["elect"] +  data["hot"] +  data["chill"] 
            data["total_c"] = data["elect_c"] +  data["hot_c"] +  data["chill_c"] 

            sub_dir_data[sub_dir] = data
        
        # dataframe with energy and cost data 
        df = pd.DataFrame.from_dict(sub_dir_data, orient="index")

        # add edited values 
        vals = pd.read_csv(os.path.join(group_path, "values.csv"))
        dict_val =  OrderedDict()
        for i, val in zip(list(df.index), vals['0']):
            dict_val[i] = val
        df["vals"] = dict_val.values()

        # save as csv 
        df.to_csv(os.path.join(group_path, "data.csv"))
        
        # add the edited values 
        return df

    "start of eppy opt functions "

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

    def get_epppy_change_fun(self, key):
        change_fun_dict = {
            "SHGC": self.change_window_shgc
        }

        return change_fun_dict[key]






        