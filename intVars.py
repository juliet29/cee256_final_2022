import pickle

# original is in /Users/julietnwagwuume-ezeoke/Documents/aho/simulation/intVars.py

# run python intVars.py
intVars = [
    # general
    "Zone Mean Radiant Temperature",
    "Zone Mean Air Temperature",
    "Zone Air Relative Humidity",
    "Zone Operative Temperature",
    "Surface Heat Storage Energy",
    # load balance terms ------------
    # electricity, people (+)
    "Zone Electric Equipment Electric Energy",
    "Zone People Total Heating Energy",
    # solar (+)
    "Zone Windows Total Transmitted Solar Radiation Energy",
    # opaque(+/-)
    "Surface Average Face Conduction Heat Transfer Energy",
    "Zone Opaque Surface Inside Faces Total Conduction Heat Gain Energy",
    "Zone Opaque Surface Inside Faces Total Conduction Heat Loss Energy",
    "Zone Opaque Surface Outside Faces Total Conduction Heat Gain Energy",
    "Zone Opaque Surface Outside Faces Total Conduction Heat Loss Energy",
    # glazing (+/-)
    "Surface Window Heat Gain Energy",
    "Surface Window Heat Gain Rate",
    "Surface Window Heat Loss Energy",
    "Zone Windows Total Transmitted Solar Radiation Energy",
    "Zone Windows Total Heat Gain Energy",
    "Zone Windows Total Heat Loss Energy",
    # facility
    "District Heating Hot Water Energy",  # J
    "District Cooling Chilled Water Energy",
    # hvac study
    "Heating Coil Heating Rate",
    "Heating Coil Heating Energy",
    "Zone Air Terminal VAV Damper Position",
    "Zone Air Terminal Minimum Air Flow Fraction",
    "Zone Lights Total Heating Rate",
    # heat gains 
    "Zone People Total Heating Rate",
    "Zone Electric Equipment Total Heating Rate",
    "Zone Total Internal Total Heating Rate",
    "Zone Air Heat Balance Surface Convection Rate",
    "Zone Infiltration Total Heat Gain Energy",
    "Zone Ventilation Total Heat Gain Energy",
    "Zone Air Terminal Outdoor Air Volume Flow Rate"
]


with open("intVars", "wb") as f:
    pickle.dump(intVars, f)

"""
cd _final_project_local/
python intVars.py
"""
