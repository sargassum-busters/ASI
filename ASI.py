# The main class for the ASI index

# ==============================================================================

import datetime
import os
import sys
import time

import numpy as np
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf
from tensorflow import keras

# ==============================================================================

class ASI_Index:
  """Aquae Satus Invenio: discovery of the waters

  A new algorithm for the satellite detection of floating sargassum on
  Sentinel-2 20m imagery using Machine Learning.
  """

  # ============================================================================

  name = "ASI"

  # Sentinel-2 channels used to compute ASI
  # Changing this list will require re-training the model
  required_channels = ["B02", "B03", "B04", "B05", "B06", "B07", "B8A", "B11", "B12"]

  # ============================================================================

  def __init__(self, model_path=None, verbose=True, batch_size=2048):

    self.verbose = verbose
    self.model_path = None
    self.model = None
    self.batch_size = batch_size
    if model_path is not None:
      self.load_model(model_path)

  # ============================================================================

  def load_model(self, model_path):

    self.model_path = model_path
    self.model = keras.models.load_model(self.model_path)
    if self.verbose:
      print("Loaded ASI model {}".format(self.model_path))

  # ============================================================================

  def load_ML_dataset(self, dataset_path):

    dataset = np.load(dataset_path)

    if dataset.ndim == 2:

      # Minimal training set: each row is a pixel
      names = ['coordX', 'coordY', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B8A', 'B11', 'B12', 'sargassum']

      X = dataset[:, 2:11]
      y = dataset[:, 11].astype(int)

    elif dataset.ndim == 3:

      # Full array training set
      names = ['B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B8A', 'B11', 'B12', 'sargassum']

      NX, NY, C = dataset.shape
      dataset = dataset.reshape(NX*NY, C)
      X = dataset[:, 0:9]
      y = dataset[:, 9].astype(int)

    return names, X, y

  # ============================================================================

  def train_model(self, train_set_path, model_out_dir="./", training_epochs=10):

    from sklearn.model_selection import train_test_split

    start_time = time.time()
    time_datetime = time.ctime(int(time.time()))
    print("Start: " + time_datetime)

    print("\n"+"-"*70)
    print("Loading training set ...")

    # --------------------------------------------------------------------------
    # Load training set

    names, X, y = self.load_ML_dataset(train_set_path)

    print()
    print(train_set_path)
    print("X shape: " + str(X.shape))
    print("y shape: " + str(y.shape))

    # Count classes
    (unique, counts) = np.unique(y, return_counts=True)
    frequencies = np.asarray((unique, counts))
    print(frequencies.shape)
    print(frequencies)

    time_loaded = time.time()
    print("\nTraining set loaded in {:.3f} s".format(time_loaded - start_time))

    # --------------------------------------------------------------------------
    # Training

    print("\n"+"-"*70)
    print("Training neural network ...\n")

    # Separate training and test data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0)

    # Create neural network
    model = keras.Sequential([
        keras.layers.Flatten(input_shape=(9,)),
        keras.layers.Dense(14, activation=tf.nn.relu),
        keras.layers.Dense(1, activation=tf.nn.sigmoid),
    ])

    # Set optimizer and loss function
    model.compile(optimizer='adam',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])

    # Tensorboard requirements
    log_dir = "logs/fit/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    tensorboard_callback = keras.callbacks.TensorBoard(log_dir=log_dir, histogram_freq=1)

    # Train
    model.fit(X_train,
              y_train,
              epochs=training_epochs,
              batch_size=32,
              verbose=1,
              validation_data=(X_test, y_test),
              callbacks=[tensorboard_callback])

    # Training time
    time_trained = time.time()
    print("\nModel trained in {:.3f} s".format(time_trained - time_loaded))

    # --------------------------------------------------------------------------
    # Save model

    out_path = os.path.join(model_out_dir, "test.h5")
    model.save(out_path)
    print("\nSaved {}".format(out_path))

    time_saved = time.time()
    # print("\nModel saved in {:.3f} s".format(time_saved - time_trained))

    # --------------------------------------------------------------------------

    print("\nTraining program complete, total time: {:.3f} s".format(time_saved - start_time))

    return model

  # ============================================================================

  def test_model(self, test_set_path, model_path, remove_masked=True, predict_threshold=0.5, batch_size=2048):

    start_time = time.time()
    time_datetime = time.ctime(int(time.time()))
    print("Start: " + time_datetime)

    # --------------------------------------------------------------------------
    # Load model

    model = keras.models.load_model(model_path)
    print("\nLoaded ASI model {}".format(model_path))

    # --------------------------------------------------------------------------
    # Load test set

    print("\n"+"-"*70)
    print("Loading test set ...")

    names, XzTest, yzTest = self.load_ML_dataset(test_set_path)

    num_non_sarg = np.count_nonzero(yzTest == 0)
    num_sargassum = np.count_nonzero(yzTest == 1)
    num_masked = np.count_nonzero(yzTest == 2)

    print()
    print(test_set_path)
    print("X shape: {}".format(" x ".join(str(x) for x in XzTest.shape)))
    print("y shape: {}".format(" x ".join(str(x) for x in yzTest.shape)))

    if remove_masked:
      XzTest = XzTest[yzTest != 2]
      yzTest = yzTest[yzTest != 2]
      num_classes = 2
    else:
      yzTest[yzTest == 2] = 0
      num_classes = 3

    print("\nSargassum pixels:        {:,}".format(num_sargassum))
    print("Non-sargassum pixels:    {:,}".format(num_non_sarg))
    print("Masked pixels{}: {:,}".format(" (removed)" if remove_masked else "", num_masked))

    time_loaded = time.time()
    print("\nTest set loaded in {:.3f} s".format(time_loaded - start_time))

    # --------------------------------------------------------------------------
    # Evaluate model

    print("\n"+"-"*70)
    print("Evaluating model ...\n")
    print("batch_size = {}".format(batch_size))

    # test_loss, test_acc = model.evaluate(XzTest, yzTest, batch_size=batch_size)
    # print('Test accuracy:', test_acc)

    # time_tested = time.time()
    # print("\nModel evaluation completed in {:.3f} s".format(time_tested - time_test_loaded))

    Ypred = model.predict(XzTest, verbose=self.verbose, batch_size=batch_size)

    Ypred_cls = np.empty_like(Ypred, dtype=int)
    Ypred_cls[Ypred >= predict_threshold] = 1
    Ypred_cls[Ypred < predict_threshold] = 0
    Ypred_cls = Ypred_cls.reshape((Ypred.shape[0],))

    cmatrix = tf.math.confusion_matrix(labels=yzTest, predictions=Ypred_cls, num_classes=num_classes).numpy()

    # Class 1 = sargassum is "positive" here
    TN = cmatrix[0, 0]
    FP = cmatrix[0, 1]
    FN = cmatrix[1, 0]
    TP = cmatrix[1, 1]

    # Just to check:
    # print(TN, np.count_nonzero((yzTest == 0) & (Ypred_cls == 0)))
    # print(FP, np.count_nonzero((yzTest == 0) & (Ypred_cls == 1)))
    # print(FN, np.count_nonzero((yzTest == 1) & (Ypred_cls == 0)))
    # print(TP, np.count_nonzero((yzTest == 1) & (Ypred_cls == 1)))

    sensitivity = TP/(TP+FN)
    specificity = TN/(TN+FP)
    miss_rate = FN/(FN+TP)
    fall_out = FN/(FP+TN)
    precision = TP/(TP+FP)
    P = TP + FN
    N = TN + FP
    accuracy = (TP+TN)/(P+N)
    F1 = 2*TP/(2*TP + FP + FN)

    print()
    print("Model accuracy: {:.1f}%".format(100*accuracy))

    print()
    print("Positive predictions: {:,}".format(TP+FP))
    print("Negative predictions: {:,}".format(TN+FN))
    print("Sensitivity (true positives): {:.1f}% ({:,})".format(100*sensitivity, TP))
    print("Specificity (true negatives): {:.1f}% ({:,})".format(100*specificity, TN))
    print("Miss rate (false negatives): {:.1f}% ({:,})".format(100*miss_rate, FN))
    print("Fall-out (false positives): {:.1f}% ({:,})".format(100*fall_out, FP))
    print("Precision (positive predictive value): {:.1f}%".format(100*precision))
    print("F1 score:  {:.1f}%".format(100*F1))

    time_eval = time.time()
    print("\nCompleted evaluation in {:.3f} s".format(time_eval - time_loaded))


  # ============================================================================

  def compute(self, channels_data, batch_size=None):

    if batch_size is not None:
      self.batch_size = batch_size

    NCH = len(channels_data)
    NX, NY = channels_data[self.required_channels[0]].shape
    NTOT = NX * NY
    dtype = channels_data[self.required_channels[0]].dtype

    # Join and reshape data in preparation for keras
    data = np.empty((NTOT, NCH), dtype=dtype)
    for i in range(NCH):
      data[:, i] = channels_data[self.required_channels[i]].reshape((NTOT,))
    if self.verbose:
      print("Input: {:,} x {}, {:.1f} MB".format(*data.shape, data.nbytes/1024**2))

    if self.verbose:
      GPUs = tf.config.experimental.list_physical_devices('GPU')
      if len(GPUs) > 0:
        s = "Executing on {} GPU{}".format(len(GPUs), "s" if len(GPUs) > 1 else "", GPUs)
      else:
        s = "Executing on CPU"
      if self.batch_size is None:
        s += " using automatic batch_size"
      else:
        s += " using batch_size = {}".format(self.batch_size)
      print(s)

    # Run through model
    result = self.model.predict(data, verbose=self.verbose, batch_size=self.batch_size)

    # Reshape result back to original image shape
    result = result.reshape((NX, NY))

    return result

  # ============================================================================
