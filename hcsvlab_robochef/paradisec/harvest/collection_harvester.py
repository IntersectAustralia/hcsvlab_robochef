import sys
import os
import urllib
import urllib2
import datetime
from xml.dom.minidom import *

# function for return dom response after parsting oai-pmh URL
def oaipmh_response(URL):
    file = urllib2.urlopen(URL)
    data = file.read()
    file.close()

    dom = parseString(data)
    return dom


# function for getting value of resumptionToken after parsting oai-pmh URL
def oaipmh_resumptionToken(URL):
    print "opening", URL
    file = urllib2.urlopen(URL)
    data = file.read()
    file.close()

    dom = parseString(data)

    token = ""

    try:
        token = dom.getElementsByTagName('resumptionToken')[0].firstChild.nodeValue
        print "START: " + str(datetime.datetime.now())
    except:
        print "No resumption token"
        token = ""

    return token

def write_xml(node, output_dir):
    doc = Document()
    new_node = node.cloneNode(True)
    identifiers = new_node.getElementsByTagName('identifier')
    name = identifiers.item(0).firstChild.nodeValue.split("/")[-1]
    doc.appendChild(new_node)
    outpath = os.path.join(output_dir,"collections","paradisec-" + name + '.xml')
    if not os.path.exists(os.path.dirname(outpath)):
        os.makedirs(os.path.dirname(outpath))
    outfile = open(outpath, 'w')
    outfile.write(doc.toxml('utf-8'))

#
# main code
#

if len(sys.argv) >= 2:
    output_dir = sys.argv[1]
else:
    print "Usage: python collection_harvester.py path_to_output"
    exit()

getRecordsURL = 'http://catalog.paradisec.org.au/oai/collection?verb=ListRecords&'
resumptionToken = "metadataPrefix=rif"

# loop parse phase
while resumptionToken != "":
    print "Resumption Token: " + resumptionToken
    getRecordsURLLoop = str(getRecordsURL + resumptionToken)
    oaipmhXML = oaipmh_response(getRecordsURLLoop)
    for node in oaipmhXML.getElementsByTagName('record'):
        ident = node.getElementsByTagName('header').item(0).getElementsByTagName('identifier').item(0).firstChild.nodeValue
        rights = node.getElementsByTagName('accessRights')[0].firstChild.nodeValue

        # only take paradisec collections
        if 'paradisec' in ident:
            write_xml(node.getElementsByTagName('metadata').item(0), output_dir)
        else:
            print "Rejecting", ident
    newToken = oaipmh_resumptionToken(getRecordsURLLoop)
    if newToken != "":
        resumptionToken = urllib.urlencode({'resumptionToken': newToken})
    else:
        resumptionToken = ""
    print "END: " + str(datetime.datetime.now())
