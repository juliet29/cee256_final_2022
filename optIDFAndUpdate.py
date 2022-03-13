# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import os
from eppy import *
from eppy.modeleditor import IDF
from datetime import datetime
import numpy as np
import pickle
import argparse

parser = argparse.ArgumentParser(description='update and run an idf file')

parser.add_argument("-f", "--folderToRun", help="entire path before the many subfolders", default=None)

args = parser.parse_args()


# %%
def getImmediateSubdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


# %%
# set the EPW and IDD Files 
iddfile = r"C:\EnergyPlusV9-4-0\Energy+.idd"
epw = r"C:\Users\juliet.ume-ezeoke\Desktop\aho\GHA_Accra.epw"

# %%
# set the idd
IDF.setiddname(iddfile)


# %%
###########################
if not args.folderToRun:
    folderToOpt = r"C:\Users\juliet.ume-ezeoke\Desktop\aho\0730\simulation\allTimber"
else:
    folderToOpt = args.folderToRun

newDirName = "output"
print(folderToOpt, newDirName)
###########################

# %%
pathName = folderToOpt
optFolders = getImmediateSubdirectories(pathName)

# run python intVars.py !!!!!!!!!!!!!!!!!
intVarsPath = r"C:\Users\juliet.ume-ezeoke\Desktop\aho\0999\intVars"
with open(intVarsPath, "rb") as f:
    intVars = pickle.load(f)



times = []
foldersToOpt = optFolders   # [0:1]

for count, currFolder in enumerate(foldersToOpt):
    # update user about progress
    now = datetime.now()
    currentTime = now.strftime("%H:%M:%S")
    foldersRemain = len(foldersToOpt) - count

    print("\n")
   
    print(currentTime, currFolder)
    print("Folder", count, "of", len(foldersToOpt))
    print("Folders Remaining:", foldersRemain)

    times.append(now)
    if len(times) > 1:   
        lastTime = np.diff(np.array(times))[0]
        print("Time Remaining:", lastTime*foldersRemain)

    print("\n")
   

    # go through all the folders + enter them 
    newPath = os.path.join(pathName, currFolder)
    print(newPath)
    os.chdir(newPath)
    print(os.getcwd())
    print(os.listdir(os.getcwd()))


    # get the idf 
    idfName = r"OpenStudio\run\in.idf"
    idf0 = IDF(idfName,epw)

    # update the outputs with interesting variables 
    currVars = [var.Variable_Name for var in idf0.idfobjects["Output:Variable"]]
    for var in intVars:
        if var not in currVars:
            newObj = idf0.newidfobject("Output:Variable", Key_Value='', Variable_Name=var)

    # change all reporting frequency
    allVars = [var for var in idf0.idfobjects["Output:Variable"]]
    for var in allVars:
        var.Reporting_Frequency = "Monthly"

    # change the run period
    runPeriod = idf0.idfobjects["RunPeriod"][0]
    runPeriod.Begin_Month = 1 
    runPeriod.Begin_Day_of_Month = 1
    runPeriod.End_Month = 1
    runPeriod.End_Day_of_Month = 31

    # change time steps per hour
    timestep = idf0.idfobjects["Timestep"][0]
    timestep.Number_of_Timesteps_per_Hour = 3

    # ensure that simulation warms up appropriately 
    building = idf0.idfobjects["Building"][0]
    building.Minimum_Number_of_Warmup_Days = 6

    # make a new dir for the output
    os.makedirs(newDirName)

    # save the updated idf there
    idf0.save(os.path.join(newDirName, "in2.idf"))

    
    # run the idf 
    idf0.run(output_directory=newDirName)

    

    

