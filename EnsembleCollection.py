# EnsembleCollection.py --- A container of ensembles
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

from platforms.PlatformSelector import PlatformSelector

class EnsembleCollection:
    '''A container of model-target ensemble pairs'''

    def __init__(self, log_level=0):
        '''Constructor.'''

        self.ensembles = {}
        self.evaluators = {}
        self.log_level = log_level


    def read_init_file(self, init_filename):
        '''Initialize ensembles from configuration file'''

        init_file = open(init_filename)
        lines = init_file.readlines()
        # Read ensemble entries
        for line in lines:
            
            line_split = line.strip().split()

            if len(line_split) == 0 or line[0] == "#":
                continue
            
            command = line_split[0]

            if command == "add_target_ensemble":
                argument_dict = self.option_list_to_ensemble_option_dict(line_split[1:])
                self.add_target_ensemble(**argument_dict)
            elif command == "add_model_ensemble":
                argument_dict = self.option_list_to_ensemble_option_dict(line_split[1:])
                self.add_model_ensemble(**argument_dict)
            elif command == "set_evaluator":
                self.set_evaluator(*line_split[1:])

        init_file.close()        

        
    def add_target_ensemble(self, id, directory, simulation_type, reweight_beta=None, iteration_range=None,
                            **platform_specific_args):
        '''Add a target ensemble. The id, directory, and iteration_range parameters
           are common to all ensemble types. The platform_specific_args argument is
           a dictionary containing options for the specific platform'''

        if not self.ensembles.has_key(id):
            self.ensembles[id] = {}

        if self.ensembles[id].has_key("target"):
            print "ERROR: Duplicate target ensemble name: ", id
            sys.exit(1)
    
        self.ensembles[id]["target"] = PlatformSelector.get_ensemble(simulation_type, directory, reweight_beta, iteration_range,
                                                                     self.log_level,
                                                                     platform_specific_args)
        self.ensembles[id]["model"] = []


    def add_model_ensemble(self, id, directory, simulation_type, reweight_beta=None, iteration_range=None, 
                           **platform_specific_args):
        '''Add a model ensemble. The id, directory, and iteration_range parameters
           are common to all ensemble types. The platform_specific_args argument is
           a dictionary containing options for the specific platform'''

        if not self.ensembles.has_key(id):
            self.ensembles[id] = {}

        if not self.ensembles[id].has_key("model"):
            self.ensembles[id]["model"] = []

        self.ensembles[id]["model"].append({})
        self.ensembles[id]["model"][-1] = PlatformSelector.get_ensemble(simulation_type, directory, reweight_beta, iteration_range,
                                                                        self.log_level,
                                                                        platform_specific_args)

            

    def set_evaluator(self, path, simulation_type):
        '''Set the path to an evaluator program for the given simulation_type'''
        self.evaluators[simulation_type] = path
        

    def __repr__(self):
        '''String representation'''

        output = ""

        for simulation_type in self.evaluators:
            output += "set_evaluator %s %s\n" % (self.evaluators[simulation_type], simulation_type)
        output += "\n";

        for id in self.ensembles.keys():            
            if not self.ensembles[id].has_key("target"):
                print "ERROR: Missing target ensemble entry for", id
                sys.exit(1)

            target = self.ensembles[id]["target"]

            output += "add_target_ensemble\t"
            for item in target.get_settings().items():
                if item[1] != None:
                    output += "%s:%s\t" % item
            output += "\n"

            for model in self.ensembles[id]["model"]:
                output += "add_model_ensemble\t"
                for item in model.get_settings().items():
                    if item[1] != None:
                        output += "%s:%s\t" % item
                output += "\n"

            output += "\n"
        return output

    def __len__(self):
        return len(self.ensembles.keys())


    @classmethod
    def option_list_to_ensemble_option_dict(self, option_list):
        '''Defines how a list of options from the command line or configuration
           file is translated into an option dictionary'''
        option_dict = dict([i.split(":",1) for i in option_list])
        return option_dict

