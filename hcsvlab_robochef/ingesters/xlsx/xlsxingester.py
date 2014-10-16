# -*- coding: utf-8 -*-
import os.path
import xlrd
import mimetypes

from hcsvlab_robochef import utils
from hcsvlab_robochef.ingesters.ingester_base import IngesterBase
from hcsvlab_robochef.ingesters.xlsx.rdf import get_map
from hcsvlab_robochef.utils.serialiser import *
from hcsvlab_robochef.utils.statistics import *
from hcsvlab_robochef.utils.filehandler import FileHandler
from hcsvlab_robochef import configmanager

QUOTE_AND_SPACE = " \"\'“”"

class XLSXIngester(IngesterBase):
    META_DEFAULTS = {'language': 'eng'}

    supported_doc_types = {
        'audio/x-wav': 'Audio',
        'audio/mpeg': 'Audio',
        'text/plain': 'Text',
        'application/rtf': 'RTF',
        'video/x-matroska': 'Video'
    }

    def __init__(self, corpus_dir, output_dir, xlsx_metadata_file, manifest_format):
        self.corpus_dir = corpus_dir
        self.corpus_id = None
        self.output_dir = output_dir or os.path.join(self.corpus_dir, 'processed')
        self.xlsx_metadata_file = xlsx_metadata_file or os.path.join(self.corpus_dir, 'metadata.xlsx')
        self.manifest_format = manifest_format or 'turtle'
        self.item_ids = []
        self.workbook = xlrd.open_workbook(self.xlsx_metadata_file)
        self.metadata = {}
        self.speakermetadata = {}

        # create output dir if not exist
        self.__create_output_dir(self.corpus_dir, self.output_dir)

    def create_n3(self):
        """
        Ingest the collection sheet and create corpus.n3 - collection metadata
        """
        collection_sheet = self.workbook.sheet_by_name('Collection') # Collection sheet

        # Collection n3 file template
        n3 = """
@prefix {corpus_id}: <{base_url}{corpus_id}> .
@prefix dcmitype: <http://purl.org/dc/dcmitype/> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix marcrel: <http://www.loc.gov/loc.terms/relators/> .


{corpus}:
    a dcmitype:Collection ;
    dc:title "{title}" ;
    dcterms:alternative "{alternative}" ;
    dcterms:abstract "{abstract}" ;
    dcterms:itemType "{item_type}" ;
    dc:creator "{creator}" ;
    dcterms:extent "{extent}" ;
    marcrel:OWN "{owner}" ;
    dcterms:language "{language}" ;
    .
"""
        # base_url
        configmanager.configinit()
        base_url = configmanager.get_config("CORPUS_BASE_URL", None)

        title = self.__convert(collection_sheet.row(1)[1]) # Collection Title
        corpus = self.__convert(collection_sheet.row(2)[1]) # Collection Identifier
        self.corpus_id = corpus.lower() # All output use lowercase corpus id
        extent = self.__convert(collection_sheet.row(3)[1]) # Extent
        language = self.__convert(collection_sheet.row(4)[1]) # Language
        item_type = self.__convert(collection_sheet.row(5)[1]) # Item Type
        creator = self.__convert(collection_sheet.row(7)[1]) # Contributors
        owner = self.__convert(collection_sheet.row(8)[1]) # Owner
        abstract = self.__convert(collection_sheet.row(12)[1]) # Abstract
        alternative = corpus

        # write n3 file
        n3_filename = "{corpus_id}.n3".format(corpus_id = self.corpus_id)
        n3_file = open(os.path.join(self.output_dir, n3_filename), 'w+')
        print "  generate collection n3 file - " + n3_file.name
        n3_file.write(n3.format(corpus_id = self.corpus_id,
                                corpus = corpus,
                                base_url = base_url,
                                title = title,
                                extent = extent,
                                language = language,
                                item_type = item_type,
                                creator = creator,
                                owner = owner,
                                abstract = abstract,
                                alternative = alternative))
        n3_file.close()

    def set_metadata(self):
        """
        Set the spreadsheet file from which corpus metadata is read. This data will
        be combined with the pathnames to the documents themselves.
        """

        # The "Files" sheet
        recording_sheet = self.workbook.sheet_by_name('Files')

        # The property names
        tags = map(self.__convert, recording_sheet.row(0))

        # The "Speakers" sheet
        speaker_sheet = self.workbook.sheet_by_name('Speakers')

        # The speaker's attributes
        speaker_attribute_names = map(self.__convert, speaker_sheet.row(0))

        for row in [recording_sheet.row(i) for i in range(1, recording_sheet.nrows)]:
            item_id = self.__convert(row[0])
            self.item_ids.append(item_id)
            item_metadata = {'sampleid': item_id}
            item_metadata.update(self.META_DEFAULTS)
            for idx in range(1, recording_sheet.ncols):
                property_name = tags[idx].strip()
                property_value = self.__convert(row[idx]).strip()
                item_metadata[property_name] = property_value

            # Collect speaker metadata
            self.speakermetadata[item_id] = []
            speaker_ids = item_metadata["Speaker"].split(',')

            for speaker_id in speaker_ids:
                speaker_id = speaker_id.strip(QUOTE_AND_SPACE)

                if len(speaker_id) == 0: continue

                speaker_row = self.__look_for_speaker(speaker_id, speaker_sheet)

                if speaker_row:
                    speaker_metadata = { "id": speaker_id }
                    for i in range(1, speaker_sheet.ncols):
                        attribute_name = speaker_attribute_names[i].strip()
                        attribute_value = self.__convert(speaker_row[i]).strip()
                        speaker_metadata[attribute_name] = attribute_value

                    self.speakermetadata[item_id].append({ u'table_person_' + speaker_id: speaker_metadata })
                else:
                    print "### WARN: Speaker with id \"{0}\" not found.".format(speaker_id)

            self.metadata[item_id] = item_metadata

    def ingest_corpus(self):
        count = 0
        total = len(self.item_ids)

        print "  converting corpus", self.corpus_dir, "into normalised data in ", self.output_dir
        print "    processing items..."

        for item_id in self.item_ids:
            count += 1
            print "   ", count, "of", total, "ITEM:" + item_id
            docs = self.metadata[item_id]["File Name"].split(',')

            source_list = []
            for doc in docs:
                doc = doc.strip(QUOTE_AND_SPACE)

                if self.__is_valid_filename(doc):
                    path = os.path.join(self.corpus_dir, doc)

                    # make sure we can at least read this file
                    os.stat(path)

                    if os.path.isfile(path):
                        # source is a dict
                        source_type = self.__get_filetype(doc)

                        if source_type == None:
                            print "      WARN:" + path + " is not one of supported types: " +\
                                  ", ".join(self.supported_doc_types.keys()) + ", ignored"
                        else:
                            if source_type == 'Text':
                                source_list.append({'filetype': source_type,
                                                    'sourcepath': path, 'rawtext': None, 'text': None})
                            else:
                                source_list.append({'filetype': source_type, 'sourcepath': path})
                            print "      DOC:" + path
                    else:
                        print "      WARN:" + path + " is not regular file, ignored"

            self.__serialise(self.output_dir, item_id, source_list)

        print "   ", total, " Items processed"

    def ingest_document(sourcepath):
        '''
        Ingest a specific source document, from which meta-data annotations and raw data is produced
        '''
        print "Error: calling unsupported operation - ingest_document(" + sourcepath + ")"
        return None

    def identify_documents(self, documents):
        # should only be one document, which is the display document
        if len(documents) == 1:
            return None, documents[0]['uri']
        return None, None

    def __serialise(self, outdir, item_id, source_list):
        '''
        Function serialises the graphs to disc and returns the object graph to the caller
        '''
        serialiser = Serialiser(outdir)

        meta = {}
        meta.update(self.metadata[item_id])

        for speaker_metadata in self.speakermetadata[item_id]:
            meta.update(speaker_metadata)

        #speaker_id = self.metadata[item_id]["Speaker"]
        #meta.update(self.speakermetadata[speaker_id])

        return serialiser.serialise_multiple(item_id, source_list, self.corpus_id,
                                              get_map(self.corpus_id), meta, [],
                                              self.identify_documents)

    def __look_for_speaker(self, speaker_id, speaker_sheet):
        ''' Function  iterates the speakers sheet looking for speaker_id '''
        for row in [speaker_sheet.row(i) for i in range(1, speaker_sheet.nrows)]:
            currentId = self.__convert(row[0])
            if currentId == speaker_id:
                return row
        return None

    def __convert(self, cell):
        ''' There are no float values in the Excel sheet. Cut hem here to int before converting to unicode. '''
        if cell.ctype == xlrd.XL_CELL_DATE:
            return unicode(xlrd.xldate.xldate_as_datetime(cell.value, self.workbook.datemode))

        if cell.ctype in (xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_BOOLEAN):
            return unicode(int(cell.value))

        return cell.value.encode('utf-8')

    def __create_output_dir(self, corpus_dir, output_dir):
        # create output directory structure, current is one single dir, should be extensible to a whole dir tree if necessary
        # output_dir by default is corpus_dir/processed if not specified
        o_dir = output_dir or os.path.join(corpus_dir, 'processed')

        if os.path.exists(o_dir):
            delete = self.__query_yes_no("Output directory exists: {0}, Delete?".format(o_dir))

            if delete:
                shutil.rmtree(o_dir)
            else:
                print "Aborted\nYou can manually delete it or use --output <DIR> to specify another one"
                sys.exit(0)

        # create output dir
        os.mkdir(o_dir)

    def __get_filetype(self, filename):
        filetype = mimetypes.guess_type(filename)[0]

        if self.supported_doc_types.has_key(filetype):
            return self.supported_doc_types[filetype]
        else:
            return None

    def __is_valid_filename(self, str):
        return len(str) > 0 and re.search(r'\w', str)

    def __query_yes_no(self, question, default = "no"):
        """Ask a yes/no question via raw_input() and return their answer.

        "question" is a string that is presented to the user.
        "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

        The "answer" return value is one of "yes" or "no".
        """
        valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}

        if default is None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            raise ValueError("invalid default answer: '%s'" % default)

        while True:
            sys.stdout.write(question + prompt)
            choice = raw_input().lower()

            if default is not None and choice == '':
                return valid[default]
            elif choice in valid:
                return valid[choice]
            else:
                sys.stdout.write("Please respond with 'yes' or 'no' "
                                 "(or 'y' or 'n').\n")