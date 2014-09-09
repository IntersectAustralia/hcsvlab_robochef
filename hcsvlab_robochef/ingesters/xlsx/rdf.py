'''
This module defines a method genrdf, which takes a metadata dictionary
as parameter and returns a rdflib Graph instance.
'''

from hcsvlab_robochef.rdf.map import *

MBEP = "mbep"
MBEPNS = corpus_property_namespace(MBEP)

# mapper for properties of a person
mbepSpeaker = FieldMapper(MBEP)
mbepSpeaker.add('Gender', mapper=FOAF.gender)

mbepMap = MetadataMapper(MBEP, documentMap = get_generic_doc_mapper(), speakerMap=mbepSpeaker)
metadata_defaults(mbepMap)

mbepMap.add('Creator', mapto=DC.creator)
mbepMap.add('Title', mapto=DC.title)
mbepMap.add('Source', mapto=DC.source)
mbepMap.add('Mode', mapto=AUSNC.mode)
mbepMap.add('Speech Style', mapto=AUSNC.speech_style)
mbepMap.add('Interactivity', mapto=AUSNC.interactivity)
mbepMap.add('Communication Context', mapto=AUSNC.communication_context)
mbepMap.add('Audience', mapto=AUSNC.audience)

mbepMap.add('Speaker', ignore=True)

