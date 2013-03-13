#! /usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright 2004, 2013 Vishwas Bhat, Apurva Pangam, Tarun Makhija, Vineet Jalali
This file is part of hbcse-crawler.

hbcse-crawler is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

hbcse-crawler is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with hbcse-crawler.  If not, see <http://www.gnu.org/licenses/>. 
"""

import urllib, urlparse, re, md5, os, sgmllib, string, datetime

config_file = "crawler.conf"
site_q = "Enter the start site: "
ply_q = "Enter the ply length: "
data_dir="data"
filenumber = 86
others = ['cnn', 'india']
threshold = 1

class StrippingParser(sgmllib.SGMLParser):

    # These are the HTML tags that we will leave intact
    valid_tags = ()
    from htmlentitydefs import entitydefs # replace entitydefs from sgmllib

    def __init__(self):
        sgmllib.SGMLParser.__init__(self)
        self.result = ""
        self.endTagList = []

    def handle_data(self, data):
        if data:
            self.result = self.result + data

    def handle_charref(self, name):
        self.result = "%s&#%s;" % (self.result, name)

    def handle_entityref(self, name):
        if self.entitydefs.has_key(name):
            x = ';'
        else:
            # this breaks unstandard entities that end with ';'
            x = ''
        self.result = "%s&%s%s" % (self.result, name, x)

    def unknown_starttag(self, tag, attrs):
        """ Delete all tags except for legal ones """
        if tag in self.valid_tags:
            self.result = self.result + '<' + tag
            for k, v in attrs:
                if string.lower(k[0:2]) != 'on' and string.lower(v[0:10]) != 'javascript':
                    self.result = '%s %s="%s"' % (self.result, k, v)
            endTag = '</%s>' % tag
            self.endTagList.insert(0,endTag)
            self.result = self.result + '>'

    def unknown_endtag(self, tag):
        if tag in self.valid_tags:
            self.result = "%s</%s>" % (self.result, tag)
            remTag = '</%s>' % tag
            self.endTagList.remove(remTag)

    def cleanup(self):
        """ Append missing closing tags """
        for j in range(len(self.endTagList)):
                self.result = self.result + self.endTagList[j]


def strip(s):
    """ Strip illegal HTML tags from string s """
    parser = StrippingParser()
    parser.feed(s)
    parser.close()
    parser.cleanup()
    return parser.result

class URLLister(sgmllib.SGMLParser):
    """needs sgmllib from SGMLParser
    """
    def reset(self):
        sgmllib.SGMLParser.reset(self)
        self.urls = []

    def start_a(self, attrs):
        href = [v for k, v in attrs if k=='href']
        if href:
            self.urls.extend(href)

def validurl(site):
    """Code to identify valid URL to find
    """
    try:
        if urlparse.urlparse(site)[0]=='http' or urlparse.urlparse(site)[0]=='https' :
            return [urllib.urlopen(site),1]
        elif urlparse.urlparse(site)[0]=='':
            site = urllib.urlopen('http://'+site)
            return [site,1]
        else:
            print 'Invalid URL'
    except IOError:
        print 'The Server is not found or is unreachable'
        return [None,0]
    except SystemExit:
            print 'Exit'

class Summary:

    def __init__(self,site,i,config):
        """initialises the object
        site   site url
        x[]    site url as an instance,flag
        y      site content
        ply    depth of search
        sign   MD5 of the site data
        npara  number of paragraphs
        para   list of paragraphs
        title  title of the page
        weights weighted vector
        """
        self.site = site
   	self.config=config
        self.sign = md5.new()
        self.ply=i
        self.npara=0
        self.x = validurl(site)
        if(self.x[0]!= 0):
            self.y=self.x[0].read()
            self.sign.update(repr(self.y))
            c=self.checkmd5()
            if self.y==None  or c==0:
                self.x[1]=0
            else:
                self.x[1]=1;
            self.x[0].close()
            self.para=['','']
            self.title=''
            self.weights= []

    def checkmd5(self):
        file1 = open(os.path.join(path,'md5.txt'),'w+')
        x=file1.readline()
        while x:
            x=x.replace('\n','')
            if x==repr(self.sign.digest()):
                return 0
            x=file1.readline()
        file1.close()
        return 1

    def get2tag(self,tag):
    #currently - removes data between p and title tags
    #goal - removing data between any tag
	w={'&nbsp;':' ','&amp;':'&','&#8226;':'','&copy':'©','&#149;':'','&#39;':''}
        l=len(tag)+2
        z=re.compile('<'+tag+'>.*?<\/'+tag+'>',re.DOTALL).findall(self.y)
        if(len(z)==0):
            z=re.compile('<'+tag+'>.*?<'+tag+'>',re.DOTALL).findall(self.y)
        if tag=='p':
            if(len(z)==0):
                length=0
                self.npara=0
                print 'The site does not contain any paragraphs'
            elif(len(z)>1):
                length = 2
                self.npara=2
                print 'The first 2 paragraphs of the site are: '
            else:
                length = len(z)
                self.npara=len(z)
            for i in range(0,length):
                m=l-1
                while z[i][m]<>'>':
                    m=m+1
                y= z[i][m+1:len(z[i])-l-1]
                y=y.strip()
                y=urllib.unquote(y)
                for a in w.keys():
                   y= y.replace(a,w[a])
                print
                print 'Paragraph No.',i+1,':'
                print y
                self.para[i]=y
        elif tag=='title':
            if len(z)!=0:
                self.title=strip(z[0])
                return strip(z[0])

    def getvector(self):
    #provides the weighted vector based on the lists in three.py
    #goal - need to iterate over various lists in the file (bio, chem,...)
        flag=0
        for x in self.config["others"]:
            z= re.compile(x).findall(self.y)
            if len(z)>=self.config["threshold"]:
                flag=1
            self.weights.append((x,len(z)))
            print 'Number of matches for',x,'=', len(z)
        return flag


    def loopurl(self):
    #finidng all URLs in the site and creating new objects of those URLs
    #uses the class URLLister
        parser = URLLister()
        parser.feed(self.y)
        for url in parser.urls:
            if url != '':
                if url != self.x[0]:
                    if url[0:4] != 'http' and url[0:4] != 'www.' :
                        if url[0] != '/':
                            site2=self.site+'/'+url
                        else:
                            site2=self.site+url
                        print site2
                        z=Summary(site2,self.ply-1, self.config)
                    else:
                        print url
                        z=Summary(url,self.ply-1, self.config)
                    if self.sign.digest() != z.sign.digest():
                        z.run()
        parser.close()

    def run(self):
        if self.x[1]==1:
            print
            print '----------------------------'
            print 'TITLE: ', self.get2tag('title')
            self.get2tag('p')
            file2 = open(os.path.join(path,'md5.txt'),'a')
            file2.write(repr(self.sign.digest())+'\n')
            file2.close()
            flag=self.getvector()
            if(flag==1):
                self.write2file()
            print '----------------------------'
            print
            if(self.ply>=1):
                self.loopurl()

    def write2file(self):
        """ prints the class instance to the file """
	part_file_name = self.config["path"]+'/page'+str(datetime.datetime.now());

        file = open(part_file_name+'.html','w')
        file.write(self.y)
        file.close()

        file = open(part_file_name+'.xml','w')
        file.write('<?xml version="1.0" encoding="ISO-8859-1"?>')
        file.write('<summary>\n')
        file.write('<siteurl>'+self.site+'</siteurl>\n')
        file.write('<title>'+self.title+'</title>\n')
        file.write('<md5>'+repr(self.sign.digest())+'</md5>\n')
        file.write('<ply>'+repr(self.ply)+'</ply>\n')
        for i in range(self.npara):
            file.write('<paragraph'+repr(i)+'>'+self.para[i]+'</paragraph'+repr(i)+'>\n')
        for i in range(len(self.weights)):
            file.write('<weight'+repr(i)+'>'+repr(self.weights[i])+'</weight'+repr(i)+'>\n')
        file.write('</summary>')
        file.close()

if __name__ == "__main__":
    # Initialization
    config = {}
    execfile(config_file, config) 

    path = os.path.join(os.getcwd(), data_dir)
    if not os.path.exists(path):
        os.mkdir(path)
    config["path"] = path
    config["threshold"] = threshold

    # User input
    site = raw_input(site_q)
    length = raw_input(ply_q)

    # Run the program
    Summary(site, int(length), config).run()


