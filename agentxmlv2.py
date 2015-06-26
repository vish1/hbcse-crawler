#! /usr/bin/env python
# -*- coding: utf-8 -*-
''' vb-crawler:
    Given a start website
    i. traverse all the links originating from the site
    ii. extract relevant text content from each page
    iii. store the content in a particular directory
    iv. repeat till provided ply length is hit
'''

import requests 

def get_url_content(url):
    'Returns the text contents for the provided URL' 
    try:
        r = requests.get(url)
    except Exception:
        return None

    return r.text if r.status_code == requests.codes.ok else None

if __name__ == '__main__':
    cnn_content = get_url_content("http://www.cnn.com")
    print cnn_content[:500]
    error_content = get_url_content("htt//www.cnn.com")
    assert error_content == None;


