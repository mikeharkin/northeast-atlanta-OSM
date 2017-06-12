import xml.etree.cElementTree as ET
from collections import defaultdict

osm_file = open("sample_k12.osm", "r")
postcodes = set([])

def is_postcode(elem):
    """Checks if element is considered a postcode in the data."""
    return (elem.attrib['k'] == "addr:postcode")
    
def audit():
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if (elem.tag == 'node') or (elem.tag == 'way'):
            for tag in elem.iter("tag"):
                if is_postcode(tag):
                    postcodes.add(tag.attrib['v']) 
    print postcodes

audit()