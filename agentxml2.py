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

""" uses files - three.py and tagscript.py"""

import urllib, urlparse, sys, re, md5, config, os
from sgmllib import SGMLParser
from tagstrip import *              # use of tagscript.py
from three import *                 # use of three.py

class URLLister(SGMLParser):
    """needs sgmllib from SGMLParser
    """
    def reset(self):
        SGMLParser.reset(self)
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

    def __init__(self,site,i):
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
            self.weights= ['']

    def checkmd5(self):
        file1 = open(os.path.join(path,'md5.txt'),'r')
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
                y=strip(y)
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
        for x in subjects:
            for a in x:
                z= re.compile(a).findall(self.y)
                if len(z)>=config.threshold:
                    print 'Number of matches for',a,'=', len(z)
                    self.weights.append((a,len(z)))
                    flag=1
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
                        z=Summary(site2,self.ply-1)
                    else:
                        print url
                        z=Summary(url,self.ply-1)
                    if self.sign.digest() != z.sign.digest():
                        z.run()
        parser.close()

    def run(self):
        if self.x[1]==1:
            print
            print '------------------------------------------------------------------------------------------------------------'
            print 'TITLE: ', self.get2tag('title')
            self.get2tag('p')
            file2 = open(os.path.join(path,'md5.txt'),'a')
            file2.write(repr(self.sign.digest())+'\n')
            file2.close()
            flag=self.getvector()
            if(flag==1):
                self.write2file()
                config.filenumber=config.filenumber+1
            print '------------------------------------------------------------------------------------------------------------'
            print
            if(self.ply>=1):
                self.loopurl()

    def write2file(self):
        """ prints the class instance to the file """
        file1 = open(os.path.join(path,'page'+repr(config.filenumber)+'.html'),'w')
        file1.write(self.y)
        file1.close()

        file = open(os.path.join(path,'page'+repr(config.filenumber)+'.xml'),'w')
        file.write('<?xml version="1.0" encoding="ISO-8859-1"?>')
        file.write('<summary>')
        file.write('\n\n')
        file.write('<siteurl>'+self.site+'</siteurl>')
        file.write('\n\n')
        file.write('<title>'+self.title+'</title>')
        file.write('\n\n')
        file.write('<md5>'+repr(self.sign.digest())+'</md5>')
        file.write('\n\n')
        file.write('<ply>'+repr(self.ply)+'</ply>')
        file.write('\n\n')
        for i in range(self.npara):
            file.write('<paragraph'+repr(i)+'>'+self.para[i]+'</paragraph'+repr(i)+'>')
            file.write('\n\n')
        for i in range(len(self.weights)):
            file.write('<weight'+repr(i)+'>'+repr(self.weights[i])+'</weight'+repr(i)+'>')
            file.write('\n\n')
        file.write('</summary>')
        file.close()

if __name__ == "__main__":
    path= os.getcwd()
    path = os.path.join(path,'data')
    if not os.path.exists(path):
        os.mkdir(path)
    file = open(os.path.join(path,'md5.txt'),'w')
    file.close()
    site = raw_input('Enter the Start site: ')
    length = raw_input('Enter the ply length: ')
    x=Summary(site,int(length))
    x.run()
    file = open('config.py','w')
    file.write('filenumber = '+repr(config.filenumber)+'\n')
    file.write('threshold = '+repr(config.threshold))
    file.close()


