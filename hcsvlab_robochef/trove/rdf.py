from hcsvlab_robochef.rdf.map import *

TROVE = "Trove"
TROVENS = corpus_property_namespace(TROVE)

troveMap = MetadataMapper(TROVE, None, get_generic_doc_mapper())
metadata_defaults(troveMap)

troveMap.add('id', mapto=DC.identifier)
troveMap.add('titleId', ignore=True)
troveMap.add('titleName',  ignore=True)
troveMap.add('date', mapto=DC.date)
troveMap.add('firstPageId',  ignore=True)
troveMap.add('firstPageSeq',  ignore=True)
troveMap.add('category',  ignore=True)
troveMap.add('state',  ignore=True)
troveMap.add('has',  ignore=True)
troveMap.add('heading',  ignore=True)
troveMap.add('fulltext',  ignore=True)
