'''
This module defines a method genrdf, which takes a metadata dictionary
as parameter and returns a rdflib Graph instance.
'''

from hcsvlab_robochef.rdf.map import *


def get_map(corpus):
    #corpus_ns = corpus_property_namespace(corpus)

    # mapper for properties of a person
    corpus_speaker = FieldMapper(corpus)
    corpus_speaker.add('Gender', mapper=FOAF.gender)

    corpus_map = MetadataMapper(corpus, documentMap = get_generic_doc_mapper(), speakerMap=corpus_speaker)
    metadata_defaults(corpus_map)

    corpus_map.add('Creator', mapto=DC.creator)
    corpus_map.add('Title', mapto=DC.title)
    corpus_map.add('Source', mapto=DC.source)
    corpus_map.add('Mode', mapto=AUSNC.mode)
    corpus_map.add('Speech Style', mapto=AUSNC.speech_style)
    corpus_map.add('Interactivity', mapto=AUSNC.interactivity)
    corpus_map.add('Communication Context', mapto=AUSNC.communication_context)
    corpus_map.add('Audience', mapto=AUSNC.audience)

    corpus_map.add('Speaker', ignore=True)

    return corpus_map

