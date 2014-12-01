
Scripts to harvest Paradisec metadata from their OAI-PMH feed at
http://catalog.paradisec.org.au/oai/item?verb=ListRecords&metadataPrefix=olac
http://catalog.paradisec.org.au/oai/collection?verb=ListRecords&metadataPrefix=rif
and prep it for RoboChefing.

harvester.py:
  Pulls metadata from the Paradisec catalog & produces item OLAC XML files for
  each page of data retrieved. This saves the xml files into argv[1]/items/

collection_harvester.py:
  Pulls metadata from the Paradisec catalog & produces collection RIF-CS XML files for
  each page of data retrieved. This saves the xml files into argv[1]/collections/

This needs scripting, but can be run like:

$ python harvester.py /data/raw/paradisec/
$ python collection_harvester.py /data/raw/paradisec/

Afterwords, run the Paradisec ingest on argv[1]

