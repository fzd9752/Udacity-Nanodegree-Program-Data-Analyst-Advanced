import xml.etree.cElementTree as ET
import re
import pprint

## get element by node
def get_element(osm_file, tags=('node', 'way')):
    """Yield element if it is the right type of tag
       Yield all elements if tags=()
    """
    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    if not tags: ## read all nodes if tags empty
        for event, elem in context:
            if event == 'end':
                yield elem
    else:
        for event, elem in context:
            if event == 'end' and elem.tag in tags:
                yield elem

## get all tags and count
def get_tags(osm_file):
    """Return a dictionary contains all tags types
       and count
    """
    n = 0
    tags = {}
    for element in get_element(osm_file, tags=()):
        tag = element.tag
        tags[tag] = tags.get(tag, 0)+1
        n += 1

    print('%s tags found.' % n)
    print(tags)

    return tags

## classify the keys
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

def key_type(osm_file):
    """Yield a dictionary that contains four classes for
       second level 'k' value
    """
    keys = {}
    keys['lower'] = []
    keys['lower_colon'] = []
    keys['problemchars'] = []
    keys['other'] = []

    for element in get_element(osm_file, tags=('tag')):
        k = element.attrib['k']
        if lower.search(k):
            keys['lower'].append(k)
        elif lower_colon.search(k):
            keys['lower_colon'].append(k)
        elif problemchars.search(k):
            keys['problemchars'].append(k)
        else:
            keys['other'].append(k)

    return  keys

## find a example of the element with interesting 'k'
def find_interest(osm_file, k, n=1):
    """Return n element(s) to overview the context of interesting 'k'"""
    for elem in get_element(osm_file, tags=('tag')):
        if n > 0:
            if elem.attrib['k'] == k:
                pprint.pprint(ET.tostring(elem))
                n -= 1
        else:
            break
