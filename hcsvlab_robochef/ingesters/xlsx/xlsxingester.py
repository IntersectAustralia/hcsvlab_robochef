import os.path
import xlrd
import mimetypes

from hcsvlab_robochef import utils
from hcsvlab_robochef.ingesters.ingester_base import IngesterBase
from hcsvlab_robochef.ingesters.xlsx.rdf import get_map
from hcsvlab_robochef.utils.serialiser import *
from hcsvlab_robochef.utils.statistics import *
from hcsvlab_robochef.utils.filehandler import FileHandler


class XLSXIngester(IngesterBase):
    metadata = {}
    speakermetadata = {}
    META_DEFAULTS = {'language': 'eng'}

    def __init__(self, corpus_dir, output_dir, xlsx_metadata_file, n3_metadata_file, manifest_format):
        self.corpus_dir = corpus_dir
        self.corpus_id = os.path.basename(corpus_dir)
        self.output_dir = output_dir or os.path.join(self.corpus_dir, 'processed')
        self.xlsx_metadata_file = xlsx_metadata_file or os.path.join(self.corpus_dir, 'metadata.xlsx')
        self.n3_metadata_file = n3_metadata_file or os.path.join(self.corpus_dir, 'metadata.n3')
        self.manifest_format = manifest_format or 'turtle'
        self.item_ids = []

        # create output dir if not exist
        self.__create_output_dir(self.corpus_dir, self.output_dir)

    def set_metadata(self):
        """
        Set the spreadsheet file from which corpus metadata is read. This data will
        be combined with the pathnames to the documents themselves.
        """

        wb = xlrd.open_workbook(self.xlsx_metadata_file)

        # The "Recordings" sheet
        recording_sheet = wb.sheet_by_index(2)

        # The property names
        tags = map(self.__convert, recording_sheet.row(0))

        # The "Speakers" sheet
        speaker_sheet = wb.sheet_by_index(3)

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
            speaker_id = self.__convert(row[11])
            speaker_row = self.__look_for_speaker(speaker_id, speaker_sheet)
            if speaker_row:
                self.speakermetadata[speaker_id] = {
                    u'table_person_' + speaker_id: {
                        "id": speaker_id,
                        "Gender": self.__convert(speaker_row[1])
                    }
                }
            else:
                print "### WARN: Speaker with id", speaker_id, "Not found."

            self.metadata[item_id] = item_metadata

    def ingest_corpus(self):
        count = 0
        total = len(self.item_ids)

        print "  converting corpus", self.corpus_dir, "into normalised data in ", self.output_dir
        print "    clearing and creating output location"

        self.clear_output_dir(self.output_dir)

        print "    processing items..."

        for item_id in self.item_ids:
            count += 1
            print "   ", count, "of", total, "ITEM:" + item_id
            docs = self.metadata[item_id]["File Name"].split(',')
            source_list = []
            for doc in docs:
                path = os.path.join(self.corpus_dir, doc)
                # source is a dict
                source_type = self.__get_filetype(doc)
                if source_type == 'Text':
                    source_list.append({'filetype': source_type, 'sourcepath': path, 'rawtext': None, 'text': None})
                else:
                    source_list.append({'filetype': source_type, 'sourcepath': path})
                print "      DOC:" + path
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
        speaker_id = self.metadata[item_id]["Speaker"]
        meta.update(self.speakermetadata[speaker_id])

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
        if cell.ctype in (2, 3, 4):
            return unicode(int(cell.value))
        return cell.value

    def __create_output_dir(self, corpus_dir, output_dir):
        # create output directory structure, current is one single dir, should be extensible to a whole dir tree if necessary
        # output_dir by default is corpus_dir/processed if not specified
        o_dir = output_dir or os.path.join(corpus_dir, 'processed')
        # create output dir
        os.mkdir(o_dir)

    def __get_filetype(self, filename):
        types = {
            'audio/x-wav': 'Audio',
            'audio/mpeg': 'MP3',
            'text/plain': 'Text',
            'application/rtf': 'RTF'
        }
        filetype = mimetypes.guess_type(filename)[0]
        return types[filetype]
