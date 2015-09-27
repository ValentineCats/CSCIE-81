import matplotlib.pyplot as plt
from sys import argv
from os import listdir, remove
from os.path import isfile, join
import numbers
import numpy as np
import scipy as sp
from scipy.stats import f


conversions = {'a':0, 'b':1, 'c':2, 'd':3,'e':4}
window = 5
baselineSize = 50
#Currently using the standard .05 alpha level, which gives us a
#high degree of confidence that a change is valid
#We are dividing by 2 for the two tailed test
confidence = .95
alphaVar = (1-confidence) / 2
  



#This cleaning function strips out any extra whitespace, 
#converts any letters to numbers (see paper for explanation),
#and converts all string objects to floats for calculation
def safeGet(fileObj):
	line = fileObj.readline().strip()
	if line == "":
		return line
	global conversions
	if line in conversions:
		line = conversions[line]
	return float(line)



#Takes as arguments a file object and a dict of 
#baseline measurements (std deviation, mean, see usage below)
#gets the next window of samples and determines if they 
#are acceptably close to the measurements given
#If the next "window" of samples is within range, a False is returned,
#if they are outside range, True is returned (it is up to the caller to
#keep track of which line in the file has been reached, based on the 
#global "window" variable)
#If the end of the file is reached, the file object is set to 
#None, so it is easy for the caller to tell if the end of the
#file has been reached or not
def getWindow(fileCon, measurements):
	global window
	global alphaVar
	global baselineSize
	
	buffered = []
	for i in range(window):
		line = safeGet(fileCon)
		if line == "":
			raise EOFError("No samples, or too few samples in file")
		buffered.append(line)
	windowMeas = {'stdDev':np.std(buffered), 'mean':np.mean(buffered), 'var':np.var(buffered), 'sem':sp.stats.sem(buffered, ddof=0)}
	
	#A variance of 0 means we can't perform the F-test
	if(windowMeas['var'] != 0):
		FValue = windowMeas['var'] / measurements['var']
		upperVal = sp.stats.f.isf(alphaVar, window, baselineSize)
		lowerVal = sp.stats.f.ppf(alphaVar, window, baselineSize)
		
		if  FValue < lowerVal or FValue > upperVal:
			print("Variance ", end = "")
			return True
	#Since the baseline variance is 0 that means finding any variance at all is a change in variance  
	else:
		if windowMeas['var'] > 0:
			print("Variance ", end = "")
			return True 


	#Calculate confidence in the mean
	stdErrDiff = sp.sqrt(windowMeas['sem']**2+measurements['sem']**2)
	meanInterval = sp.stats.norm.interval(confidence)*stdErrDiff
	print(meanInterval)
	

	#Calculate cumulative probability density
	#Now that we have the necessary data measurements, we can compare them
	if windowMeas['stdDev'] > measurements['stdDev']*1.2:
		print("Mean ", end="")
		return True



directory = argv[1]
if isfile('output.txt'):
	remove('output.txt')
output = open('output.txt', 'a')
output.truncate()
files = [ f for f in listdir(directory) if isfile(join(directory,f)) ]
#Get each file in the provided directory
for txtFile in files:
	print(txtFile)
	outputLine = txtFile+'\t'
	#TESTING
	fileCon = open(directory+'/'+txtFile, 'r')
	allData = []
	line = safeGet(fileCon)
	while line != "":
		allData.append(line)
		line = safeGet(fileCon)
	plt.plot(allData)
	plt.show()
	fileCon.close()
	#TESTING

	fileCon = open(directory+'/'+txtFile, 'r')
	baseline = []
	#We are assuming, given the assignment guidelines, that the first
	#50 samples can be used for baseline measurements
	for i in range(baselineSize+1):
		line = safeGet(fileCon)
		baseline.append(line)

	#added variance to measurements
	measurements = {'mean':np.mean(baseline), 'stdDev':np.std(baseline), 'var':np.var(baseline), 'sem':sp.stats.sem(baseline, ddof=0)}
	
	#scale = measurements['stdDev']/sp.sqrt(baselineSize)
	#interval = stats.norm.interval(confidence, loc=measurements['mean'], scale=scale)
	#measurements.append['interval':interval]
	lineCount = baselineSize
	try:
		while not getWindow(fileCon, measurements):
			lineCount += window
		print("change found on line "+str(lineCount))
		outputLine += str(lineCount)+'\n'
	except EOFError:
		print("No changes found in file")
		outputLine += '-1\n'

	output.write(outputLine)
	fileCon.close()

output.close()
