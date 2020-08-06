# Driver program to test a previously generated ASI model against a test dataset

# ==============================================================================

import sys

from ASI import ASI_Index

# ==============================================================================
# Program configuration
# See ASI.py for further details

# Path to the testing set
test_set_path = "T16QEJ_20190706T160839_ML_full.npy"
#test_set_path = sys.argv[1]

# Path to the ASI model
model_path = "ASImodelColabv2.h5"

# Batch size for evaluation -- this can be large!
batch_size = 2048

# ==============================================================================

# Initialize the ASI class
ASI = ASI_Index()

# Test the given model
ASI.test_model(test_set_path, model_path, batch_size=batch_size)
