#!/usr/bin/env python
# coding: utf-8

# Line sizing
# 
# Client: Internal\
# Project: Hydraulics in Python\
# Calc: 2023-Calc-001\
# Created By: P.Wikhe\
# Guided by: K. Dorma\
# Date: September 13, 2023
# 
# Revision history:
# 
# |Revision | Date | Description | By | Reviewer|
# | :-------| :----|:------------|:---|:--------|
# |    1.0  | 13 Sept. 2023 | Demo code | PW | KCD |
# 

# In[1]:


#Importing libraries
import numpy as np
import pandas as pd
import math
from scipy import interpolate


# ## Inputs

# In[2]:


pi = math.pi


# In[3]:


pipingFile = (r'C:\Users\prati\Downloads\line_sizing-main\line_sizing\data\input_2.xlsx')
roughnessFile = (r'C:\Users\prati\Downloads\line_sizing-main\line_sizing\data\pr_2.xlsx')
pipeIDfile = (r'C:\Users\prati\Downloads\line_sizing-main\line_sizing\data\id_2.xlsx')



# ## Get common data and piping data

# In[4]:


roughness = pd.ExcelFile(roughnessFile)
r_table =roughness.parse('pipeRoughness')

pipeID = pd.ExcelFile(pipeIDfile)
id_table=pipeID.parse('pipeIDlist')

piping = pd.ExcelFile(pipingFile)
input_table=piping.parse('lineSizingInput')


# # Formula for diameter in terms of DP per 100 m
# 
# Let L = 100 m.
# 
# $\frac{\Delta p}{\rho} = f\left(\frac{L}{D}\right) \frac{v^2}{2}$
# 
# $ v = \frac{m}{\rho (1/4) \pi d^2} $
# 
# $ v = \frac{4 m}{\rho \pi d^2} $
# 
# $\frac{\Delta p}{\rho} = f\left(\frac{L}{D}\right) \frac{1}{2} \left(\frac{4 m}{\rho \pi d^2}\right)^2$
# 
# $\frac{\Delta p}{\rho} = f\left(\frac{L}{D}\right) \frac{16 m^2}{2 \rho^2 \pi^2 D^4}$
# 
# $\Delta p = 8 f L \frac{m^2}{\rho \pi^2 D^5}$
# 
# or
# 
# $D^5 = 8 f L \frac{m^2}{\rho \pi^2 \Delta p_{100}}$
# 
# where L = 100 m.
# 
# then we calculate
# 
# $D = (D^5)^{1/5}$
# 

# ## Bunch of functions

# In[5]:


def getReynolds(mdot_kgs, id_mm, visc_mpas, dens_kgm3):
    # Re = rho u d / mu
    # u = mdot / (rho pi/4 * d2)
    # Re = rho d (mdot / rho pi/4 d2) / mu
    # Re = 4 mdot / mu.d.pi
    pi = math.pi
        
    return (4*mdot_kgs/(pi*(visc_mpas/1000)*(id_mm/1000)))
#    getReynolds = ((1000000*4*mdot/(3600*pi*u*id1))


# In[6]:


def colebrook_solver(Re,rr):
    # Re is reynolds number
    # rr is relative roughness
    max_iter = 10  # 10 iterations is lots for sucessive substituion
    to = 0.000001
    f_guess = Re*0.0 + 0.01   # initial guess for all values of friction factor
    for _ in range(max_iter):
        rhs=-2*np.log10(rr/3.7 + 2.51/(Re*np.sqrt(f_guess)))
        f_next=1/(rhs**2)
        f_guess=f_next
        
    return f_next


# In[7]:


def sizeDP100(m_new, dp, d, u, e):
    # m_new mass flow kg/s
    # dp is Pa per 100 m
    # u is viscoisty in pa.s
    # e is roughness in mm
    # return value is pipe ID mm
    pi = math.pi
    
    f  = m_new*0.0 + 0.01 # our guess for all friction factors
    L = 100.0 # pipe length 100 m used for DP
    for x in range(10):
        D5 = (8*L*f*m_new*m_new)/(d*pi*pi*dp)
        D = pow(D5,0.2)
        idmm = D*1000
        rr = e/idmm
        Re = getReynolds(m_new, idmm, u, d)
        ff = colebrook_solver(Re, rr)
        f  = pd.Series(ff)
    return idmm


# In[8]:


def getListLargerNPS(self,npsList): # self or df is linesNeeded
    # df has the mmNeeded for the ID that we are looking for
    # I don't like cycling through the entire list, but it works
    # using interpolation is a simple and dirty way to find the next higher value

    self["NPS"] = 0.0 # add NPS to the df, the decimal point is needed to initiate this column as floating point
    self["IDmm"] = 0.0 # add ID to the df


    for i,row in self.iterrows():
        theSchedule = row["Schedule"]
        shortList = npsList[npsList["Schedule"]==theSchedule]
        theID = self.at[i,"reqdIDmm"]
        # our interpolation functions
        fNPS = interpolate.interp1d(shortList["IDmm"],shortList["NPS"],kind='next')
        fIDmm = interpolate.interp1d(shortList["IDmm"],shortList["IDmm"],kind='next')
        # and now we interpolate
        self.at[i,"NPS"] = fNPS(theID)
        self.at[i,"IDmm"] = fIDmm(theID)
    return (0)


# In[9]:


def sizePiping(input_table, id_table, r_table):
    # given the inputs, do the line sizing math
    
    interResults = input_table[["Segment","Schedule","vlimit_ms"]].copy()
    
    #Erosional velocity
    interResults["vmaxErosion"] = input_table['frictionCsi']/np.sqrt(input_table['density_kgm3'])
    #Selecting the min. of erosional velocity and hard limit velocity.
    interResults["velocMax"] = interResults[['vlimit_ms','vmaxErosion']].min(axis=1)

    #New flow rate = Base flow rate * Flow margin
    interResults["m_new"] = input_table['massFlow_kghr'] * input_table['flowMargin']/3600.0 # this is in kg/s

    #corss section area of pipe based on permissible max velocity
    interResults["S1"] = interResults["m_new"] / input_table['density_kgm3'] / interResults["velocMax"]
    interResults["maxVelocID"] = 1000*2*np.sqrt(interResults["S1"]/pi) # diameter in mm
    
    merged=pd.merge(input_table,r_table,on='Material') # find pipe roughness based on material
    e = merged['roughnessMM']
    
    interResults["dp100IDmm"] = sizeDP100(interResults["m_new"],input_table['kPaPer100m']*1000,input_table['density_kgm3'],input_table['viscosity_cP'],e)
    
    #Selecting the min. of erosional velocity and hard limit velocity.
    interResults["reqdIDmm"] = interResults[['maxVelocID','dp100IDmm']].min(axis=1)
    getListLargerNPS(interResults,id_table)
    
    return (interResults)


# In[10]:


interResults = sizePiping(input_table, id_table, r_table)
interResults


# In[ ]:




