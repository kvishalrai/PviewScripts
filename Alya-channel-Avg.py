#### import the simple module from the paraview
import os
import time
import operator
import numpy as np
from paraview import vtk
from paraview import numpy_support
from paraview.simple import *

#pxm  = servermanager.ProxyManager()
#pxm.GetVersion()
#print("--|| NEK :: USING PARAVIEW VERSION",pxm)


caseName	= sys.argv[1]
model		= sys.argv[2]
nu		= float(sys.argv[3])
dim		= sys.argv[4]
geom		= sys.argv[5]

zDec = 6; xDec = 6
casePath = os.getcwd()

#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

print("--|| NEK :: READING NEK5000 ARRAYS")
startTime = time.time()

fileName1 = 'avg'+caseName+'.nek5000'
fileName2 = 'rms'+caseName+'.nek5000'
fileName3 = 'rm2'+caseName+'.nek5000'

case1 = OpenDataFile(fileName1)
case1.PointArrays = ['velocity','pressure']
case1.UpdatePipeline()

## create a new 'Programmable Filter and change names'
print("--|| NEK: CHANGING VARNAMES 1 USING A PROGRAMMABLE FILTER")
startTime = time.time()
case1 = ProgrammableFilter(Input=case1)
case1.Script = \
"""
import numpy as np
varNames0 = ['velocity','pressure']
varNames1 = ['AVVEL','AVPRE']
for (i,var) in enumerate(varNames0):
 outName = varNames1[i]
 avg = (inputs[0].PointData[var])
 output.PointData.append(avg,outName)
"""
case1.UpdatePipeline()
print("--|| NEK :: DONE. TIME =",time.time()-startTime,'sec')
case2 = OpenDataFile(fileName2)
case2.PointArrays = ['velocity','pressure']
case2.UpdatePipeline()

## create a new 'Programmable Filter and change names'
print("--|| NEK: CHANGING VARNAMES 2 USING A PROGRAMMABLE FILTER")
startTime = time.time()
case2 = ProgrammableFilter(Input=case2)
case2.Script = \
"""
import numpy as np
varNames0 = ['velocity','pressure']
varNames1 = ['AVVE2','AVPR2']
for (i,var) in enumerate(varNames0):
 outName = varNames1[i]
 avg = (inputs[0].PointData[var])
 output.PointData.append(avg,outName)
"""
case2.UpdatePipeline()
print("--|| NEK :: DONE. TIME =",time.time()-startTime,'sec')
case3 = OpenDataFile(fileName3)
case3.PointArrays = ['velocity']
case3.UpdatePipeline()

## create a new 'Programmable Filter and change names'
print("--|| NEK: CHANGING VARNAMES 3 USING A PROGRAMMABLE FILTER")
startTime = time.time()
case3 = ProgrammableFilter(Input=case3)
case3.Script = \
"""
import numpy as np
varNames0 = ['velocity']
varNames1 = ['AVVXY']
for (i,var) in enumerate(varNames0):
 outName = varNames1[i]
 avg = (inputs[0].PointData[var])
 output.PointData.append(avg,outName)
"""
case3.UpdatePipeline()
print("--|| NEK :: DONE. TIME =",time.time()-startTime,'sec')
print("--|| NEK: APPEND DATASETS")
startTime = time.time()
case = AppendAttributes(Input=[case1,case2,case3])
case.UpdatePipeline()
print("--|| NEK :: DONE. TIME =",time.time()-startTime,'sec')


print("--|| NEK :: TEMPORAL AVERAGING  NEK-AVERAGED ARRAYS")
startTime = time.time()
case = TemporalStatistics(Input=case)

# Properties modified on temporalStatistics1
case.ComputeMinimum = 0
case.ComputeMaximum = 0
case.ComputeStandardDeviation = 0
case.UpdatePipeline()

print("--|| NEK :: DONE. TIME =",time.time()-startTime,'sec')
## create a new 'Programmable Filter and change names'
print("--|| NEK: CHANGING VARIABLE NAMES USING A PROGRAMMABLE FILTER")
startTime = time.time()
case = ProgrammableFilter(Input=case)
case.Script = \
"""
import numpy as np
varNames = inputs[0].PointData.keys()
print("----|| Alya :: ALL 3D ARRAYS --> ",varNames)
for var in varNames:
 outName = str(var[0:5])
 avg = (inputs[0].PointData[var])
 output.PointData.append(avg,outName)
"""
case.UpdatePipeline()
print("--|| NEK: DONE. TIME =",time.time()-startTime,'sec')

