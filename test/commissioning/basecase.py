from pytools import testutil
import pysynphot as S
import numpy as N
import pyfits
from pysynphot import newetc as etc
from pyraf import iraf
from iraf import stsdas,hst_calib,synphot
import os,time,re
from pysynphot.wavetable import wavetable as Wavecat
from pysynphot.observationmode import ObservationMode


class calcspecCase(testutil.LogTestCase):
    def setUp(self):
        self.obsmode=None
        self.spectrum=None
        self.runpy()
        self.skip=True

    def hasSkyLines(self):
        lnames="el1215a|el1302a|el1356a|el2471a"
        ans=re.findall(lnames,self.spectrum)
        if len(ans) > 0:
            return True
        else:
            return False
        
    def setglobal(self,fname=None):
        if fname is None:
            fname=__file__
        self.propername=self.id()
        base,ext=os.path.splitext(os.path.basename(fname))
        main,case,test=self.propername.split('.')
        self.name=os.path.join(base,test,case)
        self.wavename=self.name+'_wave.fits'
        #Make sure the directories exist
        dirname=os.path.dirname(self.name)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
            
        self.file=self.name
        self.thresh=0.01
        self.superthresh=0.20
        self.sigthresh=0.005
        self.discrep=-99
        self.tda={'Obsmode':self.obsmode,
                 'Spectrum':self.spectrum,
                 'Thresh':self.thresh,
                  'Superthresh':self.superthresh,
                  'SigThresh':self.sigthresh,
                  'SkyLines':self.hasSkyLines()}
        self.tra={}

##     def run_calcspec(self,obsmode,spstring,form,output=None,binset=False):
##         if binset:
##             try:
##                 wavetab=Wavecat[self.obsmode]
##             except KeyError:
##                 self.sptest.writefits(self.wavename)
##                 wavetab=self.wavename
##             if wavetab.startswith('('):
##                 #generate a wavetab that IRAF can read.
##                 try:
##                     wmin,wmax,dw=wavetab[1:-1].split(',')
##                     iraf.genwave(self.wavename,wmin,wmax,dw)
##                     wavetab=self.wavename
##                 except ValueError:
##                     self.sptest.writefits(self.wavename)
##                     wavetab=self.wavename
                   
##         else:
##             wavetab=""

##         if obsmode in (None,"None"):
##             spec=spstring
##         else:
##             spec="band(%s)*(%s)"%(obsmode,spstring)

