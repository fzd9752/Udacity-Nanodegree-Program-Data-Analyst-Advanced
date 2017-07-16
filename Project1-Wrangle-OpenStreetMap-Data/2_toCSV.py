import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
import audit
import cerberus
import clean
import schema

OSM_PATH = "PaloAlto_MountainView_USA.osm"
example = "example.osm"

NODES_PATH = "SQL/nodes.csv"
NODE_TAGS_PATH = "SQL/nodes_tags.csv"
WAYS_PATH = "SQL/ways.csv"
WAY_NODES_PATH = "SQL/ways_nodes.csv"
WAY_TAGS_PATH = "SQL/ways_tags.csv"

#LOWER_COLON = re.compile(r'^(([a-z]|_)+):(([a-z]|_)+)')
LOWER_COLON = re.compile(r'^(([a-z]|_)+):(.+)')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    node_tags = []
    way_tags = []

    # YOUR CODE HERE
    if element.tag == 'node':
        for field in NODE_FIELDS:
            try:
                node_attribs[field] = element.attrib[field]
            except: ## Fix some 'node' missing 'user' and other fields
                node_attribs[field] = "NA"


        for tag in element.iter('tag'):
            if problem_chars.search(tag.attrib['k']):
                continue
            else:
                tag_dict = {}
                tag_dict['id'] = element.attrib['id']
                tag_dict['value'] = tag.attrib['v']

            m = LOWER_COLON.search(tag.attrib['k'])
            if m:
                tag_dict['type'] = m.group(1)
                tag_dict['key'] = m.group(3)

                ## fix over-abbreviated street names
                if tag_dict['key'] == 'street':
                    tag_dict['value'] = clean.update_name(tag_dict['value'])
                ## fix inconsistent state, cities and countries names
                if tag_dict['key'] in ['state', 'city', 'country']:
                    tag_dict['value'] = clean.update_city(tag_dict['value'])
                ## fix postal code
                if tag_dict['key'] == 'postcode':
                    tag_dict['value'] = clean.update_post(tag_dict['value'])

            else:
                tag_dict['type'] = default_tag_type
                ## fix capital 'k' values
                tag_dict['key'] = tag.attrib['k'].lower()

            node_tags.append(tag_dict)


        #print({'node': node_attribs, 'node_tags': node_tags})
        return {'node': node_attribs, 'node_tags': node_tags}

    elif element.tag == 'way':
        for field in WAY_FIELDS:
            way_attribs[field] = element.attrib[field]

        for tag in element.iter('tag'):
            if problem_chars.search(tag.attrib['k']):
                continue
            else:
                way_dict = {}
                way_dict['id'] = element.attrib['id']
                way_dict['value'] = tag.attrib['v']

            m = LOWER_COLON.search(tag.attrib['k'])
            if m and (not 'addr:street:' in tag.attrib['k']):
                #print(m.group(0))
                #index = tag.attrib['k'].index(':')
                #way_dict['type'] = tag.attrib['k'][:index]
                #way_dict['key'] = tag.attrib['k'][index+1:]
                #print(tag.attrib['k'])

                way_dict['type'] = m.group(1)
                way_dict['key'] = m.group(3)

                ## fix over-abbreviated street names
                if way_dict['key'] == 'street':
                    way_dict['value'] = clean.update_name(way_dict['value'])
                ## fix inconsistent state, cities and countries names
                if way_dict['key'] in ['state', 'city', 'country']:
                    way_dict['value'] = clean.update_city(way_dict['value'])
                ## fix postal code
                if way_dict['key'] == 'postcode':
                    way_dict['value'] = clean.update_post(way_dict['value'])

            else:
                way_dict['type'] = default_tag_type
                ## fix capital 'k' value
                way_dict['key'] = tag.attrib['k'].lower()

            way_tags.append(way_dict)

        n = 0
        for nd in element.iter('nd'):
            way_nodes_dict = {}
            way_nodes_dict['id'] = element.attrib['id']
            way_nodes_dict['node_id'] = nd.attrib['ref']
            way_nodes_dict['position'] = n
            n += 1

            way_nodes.append(way_nodes_dict)

        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': way_tags}

# ================================================== #
#               Helper Functions                     #
# ================================================== #
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

        #nodes_writer.writeheader()
        #node_tags_writer.writeheader()
        #ways_writer.writeheader()
        #way_nodes_writer.writeheader()
        #way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in audit.get_element(file_in, tags=('node', 'way')):
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
    process_map(OSM_PATH, validate=False)
