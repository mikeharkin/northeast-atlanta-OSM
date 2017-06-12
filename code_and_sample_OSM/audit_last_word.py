import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

osm_file = open("sample_k12.osm", "r")

atl_quads = ["Northeast", "Southeast", "Northwest", "Southwest"]

street_last_word_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
street_last_words = defaultdict(set)

def audit_last_word(street_types, street_name):
    """
    Audit the last word of each street name.
    Find what non-quadrant words appear.
    """
    m = street_last_word_re.search(street_name)
    if m:
        last_word = m.group()
        if last_word not in atl_quads:
            street_last_words[last_word].add(street_name)
    
def is_street_name(elem):
    """Check if element is a street name. Return True or False."""
    return (elem.attrib['k'] == 'addr:street')

def audit():
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_last_word(street_last_words, tag.attrib['v'])
    pprint.pprint(dict(street_last_words))
    
audit()