Ntotal = int(case.GetDataInformation().GetNumberOfPoints())
print("----|| ALYA :: WORKING WITH ",Ntotal," TOTAL NUMBER OF POINTS")

caseVarNames = case.PointData.keys()
indU = int([i for i, s in enumerate(caseVarNames) if 'AVVEL' in s][0]);
indP = int([i for i, s in enumerate(caseVarNames) if 'AVPRE' in s][0]);
indXX = int([i for i, s in enumerate(caseVarNames) if 'AVVE2' in s][0]);
indXY = int([i for i, s in enumerate(caseVarNames) if 'AVVXY' in s][0]);
print("--|| NEK :: CALCULATING R-STRESSES")
startTime = time.time()
# CALCULATE RStresses
CAL1 = Calculator(Input=case)
CAL1.ResultArrayName = "RS_II"
CAL1.Function = "%s - %s_%s*%s_%s*iHat - %s_%s*%s_%s*jHat - %s_%s*%s_%s*kHat" \
                % (caseVarNames[indXX],caseVarNames[indU],'X',caseVarNames[indU],'X',\
                  caseVarNames[indU],'Y',caseVarNames[indU],'Y',\
                 caseVarNames[indU],'Z',caseVarNames[indU],'Z')
CAL1.UpdatePipeline() 
CAL1 = Calculator(Input=CAL1)
CAL1.ResultArrayName = "RS_IJ"
CAL1.Function = "%s - %s_%s*%s_%s*iHat - %s_%s*%s_%s*jHat - %s_%s*%s_%s*kHat" \
                % (caseVarNames[indXY],caseVarNames[indU],'X',caseVarNames[indU],'Y',\
                  caseVarNames[indU],'Y',caseVarNames[indU],'Z',\
                  caseVarNames[indU],'X',caseVarNames[indU],'Z')
CAL1.UpdatePipeline()
print("--|| NEK :: DONE. TIME =",time.time()-startTime,'sec')
# GRADIENT CALC
print("--|| NEK :: CALCULATING PRESS GRADIENT")
startTime = time.time()
CAL1 = GradientOfUnstructuredDataSet(Input=CAL1)
CAL1.ScalarArray = ['POINTS', caseVarNames[indP]]
CAL1.ComputeGradient = 1
CAL1.ResultArrayName = 'AVPGR'
CAL1.ComputeVorticity = 0
CAL1.VorticityArrayName = 'OMEGA'
CAL1.ComputeQCriterion = 0
CAL1.QCriterionArrayName = 'QCRIT'
CAL1.UpdatePipeline()
print("--|| NEK :: DONE. TIME =",time.time()-startTime,'sec')

print("--|| NEK :: CALCULATING AVVEL GRADIENT, Q AND VORTICITY")
startTime = time.time()
CAL1 = GradientOfUnstructuredDataSet(Input=CAL1)
CAL1.ScalarArray = ['POINTS', caseVarNames[indU]]
CAL1.ComputeGradient = 1
CAL1.ResultArrayName = 'AVVGR'
CAL1.ComputeVorticity = 1
CAL1.VorticityArrayName = 'OMEGA'
CAL1.ComputeQCriterion = 1
CAL1.QCriterionArrayName = 'QCRIT'
CAL1.UpdatePipeline()
print("--|| NEK :: DONE. TIME =",time.time()-startTime,'sec')
## CALCULATE LAMBDA2
#print("--|| NEK :: CALCULATING LAMBDA")
#startTime = time.time()
#CAL1 = PythonCalculator(Input=CAL1)
#CAL1.ArrayName = "LAMDA"
#CAL1.Expression = "eigenvalue(strain(%s)**2 + (AVVGR - strain(%s))**2)"% (caseVarNames[indU],caseVarNames[indU])
#CAL1.UpdatePipeline()
#print("--|| NEK :: DONE. TIME =",time.time()-startTime,'sec')

########### 3D STATISTICS ###################
if('3D' in dim):
 # Save a 3D time averaged file
 savePath = casePath+"/AvgData_3D.vtm"
 SaveData(savePath, proxy=CAL1)
 print("----|| NEK: 3D STATISTICS FILE WRITTEN ")
################################################ 

print("--|| NEK :: EVALUATING DIMENSIONS FOR SPANWISE AVERAGE")
startTime = time.time()

(xmin,xmax,ymin,ymax,zmin,zmax) =  case.GetDataInformation().GetBounds()

