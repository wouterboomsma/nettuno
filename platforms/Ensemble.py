# Ensemble.py --- Ensemble base class
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
import copy

class Ensemble:
    '''Ensemble base class. All platform specific Ensemble implementations
should derive from this.'''

    # To allow specification of abstract base classes
    __metaclass__ = ABCMeta

    simulation_type = ""

    def __init__(self, log_level=0):
        '''Constructor'''
        self.log_level = log_level


    def set_settings(self, directory, reweight_beta, iteration_range, **platform_specific_args):
        '''Initialize with object with current settings, and saves them
for future retrieval. This method is separated from the constructor to 
make it clear that these settings should all be available for retrievable 
by get_settings(). The directory and iteration_range settings are common 
to all Ensemble types, while the platform_specific_args is a dictionary 
containing platform specific settings.'''

        self.settings = {}
        self.settings["directory"] = directory
        self.settings["iteration_range"] = iteration_range
        self.settings["reweight_beta"] = reweight_beta
        if self.settings["reweight_beta"] != None:
            self.settings["reweight_beta"] = float(self.settings["reweight_beta"])

        self.settings.update(platform_specific_args)
        for item in self.settings.items():
            setattr(self, item[0], item[1])

        # Overwrite iteration range if None
        # Note, it still has original value in settings attribute
        if self.iteration_range == None:
            self.iteration_range = [None, None,1]
        else:
            iteration_range = [None, None, 1]
            content = self.iteration_range.strip("[]")
            for i,value in enumerate(content.split(":")):
                if value == "":
                    iteration_range[i] = None
                else:
                    iteration_range[i] = int(value)
            self.iteration_range = iteration_range

    
    def get_settings(self):
        '''Retrieve settings stored by set_settings'''
        return self.settings


    def get_parameters(self, requested_parameter_list):
        '''Retrieve current force field parameters'''
        parameters = []
        for requested_parameter in requested_parameter_list:
            for cls in self.__class__.ParameterClass.__subclasses__():
                if cls.get_name() == requested_parameter:
                    parameters.append(cls(self.directory))

        return parameters        

    @abstractmethod
    def get_option_help(self):
        '''Output for ensemble options used by command line parser. This is an abstract
method that must be overridden by derived classes.'''
        pass
    

    @abstractmethod
    def read_parameter_values(self, requested_parameter_list):
        '''Read parameters from ensemble. This is an abstract
method that must be overridden by derived classes.'''
        pass    

    @abstractmethod
    def write_parameter_values(self, requested_parameter_list):
        '''Write current parameter values in platform specific syntax. This is an abstract
method that must be overridden by derived classes.'''
        pass

    @abstractmethod
    def get_parameter_derivative_values(self, evaluator_path, parameter):
        '''Calculate the derivatives for a particular parameter. This is an abstract
method that must be overridden by derived classes.'''
        pass
    
    @abstractmethod
    def get_energies(self, directory=None):
        '''Retrieve energies for all samples in the ensemble. Note that this
method does conduct any new evaluations but simply retrieves values. This is an abstract
method that must be overridden by derived classes.'''
        pass

    @abstractmethod
    def calculate_energies(self, parameters, evaluator_path):
        '''Calculate energies given a set of parameter values and the path
to an evaluator program'''
        pass

    @abstractmethod
    def get_reweight_weights(self, energies=None):
        '''Retrieve the weights necessary when calculating Boltzmann averages
over the ensemble. This is 1.0 when evaluating an ensemble at the same temperature
as it was simulated, but can be used both to reweight constant temperature simulations
to a different temperature, or for generalized ensembles.'''
        pass

    @abstractmethod
    def get_intrinsic_beta(self):
        '''Return the intrinsic beta=1/(k_bT) at which the simulation was conducted. This is an abstract
method that must be overridden by derived classes.'''
        pass

    def get_beta(self):
        '''Return the beta=1/(k_bT) value set by the user in the configuration file, or
if this is not specified, the intrinsic beta at which the simulation was conducted. '''
        if self.reweight_beta != None:
            return self.reweight_beta
        else:
            return self.get_intrinsic_beta()

    def get_reweight_beta(self):
        '''In case of a reweight_beta is available, return it. Otherwise, return
the ensembles own beta.'''
        if self.reweight_beta != None:
            return self.reweight_beta
        else:
            return self.get_beta()

    def scalar_to_ensemble_array(self, scalar):
        '''Turn a scalar into an array that is compatible with
the format that energies and weights are reported in: two columns
where the first contains the indices'''
        
        # Use energies as a template
        energies = copy.copy(self.get_energies())
        energies[:,1] = scalar
        return energies
