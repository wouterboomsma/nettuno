# SteepestDescentOptimizer.py --- Steepest descent optimization implementation
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

import copy
import numpy
from Optimizer import Optimizer, ReweightingException

class SteepestDescentOptimizer(Optimizer):
    '''Steepest descent optimization class. Works on an EnsembleCollection object'''

    def __init__(self, log_level=0):
        '''Constructor'''
        Optimizer.__init__(self, log_level)

    def outputToFile(self, filename, vals):
        f = open(filename, 'w')
        for i in vals:
            for j in i:
                print str(j[0]) + " " + str(j[1])
                f.write(str(j[0]) + " " + str(j[1]) + " ")
            f.write("\n")
        f.close()
        

    def optimize(self, ensemble_collection):
        '''Optimizes parameters given an ensemble collection'''

        model_selection_index = -1

        beta_target_derivatives_avg = {}

        model_ln_weights_reference = {}

        results=[]

        # Remove targets with no models
        for name in ensemble_collection.ensembles.keys():
            if len(ensemble_collection.ensembles[name]["model"]) == 0:
                del ensemble_collection.ensembles[name]

        active_models = {}
        for name in ensemble_collection.ensembles.keys():
            model_ensembles = ensemble_collection.ensembles[name]["model"]
            if len(model_ensembles) > 0:
                active_models[name] = model_ensembles[-1]


        parameters_reference = None

        while True:

            parameter_delta = numpy.zeros(len(self.parameter_names))
        
        # In the first iteration, we evaluate the averages over the ensembles
            for name in ensemble_collection.ensembles.keys():
                print "current name: ", name
                target_ensemble = ensemble_collection.ensembles[name]["target"]
                model_ensemble = active_models.get(name)

            # Read parameters from ensemble directory
#            parameters = model_ensemble.read_parameter_values(self.parameter_names)
                try:
                    S_rel_derivative = self.calculate_S_rel_derivative(self.parameters, 
                                                                   ensemble_collection,
                                                                       model_ensemble,
                                                                       target_ensemble)
            
                except ReweightingException:
                    self.outputToFile("nettuno-excep.out", results)
                    return
            
                if self.log_level >= 2:
                    print "S_rel_derivative: " , S_rel_derivative, " at parameter: ", self.parameters
                for i,parameter in enumerate(self.parameters):
                    parameter_delta[i] += S_rel_derivative[i]


            parameter_values = [i.get_value() for i in self.parameters]
                    
            # Update Parameters
            parameter_delta = parameter_delta / len(ensemble_collection.ensembles.keys())
            
            # Stop procedure if parameter change gets too small, promote to parameter in settings file?
            parameter_delta_sum = reduce(lambda x,y: abs(x) + abs(y), parameter_delta)

            results.append(zip(parameter_values, parameter_delta))

            if(abs(parameter_delta_sum) < 0.00001):                                       
                self.outputToFile("nettuno.out", results)
                break

            for i,parameter in enumerate(self.parameters):
                parameter.set_value(float(parameter.get_value()) - 0.25*parameter_delta[i])
            if self.log_level >= 2:
                print "parameters: ", self.parameters

