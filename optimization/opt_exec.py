from opt_fun import opt_functions as of
from IPython.display import display
import argparse

parser = argparse.ArgumentParser(description='generate and run many idf files')

parser.add_argument("-r", "--root_idf",
                    help="root idf that group will be based on", required=True)
parser.add_argument("-n", "--group_name",
                    help="name for the group of opt to be performed", required=True)
parser.add_argument(
    "-k", "--fun_key", help="type of changes to make to the idf", default="SHGC")
parser.add_argument("-p", "--pc_arr_key",
                    help="key corresponding to array of percent change to consider", default="TEST")

args = parser.parse_args()

print(args)


# init new opt class based on a root idf
root_idf_path = args.root_idf
test = of(root_idf_path)

# percent change array
pc_dict = {
    "TEST": [-1],
    "NARROW": [-10, 10],
    "WIDE": [-98, -50, -25, 0, 25, 50, 98],
    "NEGATIVE": [-98, -75, -50, -25, -10, -5, -2.5, -1, 0],
    "POSITIVE": [0, 1, 2.5, 5, 10, 25, 50, 98, 75],
    "BINARY": [0,1]

}
pc_arr = pc_dict[args.pc_arr_key]


# make new idfs
group_folder = test.new_idfs(args.group_name, args.fun_key, pc_arr)

# will only get here if the group folder name is unique 
if group_folder:
    test.run_idfs(group_folder)
    df = test.extract_data(group_folder)
    display(df)
