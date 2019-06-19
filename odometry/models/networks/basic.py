import keras
from keras import backend as K

from keras.models import Model
from keras.layers.convolutional import Conv2D
from keras.layers import Input, Flatten, Dense, Layer
from keras import regularizers

from odometry.models.layers import ConstLayer, conv2d

from keras.applications.resnet50 import ResNet50


def construct_resnet50_model(imgs, 
                             frames_concatenated, 
                             weights='imagenet', 
                             kernel_initializer='glorot_normal'):
    
    conv0 = Conv2D(3, kernel_size=7, padding='same', activation='relu',
                   kernel_initializer=kernel_initializer, name='conv0')(frames_concatenated)

    base_model = ResNet50(weights=weights, include_top=False, pooling=None)

    outputs = base_model(conv0)
    embedding = Flatten()(outputs)

    fc1 = Dense(500, activation='relu',
                kernel_initializer=kernel_initializer, name='fc1')(embedding)
    fc2 = Dense(500, activation='relu',
                kernel_initializer=kernel_initializer, name='fc2')(fc1)

    r_x = Dense(1, name='r_x')(fc2)
    r_y = Dense(1, name='r_y')(fc2)
    r_z = Dense(1, name='r_z')(fc2)
    t_x = Dense(1, name='t_x')(fc2)
    t_y = Dense(1, name='t_y')(fc2)
    t_z = Dense(1, name='t_z')(fc2)

    model = Model(inputs=imgs, outputs=[r_x, r_y, r_z, t_x, t_y, t_z])
    return model


def construct_simple_model(imgs, 
                           frames_concatenated,
                           conv_layers_count=3,
                           conv_filters=64,
                           kernel_sizes=3,
                           strides=1,
                           paddings='same',
                           fc_layers_count=2,
                           fc_sizes=500,
                           activations='elu',
                           regularizations=0,
                           batch_norms=True):
    if type(conv_filters) != list:
        conv_filters = [conv_filters] * conv_layers_count
    if type(kernel_sizes) != list:
        kernel_sizes = [kernel_sizes] * conv_layers_count
    if type(strides) != list:
        strides = [strides] * conv_layers_count
    if type(paddings) != list:
        paddings = [paddings] * conv_layers_count
    if type(fc_sizes) != list:
        fc_sizes = [fc_sizes] * fc_layers_count
    if type(activations) != list:
        activations = [activations] * (conv_layers_count + fc_layers_count)
    if type(regularizations) != list:
        regularizations = [regularizations] * (conv_layers_count + fc_layers_count)
    if type(batch_norms) != list:
        batch_norms = [batch_norms] * (conv_layers_count + fc_layers_count)

    layer = frames_concatenated

    for i in range(conv_layers_count):
        layer = conv2d(
            layer,
            conv_filters[i],
            kernel_size=kernel_sizes[i],
            batchnorm=batch_norms[i],
            padding=paddings[i],
            kernel_initializer='glorot_normal',
            strides=strides[i],
            activation=activations[i],
            activity_regularizer=regularizers.l2(regularizations[i]))

    layer = Flatten(name='flatten1')(layer)

    for i in range(fc_layers_count):
        layer = Dense(
            fc_sizes[i],
            kernel_initializer='glorot_normal',
            activation=activations[i + conv_layers_count],
            activity_regularizer=regularizers.l2(regularizations[i]))(layer)

    r_x = Dense(1, name='r_x')(layer)
    r_y = Dense(1, name='r_y')(layer)
    r_z = Dense(1, name='r_z')(layer)
    t_x = Dense(1, name='t_x')(layer)
    t_y = Dense(1, name='t_y')(layer)
    t_z = Dense(1, name='t_z')(layer)

    model = Model(inputs=imgs, outputs=[r_x, r_y, r_z, t_x, t_y, t_z, ])
    return model


def construct_constant_model(imgs, 
                             frames_concatenated, 
                             rot_and_trans_array):
    mean_r_x, mean_r_y, mean_r_z, mean_t_x, mean_t_y, mean_t_z = rot_and_trans_array.mean(axis=0)

    r_x = ConstLayer(mean_r_x, name='r_x')(frames_concatenated)
    r_y = ConstLayer(mean_r_y, name='r_y')(frames_concatenated)
    r_z = ConstLayer(mean_r_z, name='r_z')(frames_concatenated)
    t_x = ConstLayer(mean_t_x, name='t_x')(frames_concatenated)
    t_y = ConstLayer(mean_t_y, name='t_y')(frames_concatenated)
    t_z = ConstLayer(mean_t_z, name='t_z')(frames_concatenated)

    model = Model(inputs=imgs, outputs=[r_x, r_y, r_z, t_x, t_y, t_z])
    return model