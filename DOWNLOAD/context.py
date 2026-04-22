"""
define the path to important folders without having
to install anything -- just do:

import context

then the path for the data directory is

context.data_dir

"""
#%%
import sys
from pathlib import Path, PurePath
from os.path import join, abspath

path = Path(__file__).resolve()  # this file

this_dir = path.parent  # this folder
root_dir = this_dir.parent  # root folder

# on compute canada Path will not grab the two base directories --> hacky workaorund (comment out if on local)
root_dir = str(root_dir)

# get paths for important directories
utils_dir = root_dir + "/UTILS/"

sys.path.insert(0, str(root_dir))

# %%
