from tabnanny import verbose
import numpy as np
import os
from eppy import *
from eppy.modeleditor import IDF
import pandas as pd
from ladybug.sql import SQLiteResult
from ladybug import analysisperiod as ap
from collections import OrderedDict
from eppy.results import fasthtml
import witheppy
import witheppy.eppyhelpers.extfields as extfields
from eppy import modeleditor


class opt_functions():
    def __init__(self, root_idf):
        # set the idd
        iddfile = "/Applications/OpenStudioApplication-1.1.1/EnergyPlus/Energy+.idd"
        IDF.setiddname(iddfile)
        # get the epw
        self.epw = "/Users/julietnwagwuume-ezeoke/Documents/cee256_local/weather_files/CA_PALO-ALTO-AP_724937S_19.epw"

        self.root = os.getcwd()
        self.opt_models_dir = os.path.join(self.root, "opt_models")
        # TODO make this an input, class is specified by the root idf
        self.root_idf_path = root_idf
        self.root_idf = IDF(self.root_idf_path, self.epw)

    # generate new idf
    def new_idfs(self, opt_group_name, fun_key, pc_arr):
        # make a group folder
        group_folder = os.path.join(self.opt_models_dir, opt_group_name)

        # check that the group folder doesnt already exist
        exist_dirs = self.get_sub_dirs(self.opt_models_dir)
        if opt_group_name in exist_dirs:
            print("group name exists, delete existing verion!")
            return False

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
            print(f"CREATING RUN: {opt_group_name} {pc}")
            idf0 = IDF(idf0_path, self.epw)
            print("\n")

            # call function to modify the idf
            idf_adjust_fun = self.get_epppy_change_fun(fun_key)
            idf0, new_val = idf_adjust_fun(idf0, pc)

            # save the idf here
            idf0.save()
            # save the new vals
            new_vals[pc] = [new_val, run_folder]

        print(group_folder)
        # save to csv in group folder
        new_vals_df = pd.DataFrame.from_dict(new_vals, orient="index")
        new_vals_df.to_csv(os.path.join(group_folder, "values.csv"))
        return group_folder

    def get_sub_dirs(self, group_path):
        sub_dirs = [d for d in os.listdir(
            group_path) if os.path.isdir(os.path.join(group_path, d))]
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
            idf0.run(output_directory=dir, verbose="q")

    def extract_data(self, group_path):
        "can execute after run_idfs to get the data"
        print(group_path)
        # extract data based on values csv
        vals = pd.read_csv(os.path.join(group_path, "values.csv"))

        sub_dir_keys = list(vals["Unnamed: 0"])
        sub_dirs = list(vals["1"])

        sub_dir_data = OrderedDict()
        for dir, key in zip(sub_dirs, sub_dir_keys):
            # energy
            sql_path = os.path.join(dir, "eplusout.sql")
            sqld = SQLiteResult(sql_path)

            # costs
            html_path = os.path.join(dir, "eplustbl.htm")
            # get a file handle to the html file
            filehandle = open(html_path, 'r')
            namedtable = fasthtml.tablebyname(filehandle, "Tariff Summary")
            table_rows = namedtable[1]

            # compile data
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
            data["total"] = data["elect"] + data["hot"] + data["chill"]
            data["total_c"] = data["elect_c"] + data["hot_c"] + data["chill_c"]

            sub_dir_data[key] = data

        # dataframe with energy and cost data
        df = pd.DataFrame.from_dict(sub_dir_data, orient="index")

        # add eppy adjusted values and percent change
        dict_val = OrderedDict()
        for i, val, pc in zip(list(df.index), vals['0'], vals["Unnamed: 0"]):
            dict_val[i] = [val, pc]
        df["vals"] = [v[0] for v in dict_val.values()]
        df["perc_change"] = [v[1] for v in dict_val.values()]

        # save as csv
        df.to_csv(os.path.join(group_path, "data.csv"))

        # add the edited values
        return df, vals

    # -----------------------------------------------------------------------------
    # ----------------------     "start of eppy opt functions" --------------------
    # -----------------------------------------------------------------------------

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
        window_mat = [s for s in idf0.idfobjects["WindowMaterial:SimpleGlazingSystem"]
                      if s.Name == "Thornton Window Material 1"][0]
        # get current value
        curr_val = window_mat.Solar_Heat_Gain_Coefficient
        print(curr_val)
        # calculate new values
        new_val = self.perc_change_val(pc, curr_val)
        # adjust the idf
        window_mat.Solar_Heat_Gain_Coefficient = new_val
        # return the idf
        print([s for s in idf0.idfobjects["WindowMaterial:SimpleGlazingSystem"]
              if s.Name == "Thornton Window Material 1"][0])
        return (idf0, new_val)

    def change_window_u_factor(self, idf0, pc):
        window_mat = [s for s in idf0.idfobjects["WindowMaterial:SimpleGlazingSystem"]
                      if s.Name == "Thornton Window Material 1"][0]
        # get current value
        curr_val = window_mat.UFactor
        print(curr_val)
        # calculate new values
        new_val = self.perc_change_val(pc, curr_val)
        # adjust the idf
        window_mat.UFactor = new_val
        # return the idf
        print([s for s in idf0.idfobjects["WindowMaterial:SimpleGlazingSystem"]
              if s.Name == "Thornton Window Material 1"][0])
        return (idf0, new_val)

    # simple material to vary walls, roof, floor
    def make_new_const(self, u_factor, idf0, pc, curr_const):
        # convert to r value
        r_val = 1 / u_factor
        # determine new r value
        new_val = self.perc_change_val(pc, r_val)

        #  create new material
        wall_mat_obj = idf0.newidfobject(
            "Material:NoMass",
            Name="ExperimentalMaterial",
            Roughness="Smooth",  # like stucco outside material
            Thermal_Resistance=new_val
        )

        # assign it to a construction
        wall_const_obj = idf0.newidfobject(
            "Construction",
            Name="ExperimentalConstruction",
            Outside_Layer="ExperimentalMaterial"
        )

        # replace all building surfaces with this construction with the exp one
        ext_surfaces = [s for s in idf0.idfobjects["BuildingSurface:Detailed"]
                        if s.Construction_Name == curr_const]
        for s in ext_surfaces:
            s.Construction_Name = "ExperimentalConstruction"
        return(idf0, new_val)

    def change_wall_r(self, idf0, pc):
        # current value from html of calibrated model,
        #  Report: Envelope Summary, U Factor with No Film
        u_factor = 0.284  # W / m2-K
        curr_const = "Thornton Ext Wall"
        idf0, new_val = self.make_new_const(u_factor, idf0, pc, curr_const)
        return (idf0, new_val)

    def change_roof_r(self, idf0, pc):
        # current value from html of calibrated model
        u_factor = 0.283  # W / m2-K
        curr_const = "ASHRAE 90.1-2010 ExtRoof IEAD ClimateZone 2-8"
        idf0, new_val = self.make_new_const(u_factor, idf0, pc, curr_const)
        return (idf0, new_val)

    def change_floor_r(self, idf0, pc):
        # current value from html of calibrated model
        u_factor = 5.634  # W / m2-K
        curr_const = "ExtSlabCarpet 4in ClimateZone 1-8"
        idf0, new_val = self.make_new_const(u_factor, idf0, pc, curr_const)
        return (idf0, new_val)

    def change_floor_r_2(self, idf0, pc):
        # current value from html of calibrated model
        u_factor = 0.284  # W / m2-K
        curr_const = "ExtSlabCarpet 4in ClimateZone 1-8"
        idf0, new_val = self.make_new_const(u_factor, idf0, pc, curr_const)
        return (idf0, new_val)

    def change_roof_r_2(self, idf0, pc):
        # current value from html of calibrated model
        u_factor = 0.284  # W / m2-K
        curr_const = "ExtSlabCarpet 4in ClimateZone 1-8"
        idf0, new_val = self.make_new_const(u_factor, idf0, pc, curr_const)
        return (idf0, new_val)

    def change_lighting(self, idf0, pc):
        light_obj = [s for s in idf0.idfobjects["Lights"]]
        new_vals = []
        for obj in light_obj:
            # get current val
            curr_val = obj.Watts_per_Zone_Floor_Area
            # make new val
            new_val = self.perc_change_val(pc, curr_val)
            # change object
            obj.Watts_per_Zone_Floor_Area = new_val
            new_vals.append(new_val)
        # return avg for now
        new_val = np.mean(new_val)

        # print to check
        new_light_obj = [s for s in idf0.idfobjects["Lights"]]
        for obj in new_light_obj:
            print(obj.Zone_or_ZoneList_Name, obj.Watts_per_Zone_Floor_Area)
        print(f"Average Lighting: {new_val}")
        print("\n")
        return (idf0, new_val)

    def change_equip(self, idf0, pc):
        equip_obj = [s for s in idf0.idfobjects["ElectricEquipment"]]
        new_vals = []
        for obj in equip_obj:
            # get current val
            curr_val = obj.Watts_per_Zone_Floor_Area
            # make new val
            new_val = self.perc_change_val(pc, curr_val)
            # change object
            obj.Watts_per_Zone_Floor_Area = new_val
            new_vals.append(new_val)
        # return avg for now
        new_val = np.mean(new_val)

        # print to check
        new_equip_obj = [s for s in idf0.idfobjects["ElectricEquipment"]]
        for obj in new_equip_obj:
            print(obj.Zone_or_ZoneList_Name, obj.Watts_per_Zone_Floor_Area)
        print(f"Average Equip {new_val}")
        print("\n")
        return (idf0, new_val)

    # setpoints
    def change_setp(self, idf0, pc, sched_name):
        sched = [s  for s in idf0.idfobjects["Schedule:Day:Interval"] if s.Name == sched_name][0]
        curr_vals = {
            "val_1": sched.Value_Until_Time_1,
            "val_2": sched.Value_Until_Time_2,
            "val_3": sched.Value_Until_Time_3
        }
        # create new values
        new_vals = {k: self.perc_change_val(pc, v) for k, v in curr_vals.items()}
        # change the values 
        for field in sched.fieldnames:
            for i in range(3):
                if field == f"Value_Until_Time_{i+1}":
                    sched[field] = new_vals[f"val_{i+1}"]
        # return avg value 
        new_val = np.mean(list(new_vals.values()))

        # print to check 
        new_sched = [s  for s in idf0.idfobjects["Schedule:Day:Interval"] if s.Name == sched_name][0]
        for field in new_sched.fieldnames:
            for i in range(3):
                if field == f"Value_Until_Time_{i+1}":
                    print(field, new_sched[field])
        print(f"Average Setpoint {new_val}")
        return (idf0, new_val)

    def change_clgsetp(self, idf0, pc):
        idf0, new_val = self.change_setp(
            idf0, pc, "Medium Office ClgSetp Default Schedule")
        return (idf0, new_val)

    def change_htgsetp(self, idf0, pc):
        idf0, new_val = self.change_setp(
            idf0, pc, "Medium Office HtgSetp Default Schedule")
        return (idf0, new_val)

    def centeroidnp(self, arr):
        length = arr.shape[0]
        sum_x = np.sum(arr[:, 0])
        sum_y = np.sum(arr[:, 1])
        return sum_x/length, sum_y/length

    def get_zone_center(self, idf0, zone):
        # need center of zone area
        #  get vertices of zone floor
        print(zone.Name)
        surfs = idf0.idfobjects["BuildingSurface:Detailed".upper()]
        zone_surfs = [s for s in surfs if s.Zone_Name == zone.Name]
        floor = [s for s in zone_surfs if s.Surface_Type.upper() ==
                 "FLOOR"][0]  # surface
        # print(floor)

        verts = []
        for i in range(4):
            ix = i + 1
            coord = np.array(
                [floor[f"Vertex_{ix}_Xcoordinate"], floor[f"Vertex_{ix}_Ycoordinate"]])
            verts.append(coord)
        verts = np.array(verts)
        # print(verts)
        area_center = self.centeroidnp(verts)
        # print(area_center)

        # get zone height and divide by 2, and add to floor height
        height = modeleditor.zoneheight(idf0, zone.Name)

        floor_height = floor[f"Vertex_1_Zcoordinate"]
        # print(height, floor_height)
        mid_height = floor_height + height/2

        # zone center
        zone_center = (area_center[0], area_center[1], mid_height)
        print(zone_center)

        new_val = 0
        return zone_center

    def add_daylight_controls(self, idf0, pc):
        if pc != 0:
            # TODO get zone names, iterate over..
            zones = idf0.idfobjects["ZONE"]
            for ix, zone in enumerate(zones):
                # print(zone)
                zone_center = self.get_zone_center(idf0, zone)

                ref_point = idf0.newidfobject("Daylighting:ReferencePoint",
                                              Name=f"Experimental_Daylight_RefPt_{ix}",
                                              Zone_Name=zone.Name,
                                              XCoordinate_of_Reference_Point=zone_center[0],
                                              YCoordinate_of_Reference_Point=zone_center[1],
                                              ZCoordinate_of_Reference_Point=zone_center[2])

                control = idf0.newidfobject("Daylighting:Controls",
                                            Name=f"Experimental_Daylight_Controls_{ix}",
                                            Daylighting_Method="DElight",
                                            Zone_Name=zone.Name,
                                            Lighting_Control_Type="Stepped",
                                            Number_of_Stepped_Control_Steps=3,
                                            DElight_Gridding_Resolution=0.1, # sensitive to this grid size! 
                                            Daylighting_Reference_Point_1_Name=f"Experimental_Daylight_RefPt_{ix}",
                                            Fraction_of_Zone_Controlled_by_Reference_Point_1=1,
                                            Illuminance_Setpoint_at_Reference_Point_1=500)

            # remove extra ref point entries, eppy vistages
            day_controls = idf0.idfobjects["Daylighting:Controls"]
            for daycs in day_controls:
                extlist = extfields.extensiblefields2list(daycs, nested=True)
                # print(extlist, len(extlist))
                del extlist[1:10]
                # print(extlist, len(extlist))
                extfields.list2extensiblefields(daycs, extlist)

            # print(control)
            new_val = 1  # zones made
            print([d.Name for d in idf0.idfobjects["Daylighting:Controls"]])

        else:
            new_val = 0
        return(idf0, new_val)

    def get_epppy_change_fun(self, key):
        change_fun_dict = {
            # window properties 
            "SHGC": self.change_window_shgc,
            "WINDOW_U": self.change_window_u_factor,
            # external surfaces r values
            "WALL": self.change_wall_r,
            "ROOF": self.change_roof_r,
            "FLOOR": self.change_floor_r,
            # floor and roof with initial u-val same as walls
            "FLOOR_2": self.change_floor_r_2,
            "ROOF_2": self.change_roof_r_2,
            # lighting and equipment 
            "LIGHT": self.change_lighting,
            "EQUIP": self.change_equip,
            # cooling and heating setpoints 
            "COOL": self.change_clgsetp,
            "HEAT": self.change_htgsetp,
            # daylight controls 
            "DAYLIGHT": self.add_daylight_controls
        }

        return change_fun_dict[key]
