import xml.etree.cElementTree as ET
import pprint

def count_tags(filename):
    '''
    Return a dictionary with tag name as key and number of times key can be found in map as
    value.
    '''
    tags = {}
    
    for event, elem in ET.iterparse(filename):
        if elem.tag in tags.keys():
            tags[elem.tag] += 1
        elif elem.tag not in tags.keys():
            tags[elem.tag] = 1
    
    return tags

northeast_atlanta_tags = count_tags("sample_k12.osm")
pprint.pprint(northeast_atlanta_tags)