import xml.etree.cElementTree as ET

osm_file = open("sample_k12.osm", "r")
remaining_zips = ["1520", "1540"]

def is_postcode(elem):
    """Checks if element attribute is a postcode."""
    return (elem.attrib['k'] == "addr:postcode")

def audit():
    for event, elem in ET.iterparse(osm_file, events=("end",)):
        if (elem.tag == "node") or (elem.tag == "way"):
            for tag in elem.iter("tag"):
                if (is_postcode(tag)) and (tag.attrib['v'] in remaining_zips):
                    for tag in elem.iter("tag"):
                        print("key: " + tag.attrib['k'] + 
                            ", value: " + tag.attrib['v'])

audit()