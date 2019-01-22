from keras import backend as K
from keras.models import Model
from keras.layers import (BatchNormalization, Conv1D, Dense, Input, 
    TimeDistributed, Activation, Bidirectional, SimpleRNN, GRU, LSTM)

def simple_rnn_model(input_dim, output_dim=29):
    """ Build a recurrent network for speech 
    """
    # Main acoustic input
    input_data = Input(name='the_input', shape=(None, input_dim))
    # Add recurrent layer
    simp_rnn = GRU(output_dim, return_sequences=True, 
                 implementation=2, name='rnn')(input_data)
    # Add softmax activation layer
    y_pred = Activation('softmax', name='softmax')(simp_rnn)
    # Specify the model
    model = Model(inputs=input_data, outputs=y_pred)
    model.output_length = lambda x: x
    print(model.summary())
    return model 

def rnn_model(input_dim, units, activation, output_dim=29):
    """ Build a recurrent network for speech 
    """
    # Main acoustic input
    input_data = Input(name='the_input', shape=(None, input_dim))
    # Add recurrent layer
    simp_rnn = GRU(units, activation=activation,
        return_sequences=True, implementation=2, name='rnn')(input_data)
    # TODO: Add batch normalization 
    bn_rnn = BatchNormalization(name='bn_rnn')(simp_rnn)
    # TODO: Add a TimeDistributed(Dense(output_dim)) layer
    time_dense = TimeDistributed(Dense(output_dim))(bn_rnn)
    # Add softmax activation layer
    y_pred = Activation('softmax', name='softmax')(time_dense)
    # Specify the model
    model = Model(inputs=input_data, outputs=y_pred)
    model.output_length = lambda x: x
    print(model.summary())
    return model



def cnn_rnn_model(input_dim, filters, kernel_size, conv_stride,
    conv_border_mode, units, output_dim=29):
    """ Build a recurrent + convolutional network for speech 
    """
    # Main acoustic input
    input_data = Input(name='the_input', shape=(None, input_dim))
    # Add convolutional layer
    conv_1d = Conv1D(filters, kernel_size, 
                     strides=conv_stride, 
                     padding=conv_border_mode,
                     activation='relu',
                     name='conv1d')(input_data)
    # Add batch normalization
    bn_cnn = BatchNormalization(name='bn_conv_1d')(conv_1d)
    # Add a recurrent layer
    simp_rnn = SimpleRNN(units, activation='relu',
        return_sequences=True, implementation=2, name='rnn')(bn_cnn)
    # TODO: Add batch normalization
    bn_rnn = BatchNormalization(name='bn_conv_1d')(conv_1d)
    # TODO: Add a TimeDistributed(Dense(output_dim)) layer
    time_dense = TimeDistributed(Dense(output_dim))(bn_rnn)
    # Add softmax activation layer
    y_pred = Activation('softmax', name='softmax')(time_dense)
    # Specify the model
    model = Model(inputs=input_data, outputs=y_pred)
    model.output_length = lambda x: cnn_output_length(
        x, kernel_size, conv_border_mode, conv_stride)
    print(model.summary())
    return model

def cnn_output_length(input_length, filter_size, border_mode, stride,
                       dilation=1):
    """ Compute the length of the output sequence after 1D convolution along
        time. Note that this function is in line with the function used in
        Convolution1D class from Keras.
    Params:
        input_length (int): Length of the input sequence.
        filter_size (int): Width of the convolution kernel.
        border_mode (str): Only support `same` or `valid`.
        stride (int): Stride size used in 1D convolution.
        dilation (int)
    """
    if input_length is None:
        return None
    assert border_mode in {'same', 'valid'}
    dilated_filter_size = filter_size + (filter_size - 1) * (dilation - 1)
    if border_mode == 'same':
        output_length = input_length
    elif border_mode == 'valid':
        output_length = input_length - dilated_filter_size + 1
    return (output_length + stride - 1) // stride

