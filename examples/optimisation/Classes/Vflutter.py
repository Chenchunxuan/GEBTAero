from openmdao.api import ExplicitComponent
from gebtaero import *
import numpy as np

class Vflutter(ExplicitComponent):
    
    def setup(self):
        self.add_input('El',val=125e9,units='Pa')
        self.add_input('Et',val=9.3e9,units='Pa')
        self.add_input('Nult',val=0.28)
        self.add_input('Glt',val=7.5e9,units='Pa')
        self.add_input('Rho',val=1.57e3,units='kg/m**3')
        self.add_input('Thickness',val=0.00032,units='m')
        self.add_input('Ori_1',val=30.,units='deg')
        self.add_input('Ori_2',val=30.,units='deg')
        self.add_input('Chord',val=0.03,units='m')
        self.add_input('SectionLength',val=0.42,units='m')
        
        self.add_input('Vmin',val=0,units='m/s')       # Lower boundary of the search interval
        self.add_input('Vmax',val=100,units='m/s')     # Upper boundary of the search interval
        self.add_input('Vstep',val=1,units='m/s')      # Velocity step used in the algorithm
        self.add_input('DeltaV',val=0.01,units='m/s')  # Critical velocity tolerance
        self.add_input('AeroFlag',val=3)               # type of aerodynamic model used : 0 = no aero, 1 = quasi-steady, 2= quasi-steady with added mass, 3 = unsteady (Peters)
        self.add_input('GravFlag',val=1)               # type of aerodynamic model used : 0 = no aero, 1 = quasi-steady, 2= quasi-steady with added mass, 3 = unsteady (Peters)
        self.add_input('AlphaAC',val=0,units='deg')       # Aircraft angle of attack
        self.add_input('BetaAC',val=0,units='deg')        # Aircraft yaw angle
        
        self.add_output('Vflutter',val=1.,units='m/s')
        self.add_output('mVflutter',val=1.,units='m/s')
        self.add_output('Freq',val=1.,units='m/s')
        self.add_output('mFreq',val=1.,units='m/s')
        self.add_output('bendflex',val=1.,units='N**-1*m**-2')
        self.add_output('twistflex',val=1.,units='N**-1*m**-2')
        self.add_output('coupling',val=1.,units='N**-1*m**-2')
        self.add_output('mCoupling',val=1.,units='N**-1*m**-2')
        self.add_output('mCouplFlut',val=1.,units='N**-1*m**-2')
        # ~ self.add_output('mDiv',val=1.,units='m/s')
        

        
    def compute(self,inputs,outputs):
        El = inputs['El'][0]
        Et = inputs['Et'][0]
        Nult = inputs['Nult'][0]
        Glt = inputs['Glt'][0]
        Rho = inputs['Rho'][0]
        Thickness = inputs['Thickness'][0]
        Ori_1 = inputs['Ori_1'][0]
        Ori_2 = inputs['Ori_2'][0]
        Chord = inputs['Chord'][0] 
        SectionLength = inputs['SectionLength'][0]
        
        Vmin = inputs['Vmin'][0]
        Vmax = inputs['Vmax'][0]
        Vstep= inputs['Vstep'][0]
        DeltaV= inputs['DeltaV'][0]
        AeroFlag= inputs['AeroFlag'][0]
        GravFlag= inputs['GravFlag'][0]
        AlphaAC = inputs['AlphaAC'][0]
        BetaAC = inputs['BetaAC'][0]
        
        CS = CrossSection()
        Mat = OrthoMaterial(El,Et,Nult,Glt,Rho)
        Plate = CompositePlate(Chord)
        Plate.AppendPly(CompositePly(Mat,Thickness,Ori_1))
        Plate.AppendPly(CompositePly(Mat,Thickness,Ori_2))
        CS.SetFlexibilityMatrixByPlate(Plate,"he20r",1,10,10,RigidX=True,RigidZ=True)    # compute flexibility matrix (overwrite the previous flexibility matrix). RigidX = True : suppression of traction along beam axis ddl. RigidZ = True : suppression of bending in lag axis ddl
        CS.SetMassMatrixByPlate(Plate)  #compute flexibility matrix (overwrite the previous flexibility matrix)
        RefPoint = np.zeros([3])    # Plate origin
        WingAxis = np.zeros([3])
        WingAxis[1] = 1. #beam axis
        WingTwist = 0. #beam twisting
        #~ Use of Frame Class
        Fram = Frame(WingAxis,WingTwist)   #Definition of frame b of the plate
        #~ Use of WingSection class
        AileSection = WingSection(Chord,0,20,SectionLength,CS,Fram) # wing section constructor
        #~ Use of Wing class 
        Aile = Wing("Aile",RefPoint)    # Wing constructor
        Aile.AppendWingSection(AileSection) #append a section to the wing (composite plate)


		
        
        Simu = Simulation(Aile)
        print(Ori_1,Ori_2)
        Vflutter = Simu.ModalCriticalSpeed(1.225,Vmin,Vmax,Vstep,DeltaV,3,AlphaAC,BetaAC,GravFlag=GravFlag,verbosity=0,mode=0) # compute critical speed (both divergence and flutter) for the current orientation
        print(Vflutter)

        outputs['Vflutter'] = Vflutter[0]
        outputs['mVflutter'] = -Vflutter[0]
        outputs['bendflex'] = CS.GetFlexibilityMatrix()[4,4]
        outputs['twistflex'] = CS.GetFlexibilityMatrix()[3,3]
        outputs['coupling'] = CS.GetFlexibilityMatrix()[3,4]
        outputs['mCoupling'] = -CS.GetFlexibilityMatrix()[3,4]
        outputs['Freq'] = Vflutter[1]
        outputs['mFreq'] = -Vflutter[1]
        # ~ outputs['mDiv'] = -Vflutter[2]
        
        
