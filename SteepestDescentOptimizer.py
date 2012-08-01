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

from Optimizer import Optimizer, ReweightingException

class SteepestDescentOptimizer(Optimizer):
    '''Steepest descent optimization class. Works on an EnsembleCollection object'''

    def __init__(self, log_level=0):
        '''Constructor'''
        Optimizer.__init__(self, log_level)


    def optimize(self, ensemble_collection):
        '''Optimizes parameters given an ensemble collection'''

        model_selection_index = -1

        beta_target_derivatives_avg = {}

        model_ln_weights_reference = {}


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
        print "Before deriv calc. ",ensemble_collection.ensembles.keys()
            
        # In the first iteration, we evaluate the averages over the ensembles
        for name in ensemble_collection.ensembles.keys():


            target_ensemble = ensemble_collection.ensembles[name]["target"]
            model_ensemble = active_models.get(name)

            # Read parameters from ensemble directory
            parameters = model_ensemble.read_parameter_values(self.parameter_names)

            print "trying to calculate first deriv"
            S_rel_derivative = self.calculate_S_rel_derivative2(parameters, 
                                                               ensemble_collection,
                                                               model_ensemble,
                                                               target_ensemble,
                                                               reweighting=False)

            
            if self.log_level >= 2:
                print "S_rel_derivative: " , S_rel_derivative, " at parameter: ", parameters


            # print "Starting to reweight"
            # for i in range(1,15):
            #     for i,parameter in enumerate(parameters):
            #         parameter.set_value(parameter.get_value() + 0.1)

            #     for name in ensemble_collection.ensembles.keys():

            #         target_ensemble = ensemble_collection.ensembles[name]["target"]
            #         model_ensemble = active_models[name]

            #         try:
            #             S_rel_derivative = self.calculate_S_rel_derivative2(parameters, 
            #                                                            ensemble_collection,
            #                                                            model_ensemble,
            #                                                            target_ensemble,
            #                                                            reweighting=True)
            #         except ReweightingException:
            #             return

            #         if self.log_level >= 2:
            #             print "S_rel_derivative_reweighted: " , S_rel_derivative, " at parameter: ", parameters
                

            parameters_reference = copy.copy(parameters)
            for i,parameter in enumerate(parameters):
                parameter.set_value(parameter.get_value() - 0.25*S_rel_derivative[i])

            if self.log_level >= 2:
                print "parameters: ", parameters


        # Continue as long as we have enough support for reweighting
        while True:

            # In the remaining iterations, we use reweighting to estimate the derivatives
            for name in ensemble_collection.ensembles.keys():

                target_ensemble = ensemble_collection.ensembles[name]["target"]
                model_ensemble = active_models[name]

                try:
                    S_rel_derivative = self.calculate_S_rel_derivative2(parameters, 
                                                                       ensemble_collection,
                                                                       model_ensemble,
                                                                       target_ensemble,
                                                                       reweighting=True)
                except ReweightingException:
                    return

                if self.log_level >= 2:
                    print "S_rel_derivative_reweighted: " , S_rel_derivative

                for i,parameter in enumerate(parameters):
                    parameter.set_value(parameter.get_value() - 0.25*S_rel_derivative[i])

                if self.log_level >= 2:
                    print "parameters: ", parameters
