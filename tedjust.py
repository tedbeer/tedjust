#! /usr/bin/python
#coding=utf-8
"""
	Adjust flow tweak/speed for some layer(s)
	by Eduard Bespalov AKA tedbeer (edwbes@gmail.com), 2013

	License: CC BY-SA (Creative Commons Attribution-ShareAlike)
		http://creativecommons.org/licenses/by-sa/3.0

	Usage: python tedjust.py filename.gcode layer_tweak layer_tweak ...

	filename.ted.gcode will be created having required tweaks

	Layers and tweaks:
		L3.5 - layer at 3.5mm
		L3.5-5 - layers between 3.5-5mm including borders
		L3.5+ - layer at 3.5mm and all layers above
		F1.1 - flow tweak - increase extruding in 1.1 times
		S30 - change extruding speed to 30mm/sec

	It does not modify suck/prime/move speed, only speed while extruding.
	It does not tweak flow while suck/prime.
	It uses the same speed for both - perimeter and infill.

	Examples:
		L0.25 F1.1 - increase flow rate to 1.1 for layer at 0.25 mm
		L0.25+ F0.95 - set flow rate 0.95 for layers after 0.25mm (including 0.25)

		L0.25 F1.1 S11.5
			increase flow rate to 1.1 and 
			set moving speed while extruding to 11.5mm/s for layer 0.25 mm

		L0 F1.1 L10+ S100 L15.25-15.75 F1.1 S30
			change flow rate for the first layer,
			increase printing speed to 100mm/s after 10mm
			change flow rate and speed to print bridge (layers between 15.25-15.75)
"""

import sys, os, math

flOut = None #
prev = (0.0, 0.0, 0.0, 0.0) # previous position
cur = (0.0, 0.0, 0.0, 0.0) # current position
prevSpeed = curSpeed = 0 # previous and current speed from g-code

layers = [] #configuration - Array of tuples (startLayer, endLayer, flow, speed)

# updates global prev, cur positions and velocity
# returns True if it's a 'move' command
def extractMove(line):
	global prev, cur, curSpeed

	arr = line.split()
	x = cur[0]
	y = cur[1]
	z = cur[2]
	e = cur[3]

	if line.startswith('G1'): #move command
		for chunk_ in arr:
			if chunk_.startswith('G1'): #moving/extruding
				prev = cur
			elif chunk_.startswith('X'):
				try:
					x = float(chunk_[1:])
				except:
					pass
			elif chunk_.startswith('Y'):
				try:
					y = float(chunk_[1:])
				except:
					pass
			elif chunk_.startswith('Z'):
				try:
					z = float(chunk_[1:])
				except:
					pass
			elif chunk_.startswith('E'):
				try:
					e = float(chunk_[1:])
				except:
					pass
			elif chunk_.startswith('F'):
				try:
					prevSpeed = curSpeed
					curSpeed = int(chunk_[1:])
				except:
					pass
		cur = (x, y, z, e)
		return True
	elif line.startswith('G92'): #reset extruding position
		e = cur[3]
		for chunk_ in arr:
			if chunk_.startswith('E'):
				try:
					e = float(chunk_[1:]) #usually it's zero
				except:
					pass
		prev = cur
		cur = (cur[0], cur[1], cur[2], e)
	return False

def parseArgs():
	global layers, flOut
	#create out file
	names = os.path.splitext(sys.argv[1])
	flOut = open(names[0] + '.ted' +  names[1], "w", encoding="utf-8")

	start_ = end_ = -1
	f = 0
	v = 0
	for arg in sys.argv[2:]:
		if arg.startswith('L'): #new layer
			#save prev layer
			if f > 0 or v > 0:
				layers.append((start_, end_, f, v))
			#reset vars
			f = 0
			v = 0
			if arg.find("-") >= 0:
				(ss, se) = arg[1:].split("-", 2)
			elif arg.find("+") >= 0:
				ss = arg[1:-1] #strip L and +
				se = -1 #no limit
			else:
				ss = se = arg[1:] #strip L
			try:
				start_ = float(ss)
				end_ = float(se)
			except:
				pass
		elif arg.startswith('F'): #flow tweak
			try:
				f = float(arg[1:])
			except:
				pass
		elif arg.startswith('S'): #speed
			try:
				v = int(float(arg[1:]) * 60) #convert mm/s => mm/min
			except:
				pass
	if f > 0 or v > 0:
		layers.append((start_, end_, f, v))

