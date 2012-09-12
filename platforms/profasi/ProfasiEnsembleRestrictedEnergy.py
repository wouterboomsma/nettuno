from ProfasiEnsemble import ProfasiEnsemble
from numpy import genfromtxt
import os
import copy 
import numpy

class ProfasiEnsembleRestrictedEnergy(ProfasiEnsemble):

    filter_indices = None

    def __init__(self, log_level=0):
        ProfasiEnsemble.__init__(self, log_level)

    def set_settings(self, directory, reweight_beta, iteration_range,
                     simulation_index=0, temperature_index=0):        
        ProfasiEnsemble.set_settings(self, **dict((key,value) for key, value in locals().iteritems() if key != "self"))
        # Filter out step indices with correct energy values
        vals = self.get_initial_energies()
        self.filter_indices = [i[0] for i in vals if float(i[1]) < 50.0 ]

    def get_observable_values(self, observable_name, directory=None):
        cache_id = self.directory + observable_name
        if(cache_id in self.cachedObservableValues):
            return self.cachedObservableValues[cache_id]
        else:
            super(ProfasiEnsembleRestrictedEnergy, self).get_observable_values(observable_name, directory=None)
            vals = self.cachedObservableValues[cache_id]        
            if(self.filter_indices != None):
                vals = numpy.array([i for i in vals if i[0] in self.filter_indices])
                self.cachedObservableValues[cache_id] = vals
            return vals

    def get_initial_energies(self, directory=None):
        if not directory:
            directory = os.path.join(self.directory, "n%s" % self.simulation_index)

        rt_filename = os.path.join(directory, "rt")
        rt_matrix = genfromtxt(rt_filename)
                
        rtkeyFile = open(os.path.join(directory, "rtkey"))
        self.observables = [line.rstrip("\n ") for line in rtkeyFile.readlines()[1:]]        
        colindex = self.observables.index('Etot')

        rtcolumn = rt_matrix[:,0:colindex+1:colindex]
        
        # Optionally limit rtcolumn to a specified range
        limits = copy.copy(self.iteration_range)
        if limits[0] == None:
            limits[0] = 0
        if limits[1] == None:
            limits[1] = max(rtcolumn[:,0])
        rtcolumn = rtcolumn[numpy.logical_and.reduce([rtcolumn[:,0] >= limits[0], rtcolumn[:,0] <= limits[1]])]
        return rtcolumn
