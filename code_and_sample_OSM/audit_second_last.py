import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

osm_file = open("sample_k12.osm", "r")

expected_street_types = ["Street", "Avenue", "Boulevard", "Drive", "Court",
    "Place", "Square", "Lane", "Road", "Trail", "Parkway", "Circle"]
atl_quads_abbrevs = ["Northwest", "NW", "N.W.", "Southwest", "S.W.", "SW",
    "Northeast", "NE", "N.E.", "Southeast", "SE", "S.E."]

street_last_word_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
street_second_last_words = defaultdict(set)

def audit_second_last(street_types, street_name):
    """
    If the last word of a street name is a quadrant, look at second-to-last
    word in street name. If second-to-last word is not in expected street types,
    catalog in defaultdict.
    """
    m = street_last_word_re.search(street_name)
    if m:
        split_street_name = street_name.split(" ")
        if split_street_name[-1] in atl_quads_abbrevs:
            second_to_last_word = street_name.split(" ")[-2]
            if second_to_last_word not in expected_street_types:
                street_second_last_words[second_to_last_word].add(street_name)

def is_street_name(elem):
    """Check if element is street name."""
    return (elem.attrib['k'] == "addr:street")

def audit():
    """Use event-based iterative parsing to audit data."""
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "way":
            # iter method returns all specified nested subtags in element
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_second_last(street_second_last_words, tag.attrib['v'])
    pprint.pprint(dict(street_second_last_words))

audit()