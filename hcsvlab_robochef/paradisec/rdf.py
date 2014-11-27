from hcsvlab_robochef.rdf.map import *

PARADISEC = "PARADISEC"

paradisecSpeakerMap = FieldMapper(AUSNC)
paradisecSpeakerMap.add('name', mapto=FOAF.name)
paradisecSpeakerMap.add('role', ignore=True)

paradisecMap = MetadataMapper(PARADISEC, speakerMap=paradisecSpeakerMap, documentMap = get_generic_doc_mapper())
paradisecMap.add('Box', mapto=DC.box)
paradisecMap.add('DCMIType', mapto=DC.type, ignore=True)
paradisecMap.add('ISO3166', mapto=DC.coverage)
paradisecMap.add('URI', ignore=True)
paradisecMap.add('W3CDTF', mapto=DC.created)
paradisecMap.add('accessRights', mapto=DC.accessRights)
paradisecMap.add('author', mapto=OLAC.author, ignore=True)
paradisecMap.add('bibliographicCitation', mapto=DC.bibliographicCitation)
paradisecMap.add('compiler', mapto=OLAC.compiler, ignore=True)
paradisecMap.add('consultant', mapto=OLAC.consultant, ignore=True)
paradisecMap.add('data_inputter', mapto=OLAC.data_inputter, ignore=True)
paradisecMap.add('depositor', mapto=OLAC.depositor, ignore=True)
paradisecMap.add('description', mapto=DC.description)
paradisecMap.add('discourse-type', mapto=OLAC.discourse_type)
paradisecMap.add('format', ignore=True)
paradisecMap.add('identifier', mapto=DC.identifier)
paradisecMap.add('interviewer', mapto=OLAC.interviewer, ignore=True)
paradisecMap.add('language', mapto=OLAC.language)
paradisecMap.add('linguistic-field', mapto=OLAC.linguistic_field)
paradisecMap.add('linguistic-type', mapto=OLAC.linguistic_type)
paradisecMap.add('photographer', mapto=OLAC.photographer, ignore=True)
paradisecMap.add('recorder', mapto=OLAC.recorder, ignore=True)
paradisecMap.add('researcher', mapto=OLAC.researcher, ignore=True)
paradisecMap.add('rights', mapto=DC.rights)
paradisecMap.add('speaker', mapto=OLAC.speaker, ignore=True)
paradisecMap.add('tableOfContents', ignore=True)
paradisecMap.add('title', mapto=DC.title)
paradisecMap.add('type', mapto=DC.type, ignore=True)


