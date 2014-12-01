from hcsvlab_robochef.annotations import *
from hcsvlab_robochef.ingest_base import IngestBase
from hcsvlab_robochef.rdf.map import *
from hcsvlab_robochef.utils.serialiser import *
from hcsvlab_robochef.utils.statistics import *
from rdf import paradisecMap
from xml.etree import ElementTree as ET
import codecs
import mimetypes
import urllib
import re
from collections import Counter

from rdflib.term import Literal

class ParadisecIngest(IngestBase):
    olac_role_map = {'annotator': OLAC.annotator, 'author': OLAC.author, 'compiler': OLAC.compiler,
                     'consultant': OLAC.consultant, 'data_inputter': OLAC.data_inputter,
                     'depositor': OLAC.depositor, 'developer': OLAC.developer, 'editor': OLAC.editor,
                     'illustrator': OLAC.illustrator, 'interpreter': OLAC.interpreter,
                     'interviewer': OLAC.interviewer, 'participant': OLAC.participant,
                     'performer': OLAC.performer, 'photographer': OLAC.photographer,
                     'recorder': OLAC.recorder, 'researcher': OLAC.researcher,
                     'research_participant': OLAC.research_participant, 'responder': OLAC.responder,
                     'signer': OLAC.signer, 'singer': OLAC.singer, 'speaker': OLAC.speaker,
                     'sponsor': OLAC.sponsor, 'transcriber': OLAC.transcriber, 'translator': OLAC.translator}

    def ingestCorpus(self, srcdir, outdir):
        ''' This function will initiate the ingest process for the PARADISEC corpus '''

        print "  converting corpus in", srcdir, "into normalised data in", outdir
        print "    clearing and creating output location"

        self.clear_output_dir(outdir)

        print "    processing files..."

        files_to_process = self.__get_files(srcdir)
        sofar = 0

        for f in files_to_process:
            if "paradisec-" in os.path.basename(f):
                meta_dict = self.ingestCollection(srcdir, f)
                uri_ref = URIRef(meta_dict['uri'])
                metadata_graph = Graph(identifier=uri_ref)
                metadata_graph.bind('paradisec', uri_ref)
                bind_graph(metadata_graph)

                metadata_graph.add((uri_ref, RDF.type, DCMITYPE.Collection))
                metadata_graph.add((uri_ref, DC.title, Literal(meta_dict['namePart'])))
                metadata_graph.add((uri_ref, DC.description, Literal(meta_dict.get('brief'), "")))
                metadata_graph.add((uri_ref, DC.bibliographicCitation, Literal(meta_dict['fullCitation'])))
                metadata_graph.add((uri_ref, DC.creator, Literal(meta_dict['fullCitation'].split(" (", 1)[0])))
                metadata_graph.add((uri_ref, DC.rights, Literal(meta_dict['accessRights'])))

                serializer = plugin.get('turtle', Serializer)(metadata_graph)
                outfile = open(os.path.abspath(os.path.join(outdir, "paradisec-" + meta_dict['corpus_suffix'].lower() + ".n3")), 'w')
                serializer.serialize(outfile, encoding='utf-8')
                outfile.close()
            else:
                meta_dict = self.ingestDocument(srcdir, f)

                corpus_suffix = meta_dict.pop('corpus_suffix')
                subdir = os.path.join(outdir, corpus_suffix)

                try:
                    os.makedirs(subdir)
                except:
                    pass
                sampleid = corpus_suffix + "-" + meta_dict['identifier']
                serialiser = MetaSerialiser()
                serialiser.serialise(subdir, sampleid, paradisecMap, meta_dict, self.identify_documents, True)

            sofar = sofar + 1
            print "\033[2K   ", sofar, " ", f, "\033[A"

        print "\033[2K   ", sofar, "files processed"


    def setMetaData(self, srcdir):
        ''' Loads the meta data for use during ingest '''
        pass

    def ingestCollection(self, srcdir, sourcepath):
        """ Read and process a corpus document """

        xml_tree = self.__load_xml_tree(sourcepath)
        meta_dict = metadata.xml2paradisecdict(xml_tree, ignorelist=['olac', 'metadata'])
        corpus_suffix = meta_dict['uri'].split("/")[-1]
        meta_dict['corpus_suffix'] = corpus_suffix
        return meta_dict

    def ingestDocument(self, srcdir, sourcepath):
        """ Read and process a corpus document """

        xml_tree = self.__load_xml_tree(sourcepath)
        meta_dict = metadata.xml2paradisecdict(xml_tree, ignorelist=['olac', 'metadata'])
        self.__get_documents(meta_dict)
        self.__get_people(meta_dict)
        corpus_suffix, identifier = meta_dict['identifier'].split("-", 1)
        meta_dict['identifier'] = identifier
        meta_dict['corpus_suffix'] = corpus_suffix
        paradisecMap.corpusID = "PARADISEC-" + corpus_suffix
        return meta_dict

    def identify_documents(self, documents):
        cnt = Counter()
        display = None
        indexable = None

        for doc in documents:
            cnt[doc['filetype']] += 1
        if cnt['Video'] == 1:
            display_type = "Video"
        elif cnt['Audio'] == 1:
            display_type = "Audio"
        elif cnt['Text'] == 1:
            display_type = "Text"
        else:
            display_type = None

        if display_type:
            for doc in documents:
                if doc['filetype'] == display_type:
                    display = doc['uri']
                    if display_type == "Text":
                        indexable = doc['uri']
                    break

        return (indexable, display)

    def __get_documents(self, meta_dict):
        v = meta_dict.pop('tableOfContents', None)
        if v is not None:
            filetype = self.__get_type(v)
            file_meta = {'id': v, 'filename': v, 'filetype': filetype, 'documenttitle': v}
            meta_dict['table_document_' + v] = file_meta

    def __get_people(self, meta_dict):
        roles = self.olac_role_map.keys()

        for role in roles:
            v = meta_dict.pop(role, None)
            if v is not None:
                person = {'role': self.olac_role_map[role], 'id': re.sub(' ', '_', v), 'name': v}
                meta_dict['table_person_' + role] = person


    # TODO: this could be moved to somewhere like ../utils where other modules could use it
    def __get_type(self, filepath):
        url = urllib.pathname2url(filepath)
        mime_type, _ = mimetypes.guess_type(url)
        filetype = None
        if mime_type:
            filetype = mime_type.split('/')[0].title()
        if not filetype or filetype == 'Application':
            filetype = 'Other'
        return filetype


    def __get_files(self, srcdir):
        item_pattern = "^.+\.xml"

        for root, dirnames, filenames in os.walk(srcdir):
            for filename in filenames:
                if re.match(item_pattern, filename):
                    yield os.path.join(root, filename)

    def __tuplelist2dict__(self, tuplelist):
        result = dict()
        for (k, v) in tuplelist:
            if k and v:
                result[k] = v
        return result

    def __load_xml_tree(self, sourcepath):
        '''
        This function reads in a XML docment as a text file and converts it into
        an XML tree for further processing
        '''

        fhandle = codecs.open(sourcepath, "r", "utf-8")
        text = fhandle.read()
        fhandle.close()

        text = text.replace('&ndash;', u"\u2013")
        text = text.replace('&mdash;', u"\u2014")
        text = text.replace('&copy;', u"\u00A9")
        text = text.replace('&ldquo;', u"\u201C")
        text = text.replace('&rdquo;', u"\u201D")
        text = text.replace('&emsp;', u"\u2003")
        text = text.replace('&eacute;', u"\u00E9")
        text = text.replace('&lsquo;', u"\u2018")
        text = text.replace('&rsquo;', u"\u2019")
        text = text.replace('&ecirc;', u"\u00EA")
        text = text.replace('&agrave;', u"\u00E0")
        text = text.replace('&egrave;', u"\u00E8")
        text = text.replace('&oelig;', u"\u0153")
        text = text.replace('&aelig;', u"\u00E6")
        text = text.replace('&hellip;', u"\u2026")

        return ET.fromstring(text.encode("utf-8"))