##         iraf.calcspec(spectrum=spec,
##                       output=output,
##                       form=form,wavetab=wavetab)

    def run_countrate(self,form,output=None):
        if output is None:
            output=""
        iraf.countrate(spectrum=self.spectrum,magnitude="",
                       instrument=self.obsmode,
                       output=output,form=form)

    def runpy(self):
        self.sptest=etc.parse_spec(self.spectrum)
        self.csname=self.name+'.fits'
        for name in (self.csname, self.wavename):
            try:
                os.remove(self.csname)
            except OSError:
                pass

    def arraydiff(self,test,ref):
        idx=N.nonzero(ref)
        ans=(test[idx]-ref[idx])/ref[idx]
        return ans

    def arraysigtest(self,test,ref):
        #Raise an error if the arrays are not the same size
        if test.shape != ref.shape:
            raise ValueError("Array size mismatch")
        tt=test[2:-2]
        rr=ref[2:-2]
        #Identify the significant elements
        tidx=N.where(tt>(self.sigthresh*tt.max()))[0]
        ridx=N.where(rr>(self.sigthresh*rr.max()))[0]
        #Fail if they're not the same set
        self.failUnless(N.alltrue(tidx == ridx),
                        msg="Significant elements are not the same")

        #Now compare only the significant elements.
        #We no longer need to exclude points with zero value, because
        #those points were already excluded as insignificant.
        self.arraytest(tt[ridx],rr[ridx])


    def count_outliers(self,Nsigma=3):
        mean=self.adiscrep.mean()
        std=self.adiscrep.std()
        outliers=N.where(abs(self.adiscrep) > mean + Nsigma*std)
        return len(outliers[0])
    
    def arraytest(self,test,ref):
        #Exclude the endpoints where the gradient is very steep
        self.adiscrep=self.arraydiff(test,ref)#[2:-2]
        count=N.where(abs(self.adiscrep)>self.thresh)[0].size
        try:
            self.tra['Discrepfrac']=float(count)/self.adiscrep.size
            self.tra['Discrepmin']=self.adiscrep.min()
            self.tra['Discrepmax']=self.adiscrep.max()
            self.tra['Discrepmean']=self.adiscrep.mean()
            self.tra['Discrepstd']=self.adiscrep.std()
            self.tra['Outliers']=self.count_outliers(5)
            if (self.tra['Discrepfrac'] > self.superthresh):
                self.tra['Extreme']=True
            self.failUnless(N.alltrue(abs(self.adiscrep)<self.thresh),
                            msg="Worst case %f"%abs(self.adiscrep).max())
        except ZeroDivisionError:
            self.tra['Discrepfrac']=0.0
            self.tra['Discrepmin']=0.0
            self.tra['Discrepmax']=0.0


    def savepysyn(self,wave,flux,fname,units=None):
        """ Cannot ever use the .writefits() method, because the array is
        frequently just sampled at the synphot waveset; plus, writefits
        is smart and does things like tapering."""
        if units is None:
            ytype='throughput'
            units=' '
        else:
            ytype='flux'
        col1=pyfits.Column(name='wavelength',format='D',array=wave)
        col2=pyfits.Column(name=ytype,format='D',array=flux)
        tbhdu=pyfits.new_table(pyfits.ColDefs([col1,col2]))
        tbhdu.header.update('tunit1','angstrom')
        tbhdu.header.update('tunit2',units)
        tbhdu.writeto(fname.replace('.fits','_pysyn.fits'))
                               
class calcphotCase(calcspecCase):
        
    def runpy(self):
        self.sptest=etc.parse_spec(self.spectrum)
        self.bp=S.ObsBandpass(self.obsmode)
        self.cbname=self.name+'.fits'
        self.csname=self.name+'_cs.fits'

        for fname in (self.cbname, self.csname):
            try:
                os.remove(fname)
                os.remove(fname.replace('.fits','_pysyn.fits'))
            except OSError:
                pass
        self.discrep=-99
        

     
                    
    def testthru(self):
        iraf.calcband(obsmode=self.obsmode,output=self.cbname)
        ref=S.FileBandpass(self.cbname)
        rthru=ref.throughput
        rwave=ref.wave
        tthru=self.bp(rwave)
        self.savepysyn(rwave,tthru,self.cbname)
        self.arraysigtest(tthru,rthru)

        
    def testefflam(self):
        iraf.calcphot(obsmode=self.obsmode,spectrum=self.spectrum,
                      form='photlam', func='efflerg')
        rlam=iraf.calcphot.getParam('calcphot.result',native=1)
        obs=S.Observation(self.sptest,self.bp)
        tlam=obs.efflam()
        if rlam != 0:
            self.discrep=(tlam-rlam)/rlam
        else:
            self.discrep=tlam-rlam
        self.tra['Discrep']=self.discrep
        if abs(self.discrep)>self.superthresh:
            self.tra['Extreme']=True
        self.tra['Syn']=rlam
        self.tra['Pysyn']=tlam

        self.failUnless(abs(self.discrep) < self.thresh,msg="Discrep=%f"%self.discrep)

        

