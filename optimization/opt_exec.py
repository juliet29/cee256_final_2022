from opt_fun import opt_functions as of
from IPython.display import display
import argparse

parser = argparse.ArgumentParser(description='generate and run many idf files')

parser.add_argument("-r", "--root_idf", help="root idf that group will be based on", required=True)
parser.add_argument("-n", "--group_name", help="root idf that group will be based on", required=True)
parser.add_argument("-k", "--fun_key", help="root idf that group will be based on", default="SHGC")
parser.add_argument("-p", "--pc_arr", nargs="+", type=int, help="root idf that group will be based on", default=[-10, 10])

args = parser.parse_args()

print(args.pc_arr)


# init new opt class based on a root idf 
root_idf_path = args.root_idf
test = of(root_idf_path)

# percent change array 
pc_arr = [-10, 10]

# make new idfs 
group_folder = test.new_idfs(args.group_name, args.fun_key, args.pc_arr)

test.run_idfs(group_folder)

df = test.extract_data(group_folder)
display(df)


