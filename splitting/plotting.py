"""
Some plotting routines
"""

import matplotlib.pyplot as plt

def plot_pair(pair):
    from matplotlib import gridspec
    fig = plt.figure(figsize=(12, 3)) 
    gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1]) 
    ax0 = plt.subplot(gs[0])
    ax0.plot(pair.T)
    ax1 = plt.subplot(gs[1])
    ax1.plot(pair[0,:],pair[1,:])
    plt.axis('equal')
    plt.show()
    
# def plt_surf(surf):
#     from matplotlib import colors, ticker, cm
#     plt.contourf(surf.lag,surf.deg,surf.l2/(surf.l1+surf.l2),locator=ticker.LogLocator(),cmap='viridis_r')