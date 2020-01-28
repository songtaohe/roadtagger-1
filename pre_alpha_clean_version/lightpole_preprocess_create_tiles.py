import json 
import sys  
from rtree import index
import cv2 
import scipy.ndimage
import scipy.misc
import scipy 
import pickle 
import math 
import roadtagger_road_network

def get_image_coordinate(lat, lon, size, region):
	x = int((region[2]-lat)/(region[2]-region[0])*size)
	y = int((lon-region[1])/(region[3]-region[1])*size)

	return x,y 

def gps_distance(p1,p2):
	x = (p1[0]-p2[0]) * 111111.0 
	y = (p1[1]-p2[1]) * 111111.0 * math.cos(math.radians(p1[0]))

	return math.sqrt(x*x + y*y )


lights = []
lights_idx = index.Index()
cc = 0 

# load dataset 
with open(sys.argv[1],"r") as fin:
	for line in fin.readlines()[1:]:
		items = line.split(",")

		if len(items) < 2:
			continue

		lon = float(items[0])
		lat = float(items[1])
		r = 0.000001 

		lights_idx.insert(cc, (lat-r, lon-r,lat+r, lon+r))
		lights.append((lat,lon))

		cc += 1 

# create annotation 

pool = []
max_processes = 4
prefix = "dataset/la" 

good_regions = []

for ilat in range(10):
	for ilon in range(6):
		path = "/data/songtao/roadtagger-1/pre_alpha_clean_version/dataset/la/region_%d_%d" % (ilat, ilon)
		print(path)
		cfg = json.load(open(path+"/config.json","r"))
		region = cfg["region"]

		number_of_lights = len(list(lights_idx.intersection(region))) 

		print("lights in region", len(list(lights_idx.intersection(region))))
			
		if number_of_lights > 500:
			good_regions.append((ilat, ilon))

			print("number of good regions", len(good_regions))

			while len(pool) == max_processes:
				sleep(1.0)
				new_pool = []
				for p in pool:
					if p.poll() is None:
						new_pool.append(p)

				pool = new_pool

			print("start a new process ",prefix, ilat, ilon)
			pool.append(Popen("python roadtagger_generate_dataset.py tiles %s/region_%d_%d/config.json" % (prefix, ilat,ilon), shell=True))
          

for p in pool:
	p.wait()


json.dump(good_regions, open("good_regions_for_light.json","w"))



