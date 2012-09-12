# Parameter.py --- Forcefield parameter base class
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

class Parameter(object):
    '''The base class for all forcefield parameter classes.'''

    # To allow specification of abstract base classes
    __metaclass__ = ABCMeta

    _name = 'UNDEFINED'

    @classmethod
    def get_name(self):
        return self._name

    def __init__(self, value):
        '''Constructor. Note that parameter objects are always initialized with a value.'''
        self.value = value

    def get_value(self):
        '''Return value associated with parameter'''
        return self.value

    def set_value(self, value):
        '''Set new value for parameter'''        
        self.value = value

    @abstractmethod
    def get_derivative_settings(self):
        '''Get settings necessary to calculate derivative.'''
        pass

    def __repr__(self):
        '''String representation'''
        return repr(self.value)


class ReferenceParameter(Parameter):
    def __init__(self, name,  value):
        Parameter.__init__(self, value)
        self._name =  name

    def get_name(self):
        return self._name

    def get_derivative_settings(self):
        print "Trying to read derivative for working parameter, does not make sense: ", _name
