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
from platforms.Parameter import ReferenceParameter
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
        self.parameters=[]
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
#            if command == "add_parameter":
#                self.parameter_names.append(line_split[1])
            if command == "add_parameter":
                # New parameter type: added size, add error message if no parameter set
                [parameter_name, parameter_value] = line_split[1].split("=")
                # Should implement a nicer way than to abuse the Parameter subclasses here
                self.parameters.append(ReferenceParameter(parameter_name, parameter_value))
                self.parameter_names.append(parameter_name)
                print self.parameters
 
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

        fraction = numpy.exp(-numpy.sum(numpy.log(p) * p))/float(len(weights[:,1]))

        if self.log_level >= 2:
            print "fraction=", fraction

        return fraction>0.5



    def calculate_first_derivative_averages(self, evaluator_path, parameters, ensemble, weights=None):
        '''Calculate average of first derivatives for all parameters'''
        
        if weights == None:
            weights = ensemble.scalar_to_ensemble_array(1.0)

        derivative_averages = []
        for parameter in parameters:
            derivative_values = ensemble.get_parameter_derivative_values(evaluator_path, parameter)

            derivative_values, weights = self.truncate_to_common_iteration_range(derivative_values, 
                                                                                 weights)
            derivative_values_avg = numpy.average(derivative_values[:,1], weights=weights[:,1])
            derivative_averages.append(derivative_values_avg)

        return numpy.array(derivative_averages)



    def calculate_S_rel_derivative(self, parameters, ensemble_collection,
                                   model_ensemble, target_ensemble):
        '''Calculate derivative of the relative entropy for all parameters. If the reweighting
flag is set, the calculations will be done according to Ferrenberg-Swendsen'''

        # Evaluators
        model_evaluator_path = ensemble_collection.evaluators[model_ensemble.simulation_type]
        target_evaluator_path = ensemble_collection.evaluators[target_ensemble.simulation_type]

        # Attempt to get beta from ensemble (model ensemble)
        beta = model_ensemble.get_beta()

        ### <dU_M/dlambda>_T ###

        # Even when we are not doing a reweighted calculation of the derivative, 
        # the ensemble itself might still need to be reweighted (for instance
        # when working with generalized ensembles.
        reweight_weights = target_ensemble.get_reweight_weights()
            
        target_derivatives_avg =  self.calculate_first_derivative_averages(target_evaluator_path, 
                                                                           parameters,  
                                                                           target_ensemble,
                                                                           weights=reweight_weights)

        ### <dU_M/dlambda>_M ###

        # Even when we are not doing a reweighted calculation of the derivative, 
        # the ensemble itself might still need to be reweighted (for instance
        # when working with generalized ensembles.
        reweight_weights = model_ensemble.get_reweight_weights()
        

        # Evaluate the model energies and weights with the new parameters
        model_energies_in_model_ensemble = model_ensemble.calculate_energies(parameters, model_evaluator_path)
        # The weights occording to the original model ensemble
        model_energies_reference = model_ensemble.get_energies()

        # Truncate so that all vectors agree on indices
        (model_energies_reference, 
         reweight_weights,
         model_energies_in_model_ensemble) = self.truncate_to_common_iteration_range(model_energies_reference,
                                                                                     reweight_weights,
                                                                                     model_energies_in_model_ensemble)
         
         
        # The reweighting weights (the negative sign is because we use log-weights 
        # instead of energies: lnw = -betaE)
        w = copy.copy(model_energies_reference)
        w[:,1] = numpy.exp(model_ensemble.get_beta()*(model_energies_reference[:,1] - model_energies_in_model_ensemble[:,1]))

        if not self.reweighting_support(w):
            raise ReweightingException
        
        # The two types of reweighting can be combined. In order to avoid
         # problems with the normalization constant, the original weights must be
         # normalized first
        reweight_weights[:,1]/float(sum(reweight_weights[:,1]))
        reweight_weights[:,1] *= w[:,1]
                    
        # Average of derivatives over model ensemble
        model_derivatives_avg = self.calculate_first_derivative_averages(model_evaluator_path, 
                                                                         parameters, 
                                                                         model_ensemble,
                                                                         weights=reweight_weights)

        S_rel_derivative = beta*(target_derivatives_avg - model_derivatives_avg)

        if self.log_level >= 2:
            print "target_beta_derivatives_avg=",target_derivatives_avg,"\tmodel_beta_derivatives_avg=",model_derivatives_avg

        return S_rel_derivative



    @abstractmethod
    def optimize(self, ensemble_collection):
        '''Main method. This method must be overrided by derived classes'''
        pass    




