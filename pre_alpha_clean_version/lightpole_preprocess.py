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

for ilat in range(10):
	for ilon in range(6):
		path = "/data/songtao/roadtagger-1/pre_alpha_clean_version/dataset/la/region_%d_%d" % (ilat, ilon)
		print(path)
		cfg = json.load(open(path+"/config.json","r"))
		region = cfg["region"]


		roadnetwork = pickle.load(open(path+"/roadnetwork.p","r"))

		jsongraph = {}
		jsongraph["nodes"] = []
		jsongraph["edges"] = []
		jsongraph["nodelabels"] = []

		node_idx = index.Index()

		cc = 0
		for nid in range(roadnetwork.node_num):
			loc = roadnetwork.nid2loc[nid]
			loc = [loc[0]/111111.0, loc[1]/111111.0]
			
			r = 0.000001 

			node_idx.insert(cc, (loc[0]-r, loc[1]-r,loc[0]+r, loc[1]+r))


			#r_lat = 0.00010
			#r_lon = 0.00010 / math.cos(math.radians(33))
			#neighbors = list(lights_idx.intersection((loc[0]-r_lat, loc[1]-r_lon, loc[0]+r_lat, loc[1]+r_lon)))

			jsongraph["nodes"].append(loc)
			jsongraph["nodelabels"].append([0])
			cc += 1

		for edge in roadnetwork.edges:
			jsongraph["edges"].append(edge)


		print("lights in region", len(list(lights_idx.intersection(region))))
		
		for light_loc in list(lights_idx.intersection(region)):
			r_lat = 0.00100
			r_lon = 0.00100 / math.cos(math.radians(33))

			best_node = None 
			best_d = 10000 

			loc = lights[light_loc]

			for candidate_node in list(node_idx.intersection((loc[0]-r_lat, loc[1]-r_lon, loc[0]+r_lat, loc[1]+r_lon))):
				d = gps_distance(jsongraph["nodes"][candidate_node], loc)

				if d < best_d or best_node is None :
					best_node = candidate_node
					best_d = d 

			if best_node is not None:
				jsongraph["nodelabels"][best_node][0] = 1 


		json.dump(jsongraph, open(path+"/graph.json","w"))

		img = cv2.imread(path+"/sat_16384.png")
		img = cv2.resize(img,  None, fx=0.25,fy=0.25)
		cv2.imwrite(path+"/sat_4096.png", img)

		# draw the map 

		for edge in jsongraph["edges"]:
			loc0 = jsongraph["nodes"][edge[0]]
			loc1 = jsongraph["nodes"][edge[1]]

			x0,y0 = get_image_coordinate(loc0[0], loc0[1], 4096,region)
			x1,y1 = get_image_coordinate(loc1[0], loc1[1], 4096,region)

			cv2.line(img, (y0,x0), (y1,x1), (0,255,255),2)
		

		for items in zip(jsongraph["nodes"], jsongraph["nodelabels"]):
			loc0 = items[0] 
			x0,y0 = get_image_coordinate(loc0[0], loc0[1], 4096,region)
			
			if items[1][0] == 0:
				color = (0,255,255)
			else:
				color = (0,255,0)

			cv2.circle(img, (y0,x0), 5, color, -1)


		for light_loc in list(lights_idx.intersection(region)):
			loc0 = lights[light_loc]
			x0,y0 = get_image_coordinate(loc0[0], loc0[1], 4096,region)
			cv2.circle(img, (y0,x0), 3, (0,0,255), -1)



		cv2.imwrite(path+"/graph_label_vis.png", img)





