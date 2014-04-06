# -*- coding: utf-8 -*-
import logging
from gibbs import constants
import numpy

class _BasePhase(object):
    def PhaseName(self):
        return NotImplementedError
    def Name(self):
        return NotImplementedError
    def Subscript(self):
        return NotImplementedError
    def Units(self):
        return NotImplementedError
    def Value(self):
        # the value in the given units (i.e. the number shown to the user)
        return 1
    def ValueString(self):
        return '%.2g' % self.Value()
    def IsConstant(self):
        return True
    def HumanValueAndUnits(self):
        """
            convert the value to human readable numbers by changing
            the units (adding milli, micro modifiers)
        """
        
        # make an exception for standard values (e.g. instead of 1 M the
        # default value will be 1000 mM). This is more convenient for users.
        if self.Value() == 1:
            return (1e3, 1e-3, 'x10<sup>-3</sup>&nbsp;%s' % self.Units())
            
        logv = numpy.log10(self.Value())
        exp = numpy.floor(logv / 3.0)*3
        prefactor = 10**(logv - exp)
        
        if exp != 0:
            return (prefactor, 10**(exp),
                    'x10<sup>%d</sup>&nbsp;%s' % (exp, self.Units()))
        else:
            # avoid writing 10^0 as a prefix for the units
            return (self.Value(), 1, self.Units())
            
        
    def HumanValueAndUnits_letters(self):
        """
            convert the value to human readable numbers by changing
            the units (adding milli, micro modifiers)
        """
        logging.info('phase = %s %g %s' % (self.Name(), self.Value(), self.Units()))
        #if self.Value() > 1e-2:
        #    return (self.Value(), self.Units())
        
        if self.Value() >= 1e-4:
            return (self.Value() * 1e3, 1e-3, 'm' + self.Units())

        if self.Value() >= 1e-7:
            return (self.Value() * 1e6, 1e-6, 'μ' + self.Units())
        
        return (self.Value() * 1e9, 1e-9, 'n' + self.Units())
        
    def __str__(self):
        return '%g %s' % self.HumanValueAndUnits()

class StandardAqueousPhase(_BasePhase):
    def PhaseName(self):
        return constants.AQUEOUS_PHASE_NAME
    def Name(self):
        return constants.STANDARD_AQUEOUS_PHASE_NAME
    def Subscript(self):
        return '(aq)'
    def Units(self):
        return 'M'

class StandardGasPhase(_BasePhase):
    def PhaseName(self):
        return constants.GAS_PHASE_NAME
    def Name(self):
        return constants.STANDARD_GAS_PHASE_NAME
    def Subscript(self):
        return '(g)'
    def Units(self):
        return 'bar'

class StandardLiquidPhase(_BasePhase):
    def PhaseName(self):
        return constants.LIQUID_PHASE_NAME
    def Name(self):
        return constants.STANDARD_LIQUID_PHASE_NAME
    def Subscript(self):
        return '(l)'
    def Units(self):
        return 'bar'

class StandardSolidPhase(_BasePhase):
    def PhaseName(self):
        return constants.SOLID_PHASE_NAME
    def Name(self):
        return constants.STANDARD_SOLID_PHASE_NAME
    def Subscript(self): 
        return '(s)'
    def Units(self):
        return 'bar'

class CustomAqueousPhase(StandardAqueousPhase):
    def __init__(self, concentration=1.0): # in units of M
        self._concentration = concentration
    def Name(self):
        return constants.CUSTOM_AQUEOUS_PHASE_NAME
    def IsConstant(self):
        return False
    def Value(self):
        return self._concentration

class CustomGasPhase(StandardGasPhase):
    def __init__(self, partial_pressure=1.0):
        self._partial_pressure = partial_pressure
    def Name(self):
        return constants.CUSTOM_GAS_PHASE_NAME
    def IsConstant(self):
        return False
    def Value(self):
        return self._partial_pressure
        
###############################################################################


class _BaseConditions(object):

    def __init__(self,
                 pH=constants.DEFAULT_PH,
                 pMg=constants.DEFAULT_PMG,
                 ionic_strength=constants.DEFAULT_IONIC_STRENGTH,
                 temperature=constants.DEFAULT_TEMP,
                 e_reduction_potential=constants.DEFAULT_ELECTRON_REDUCTION_POTENTIAL):
        self.pH = pH
        self.pMg = pMg
        self.ionic_strength = ionic_strength
        self.temperature = temperature
        self.e_reduction_potential = e_reduction_potential
        self._phases = {}

    @staticmethod
    def _GeneratePhase(phase, value):
        if phase == constants.AQUEOUS_PHASE_NAME:
            return CustomAqueousPhase(value)
        if phase == constants.GAS_PHASE_NAME:
            return CustomGasPhase(value)
        if phase == constants.LIQUID_PHASE_NAME:
            return StandardLiquidPhase()
        if phase == constants.SOLID_PHASE_NAME:
            return StandardSolidPhase()    
        raise NotImplementedError

    def GetTemplateDict(self):
        return {'ph': self.pH, 'pmg': self.pMg,
                'ionic_strength': self.ionic_strength,
                'temperature': self.temperature,
                'e_reduction_potential': self.e_reduction_potential,
                'conditions': self.__str__()}

    def SetPhasesAndRatios(self, all_ids, all_phases, all_ratios):
        for kegg_id, phase, ratio in zip(all_ids, all_phases, all_ratios):
            self.SetPhase(kegg_id, phase, ratio)

    def SetPhase(self, kegg_id, phase, ratio=1):
        raise NotImplementedError

    def GetPhase(self, kegg_id):
        if kegg_id not in self._phases:
            logging.debug('Condition requested for unknown id: %s', kegg_id)
            return None

        return self._phases[kegg_id]

    def _GetUrlParams(self, kegg_id):
        phase = self.GetPhase(kegg_id)
        return ['conditions=%s' % self.__str__(),
                'reactantsPhase=%s' % phase.PhaseName(),
                'reactantsConcentration=%s' % phase.Value()]
        
class StandardConditions(_BaseConditions):

    def __str__(self):
        return constants.STANDARD_CONDITION_STRING

    def SetPhase(self, kegg_id, phase, ratio=1):
        self._phases[kegg_id] = CustomConditions._GeneratePhase(phase, 1)
        
class MillimolarConditions(_BaseConditions):

    def __str__(self):
        return constants.MILLIMOLAR_CONDITION_STRING

    def SetPhase(self, kegg_id, phase, ratio=1):
        self._phases[kegg_id] = CustomConditions._GeneratePhase(phase, 1e-3)
    
class CustomConditions(_BaseConditions):

    def __str__(self):
        return constants.CUSTOM_CONDITION_STRING

    def SetPhase(self, kegg_id, phase, ratio=1):
        logging.info('For %s, setting phase to %s and ratio to %g' % 
                     (kegg_id, phase, ratio))
        self._phases[kegg_id] = CustomConditions._GeneratePhase(phase, ratio)
    
###############################################################################

def CreateConditions(name, all_ids=None, all_phases=None, all_ratios=None):
    
    if name == constants.STANDARD_CONDITION_STRING:
        return StandardConditions()

    if name == constants.MILLIMOLAR_CONDITION_STRING:
        return MillimolarConditions()
    
    if name == constants.CUSTOM_CONDITION_STRING:
        assert all_ids and all_phases and all_ratios
        cc = CustomConditions()        
        cc.SetPhasesAndRatios(all_ids, all_phases, all_ratios)
        return cc

    logging.warning('unrecognized condition name: ' + name)
    return None