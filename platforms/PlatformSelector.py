# PlatformSelector.py --- Factory for constructing ensembles of specific type
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


from profasi.ProfasiEnsemble import ProfasiEnsemble

class UnknownPlatformException(Exception):
    '''Exception used when confronted with an unknown ensemble type.'''

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class PlatformSelector:
    '''Factory class for constructing ensembles of specific type.'''

    @classmethod
    def get_ensemble(self, simulation_type, directory, beta, iteration_range, log_level=0, platform_specific_args={}):
        '''Construct an ensemble. The directory and iteration_range parameters
are common to all ensembles, while platform_specific_args is a dictionary containing
platform-specific options.'''

        if simulation_type == "PROFASI":
            ensemble = ProfasiEnsemble(log_level)
            ensemble.set_settings(directory, beta, iteration_range, **platform_specific_args)
            return ensemble
        else:
            raise UnknownPlatformException(simulation_type)
    