class thermbackCase(calcphotCase):
        
    def runpy(self):

        #self.sptest=etc.parse_spec(self.spectrum)
        self.bp=S.ObsBandpass(self.obsmode)
        self.cbname=self.name+'.fits'
        self.csname=self.name+'_cs.fits'

        for fname in (self.cbname, self.csname):
            try:
                os.remove(fname)
                os.remove(fname.replace('.fits','_pysyn.fits'))
            except OSError:
                pass
        self.discrep=-99

        iraf.thermback(obsmode=self.obsmode,form='counts',
                       output=self.csname)

        omode=ObservationMode(self.obsmode)
        self.sp=omode.ThermalSpectrum()
        self.ttherm=self.sp.integrate()*omode.pixscale**2*omode.area
        self.sp.convert('counts')
        self.savepysyn(self.sp.wave,self.sp.flux,self.csname,units='counts')

    def testspecphotlam(self):
        __test__ = False

    def testefflam(self):
        __test__ = False


    def testthermspec(self):
        ref=S.FileSpectrum(self.csname)
        if N.any(self.sp.wave != ref.wave):
            raise ValueError('wave arrays not equal')
        self.arraysigtest(self.sp.flux,ref.flux)
        
    def testthermback(self):
        rtherm=iraf.thermback.getParam('thermback.thermflux',native=1)
        ttherm=self.ttherm
        if rtherm != 0:
            self.discrep=(ttherm-rtherm)/rtherm
        else:
            self.discrep=ttherm-rtherm
        self.tra['Discrep']=self.discrep
        if abs(self.discrep)>self.superthresh:
            self.tra['Extreme']=True
        self.tra['Syn']=rtherm
        self.tra['Pysyn']=ttherm

        self.failUnless(abs(self.discrep) < self.thresh,msg="Discrep=%f"%self.discrep)

        

class countrateCase(calcphotCase):
    def runpy(self):
        self.sptest=etc.parse_spec(self.spectrum)
        self.bp=S.ObsBandpass(self.obsmode)
        self.csname=self.name+'_cs.fits'
        self.crname=self.name+'_cr.fits'
        self.cbname=self.name+'.fits'
        for fname in (self.cbname, self.csname, self.crname):
            try:
                os.remove(fname)
                os.remove(fname.replace('.fits','_pysyn.fits'))
            except OSError:
                pass
    def testcrphotlam(self):
        obs=S.Observation(self.sptest,self.bp)
        obs.convert('photlam')
        self.run_countrate('photlam',self.crname)
        spref=S.FileSpectrum(self.crname)
        rflux=spref.flux
        tflux=obs.binflux
        self.savepysyn(obs.binwave,obs.binflux,
                       self.crname,units='photlam')

        self.arraysigtest(tflux,rflux)

    def testcrcounts(self):
        self.run_countrate('counts',self.crname.replace('.fits','_counts.fits'))
        spref=S.FileSpectrum(self.crname.replace('.fits','_counts.fits'))
        obs=S.Observation(self.sptest,self.bp,binset=spref.wave)
        obs.convert('counts')
        rflux=spref.flux
        tflux=obs.binflux
        self.savepysyn(obs.binwave,obs.binflux,
                       self.crname.replace('.fits','_counts.fits'),
                       units='counts')
        if N.any(obs.binwave != spref.wave):
            raise ValueError('wave arrays not equal')
        
        self.arraysigtest(tflux,rflux)

    def testcountrate(self):
        obs=S.Observation(self.sptest,self.bp)
        self.run_countrate('counts')
        rval=iraf.countrate.getParam('flux_tot',native=1)
        tval=obs.countrate()
        if rval != 0:
            self.discrep=(tval-rval)/rval
        else:
            self.discrep=tval-rval
        self.tra['Discrep']=self.discrep
        self.tra['Syn']=rval
        self.tra['Pysyn']=tval
        if abs(self.discrep)>self.superthresh:
            self.tra['Extreme']=True
        self.failUnless(abs(self.discrep) < self.thresh,msg="Discrep=%f"%self.discrep)
      
class SpecSourcerateSpecCase(countrateCase):
    def placeholder(self):
        pass
