"""Support for uploading RDF data directly to a Sesame instance"""

import urllib, urllib2
import os

class RequestWithMethod(urllib2.Request):
  def __init__(self, *args, **kwargs):
    self._method = kwargs.get('method')
    if self._method:
        del kwargs['method']
    urllib2.Request.__init__(self, *args, **kwargs)

  def get_method(self):
    return self._method if self._method else super(RequestWithMethod, self).get_method()



class SesameServer():
    """A utility class to support HTTP interaction with a sesame triple store"""
    
    def __init__(self, url):
        
        self.url = url
        
    def _get(self, url):
        """Send a get request to the given URL (which can also be a Request object)
        and return a tuple of the response code and the response body ('200', 'whatever')"""
        
        
        try:
            h = urllib2.urlopen(url)
            result = h.read()
            return (h.code, result)
        except urllib2.URLError, e:
            print "Error", e
            return (e.code, e)
        


    
    def size(self):
        """Query the repository size, return size
        in triples"""
        
        path = "/size"
        
        result = self._get(self.url + path)
        
        return result[1]
    
    
    def upload(self, filename):
        """Upload RDF data from filename"""
        
        path = "/statements"
        h = open(filename)
        data = h.read()
        h.close()
        headers = {'Content-Type': 'application/x-turtle'}
        req = urllib2.Request(self.url+path, data=data, headers=headers)
        
        result = self._get(req)
        # check that return code is 204
        if result[0] == 204:
            return result[1]
        else:
            raise Exception("Problem with upload of data, result code %s" % result[0])
        
    def upload_dir(self, dirname):
        """upload all RDF files found inside dirname and
        subdirectories (recursively)"""
        
        retry = []
        
        for dirpath, dirnames, filenames in os.walk(dirname):
            for fn in filenames:
                if fn.endswith(".rdf"): 
                    print "Upload", fn
                    try:
                        self.upload(os.path.join(dirpath, fn))
                    except:
                        print "problem uploading", fn
                        retry.append(os.path.join(dirpath, fn))
        
        print "Retrying ", len(retry), "uploads"
        while len(retry) > 0:
            fn = retry.pop()
            print "Upload", fn
            try: 
                self.upload(fn)
            except:
                print "problem with retry of ", fn
                retry.append(fn)
            
    def upload_graph(self, graph):
        """Upload the contents of an RDFlib graph to the store"""
        
        data = graph.serialize(format='xml')
        
        path = "/statements"
        headers = {'Content-Type': 'application/rdf+xml'}
        req = urllib2.Request(self.url+path, data=data, headers=headers)
        
        result = self._get(req)
        # check that return code is 204
        if result[0] == 204:
            return result[1]
        else:
            raise Exception("Problem with upload of data, result code %s" % result[0])
       
        
    def clear(self):
        """Remove all triples in the store"""
        
        path = "/statements"
        req = RequestWithMethod(self.url+path, method="DELETE")
        
        result = self._get(req)
        
        return result
        
    
if __name__=='__main__':
    
    import sys
    
    url = "http://115.146.93.47/openrdf-sesame/repositories/ausnc_dev"
    rdfbase = sys.argv[1]
    
    server = SesameServer(url)

    server.clear()
    server.upload_dir(rdfbase)

    size = server.size()
    
    print "Size: ", size