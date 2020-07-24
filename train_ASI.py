# Driver program to train a new ASI model from a pre-generated training set

# ==============================================================================

from ASI import ASI_Index

# ==============================================================================
# PROGRAM CONFIGURATION

# Path to the training set
train_set_path = "T16QEJ_20190706T160839_ML_small.npy"

# Number of training epochs to use
training_epochs = 10

# The directory where the trained model is to be saved
model_out_dir = "./"

# ==============================================================================

ASI = ASI_Index()

model = ASI.train_model(train_set_path, model_out_dir=model_out_dir, training_epochs=training_epochs)