if("DFUSER" in geom):
  
  slice1 = Slice(Input=CAL1)
  slice1.SliceType = 'Plane'
  slice1.SliceOffsetValues = [0.0]
  ## init the 'Plane' selected for 'SliceType'
  slice1.SliceType.Origin = [0.0, 0.0, 0.0]
  ## Properties modified on slice1.SliceType
  slice1.SliceType.Normal = [1.0, 0.0, 0.0]
  slice1.UpdatePipeline()
  #------------------------------#
  slice1 = Clip(Input=slice1)
  slice1.ClipType = 'Plane'
  slice1.ClipType.Origin = [0.0, 0.0, 0.0]
  slice1.ClipType.Normal = [0.0, 1.0, 0.0]
  slice1.UpdatePipeline()

  Nplane = int(slice1.GetDataInformation().GetNumberOfPoints())
  print("----|| ALYA :: WORKING WITH ",Nplane," PLANAR POINTS")
  
  N = int(Ntotal/Nplane)
  thMax = 2.0*np.pi; thMin = 0.0;
  thMid = np.pi/2
  zpos = np.arange(N)*(thMax-thMin)/(N-1)
  print("----|| ALYA: WORKING WITH %d THETA-PLANES" % (len(zpos)))
  print("----|| ALYA: DELTA-THETA = %f" % ((thMax-thMin)/(N-1)))
  print("--|| ALYA :: DONE. TIME =",time.time()-startTime,'sec')

else:
  slice1 = Slice(Input=CAL1)
  slice1.SliceType = 'Plane'
  slice1.SliceOffsetValues = [0.0]
  slice1.SliceType.Origin = [(xmin+xmax)/2, (ymin+ymax)/2, (zmin+zmax)/2]
  slice1.SliceType.Normal = [0.0, 0.0, 1.0]
  slice1.UpdatePipeline()
  
  Nplane = int(slice1.GetDataInformation().GetNumberOfPoints())
  print("----|| ALYA :: WORKING WITH ",Nplane," PLANAR POINTS")
  
  N = int(Ntotal/Nplane)
  zmid = (zmin+zmax)/2
  zpos = np.around(np.asarray(np.arange(N)*(zmax-zmin)/(N-1),dtype=np.double),decimals=zDec)
  delta_z = (zmax-zmin)/(N-1)
  print("----|| ALYA: WORKING WITH %d Z-PLANES" % (len(zpos)))
  print("----|| ALYA: DELTA-Z = %f" % (delta_z))
  print("--|| ALYA :: DONE. TIME =",time.time()-startTime,'sec')

########### PERFORM AVERAGING ################
print("--|| NEK :: CREATING TRANSFORMATIONS")
startTime = time.time()
resample_transforms=list();
data=list();

for i in range(N):
	# create a new 'Transform'
	transform1 = Transform(Input=slice1,guiName="transform{}".format(i))
	# Properties modified on transform1.Transform
	if("DFUSER" in geom):
	  transform1.Transform.Rotate = [0.0, 0.0, zpos[i]-thMid]
	else:
	  transform1.Transform.Translate = [0.0, 0.0, zpos[i]-zmid]
	#resampleWithDataset1 = ResampleWithDataset(Input=CAL1,Source=transform1)
	resampleWithDataset1 = ResampleWithDataset(SourceDataArrays=CAL1,DestinationMesh=transform1)
	resample_transforms.append(resampleWithDataset1)
print("--|| NEK: TRANSFORMATION DONE. TIME =",time.time()-startTime,'sec')
HideAll()


## create a new 'Programmable Filter'
print("--|| NEK: AVERAGING USING A PROGRAMMABLE FILTER")
startTime = time.time()

PF1 = ProgrammableFilter(Input=[slice1]+resample_transforms)
### first input is the grid
### the rest of them are data to be averaged
PF1.Script = \
"""
#from vtk.numpy_interface import dataset_adapter as dsa
#from vtk.numpy_interface import algorithms as algs
import numpy as np

varFull = []
varFull = inputs[0].PointData.keys()
print("----|| Alya - WORKING ON ARRAYS::",varFull)
N=len(inputs)-1;
print("--|| NEK: AVERAGING %d DATA-PLANES" % (N))

for varName in varFull:
   varName0=varName[0:5]
   avg = 0.0*(inputs[0].PointData[varName])
   for i in range(N):
       d = inputs[i+1].PointData[varName]
       avg = avg + d
   avg = avg/N
   output.PointData.append(avg,varName0)
"""
PF1.UpdatePipeline()
print("--|| NEK: SPANWISE AVERAGING DONE. TIME =",time.time()-startTime,'sec')

