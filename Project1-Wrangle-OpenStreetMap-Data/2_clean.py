# -*- coding: utf-8 -*-s
import re

mapping_streetname = { "St": "Street",
            "St.": "Street",
            "Ave": "Avenue",
            "Rd.": "Road",
            "ave": "Avenue",
            "Blvd": "Boulevard",
            "Dr.": "Drive",
            "W": "West",
            "W.": "West",
            "S": "South",
            "S.": "South"
            }

mapping_cityandstatename= {
            'East Palo Alto': 'Palo Alto',
            'Los Altos Hills': 'Los Altos',
            'Mountain View, CA': 'Mountain View',
            'San José': 'San Jose',
            'Sunnyvale, CA': 'Sunnyvale',
            'cupertino': 'Cupertino',
            'menlo park': 'Menlo Park',
            'sunnyvale': 'Sunnyvale',
            'CA': 'California',
            'Ca': 'California',
            'ca': 'California'
            }


def update_name(name, mapping=mapping_streetname):
    words = name.split()
    for w in range(len(words)):
        if words[w] in mapping:
            if words[w].lower() not in ['suite', 'ste.', 'ste']:
                # For example, don't update 'Suite E' to 'Suite East'
                words[w] = mapping[words[w]]
                name = " ".join(words)
    return name


def update_city(name, mapping=mapping_cityandstatename):
    if name in mapping:
        name = mapping[name]
    return name


error_post = re.compile(r'(^\D*)\s(\d.*)')

def update_post(post):
    if error_post.search(post):
        post = error_post.match(post).groups()[1]
    return post
