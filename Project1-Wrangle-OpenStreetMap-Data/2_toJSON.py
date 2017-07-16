import clean
import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json

OSM_PATH = "PaloAlto_MountainView_USA.osm"
example = "example.osm"

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]


def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way" :
        # YOUR CODE HERE
        created = {}
        node['id'] = element.attrib['id']
        node['type'] = element.tag
        try:
            node["visible"] = element.attrib["visible"]
        except:
            pass

        for l in range(len(CREATED)):
            try:
                created[CREATED[l]] = element.attrib[CREATED[l]]
            except:
                created[CREATED[l]] = "NA"
        node['created'] = created

        for tag in element.iter():

            if tag.tag == 'tag':
                if problemchars.search(tag.attrib['k']):
                    pass
                if tag.attrib['k'] == "amenity":
                    node["amenity"] = tag.attrib['v']
                if tag.attrib['k'] == "cuisine":
                    node["cuisine"] = tag.attrib['v']
                if tag.attrib['k'] == "name":
                    node["name"] = tag.attrib['v']
                if tag.attrib['k'] == "phone":
                    node["phone"] = tag.attrib['v']

                if tag.attrib['k'].startswith('addr:') and (tag.attrib['k'].count(':') == 1):
                    key = tag.attrib['k']
                    try:
                        node['address'][key[5:]] = tag.attrib['v']
                    except:
                        node['address'] = {key[5:]: tag.attrib['v']}

                    if key[5:] == 'street':
                        node['address'][key[5:]] = clean.update_name(node['address'][key[5:]])
                    if key[5:] in ["state", "city"]:
                        node['address'][key[5:]] = clean.update_city(node['address'][key[5:]])
                    if key[5:] == 'postcode':
                        node['address'][key[5:]] = clean.update_post(node['address'][key[5:]])

            elif tag.tag == 'nd':
                try:
                    node["node_refs"].append(tag.attrib['ref'])
                except:
                    node["node_refs"] = [tag.attrib['ref']]

        try:
            node['pos'] = [float(element.attrib['lat']), float(element.attrib['lon'])]
        except:
            pass

        return node
    else:
        return None


def process_map(file_in, pretty = False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

if __name__ == "__main__":
    process_map(OSM_PATH)