if('2D' in dim):
  #if("DFUSER" in geom):
  #  # Convert the plane (x,y,z) to (z,r,th) plane
  #  PF1 = Calculator(Input=PF1)
  #  PF1.ResultArrayName = "result"
  #  PF1.CoordinateResults = 1
  #  PF1.Function = "coordsZ*iHat + sqrt(coordsX^2+coordsY^2)*jHat"
  #  PF1.UpdatePipeline()
  savePath = casePath+"/AvgData_2D.vtm"
  SaveData(savePath, proxy=PF1)
  savePath = casePath+"/AvgData_2D.csv"
  SaveData(savePath, proxy=PF1)
  print("----|| NEK: 2D STATISTICS FILE WRITTEN AS: ",savePath)

  ########### STREAMWISE AVERAGING ################
if('1D' in dim):
  print("--|| ALYA :: GENERATING SLICE FOR STREAMWISE AVERAGE")
  slice1 = Slice(Input=PF1)
  slice1.SliceType = 'Plane'
  slice1.SliceOffsetValues = [0.0]
  ## init the 'Plane' selected for 'SliceType'
  slice1.SliceType.Origin = [(xmin+xmax)/2, (ymin+ymax)/2, (zmin+zmax)/2]
  ## Properties modified on slice1.SliceType
  if("DFUSER" in geom):
    slice1.SliceType.Normal = [0.0, 0.0, 1.0]
  else:
    slice1.SliceType.Normal = [1.0, 0.0, 0.0]
  slice1.UpdatePipeline()
  
  Ny = int(slice1.GetDataInformation().GetNumberOfPoints())
  print("----|| ALYA :: WORKING WITH ",Ny," PLANAR POINTS")

  N = int(Nplane/Ny)
  if("DFUSER" in geom):
    xmid = (zmin+zmax)/2
    xpos = np.around(np.asarray(np.arange(N)*(zmax-zmin)/(N-1),dtype=np.double),decimals=zDec)
  else:  
    xmid = (xmin+xmax)/2
    xpos = np.around(np.asarray(np.arange(N)*(xmax-xmin)/(N-1),dtype=np.double),decimals=xDec)
  print("----|| ALYA: WORKING WITH %d X-PLANES" % (len(xpos)))
  print("----|| ALYA: DELTA-X = %f" % ((np.amax(xpos)-np.amin(xpos))/(N-1)))
  print("--|| ALYA :: DONE. TIME =",time.time()-startTime,'sec')
  
  print("--|| NEK: CREATING X TRANSFORMATIONS")
  resample_transforms=list();
  data=list();
  
  startTime = time.time()
  for i in range(N):
  	# create a new 'Transform'
  	transform1 = Transform(Input=slice1,guiName="transform{}".format(i))
  	# Properties modified on transform1.Transform
  	if("DFUSER" in geom):
  	  transform1.Transform.Translate = [0.0, 0.0, xpos[i]-xmid]  
  	else:  
  	  transform1.Transform.Translate = [xpos[i]-xmid, 0.0, 0.0]  
  	#resampleWithDataset1=ResampleWithDataset(Input=PF1,Source=transform1)
  	resampleWithDataset1 = ResampleWithDataset(SourceDataArrays=PF1,DestinationMesh=transform1)
  	resample_transforms.append(resampleWithDataset1)
  print("--|| NEK: TRANSFORMATION DONE. TIME =",time.time()-startTime,'sec')
  HideAll()
  
  ## create a new 'Programmable Filter'
  print("--|| NEK: X AVERAGING USING A PROGRAMMABLE FILTER")
  startTime = time.time()
  PF1 = ProgrammableFilter(Input=[slice1]+resample_transforms)
  ### first input is the grid
  ### the rest of them are data to be averaged
  PF1.Script = \
  """
  import numpy as np

  varFull = inputs[0].PointData.keys()
  print("----|| ST AVG INFO : WORKING ON ",varFull)
  N=len(inputs);
  for varName in varFull:
     avg = 0.0*(inputs[0].PointData[varName])
     for i in range(N):
         d = inputs[i+1].PointData[varName]
         avg = avg + d
     avg = avg/N
     output.PointData.append(avg,varName)
  """
  PF1.UpdatePipeline()
  print("--|| NEK: STREAMWISE AVERAGING DONE. TIME =",time.time()-startTime,'sec')
  
  #### write
  print("--|| NEK: SAVING THE AVERAGED FILES")
  startTime = time.time()
  savePath = casePath+"/AvgData_1D.vtm"
  SaveData(savePath, proxy=PF1)
  savePath = casePath+"/AvgData_1D.csv"
  SaveData(savePath, proxy=PF1)
  print("----|| NEK: 1D STATISTICS FILE WRITTEN AS: ",savePath)
  print("--|| NEK: FILE SAVED. TIME =",time.time()-startTime,'sec')
