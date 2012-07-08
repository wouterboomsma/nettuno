# Optimizer.py --- Base class for all optimizer algorithms
# Copyright (C) 2012 Sandro Bottaro, Christian Holzgraefe, Wouter Boomsma
#
# This file is part of Nettuno
#
# Nettuno is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Nettuno is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Nettuno.  If not, see <http://www.gnu.org/licenses/>.

from abc import ABCMeta, abstractmethod
import numpy
import copy
import sys

class ReweightingException(Exception):
    '''Exception raised when there is no support for reweighting'''
    pass


class Optimizer:
    '''Optimization Base class'''

    # To allow specification of abstract base classes
    __metaclass__ = ABCMeta


    def __init__(self, log_level):
        '''Constructor'''
        self.parameter_names = []
        self.beta = None
        self.log_level = log_level


    def read_init_file(self, init_filename):
        '''Initialize ensembles from configuration file'''        
        
        self.init_filename = init_filename

        init_file = open(init_filename)
        lines = init_file.readlines()

        # Read parameter entries 
        self.parameter_names = []
        for line in lines:
            line_split = line.strip().split(" ")            

            if len(line_split) == 0 or line[0] == "#":
                continue

            command = line_split[0]
            if command == "add_parameter":
                self.parameter_names.append(line_split[1])

        init_file.close()        


    def __repr__(self):
        '''String representation'''
        
        output = ""

        for parameter in self.parameter_names:
            output += "add_parameter %s \n" % parameter

        return output


    def truncate_to_common_iteration_range(self, *data_vectors):
        '''Given a vector of data vectors, truncate them to 
           ensure that they cover the same range. All data vectors
           are expected to contain two columns, where the first
           contains the iteration indices and the second contains
           the data'''
        
        range_start = -numpy.inf
        range_end = numpy.inf
        for data_vector in data_vectors:
            range_start = max(range_start, min(data_vector[:,0]))
            range_end = min(range_end, max(data_vector[:,0]))

        # Detect maximum interval
        maximum_interval = 1
        minimum_interval = sys.maxint
        index_intervals = [1]*len(data_vectors)
        for data_vector in data_vectors:
            interval = data_vector[1,0] - data_vector[0,0]
            maximum_interval = max(maximum_interval, interval)
        for i,data_vector in enumerate(data_vectors):
            interval = data_vector[1,0] - data_vector[0,0]
            index_intervals[i] = maximum_interval/interval
        

        iteration_range = [range_start, range_end]

        # print iteration_range

        # Check that vectors reduce to same size (i.e., stride is the same)
        length = None
        truncated_data_vectors = []
        for i, data_vector in enumerate(data_vectors):
            data_vector_using_maximum_interval = data_vector[::index_intervals[i]]
            truncated_data_vector = data_vector_using_maximum_interval[numpy.logical_and.reduce([data_vector_using_maximum_interval[:,0] >= iteration_range[0], 
                                                                                                 data_vector_using_maximum_interval[:,0] <= iteration_range[1]])]

            truncated_data_vectors.append(truncated_data_vector)

            if length == None:
                length = truncated_data_vector.shape[0]
            else:                    
                if length != truncated_data_vector.shape[0]:
                    print "Error: input sequences have different iteration interval. Aborting."
                    assert(False)

        return truncated_data_vectors


    def reweighting_support(self, weights):
        '''Check whether there is support enough for reweighting'''

        weights_sum = sum(weights[:,1])
        p = weights[:,1]/float(weights_sum)

        fraction = numpy.exp(-numpy.average(numpy.log(p), weights=p))/float(len(weights[:,1]))

        if self.log_level >= 2:
            print "fraction=", fraction

        return fraction>0.5



    def calculate_first_derivative_averages(self, evaluator_path, parameters, ensemble, weights):
        '''Calculate average of first derivatives for all parameters'''
        
        derivative_averages = []
        for parameter in parameters:
            derivative_values = ensemble.get_parameter_derivative_values(evaluator_path, parameter)

            derivative_values, weights = self.truncate_to_common_iteration_range(derivative_values, 
                                                                                 weights)

            derivative_values_avg = numpy.average(derivative_values[:,1], weights=weights[:,1])
            derivative_averages.append(derivative_values_avg)

        return numpy.array(derivative_averages)



    def calculate_S_rel_derivative(self, parameters, ensemble_collection,
                                   model_ensemble, target_ensemble,
                                   reweighting = False):
        '''Calculate derivative of the relative entropy for all parameters. If the reweighting
flag is set, the calculations will be done according to Ferrenberg-Swendsen'''

        # Evaluators
        model_evaluator_path = ensemble_collection.evaluators[model_ensemble.simulation_type]
        target_evaluator_path = ensemble_collection.evaluators[target_ensemble.simulation_type]


        ### beta<dU_M/dlambda>_T ###

        # Weights for calculating average
        target_ln_weights_in_target_ensemble = target_ensemble.get_ln_weights()

        # Attempt to get beta from ensemble
        beta = model_ensemble.get_beta()
        if beta == None:

            # Evaluate the model energies over the target ensemble
            model_energies_in_target_ensemble = target_ensemble.calculate_energies(parameters, model_evaluator_path)

            # Evaluate the energies from the target ensemble using the weights of the model ensemble
            model_ln_weights_in_target_ensemble = model_ensemble.get_ln_weights(model_energies_in_target_ensemble)

            # Truncate so that all vectors agree on indices
            (model_energies_in_target_ensemble, 
             model_ln_weights_in_target_ensemble,
             target_ln_weights_in_target_ensemble) = self.truncate_to_common_iteration_range(model_energies_in_target_ensemble,
                                                                                             model_ln_weights_in_target_ensemble,
                                                                                             target_ln_weights_in_target_ensemble)

            # If beta is not available, it means we are dealing with a generalized ensemble. 
            # In this case, we calculate beta as -ln(weight)/energy 
            beta_values_in_target_ensemble = copy.copy(model_ln_weights_in_target_ensemble)
            beta_values_in_target_ensemble[:,1] /= model_energies_in_target_ensemble[:,1]
            
            beta = beta_values_in_target_ensemble[:,1]


        # Since beta is not necessarily constant, we include
        # it as weights in the average
        target_weights_in_target_ensemble = copy.copy(target_ln_weights_in_target_ensemble)
        target_weights_in_target_ensemble[:,1] = numpy.exp(target_ln_weights_in_target_ensemble[:,1])
        target_weights_in_target_ensemble[:,1] *= beta

        # Average of derivatives over target ensemble
        target_beta_derivatives_avg = self.calculate_first_derivative_averages(target_evaluator_path, 
                                                                               parameters, 
                                                                               target_ensemble, 
                                                                               target_weights_in_target_ensemble)

        ### beta<dU_M/dlambda>_M ###

        model_beta_derivatives_avg = None
        model_ln_weights_in_model_ensemble = None
        model_energies_in_model_ensemble = None
        model_weights_in_model_ensemble = None

        if not reweighting:

            # Model energies and weights are stored in the ensemble
            model_energies_in_model_ensemble = model_ensemble.get_energies()
            model_ln_weights_in_model_ensemble = model_ensemble.get_ln_weights()

            # Weights for calculating average
            model_weights_in_model_ensemble = copy.copy(model_ln_weights_in_model_ensemble)
            model_weights_in_model_ensemble[:,1] = numpy.exp(model_ln_weights_in_model_ensemble[:,1])

        else: 

            # Evaluate the model energies and weights with the new parameters
            model_energies_in_model_ensemble = model_ensemble.calculate_energies(parameters, model_evaluator_path)
            model_ln_weights_in_model_ensemble = model_ensemble.get_ln_weights(model_energies_in_model_ensemble)

            # The weights occording to the original model ensemble
            model_ln_weights_reference = model_ensemble.get_ln_weights()   # TODO: Cache this value

            # Truncate so that all vectors agree on indices
            (model_ln_weights_reference, 
             model_ln_weights_in_model_ensemble) = self.truncate_to_common_iteration_range(model_ln_weights_reference,
                                                                                           model_ln_weights_in_model_ensemble)

            # The reweighting weights (the negative sign is because we use log-weights 
            # instead of energies: lnw = -betaE)
            w = copy.copy(model_ln_weights_reference)
            w[:,1] = numpy.exp(-(model_ln_weights_reference[:,1] - model_ln_weights_in_model_ensemble[:,1]))

            if not self.reweighting_support(w):
                raise ReweightingException

            # Averages are evaluated over the original model ensemble
            model_weights_in_model_ensemble = copy.copy(model_ln_weights_reference)
            model_weights_in_model_ensemble[:,1] = numpy.exp(model_ln_weights_reference[:,1])

            # reweighting normalization constant
            w_avg = numpy.average(w[:,1], weights=model_weights_in_model_ensemble[:,1])
            normalization_constant = w_avg

            if self.log_level >= 2:
                print "w_avg=",w_avg            

            # To calculate the average over the derivate*w, we
            # modify the weights to incorporate w
            model_weights_in_model_ensemble[:,1] *= w[:,1]


        # Attempt to get beta from ensemble
        beta = model_ensemble.get_beta()
        normalization_constant = 1.0
        if beta == None:

            # If beta is not available, it means we are dealing with a generalized ensemble. 
            # In this case, we calculate beta as -ln(weight)/energy 
            beta_values_in_model_ensemble = copy.copy(model_ln_weights_in_model_ensemble)
            beta_values_in_model_ensemble[:,1] /= model_energies_in_model_ensemble[:,1]

            beta = beta_values_in_model_ensemble[:,1]


        # Since beta is not necessarily constant, we include
        # it as weights in the average
        model_weights_in_model_ensemble[:,1] *= beta

        # Average of derivatives over model ensemble
        model_beta_derivatives_avg = self.calculate_first_derivative_averages(model_evaluator_path, 
                                                                              parameters, 
                                                                              model_ensemble,
                                                                              model_weights_in_model_ensemble)/normalization_constant

        S_rel_derivative = target_beta_derivatives_avg - model_beta_derivatives_avg

        if self.log_level >= 2:
            print "target_beta_derivatives_avg=",target_beta_derivatives_avg,"\tmodel_beta_derivatives_avg=",model_beta_derivatives_avg

        return S_rel_derivative



    @abstractmethod
    def optimize(self, ensemble_collection):
        '''Main method. This method must be overrided by derived classes'''
        pass    




