import sys 
import json  

regions = json.load(open(sys.argv[1],"r"))
prefix = sys.argv[2]

result = []

for region in regions:
	s = prefix + "/region_%d_%d/" % (region[0], region[1])

	result.append(s)

json.dump(result,open("tmp.json","w"), indent=2)