def deep_rnn_model(input_dim, units, recur_layers, output_dim=29):
    """ Build a deep recurrent network for speech 
    """
    # Main acoustic input
    input_data = Input(name='the_input', shape=(None, input_dim))
    # TODO: Add recurrent layers, each with batch normalization
    rnn_1 = GRU(units, activation='relu',
        return_sequences=True, implementation=2, name='rnn_1')(input_data)
    
    # Here, we'll create rnn layers for number asked by the user (recur_layers)
    
    rnn_input_for_next_rnn = rnn_1
    for layer in range(recur_layers - 1):
        layer_name = "rnn_" +  str(layer)
        rnn = GRU(units, activation="relu",return_sequences=True, 
                 implementation=2, name=layer_name) (rnn_input_for_next_rnn)
        
        batchnorm_name = "bn_" + str(layer)
        rnn_out = BatchNormalization(name=batchnorm_name)(rnn)
        rnn_input_for_next_rnn = rnn_out
        
        
    # TODO: Add a TimeDistributed(Dense(output_dim)) layer
    time_dense = TimeDistributed(Dense(output_dim))(rnn_out)
    # Add softmax activation layer
    y_pred = Activation('softmax', name='softmax')(time_dense)
    # Specify the model
    model = Model(inputs=input_data, outputs=y_pred)
    model.output_length = lambda x: x
    print(model.summary())
    return model

def bidirectional_rnn_model(input_dim, units, output_dim=29):
    """ Build a bidirectional recurrent network for speech
    """
    # Main acoustic input
    input_data = Input(name='the_input', shape=(None, input_dim))
    # TODO: Add bidirectional recurrent layer
    bidir_rnn = Bidirectional(GRU(units, activation="relu",return_sequences=True, 
                 implementation=2, name="bidir_rnn"))(input_data)
    # TODO: Add a TimeDistributed(Dense(output_dim)) layer
    time_dense = TimeDistributed(Dense(output_dim))(bidir_rnn)
    # Add softmax activation layer
    y_pred = Activation('softmax', name='softmax')(time_dense)
    # Specify the model
    model = Model(inputs=input_data, outputs=y_pred)
    model.output_length = lambda x: x
    print(model.summary())
    return model

from keras.layers import Dropout

def final_model(input_dim, filters=50, kernel_size=15, units=200, output_dim=29, recur_layers=2,
                activation='relu', dropout_rate=0.6):
    """ Build a deep network for speech
    """
    conv_stride=1
    conv_border_mode='same'
    # Main acoustic input
    # we add a dimension, to be able to apply convolution1d to frequencies only
    input_data = Input(name='the_input', shape=(None, input_dim))
    # applying convolution to frequency domain -> allowing to model spectral variance due to speaker change (better than fullly connected because it preserve orders of frequencies)
    
    conv_0 = Conv1D(filters, 1, strides=1, padding=conv_border_mode, activation='relu')(input_data)
    conv_0 = BatchNormalization()(conv_0)
    conv_1 = Conv1D(filters, 3, strides=1, padding=conv_border_mode, activation='relu')(conv_0)
    conv_1 = BatchNormalization()(conv_1)
    conv_2 = Conv1D(filters, 1, strides=1, padding=conv_border_mode, activation='relu')(conv_1)
    conv_2 = BatchNormalization()(conv_2)
    
    rnn_input = conv_2
    #units = filters//4
    #rnn_input = input_data
    for num in range(recur_layers):
        rnn_name = 'rnn_{}'.format(num)
        #  TODO: en ajoutant un dropout en input
        rnn_input = Dropout(dropout_rate)(rnn_input)
        # TODO: tester avec LSTM
        # TODO: tester avec activation ='elu' ou tanh?
        # TODO: tester avec un clipped
        simp_rnn = LSTM(units, activation='tanh', return_sequences=True, implementation=2, name=rnn_name)
        rnn = Bidirectional(simp_rnn)(rnn_input)
        output = BatchNormalization()(rnn)
        # we set rnn_input to new output, thus allowing to chain rnn
        rnn_input = output

    # and finally we add a TimeDistributed
    time_dense = TimeDistributed(Dense(output_dim))(rnn_input)

    # TODO: Add softmax activation layer
    y_pred = Activation('softmax', name='softmax')(time_dense)
    # Specify the model
    model = Model(inputs=input_data, outputs=y_pred)
    # TODO: Specify model.output_length
    model.output_length = lambda x: x
    #model.output_length = lambda x: cnn_output_length( x, kernel_size, conv_border_mode, conv_stride)
    print(model.summary())
    return model