# Driver program to test a previously generated ASI model against a test dataset

# ==============================================================================

from ASI import ASI_Index

# ==============================================================================
# PROGRAM CONFIGURATION

# Path to the testing set
test_set_path = "T16QEJ_20190706T160839_ML_full.npy"

# Path to the ASI model
model_path = "ASImodelColabv2.h5"

# Batch size for evaluation
batch_size = 2048

# ==============================================================================

ASI = ASI_Index()

model = ASI.test_model(test_set_path, model_path, batch_size=batch_size)
