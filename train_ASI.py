# Driver program to train a new ASI model from a pre-generated training set

# ==============================================================================

import sys

from ASI import ASI_Index

# ==============================================================================
# Program confgiruation
# See ASI.py for further details

# Path to the training set
train_set_path = ""
#train_set_path = sys.argv[1]

# Batch size used for training -- should not be large!
batch_size = 32

# Number of training epochs to use
training_epochs = 10

# Directory where the trained model is to be saved
model_out_dir = "./"

# ==============================================================================

# Initialize the ASI class (without loading a model)
ASI = ASI_Index()

# Train ASi using the given training set
model = ASI.train_model(train_set_path, model_out_dir=model_out_dir, batch_size=batch_size, training_epochs=training_epochs)
