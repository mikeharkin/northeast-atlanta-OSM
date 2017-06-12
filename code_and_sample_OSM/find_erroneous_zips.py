import xml.etree.cElementTree as ET
import pprint
from collections import defaultdict

osm_file = open("sample_k12.osm", "r")
erroneous_zips = ["300313", "1520", "1540"]
problem_elements = defaultdict(set)

def is_postcode(elem):
    """Checks if element attribute is a postcode."""
    return (elem.attrib['k'] == "addr:postcode")

def is_name(elem):
    """Checks if element attribute is a name."""
    return (elem.attrib['k'] == "name")

def audit():
    for event, elem in ET.iterparse(osm_file, events=("end",)):
        if (elem.tag == "node") or (elem.tag == "way"):
            for tag in elem.iter("tag"):
                if (is_postcode(tag)) and (tag.attrib['v'] in erroneous_zips):
                    zip_code = tag.attrib['v']
                    for tag in elem.iter("tag"):
                        if (is_name(tag)):
                            problem_elements[zip_code].add(tag.attrib['v'])
    pprint.pprint(problem_elements)

audit()