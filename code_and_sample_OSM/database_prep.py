import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema

OSM_PATH = "sample_k12.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "node_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

# Lists and mappings for helper functions
cardinal_directions_abbrevs = ["N", "N.", "E", "E.", "W", "W.", "S", "S."]
atl_quadrants = ["Northeast", "Southeast", "Northwest", "Southwest"]
expected_street_types = ["Street", "Avenue", "Boulevard", "Drive", "Court",
    "Place", "Square", "Lane", "Road", "Trail", "Parkway", "Circle", "Row",
    "Promenade", "Way"]
atl_quads_abbrevs = ["NW", "N.W.", "SW", "S.W.", "NE", "N.E.", "SE", "S.E."]
mapping = {"St": "Street", "St.": "Street", "Ave": "Avenue", "Ave.": 
    "Avenue", "Blvd": "Boulevard", "Blvd.": "Boulevard", "Dr": "Drive", "Dr.":
    "Drive", "Ct": "Court", "Ct.": "Court", "Pl": "Place", "Pl.": "Place", "Sq":
    "Square", "Sq.": "Square", "Ln": "Lane", "Ln.": "Lane", "Rd": "Road", "Rd.":
    "Road", "Tr": "Trail", "Tr.": "Trail", "Pkwy": "Parkway", "Pkwy.":
    "Parkway", "Cir": "Circle", "Cir.": "Circle", "NE": "Northeast", 
    "N.E.": "Northeast", "SE": "Southeast", "S.E.": "Southeast", 
    "NW": "Northwest", "N.W.": "Northwest", "SW": "Southwest", 
    "S.W.": "Southwest", "N": "North", "N.": "North", "S": "South", 
    "S.": "South", "E": "East", "E.": "East", "W": "West", "W.": "West"}
zip_mapping = {"30033-5367": "30033", "GA 30307": "30307", "GA 30309": "30309",
    "30030-3807": "30030", "30303-3506": "30303", "30308-3217": "30308", 
    "30313-1591": "30313", "300313": "30313", "1520": "30329", "1540": "30329"}

def is_street_name(elem):
    """Check if element is street name."""
    return (elem.attrib['k'] == "addr:street")

def is_postcode(elem):
    """Check if element is postcode."""
    return (elem.attrib['k'] == "addr:postcode")

def update_street_name(street_name, mapping):
    """Fix a street name in the NE Atlanta dataset to fit conventions."""
    split_street = street_name.split(" ")
    # Look at first word of street name. If it is an abbreviation of a cardinal
    #   direction, change it to the full word.
    if split_street[0] in cardinal_directions_abbrevs:
        fixed_cardinal = mapping[split_street[0]]
        del split_street[0]
        split_street.insert(0, fixed_cardinal)
    # If last word of street name is quadrant spelled out, look at
    #   second-to-last word and spell it out if it is an abbreviation of a
    #   street type
    if split_street[-1] in atl_quadrants:
        if split_street[-2] not in expected_street_types:
            if split_street[-2] in mapping.keys():
                fixed_second_last = mapping[split_street[-2]]
                del split_street[-2]
                split_street.insert(-1, fixed_second_last)
    # If the last word is an abbreviated quadrant, change it to spelled-out 
    #   quadrant name. Then look at second-to-last word and spell it out if
    #   it is an abbreviation of a street type. 
    elif split_street[-1] not in atl_quadrants:
        if split_street[-1] in atl_quads_abbrevs:
            fixed_quad_abbrev = mapping[split_street[-1]]
            del split_street[-1]
            split_street.append(fixed_quad_abbrev)
            if split_street[-2] not in expected_street_types:
                if split_street[-2] in mapping.keys():
                    fixed_second_last = mapping[split_street[-2]]
                    del split_street[-2]
                    split_street.insert(-1, fixed_second_last)
    # If last word is in the list of expected street types, leave as is.
    #   If it is an abbreviated street type, correct to fully spelled-out type.
        elif split_street[-1] not in expected_street_types:
            if split_street[-1] in mapping.keys():
                fixed_last = mapping[split_street[-1]]
                del split_street[-1]
                split_street.append(fixed_last)

    fixed_street_name = (" ").join(split_street)
    if fixed_street_name == "Park Ave West Northwest":
        fixed_street_name = "Park Avenue West Northwest"
    return fixed_street_name

def update_postcode(postcode, mapping):
    """Fix postcode from Northeast Atlanta dataset."""
    if postcode in mapping.keys():
        fixed_postcode = zip_mapping[postcode]
        return fixed_postcode
    else:
        return postcode

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []

    if element.tag == 'node':
        for field in NODE_FIELDS:
            node_attribs[field] = element.attrib[field]

        for tag in element.iter("tag"):
            if is_street_name:
                cleaned_street_name = update_street_name(tag.attrib['v'], mapping)
                tag.attrib['v'] = cleaned_street_name

            if (is_postcode) and (tag.attrib['v'] in zip_mapping.keys()):
                cleaned_postcode = update_postcode(tag.attrib['v'], zip_mapping)
                tag.attrib['v'] = cleaned_postcode

            pc = PROBLEMCHARS.search(tag.attrib['k'])
            if pc:
                continue

            tag_dict = {}
           
            lc = LOWER_COLON.search(tag.attrib['k'])
            if lc:
                k_key_value = tag.attrib['k'].split(":", 1)
                tag_dict['type'] = k_key_value[0]
                tag_dict['key'] = k_key_value[1]
            else:
                tag_dict['type'] = 'regular'
                tag_dict['key'] = tag.attrib['k']
            tag_dict['id'] = node_attribs['id']
            tag_dict['value'] = tag.attrib['v']
            tags.append(tag_dict)
            
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        for field in WAY_FIELDS:
            way_attribs[field] = element.attrib[field]

        for tag in element.iter("tag"):
            if (is_postcode) and (tag.attrib['v'] in zip_mapping.keys()):
                cleaned_postcode = update_postcode(tag.attrib['v'], zip_mapping)
                tag.attrib['v'] = cleaned_postcode

            pc = PROBLEMCHARS.search(tag.attrib['k'])
            if pc:
                continue

            tag_dict = {}

            lc = LOWER_COLON.search(tag.attrib['k'])
            if lc:
                k_key_value = tag.attrib['k'].split(":", 1)
                tag_dict['type'] = k_key_value[0]
                tag_dict['key'] = k_key_value[1]
            else:
                tag_dict['type'] = 'regular'
                tag_dict['key'] = tag.attrib['k']
            tag_dict['id'] = way_attribs['id']
            tag_dict['value'] = tag.attrib['v']
            tags.append(tag_dict)

        nd_position = 0
        for nd in element.iter("nd"):
            nd_dict = {}
            nd_dict['id'] = way_attribs['id']
            nd_dict['node_id'] = nd.attrib['ref']
            nd_dict['position'] = nd_position
            way_nodes.append(nd_dict)
            nd_position += 1
            
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=True)
