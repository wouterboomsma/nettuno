# nettuno_optimizer.py --- Main program
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

import optparse
import utils
import sys

from EnsembleCollection import EnsembleCollection
from SteepestDescentOptimizer import SteepestDescentOptimizer
from platforms.PlatformSelector import PlatformSelector
from platforms.Ensemble import Ensemble


class Nettuno:
    '''Main Nettuno class containing EnsembleCollection and Optimizer objects'''

    def __init__(self, optimizer, init_filename=".nettuno", log_level=0):
        self.init_filename = init_filename
        self.ensemble_collection = EnsembleCollection(log_level)
        # self.optimizer = Optimizer()
        if optimizer == "steepest_descent":
            self.optimizer = SteepestDescentOptimizer(log_level)
        else:
            print "Unknown optimization algorithm: %s. Aborting." % optimizer
            sys.exit(1)
        self.read_init_file()

    def read_init_file(self):
        '''Reads configuration file'''
        self.ensemble_collection.read_init_file(self.init_filename)
        self.optimizer.read_init_file(self.init_filename)
    
    def output_init_file(self, init_file_output):
        '''Writes configuration file'''
        if init_file_output == self.init_filename:
            backup_name = self.init_filename + "_"+ datetime.datetime.today().isoformat("-")
            shutil.copyfile(self.init_filename, backup_name)

        if init_file_output == "stdout":
            print "### Nettuno settings output ###\n"
            print repr(self),
            print "###############################"
        else :
            init_file = open(self.init_filename, "w")
            init_file.write(repr(self))
            init_file.close()

    def get_ensemble_collection(self):
        '''Retrieve EnsembleCollection object'''
        return self.ensemble_collection

    def get_optimizer(self):
        '''Retrieve Optimizer object'''
        return self.optimizer

    def optimize(self):
        '''Start optimization procedure'''
        if len(self.ensemble_collection) > 0:
            self.optimizer.optimize(self.ensemble_collection)

    def __repr__(self):
        return repr(self.optimizer) + "\n" + repr(self.ensemble_collection)



if __name__ == "__main__":

    usage = '''
Nettuno - Relative Entropy Optimizer

Strategy:
1. Generate target ensemble (external).
2. Register target ensemble (using --add-target-ensemble option).
3. Generate new model ensemble (external).
4. Register new model ensemble (using --add-model-ensemble option).
5. Optimize (using --optimize option).
6. Repeat 3-6 with the parameter values found by 5.

'''

    # Output for general platform options
    ensemble_option_help = "\nGeneral platform options:"
    ensemble_option_help += str(utils.SubOptions({'id':'ID (connects target and model ensembles)',
                                                  'directory': 'Directory containing simulation data',
                                                  'beta': 'Inverse temperature at which analysis should be done',
                                                  'iteration_range': 'Range used in analysis:\n\t[start_index, end_index, interval]'}))

    # Platform specific options are retrieved from classes
    ensemble_option_help += "\nPlatform specific options:\n"
    for cls in Ensemble.__subclasses__():
        ensemble_option_help += "\n"+cls.simulation_type + "\t" + cls.get_option_help()


    # Option definitions
    parser = optparse.OptionParser(usage=usage, formatter=utils.HelpFormatterInnerOptions(),
                                   option_class=utils.CallbackHasMetaVarOption)
    parser.add_option("--add_target_ensemble", dest="new_target_ensembles", action="callback", default=[],
                      callback=utils.vararg_callback,
                      help="Add new target ensemble entry." + ensemble_option_help)
    parser.add_option("--add_model_ensemble", dest="new_model_ensembles", action="callback", default=[], type="string", nargs=0,
                      callback=utils.vararg_callback,
                      metavar = "simulation_type:SIMULATION_TYPE id:ID directory:DIRECTORY [platform-specific-options]",
                      help="Add new model ensemble entry." + ensemble_option_help)
    parser.add_option("--init_file", dest="init_file", default=".nettuno",
                      help="File in which to read optimization settings.")
    parser.add_option("--init_file_output", dest="init_file_output", default="stdout",
                      help="File/stream in which to write optimization settings.")
    parser.add_option("--optimizer", dest="optimizer", type='choice', choices=['steepest_descent'], 
                      default="steepest_descent",
                      help="Which optimization algorithm to use")
    parser.add_option("--log_level", dest="log_level", default="1",
                      help="How much information to output to screen")

    (options, args) = parser.parse_args()

    # Allocate main object
    nettuno = Nettuno(options.optimizer, options.init_file, int(options.log_level))

    # Add ensembles specified from command line
    for target_ensemble_tuple in options.new_target_ensembles:
        option_dict = EnsembleCollection.option_list_to_ensemble_option_dict(target_ensemble_tuple)
        nettuno.get_ensemble_collection().add_model_ensemble(**option_dict)

    for model_ensemble_tuple in options.new_model_ensembles:
        option_dict = EnsembleCollection.option_list_to_ensemble_option_dict(model_ensemble_tuple)
        nettuno.get_ensemble_collection().add_model_ensemble(**option_dict)

    # Optionally write out settings to file or stdout
    if options.init_file_output != "stdout" or options.log_level >=1:
        nettuno.output_init_file(options.init_file_output)


    # Call optimization
    nettuno.optimize()
