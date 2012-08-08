# ProfasiEnsemble.py --- Ensemble implementation for the Profasi platform
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


from numpy import genfromtxt, log, exp
import optparse
import tempfile
import os
import shutil
import numpy
import copy
import sys
import subprocess

from ..Ensemble import Ensemble
from ProfasiParameters import ProfasiParameter
from utils import SubOptions


class ProfasiEnsemble(Ensemble):
    '''Ensemble implementation for the Profasi platform'''

    # Couple parameter class to ensemble class
    # Used by base class to automatically create relevant Parameter objects
    ParameterClass = ProfasiParameter

    # Class variable specifying the name of the platform
    simulation_type = "PROFASI"


    def __init__(self, log_level=0):
        '''Constructor.'''
        Ensemble.__init__(self, log_level)


    def set_settings(self, directory, reweight_beta, iteration_range,
                     simulation_index=0, temperature_index=0):        
        '''Initialize with object with current settings, and saves them
for future retrieval. This method is separated from the constructor to 
make it clear that these settings should all be available for retrievable 
by get_settings(). It is overwritten from the base class to specify exactly
which settings are expected by this platform.'''        
        Ensemble.set_settings(self, **dict((key,value) for key, value in locals().iteritems() if key != "self"))


    @classmethod
    def get_option_help(self):
        '''Output for ensemble options used by command line parser.'''
        return str(SubOptions({'simulation_index':'Which simulation directory (n?) \n\tto use',
                               'temperature_index':'The index of the temperature \n\tto use for the analysis'}))


    
    def read_parameter_values(self, requested_parameter_list):
        '''Read parameters from ensemble.'''
        return self.get_parameters(requested_parameter_list)


    def write_parameter_values(self, requested_parameter_list):
        '''Write current parameter values in platform specific syntax.'''
        pass
    

    def get_energies(self, directory=None):
        '''Retrieve energies for all samples in the ensemble. Note that this
method does conduct any new evaluations but simply retrieves values.'''

        # If no directory is specified, use the one associated with this ensemble
        if not directory:
            directory = os.path.join(self.directory, "n%s" % self.simulation_index)

        # Read in rt file
        rt_filename = os.path.join(directory, "rt")
        rt_matrix = genfromtxt(rt_filename)

        energies = rt_matrix[:,0:3:2]

        # Optionally limit energies to a specified range
        limits = copy.copy(self.iteration_range)
        if limits[0] == None:
            limits[0] = 0
        if limits[1] == None:
            limits[1] = max(energies[:,0])
        energies = energies[numpy.logical_and.reduce([energies[:,0] >= limits[0], energies[:,0] <= limits[1]])]

        return energies

        
    def calculate_energies(self, parameters, evaluator_path):
        '''Calculate energies given a set of parameter values and the path
to an evaluator program'''
            
        # Read in original settings file
        settings_filename = self.directory + "/settings.cnf" 
        settings_file = open(settings_filename)

        settings_file_lines = settings_file.readlines()
        settings_file_lines_dict = {}
        for i,line in enumerate(settings_file_lines):

            split_line = line.strip().split()

            if len(split_line) == 0:
                continue

            settings_file_lines_dict[split_line[0]] = i

        # Construct new settings file
        parameter_dict = {}
        for parameter in parameters:
            if not parameter_dict.has_key(parameter.get_term_name()):
                parameter_dict[parameter.get_term_name_settings_file()] = []
            parameter_dict[parameter.get_term_name_settings_file()].append(parameter)

        for key in parameter_dict.keys():
            value = ""
            for parameter in parameter_dict[key]:
                value += parameter.get_partial_name() + ":" + repr(parameter.get_value()) + " "
            value += "\n"

            line_number = settings_file_lines_dict[key]
            settings_file_lines[line_number] = key + " " + value

        settings_file_content = "".join(settings_file_lines)

        energies = self.run_evaluator(evaluator_path, settings_file_content)

        assert(len(energies) != 0)

        return energies


    def run_evaluator(self, evaluator_path, settings_file_content):
        '''Wrapper code to run the evaluator given the specified settings.'''

        # Prefix for temporary directory
        tmp_dir = tempfile.mkdtemp(prefix="nettuno_")

        if self.log_level >= 5:
            print "Using temporary directory: ",tmp_dir

        # Write settings to file in temporary directory
        settings_filename = tmp_dir + "/settings.cnf"
        settings_file = open(settings_filename, 'w')
        settings_file.write(settings_file_content)
        settings_file.close()

        # If specified, limit simulation to range
        start_str = ""
        if self.iteration_range[0] != None:
            start_str = "--start %s" % self.iteration_range[0]
        end_str = ""
        if self.iteration_range[1] != None:
            end_str = "--end %s" % self.iteration_range[1]
        interval_str = ""
        if self.iteration_range[1] != 1:
            interval_str = "--every %s" % self.iteration_range[2]

        command_line = "cd %s; %s %s %s %s --get_rt %s/n%s/traj &> out.txt" % (tmp_dir, os.path.abspath(evaluator_path), 
                                                                               start_str, end_str, interval_str,
                                                                               os.path.abspath(self.directory), 
                                                                               self.simulation_index)
        if self.log_level >= 5:
            print "Command line: ", command_line

        if self.log_level >=1:
            print "Running evaluator...",
            sys.stdout.flush()

        # Call evaluator
        subprocess.call(command_line, shell=True)

        if self.log_level >=1:
            print "done"

        values = self.get_energies(tmp_dir)

        # Remove temporary directory
        shutil.rmtree(tmp_dir)
        
        return values


    def get_reweight_weights(self, energies=None):
        '''Retrieve the weights necessary when calculating Boltzmann averages
over the ensemble. This is 1.0 when evaluating an ensemble at the same temperature
as it was simulated, but can be used both to reweight constant temperature simulations
to a different temperature, or for generalized ensembles.'''

        if energies == None:
            energies = self.get_energies()

        # Transfer the index column
        weights = copy.copy(energies)
        
        # Check for muninn log file (suggesting a generalized ensemble simulation)
        muninn_filename = self.directory + "/muninn.txt" 
        if os.path.exists(muninn_filename):
        
            from external.muninn_scripts.details.CanonicalAverager import CanonicalAverager
            ca = CanonicalAverager(muninn_filename, -1)
            
            weights[:,1] = ca.calc_weights(energies[:,1], float(self.reweight_beta))

        else:

            if (not self.reweight_beta or (self.reweight_beta - self.get_beta()) < 0.001):
                weights[:,1] = 1.0
            else:
                print "Attempting to reweight an ensemble conducted at beta=%s to the inverse temperature beta=%s. Reweighting contant temperature ensembles to a different temperature is not yet implemented.\n" % (self.get_beta(), self.reweight_beta)
                sys.exit(1);

        return weights


    def get_parameter_derivative_values(self, evaluator_path, parameter):
        '''Calculate the derivatives for a particular parameter.'''

        print "trying to evaluate derivative"
        settings_file_content = parameter.get_derivative_settings()
        print "with settings file: ", settings_file_content
        values = self.run_evaluator(evaluator_path, settings_file_content)
        return values


    def get_intrinsic_beta(self):
        '''Return the beta=1/(k_bT) at which the simulation was conducted, or
None if it was conducted in a generalized ensemble. '''

        # Check if muninn output file is available
        # if so, we return None to indicate that the simulation
        # cannot be said to have a corresponding beta
        muninn_filename = self.directory + "/muninn.txt" 
        if os.path.exists(muninn_filename):

            # When doing a generalize ensemble, a reweighting temperature 
            # option must be specified
            if not self.reweight_beta:
                print "Generalized ensemble simulations must specify reweight_beta option"
                sys.exit(1)
            else:
                return None

        # Read information from temperature file
        temperature_filename = self.directory + "/n%s/temperature.info" % self.simulation_index
        temperature_file = open(temperature_filename)
        beta_column_index = 3
        for line in temperature_file.readlines():
            line = line.strip()
            if line[0] == "#":
                continue;
            split_line = line.split()
            
            if int(split_line[0]) == int(self.temperature_index):
                return float(split_line[beta_column_index])
        print "No beta found in %s at temperature index %s" % (temperature_filename, self.temperature_index)
        sys.exit(1)


