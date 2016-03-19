import pickle
import json
import csv

LOCAL_EVENTS = {"OGLE-2016-BLG-0229": {"tE_OGLE": "4.8"}, "OGLE-2016-BLG-0220": {"tE_OGLE": "3.4"}, \
				   "OGLE-2016-BLG-0197": {"tE_OGLE": "4.9"}, "OGLE-2016-BLG-0118": {"tE_OGLE": "3.2"}}


def save_obj_pickle(obj, name ):
    with open('obj/'+ name + '.pkl', 'w') as f:
        pickle.dump(obj, f, 0)

def load_obj_pickle(name ):
    with open('obj/' + name + '.pkl', 'r') as f:
        return pickle.load(f)

def save_obj_csv(dictionary, filepath):
	with open(filepath, "w") as f:
		w = csv.writer(f)
		for key, val in dictionary.items():
			w.writerow([key, val])

def load_obj_csv(filepath):
	dictionary = {}
	with open(filepath, "r") as f:
		csvReader = csv.reader(f)
		for key, val in csvReader:
			dictionary[key] = val
	return dictionary

def pickleTest():
	print "Old:"
	print LOCAL_EVENTS
	print

	print "Pickle test:"
	filename = "localEvents"
	save_obj_pickle(LOCAL_EVENTS, filename)
	print "New:"
	print load_obj_pickle(filename)
	print "-----------------------------------"

def jsonTest():
	print "JSON test:"
	print "Old:"
	print LOCAL_EVENTS
	print

	filepath = "obj/localEvents.txt"
	with open(filepath, "w") as f:
		json.dump(LOCAL_EVENTS, f)
	with open(filepath, "r") as f:
		localEvents2 = json.load(f)	
	print "New:"
	print localEvents2
	print "-----------------------------------"

def csvTest():
	print "CSV test:"
	print "Old:"
	print LOCAL_EVENTS
	print

	save_obj_csv(LOCAL_EVENTS, "obj/localEvents.csv")
	print "New:"
	print load_obj_csv("obj/localEvents.csv")
	print "-----------------------------------"


def main():
	pickleTest()
	jsonTest()
	csvTest()
	
if __name__ == "__main__":
	main()
