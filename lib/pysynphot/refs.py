import os.path
import warnings

import numpy as np

from locations import irafconvert, _refTable

_default_waveset = None
_default_waveset_str = None

#Constants to hold tables.
GRAPHTABLE= ''
GRAPHDICT = {}
COMPTABLE = ''
COMPDICT = {}
THERMTABLE = ''
THERMDICT = {}
HSTAREA = 45238.93416  # cm^2

def set_default_waveset(minwave=500, maxwave=26000, num=10000., 
                        delta=None, log=True):
    """
    Set the default waveset for pysynphot spectral types. Calculated wavesets
    are inclusive of `minwave` and `maxwave`.
    
    When a waveset is specified using the `delta` parameter the waveset is
    calculated such that the ends are exactly `minwave` and `maxwave` and
    points are evenly distributed with spacing as close to `delta` as possible.
    
    Parameters
    ----------
    minwave : float, optional
        The starting point of the waveset.
        
    maxwave : float, optional
        The end point of the waveset.
        
    num : int, optional
        The number of elements in the waveset. If `delta` is not None this
        is ignored.
        
    delta : float, optional
        Delta between values in the waveset. If not None, this overrides
        the `num` parameter. If `log` is True then `delta` is assumed to be
        the spacing in log space.
        
        The waveset may not have a spacing of exactly `delta`. Rather,
        the waveset is calculated such that the value separation is as close to
        `delta` as possible while being evenly spaced and including the
        end points.
        
    log : bool, optional
        Sets whether the waveset is evenly spaced in log or linear space. If
        `log` is True then `delta` is assumed to be the delta in log space.
        `minwave` and `maxwave` should be given in normal space regardless
        of the value of `log`.
    
    """
    global _default_waveset
    global _default_waveset_str
    
    s = 'Min: %s, Max: %s, Num: %s, Delta: %s, Log: %s'
    
    if log and not delta:
        s = s % tuple([str(x) for x in (minwave, maxwave, num, None, log)])
    
        logmin = np.log10(minwave)
        logmax = np.log10(maxwave)
        
        _default_waveset = np.logspace(logmin,logmax,num)
        
    elif log and delta:
        s = s % tuple([str(x) for x in (minwave, maxwave, None, delta, log)])
    
        logmin = np.log10(minwave)
        logmax = np.log10(maxwave)
        
        num = np.round((logmax - logmin) / delta) + 1
        
        _default_waveset = np.logspace(logmin,logmax,num)
        
    elif not log and not delta:
        s = s % tuple([str(x) for x in (minwave, maxwave, num, None, log)])
    
        _default_waveset = np.linspace(minwave,maxwave,num)
        
    elif not log and delta:
        s = s % tuple([str(x) for x in (minwave, maxwave, None, delta, log)])
    
        num = np.round((maxwave - minwave) / delta) + 1
        
        _default_waveset = np.linspace(minwave,maxwave,num)
        
    _default_waveset_str = s


def _set_default_refdata():
    global GRAPHTABLE, COMPTABLE, THERMTABLE, HSTAREA
    # Component tables are defined here.

    try:
        GRAPHTABLE = _refTable(os.path.join('mtab','*_tmg.fits'))
        COMPTABLE  = _refTable(os.path.join('mtab','*_tmc.fits'))
    except IOError, e:
        GRAPHTABLE = None
        COMPTABLE = None
        warnings.warn("PYSYN_CDBS is undefined; No graph or component tables could be found; functionality will be SEVERELY crippled.",UserWarning)
    
    try:
        THERMTABLE = _refTable(os.path.join('mtab','*_tmt.fits'))
    except IOError, e:
        THERMTABLE = None
        print "Warning: %s" % str(e)
        print "         No thermal calculations can be performed."

    HSTAREA = 45238.93416  # cm^2
    
    set_default_waveset()

#Do this on import
_set_default_refdata()


def setref(graphtable=None, comptable=None, thermtable=None,
           area=None, waveset=None):
    """provide user access to global reference data.
    Graph/comp/therm table names must be fully specified."""

    global GRAPHTABLE, COMPTABLE, THERMTABLE, HSTAREA, GRAPHDICT, COMPDICT, THERMDICT
    
    GRAPHDICT = {}
    COMPDICT = {}
    THERMDICT = {}
    
    #Check for all None, which means reset
    kwds=set([graphtable,comptable,thermtable,area,waveset])
    if kwds == set([None]):
        #then we should reset everything.
        _set_default_refdata()
        return

    #Otherwise, check them all separately
    if graphtable is not None:
        GRAPHTABLE = irafconvert(graphtable)

    if comptable is not None:
        COMPTABLE = irafconvert(comptable)

    if thermtable is not None:
        THERMTABLE = irafconvert(thermtable)

    #Area is a bit different:
    if area is not None:
        HSTAREA = area
    
    if waveset is not None:
        if len(waveset) not in (3,4):
            raise ValueError('waveset tuple must contain 3 or 4 values')
        
        minwave = waveset[0]
        maxwave = waveset[1]
        num = waveset[2]
        
        if len(waveset) == 3:
            log = True
        elif len(waveset) == 4:
            if waveset[3].lower() == 'log':
                log = True
            elif waveset[3].lower() == 'linear':
                log = False
            else:
                raise ValueError('fourth waveset option must be "log" or "linear"')
                
        set_default_waveset(minwave,maxwave,num,log=log)

    #That's it.
    return


def getref():
    """Collects & returns the current refdata as a dictionary"""
    ans=dict(graphtable=GRAPHTABLE,
             comptable=COMPTABLE,
             thermtable=THERMTABLE,
             area=HSTAREA,
             waveset=_default_waveset_str)
    return ans


def showref():
    """Prints the values settable by setref"""
    refdata = getref()
    for k, v in refdata.items():
        print "%10s: %s" % (k,v)
