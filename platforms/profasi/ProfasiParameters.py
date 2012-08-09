# ProfasiParameters.py --- Parameter classes for all relevant Profasi parameters
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


from ..Parameter import Parameter

class ParameterValueNotFoundError(Exception):
    '''Exception raised when a requested parameter is not found.'''

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "Couldn't read parameter value: " + repr(self.value)



class ProfasiParameter(Parameter):
    '''Base class for all profasi parameters. Contains functionality to 
read write Profasi style parameters.'''

    # Profasi energy term name should be overriden by derived classes
    _term_name='UNDEFINED'

    @classmethod
    def get_name(self):
        '''Get full profasi energy term parameter name.'''
        return self._term_name + "_"+self._name


    @classmethod
    def get_partial_name(self):
        '''Get parameter term name (without term name).'''
        return self._name


    @classmethod
    def get_term_name(self):
        '''Get profasi energy term name (without parameter name).'''
        return self._term_name


    @classmethod
    def get_term_name_settings_file(self):
        '''Get profasi energy term name as it appears in the settings file (with _pars suffix).'''
        return self._term_name + "_pars"


    def __init__(self, directory):
        '''Constructor'''

        self.directory = directory
        value = float(self.extract_value_from_settings_file())
        Parameter.__init__(self, value)


    def extract_value_from_settings_file(self):
        '''Retrieve parameter value from settings file.'''
        
        settings_filename = self.directory + "/settings.cnf" 
        settings_file = open(settings_filename)

        for line in settings_file.readlines():
            split_line = line.strip().split()

            if len(split_line) == 0:
                continue

            if split_line[0].upper() == (self.get_term_name_settings_file()).upper():
                
                for token in split_line[1:]:
                    split_token = token.strip().split(":")
                    
                    if split_token[0].upper() == self.get_partial_name().upper():
                        return split_token[1]

        raise ParameterValueNotFoundError(self.get_name())
    


class ProfasiChargedScInteractionScale(ProfasiParameter):
    '''Parameter class for the scale parameter in the charge sidechain term.'''

    _name='scale'
    _term_name='charged_sc_interaction'

    _type='linear'
    _rtname='ChargedSCInteraction'

    def __init__(self, directory):
        '''Constructor.'''
        ProfasiParameter.__init__(self, directory)

    def get_derivative_settings(self):
        '''Get settings necessary to calculate derivative.'''
        settings_content = "charged_sc_interaction_pars SCALE:1.0\nforce_field FF08DR=FF08:ChargedSCInteraction"
        return settings_content




class ProfasiHBMMScale(ProfasiParameter):
    '''Parameter class for the scale parameter in the main chain hydrogen bond term.'''

    _name='scale'
    _term_name='main_chain_hydrogenbonds'

    _type='linear'
    _rtname='HBMM'

    def __init__(self, directory):
        '''Constructor.'''
        ProfasiParameter.__init__(self, directory)

    def get_derivative_settings(self):
        '''Get settings necessary to calculate derivative.'''
        settings_content = "main_chain_hydrogenbonds_pars SCALE:1.0\nforce_field FF08DR=FF08:HBMM"
        return settings_content
