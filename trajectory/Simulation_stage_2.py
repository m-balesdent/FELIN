# -*- coding: utf-8 -*-
"""
Created on Thu Jul 19 13:31:11 2018

@author: lbrevaul
"""

import numpy as np

import trajectory.Command_stage_2 as Cmd
import constants as Cst
##NOTATIONS 

#alpha : incidence [-pi/2,pi/2]
#theta : assiette longitudinale [-pi/2,pi/2]  
#longi : longitude [0,2pi]   
#lat : latitude [-pi/2,pi/2]

import specifications as Spec
import geopy.distance as dist
from trajectory.modele_atmos import compute_atmos

def simulation_stage_2(t,x, Parameters):


    r = x[0] 
    V = x[1]
    gamma = x[2]
    longi = x[3]
    m = x[4]

    #Parameters
    Diameter = Parameters['geometry']['Diameter']
    Isp = Parameters['propulsion']['Isp']
    Mass_flow_rate_0 = Parameters['propulsion']['Mass_flow_rate']
    N_eng = Parameters['propulsion']['N_eng']
    Integration = Parameters['simu']['Mode_simu']
    Exit_nozzle_area = Parameters['geometry']['Exit_nozzle_area']
    Mass_f = Parameters['masses']['Mass_f']
    theta_i = Parameters['command']['Theta_i']
    theta_f = Parameters['command']['Theta_f']
    ksi = Parameters['command']['Ksi']
    tf2 = Parameters['simu']['Duration_flight']
    duration_separation = Parameters['simu']['Duration_separation']
   

    #Launcher characteristics
    S_ref = np.pi * Diameter**2/4.
    
    #Compute atmosphere
    alt = r-Cst.RT
    (Temp,Pa,rho,c) = compute_atmos(alt)
    Mach = V/c
    g_current = Cst.mu/((alt+Cst.RT)**2)


    #Control command
    cmd_tmp= Cmd.Commande_Stage_2(t,m,N_eng,Pa,Exit_nozzle_area,
                      gamma,rho,V,Mass_flow_rate_0,Mass_f,
                      Isp, theta_i,theta_f,ksi,
                      tf2,alt,duration_separation)   
    
    
    
    thrust= cmd_tmp[0]
    alpha= cmd_tmp[1]
    theta= cmd_tmp[2]
    Mass_flow_rate= cmd_tmp[3]

    #Aerodynamic forces
    CX = 0.2

    #Equations of motion    
    r_dot = V* np.sin(gamma)
    V_dot = -0.5*rho*S_ref*CX*V**2./m - g_current*np.sin(gamma) + thrust*np.cos(theta-gamma)/m
    gamma_dot = (V/r-g_current/V)*np.cos(gamma) + thrust*np.sin(theta-gamma)/(m*V) 
    longi_dot = V*np.cos(gamma)/r
    m_dot = - Mass_flow_rate

    dx = np.zeros([1,5])
    dx[0][0] = r_dot
    dx[0][1] = V_dot
    dx[0][2] = gamma_dot
    dx[0][3] = longi_dot
    dx[0][4] = m_dot

    
    if alt<0. :
        dx = np.zeros([1,5])
    
    if Integration == 1.:
        return dx[0]
    else:
        #Load factors

        # Pdyn, Flux, Distance    
        Pdyn = 0.5*rho*V**2
        flux= Pdyn*V
        lat = Spec.specifications['launch_site']['latitude']
        distance = dist.great_circle((Spec.specifications['launch_site']['latitude'],Spec.specifications['launch_site']['longitude']),\
                                     (lat,longi*180/np.pi+Spec.specifications['launch_site']['longitude'])).km
     
        CA = CX*np.cos(np.abs(alpha))
        NX = (thrust-Pdyn*CA*S_ref)/(m*Cst.mu/((alt+Cst.RT)**2))
        
        return (r, V, gamma, longi, m, NX,
                Mach,Pdyn,flux,
                alt,alpha,theta,
                rho, CX,thrust,Mass_flow_rate,distance,lat)