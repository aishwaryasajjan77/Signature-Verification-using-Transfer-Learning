# -*- coding: utf-8 -*-
# using vgg16 for signature verification

from google.colab import drive
drive.mount("/content/gdrive")

!pip install keras

import keras
from tensorflow.keras.applications import VGG16
# MobileNet was designed to work on 224 x 224 pixel input images sizes
img_rows, img_cols = 224, 224

# Re-loads the MobileNet model without the top or FC layers
VGG16 = VGG16(weights = 'imagenet',
                 include_top = False,
                 input_shape = (img_rows, img_cols, 3))

# Here we freeze the last 4 layers
# Layers are set to trainable as True by default
for layer in VGG16.layers:
    layer.trainable = False

def add(bottom_model, num_classes):
    """creates the top or head of the model that will be
    placed ontop of the bottom layers"""
    top_model = VGG16.output
    top_model = GlobalAveragePooling2D()(top_model)
    top_model = Dense(1024,activation='relu')(top_model)
    top_model = Dense(512,activation='relu')(top_model)
    top_model = Dense(256,activation='relu')(top_model)
    top_model = Dense(num_classes,activation='softmax')(top_model)
    return top_model

#create a final model
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Activation, Flatten, GlobalAveragePooling2D
from tensorflow.keras.layers import Conv2D, MaxPooling2D, ZeroPadding2D
from tensorflow.keras.models import Model
# Set our class number to 9 (types of boat)
num_classes = 2

FC_Head = add(VGG16, num_classes)

model = Model(inputs = VGG16.input, outputs = FC_Head)

print(model.summary())

from keras.preprocessing.image import ImageDataGenerator

train_data_dir = '/content/gdrive/My Drive/sample_Signature/sample_Signature'
validation_data_dir = '/content/gdrive/My Drive/Dataset_Signature_Final/Dataset/dataset1'
"""rotation_range=45,
      width_shift_range=0.3,
      height_shift_range=0.3,"""
# Let's use some data augmentaiton
train_datagen = ImageDataGenerator(
      rescale=1./255,
      horizontal_flip=True,
      fill_mode='nearest')

validation_datagen = ImageDataGenerator(rescale=1./255)

# set our batch size (typically on most mid tier systems we'll use 16-32)
batch_size = 32

train_generator = train_datagen.flow_from_directory(
        train_data_dir,
        target_size=(img_rows, img_cols),
        batch_size=batch_size,
        class_mode='categorical')

validation_generator = validation_datagen.flow_from_directory(
        validation_data_dir,
        target_size=(img_rows, img_cols),
        batch_size=batch_size,
        class_mode='categorical')

from keras.optimizers import RMSprop
from keras.callbacks import ModelCheckpoint, EarlyStopping


checkpoint = ModelCheckpoint("signature_verification.h5",
                             monitor="val_loss",
                             mode="min",
                             save_best_only = True,
                             verbose=1)

earlystop = EarlyStopping(monitor = 'val_loss',
                          min_delta = 0,
                          patience = 5,
                          verbose = 1,
                          restore_best_weights = True)

# we put our call backs into a callback list
callbacks = [earlystop, checkpoint]

# We use a very small learning rate
model.compile(loss = 'categorical_crossentropy',
              optimizer = RMSprop(lr = 0.00035),
              metrics = ['accuracy'])

# Enter the number of training and validation samples here
nb_train_samples = 300
nb_validation_samples = 120

# We only train 5 EPOCHS
epochs = 100
batch_size = 32

history = model.fit(
    train_generator,
    epochs =epochs,
    callbacks = callbacks,
    validation_data = validation_generator)

import matplotlib.pyplot as plt
import numpy
plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('model accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()
# summarize history for loss
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('model loss' )
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()

from keras.models import load_model
classifier = load_model('signature_verification.h5')

import os
import cv2
import numpy as np
from os import listdir
from google.colab.patches import cv2_imshow
from os.path import isfile, join

face_reco = {"[0]": "forged",
                      "[1]": "genuine",
                      }
face_reco_n = {"forged": "FORGED",
                      "genuine": "REAL",
                      }

def draw_test(name, pred, im):
    face = face_reco[str(pred)]
    BLACK = [0,0,0]
    expanded_image = cv2.copyMakeBorder(im, 80, 0, 0, 100 ,cv2.BORDER_CONSTANT,value=BLACK)
    cv2.putText(expanded_image, face, (20, 60) , cv2.FONT_HERSHEY_SIMPLEX,1, (0,0,255), 2)
    cv2_imshow(expanded_image)

def getRandomImage(path):
    """function loads a random images from a random folder in our test path """
    folders = list(filter(lambda x: os.path.isdir(os.path.join(path, x)), os.listdir(path)))
    random_directory = np.random.randint(0,len(folders))
    path_class = folders[random_directory]
    print("Class - " + face_reco_n[str(path_class)])
    file_path = path + path_class
    file_names = [f for f in listdir(file_path) if isfile(join(file_path, f))]
    random_file_index = np.random.randint(0,len(file_names))
    image_name = file_names[random_file_index]
    return cv2.imread(file_path+"/"+image_name)

for i in range(0,10):
    input_im = getRandomImage("/content/gdrive/My Drive/Dataset_Signature_Final/Dataset/dataset1/")
    input_original = input_im.copy()
    input_original = cv2.resize(input_original, None, fx=0.5, fy=0.5, interpolation = cv2.INTER_LINEAR)

    input_im = cv2.resize(input_im, (224, 224), interpolation = cv2.INTER_LINEAR)
    input_im = input_im / 255.
    input_im = input_im.reshape(1,224,224,3)

    # Get Prediction
    res = np.argmax(classifier.predict(input_im, 1, verbose = 0), axis=1)

    # Show image with predicted class
    draw_test("Prediction", res, input_original)
    cv2.waitKey(0)

cv2.destroyAllWindows()

import os
import cv2
import numpy as np
from os import listdir
from os.path import isfile, join
from google.colab.patches import cv2_imshow

j=0
k=0
y_true=[]
y_pred=[]
sign_rec = {"[0]": "forged",
                      "[1]": "genuine",
                      }
sign_rec_n = {"forged": "forged",
                      "genuine": "genuine",
                      }

def draw_test(name, pred, im):
    face = sign_rec[str(pred)]
    y_pred.append(face)
    BLACK = [0,0,0]
    expanded_image = cv2.copyMakeBorder(im, 80, 0, 0, 100 ,cv2.BORDER_CONSTANT,value=BLACK)
    cv2.putText(expanded_image, face, (20, 60) , cv2.FONT_HERSHEY_SIMPLEX,1, (0,0,255), 2)
    cv2_imshow(expanded_image)

def getRandomImage(path,i,j):
    if j<60:
        """function loads a random images from a random folder in our test path """
        folders = list(filter(lambda x: os.path.isdir(os.path.join(path, x)), os.listdir(path)))
        #random_directory = np.random.randint(0,len(folders))
        #path_class = folders[random_directory]
        path_class = folders[i]
        print("Class - " + sign_rec_n[str(path_class)])
        y_true.append(sign_rec_n[str(path_class)])
        file_path = path + path_class
        file_names = [f for f in listdir(file_path) if isfile(join(file_path, f))]
        #random_file_index = np.random.randint(0,len(file_names))
        #image_name = file_names[random_file_index]
        image_name = file_names[j]
        return cv2.imread(file_path+"/"+image_name)
    else:
        return 'STOP'
while(1):
    input_im = getRandomImage("/content/gdrive/My Drive/Dataset_Signature_Final/Dataset/dataset1/",0,j)
    if input_im == 'STOP' :
        break
    else:
        print(j)
        input_original = input_im.copy()
        input_original = cv2.resize(input_original, None, fx=0.5, fy=0.5, interpolation = cv2.INTER_LINEAR)
        input_im = cv2.resize(input_im, (224, 224), interpolation = cv2.INTER_LINEAR)
        input_im = input_im / 255.
        input_im = input_im.reshape(1,224,224,3)
        # Get Prediction
        res = np.argmax(classifier.predict(input_im, 1, verbose = 0), axis=1)
        # Show image with predicted class
        draw_test("Prediction", res, input_original)
        j+=1
while(1):
    input_im = getRandomImage("/content/gdrive/My Drive/Dataset_Signature_Final/Dataset/dataset1/",1,k)
    if input_im == 'STOP':
        break
    else:
        print(k)
        input_original = input_im.copy()
        input_original = cv2.resize(input_original, None, fx=0.5, fy=0.5, interpolation = cv2.INTER_LINEAR)
        input_im = cv2.resize(input_im, (224, 224), interpolation = cv2.INTER_LINEAR)
        input_im = input_im / 255.
        input_im = input_im.reshape(1,224,224,3)
        # Get Prediction
        res = np.argmax(classifier.predict(input_im, 1, verbose = 0), axis=1)
        # Show image with predicted class
        draw_test("Prediction", res, input_original)
        k+=1

cv2.destroyAllWindows()
print(y_true,y_pred)

from sklearn.metrics import confusion_matrix
confusion_matrix(y_true, y_pred,labels=['forged','genuine'])



