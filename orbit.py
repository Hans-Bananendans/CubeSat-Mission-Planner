from numpy import log

class Orbit:
    """This class stores and supplies orbital parameters for given circular 
    SSO orbit"""
    
    def __init__(self,h,i,LTAN):
        self.h = h #[km]
        self.i = i #[deg]
        self.LTAN = LTAN #0-23[h] e.g. 14 is 14:00
    
    
    def period(self):
        """
        Parameters
        ----------
        h : double
            Orbital altitude in [km].

        Returns
        -------
        int
            Orbital period in [s].

        """
        return int(2*3.141593 * ((1000*(6371+self.h))**3/(3.986*10**14))**0.5)
    
    def eclipse(self):
        """
        eclipse(h)
        Note: Only valid between LTAN [10:00, 11:00], based on logarithmic
            regression of simulated eclipse data in GMAT. For more info,
            consult eclipse_predictions.xlsx.
            
        ACCURATE TO WITHIN A FEW SECONDS
        
        Parameters
        ----------
        h : double
            Orbital altitude in [km].

        Returns
        -------
        double
            Total eclipse duration (including penumbras) in [s].

        """
        
        # If LTAN is 10:00
        # e = -151*log(self.h) + 2965 # [s]
        
        # If LTAN is 10:30
        e = -125*log(self.h) + 2860 # [s]
        
        # If LTAN is 11:00
        # e = -109*log(self.h) + 2800 # [s]        

        return e
    
    def eclipse_frac(self):
        """
        eclipse(h)
        Note: Only valid for LTAN 10:00, 10:30, 11:00, based on logarithmic
            regression of simulated eclipse data in GMAT. For more info,
            consult eclipse_predictions.xlsx.
            
        ACCURACY TO WITHIN 0.1 OF TRUE VALUE
        
        Parameters
        ----------
        h : double
            Orbital altitude in [km].

        Returns
        -------
        double
            Percentage of orbit that is in ECLIPSE [%].

        """
        return self.eclipse()/self.period()