def printHead():
	print("; extruding modified by tedjust", file=flOut)
	print("; parameters: " + ' '.join(map(str, sys.argv[2:])), file=flOut)
	print(";", file=flOut)

def formatFloat(f, v):
	return f.format(v).rstrip('0').rstrip('.')

def adjustFile(flname):
	flow = tweakSpeed = 0 #tweak flow and speed
	oldFlow = 0
	curE = 0
	speed = newSpeed = 0 #current speed in resulting g-code
	eSpeed = 0 #move speed and extruding speed may be different while they are the same in g-code
	bSuck = False
	bWait4Prime = False

	with open(flname) as fl:
		printHead()
		for line in fl:
			line = line.strip()
			if extractMove(line): #move
				bWasTweaked = flow != 0 or tweakSpeed != 0
				flow = tweakSpeed = 0
				# if was suck before and extrusion happens
				bPrime = bWait4Prime and cur[3] > prev[3]
				#if destring - no tweaks, until extruding position is back
				bSuck = cur[3] > 0 and cur[3] < prev[3]
				if bSuck:
					bWait4Prime = True

				#suck and prime are without tweaks
				if not bWait4Prime: #not (bSuck or bPrime):
					z = cur[2]
					for i, cfg in enumerate(layers):
						if z >= cfg[0]:
							if (cfg[1] < 0 or z <= cfg[1]):
								# z between layers
								if cfg[2] > 0: flow = cfg[2]
								if cfg[3] > 0: tweakSpeed = cfg[3]
						else: #did not reach changed area
							break

				if flow == 0 and tweakSpeed == 0:
					if bWasTweaked and speed != curSpeed:
						#restore speed from g-code
						print("G1 F{:d}; tedjust restore speed".format(curSpeed), file=flOut)
					if prev[3] != curE:
						print("G92 E{:.4f} ; tedjust restore extruder".format(prev[3]), file=flOut)
					speed = curSpeed
					curE = cur[3]
					print(line, file=flOut)
					if bPrime:
						bWait4Prime = False
				else:
					bMove = False # move hotend

					if flow == 0: #don't modify destring values
						eDelta = cur[3] - prev[3]
					else:
						#avoid rounding error accumulating
						eDelta = round((cur[3] - prev[3]) * flow, 4)
					cmd_ = 'G1' # move g-code
					if cur[0] != prev[0]: #X coord
						cmd_ = cmd_ + formatFloat(' X{:.2f}', cur[0])
						bMove = True

					if cur[1] != prev[1]: #Y coord
						cmd_ = cmd_ + formatFloat(' Y{:.2f}', cur[1])
						bMove = True

					if cur[2] != prev[2]: #Z coord
						cmd_ = cmd_ + formatFloat(' Z{:.2f}', cur[2])
						bMove = True

					# extruding
					if oldFlow != flow:
						oldFlow = flow
						if cur[3] != 0:
							print("G92 E0 ; tedjust reset extruder", file=flOut)
						curE = 0

					bExtruding = eDelta > 0 #it can be negative in a case of destring

					if bExtruding:
						curE = curE + eDelta
						cmd_ = cmd_ + formatFloat(' E{:.4f}', curE)

					#speed
					if curSpeed != prevSpeed:
						if bExtruding: #update extruding speed if it's extruding
							eSpeed = tweakSpeed if tweakSpeed > 0 else curSpeed

					newSpeed = eSpeed if bExtruding else curSpeed

					# change speed on real moves only
					if (bMove or bExtruding) and newSpeed != speed: #change speed
						speed = newSpeed
						cmd_ = cmd_ + ' F%d' % speed

					if len(cmd_) > 2: #not just G1
						print(cmd_, file=flOut)
					# else:
					# 	print(";skip: {}".format(line), file=flOut)
			else:
				print(line, file=flOut) #print line as is, no modification needed
				if cur[3] < prev[3]: curE = cur[3] #G92 FIXME: or suck??

if len(sys.argv) > 2: # script_name file_name parameters
	parseArgs()
	adjustFile(sys.argv[1])
else:
	print("Usage: python tedjust.py file.gcode L0 F1.1 L5.25-5.75 F1.1 S10 L20+ S200")

