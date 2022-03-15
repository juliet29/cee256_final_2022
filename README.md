# cee256_final_2022

## CEE256 Final Project using EnergyPlus

The goal of this project was to create a model of an existing building and
calibrate it using historical data. By performing a sensitivity analysis, it was
possible to point out opportunities for optimizing the building's energy
performance.

### Description of Relevant Folders and Files

    .
    ├── ...
    ├── calibration
    │   ├── eppy_adjusted_models_2       # Models created in the process of calibration
    |   ├── calibration_03-09.ipynb      # Plots of calibrated models
    |   ├── calibration_fun.ipynb        # Functions to create plots of calibrated models
    |   ├── adjustModels.ipynb           # Adjust and run model .idf files, adjustments for the final calibrated model
    │   └── ...
    ├── optimization
    │   ├── opt_models                   # Model groups of variables adjusted to perform sensitivity analysis
                                         # contains data.csv files with summary data for a variable group
    |   ├── opt_fun.py                   # Functions used to generate models for sensitivity analysis
    |   ├── opt_exec.py                  # Executable to generate a model group using command line
    |   ├── analysis_fun.py              # Functions to create plots for comparing energy use across model groups
    |   ├── analysis.ipynb               # Examine plots of energy use across model groups
    │   └── ...
    └── ...
