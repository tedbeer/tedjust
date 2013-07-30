tedjust
=======

**tedjust** is python 3 script to tweek G-code files. It can adjust flow rate/printing speed for some layer(s) and can be used for post-processing after slicing.

Created by Eduard Bespalov AKA tedbeer (edwbes@gmail.com), 2013

**License:** CC BY-SA (Creative Commons Attribution-ShareAlike)
	http://creativecommons.org/licenses/by-sa/3.0

**In what cases it can be usefull:**
 * modify flow rate for the first level(s) to improve stickness, to compensate rough bed
 * modify speed/flow rate for bridge layer if slicer can't do it
 * increase printing speed for layers where model is simple
 * decrease printing speed for layers where precision is important

**Usage:** python tedjust.py filename.gcode layer_tweak layer_tweak [layer_tweak layer_tweak ...]

filename.ted.gcode will be created with required tweaks

**Parameters**
------------
Specifing layers:
 * L3.5 - layer at 3.5mm
 * L3.5-5 - layers between 3.5-5mm including borders
 * L3.5+ - layer at 3.5mm and all layers above
 
Specifing tweaks:
 * F1.1 - flow tweak - increase extruding in 1.1 times
 * S30 - change extruding speed to 30mm/sec

It does not modify suck/prime/move speed, only speed while extruding.  
It does not tweak flow while suck/prime.  
It uses the same speed for both - perimeter and infill.  
Multiple layers/tweaks can be specified.

**Examples:**
 * L0.25 F1.1  
 	increase flow rate to 1.1 for layer at 0.25 mm
 * L0.25+ F0.95  
	set flow rate 0.95 for layers after 0.25mm (including 0.25)
 * L0.25 F1.1 S11.5  
 	increase flow rate to 1.1 and set moving speed while extruding to 11.5mm/s for layer 0.25 mm
 * L0 F1.1 L10+ S100 L15.25-15.75 F1.1 S30   
	change flow rate for the first layer,  
	increase printing speed to 100mm/s after 10mm  
	change flow rate and speed to print bridge (layers between 15.25-15.75)
