from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from . import core
from . import plotting
from .window import Window

import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
import copy

class Pair:
    """
    The Pair: work with 2-component data.
        
    Usage: Pair()     => create Pair of synthetic data
           Pair(x,y) => creates Pair from two traces stored in numpy arrays x and y.
    
    Keyword Arguments:
        - delta = 1. (sample interval) [default] | float
        - units = 's' (for labelling) | string
        - angle = 0. (component 1 angle) | float
    
    Advanced Keyword Arguments (if in doubt don't use):
        - geom = 'geo' (N,E) [default] | 'ray' (SV,SH)
        - xy = np.ones(2) | custom numpy array
        - rcvloc = None
        - srcloc = None    

    Methods:
        - plot()
        -
    """
    def __init__(self,*args,**kwargs):
        
        if ('delta' in kwargs):
            self.delta = kwargs['delta']
        else:
            self.delta = 1.
            
        if ('units' in kwargs):
            self.units = kwargs['units']
        else:
            self.units = 's'
            
        if ('angle' in kwargs):
            self.angle = kwargs['angle']
        else:
            self.angle = 0.
        
        if ('window' in kwargs):
            self.window = kwargs['window']
        else:
            self.window = None
        
        if len(args) == 0:
            if ('lag' in kwargs):
                # convert time shift to nsamples -- must be even
                nsamps = int(kwargs['lag']/self.delta)
                nsamps = nsamps if nsamps%2==0 else nsamps + 1
                kwargs['lag'] = nsamps                                      
            self.x, self.y = _synth(**kwargs)                   
        elif len(args) == 2:            
            self.x, self.y = args[0], args[1]
        else: 
            raise Exception('Unexpected number of arguments')
                    
        # some sanity checks
        if self.x.ndim != 1:
            raise Exception('data must be one dimensional')
        if self.x.size%2 == 0:
            raise Exception('data must have odd number of samples')
        if (self.x.size != self.y.size):
            raise Exception('x and y must be the same length')
            
        # add geometry info
        if ('geom' in kwargs):
            self.geom = kwargs['geom']
        else:
            # if using 2-component data I'll guess the user wants geo coordinates.
            self.geom = 'geo'
            
        if ('srcloc' in kwargs):
            self.srcloc = kwargs['srcloc']
            
        if ('rcvloc' in kwargs):
            self.rcvloc = kwargs['rcvloc']
            
        # if ('xyz' in kwargs):
        #     self.xyz = kargs['xyz']
        # else:
        #     self.xyz = np.ones(3)

    # methods
    
    # time from start
    def t(self):
        return np.arange(self.x.size) * self.delta
        
    def nsamps(self):
        return self.x.size

    def power(self):
        return self.x**2+self.y**2
        
    def centre(self):
        return int(self.x.size/2)
    
    def xy(self):
        return np.vstack((self.x,self.y))

    def plot(self,window=None):
        """
        Plot trace data and particle motion
        """
        from matplotlib import gridspec
        fig = plt.figure(figsize=(12, 3)) 
        if window is None:
            gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1]) 
            ax0 = plt.subplot(gs[0])
            ax0.plot(self.t(),self.x)
            ax0.plot(self.t(),self.y)
            # particle  motion
            lim = abs(self.xy().max()) * 1.1
            # the polar axis:
            # ax_polar = plt.subplot(gs[1], polar=True, frameon=False)
            # ax_polar.set_rmax(lim)
            # ax_polar.patch.set_facecolor(111)
            # ax_polar.get_xaxis.set_visible(False)
            # ax_polar.grid(True)
            # the data
            ax1 = plt.subplot(gs[1])
            # ax1.patch.set_alpha(0)
            ax1.axis('equal')
            ax1.plot(self.y,self.x)
            ax1.set_xlim([-lim,lim])
            ax1.set_ylim([-lim,lim])
            ax1.axes.get_xaxis().set_visible(False)
            ax1.axes.get_yaxis().set_visible(False)
        else:
            gs = gridspec.GridSpec(1, 3, width_ratios=[3,1,1])
            ax0 = plt.subplot(gs[0])
            ax0.plot(self.t(),self.x)
            ax0.plot(self.t(),self.y)
            # the window limits
            nsamps = self.nsamps()
            wbeg = window.start(nsamps)*self.delta
            wend = window.end(nsamps)*self.delta
            ax0.axvline(wbeg,linewidth=2,color='r')
            ax0.axvline(wend,linewidth=2,color='r')
            # windowed data
            d2 = self.chop(window,copy=True)
            ax1 = plt.subplot(gs[1])
            ax1.plot(d2.t()+wbeg,d2.x)
            ax1.plot(d2.t()+wbeg,d2.y)
            # particle  motion
            lim = abs(self.xy().max()) * 1.1
            ax2 = plt.subplot(gs[2])
            ax2.axis('equal')
            ax2.plot(d2.y,d2.x)
            ax2.set_xlim([-lim,lim])
            ax2.set_ylim([-lim,lim])
            ax2.axes.get_xaxis().set_visible(False)
            ax2.axes.get_yaxis().set_visible(False)

        # show
        plt.show()
    
    def split(self,degrees,tlag):
        """
        Applies splitting operator (phi,dt) to Pair.
        
        Rotates data so that trace1 is lined up with degrees (and trace2 90 degrees clockwise).
        Applies a relative time shift by the nearest even number of samples to tlag,
        trace1 is shifted tlag/2 forward in time, and trace2 tlag/2 backward in time.
        Then undoes the original rotation.
        """
        # convert time shift to nsamples -- must be even
        nsamps = int(tlag / self.delta)
        nsamps = nsamps if nsamps%2==0 else nsamps + 1
        # find appropriate rotation angle
        rangle = degrees - self.angle
        # apply splitting
        self.x, self.y = core.split(self.x,self.y,rangle,nsamps)
        
    
    def unsplit(self,degrees,tlag):
        """
        Applies reverse splitting operator (phi,dt) to Pair.
        
        Rotates data so that trace1 is lined up with degrees (and trace2 90 degrees clockwise).
        Applies a relative time shift by the nearest even number of samples to tlag,
        trace1 is shifted tlag/2 backward in time, and trace2 tlag/2 forward in time.
        Then undoes the original rotation.
        """
        # convert time shift to nsamples -- must be even
        nsamps = int(tlag / self.delta)
        nsamps = nsamps if nsamps%2==0 else nsamps + 1
        # find appropriate rotation angle
        rangle = degrees - self.angle
        self.x, self.y = core.unsplit(self.x,self.y,rangle,nsamps)
        
            
    def rotateto(self,degrees):
        """
        Rotate data so that trace1 lines up with *degrees*
        """
        # find appropriate rotation angle
        rangle = -degrees - self.angle 
        self.x, self.y = core.rotate(self.x,self.y,rangle)
        self.angle = degrees
        
             
    def lag(self,tlag):
        """
        Relative shift trace1 and trace2 by tlag seconds
        """
        # convert time shift to nsamples -- must be even
        nsamps = int(tlag / self.delta)
        nsamps = nsamps if nsamps%2==0 else nsamps + 1
        self.x, self.y = core.lag(self.x,self.y,nsamps)
        
     
    def chop(self,window):
        """
        Chop data around window
        """
        self.x, self.y = core.chop(self.x,self.y,window)
        
        
    def window(self,time_centre,time_width,tukey=None):
        """
        Return a window object about time_centre with time_width.
        """
        tcs = int(time_centre / self.delta)
        offset = tcs - self.centre()
        # convert time to nsamples -- must be odd
        width = int(time_width / self.delta)
        width = width if width%2==1 else width + 1        
        return Window(width,offset,tukey=tukey)
        
    # def autowindow(self,time_centre=None):
    #     """
    #     Makes a guess based on energy near *time_centre* about a suitable window
    #
    #     *time centre* should be the shear wave pick at the centre of the energy packet.
    #     By default will use centre sample.
    #     """
    #     if time_centre is None:
    #         t0 = self.centre()
    #     else:
    #         t0 = int(time_centre / self.delta)
            
        
               
    def copy(self):
        return copy.copy(self)
        
def _synth(**kwargs):
    """return ricker wavelet synthetic data"""
    
    if ('pol' in kwargs):
        pol = kwargs['pol']
    else:
        pol = 0.
        
    if ('fast' in kwargs):
        fast = kwargs['fast']
    else:
        fast = 0.
        
    if ('lag' in kwargs):
        lag = kwargs['lag']
    else:
        lag = 0
        
    if ('noise' in kwargs):
        noise = kwargs['noise']
    else:
        noise = 0.03
        
    if ('nsamps' in kwargs):
        nsamps = kwargs['nsamps']
    else:
        nsamps = 501
        
    if ('width' in kwargs):
        width = kwargs['width']
    else:
        width = 16.
        
    if ('window' in kwargs):
        window = kwargs['window']
    else:
        window = Window(width*3)

    nsamps = int(nsamps)
    
    x = signal.ricker(nsamps, width) + core.noise(nsamps,noise,width/4)
    y = core.noise(nsamps,noise,width/4)
    
    # rotate to polarisation
    x,y = core.rotate(x,y,-pol)
    
    # add any splitting -- this will reduce nsamps
    x,y = core.split(x,y,fast,lag)
    
    return x,y

