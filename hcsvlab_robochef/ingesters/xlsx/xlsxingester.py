import os.path
import xlrd

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

        # create output dir if not exist
        self.__create_output_dir(self.corpus_dir, self.output_dir)


    def set_metadata(self):
        """
        Set the spreadsheet file from which corpus metadata is read. This data will
        be combined with the pathnames to the documents themselves.
        """

        wb = xlrd.open_workbook(self.xlsx_metadata_file)
        sheet = wb.sheet_by_index(2)
        tags = map(self.__convert, sheet.row(0))

        speaker_sheet = wb.sheet_by_index(3)

        for row in [sheet.row(i) for i in range(1, sheet.nrows)]:
            sampleid = self.__convert(row[0]).replace(".wav", "")
            row_metadata = {'sampleid': sampleid}
            row_metadata.update(self.META_DEFAULTS)
            for idx in range(1, sheet.ncols):
                propertyName = tags[idx].strip()
                propertyValue = self.__convert(row[idx]).strip()
                row_metadata[propertyName] = propertyValue

            # Collect speaker metadata
            speaker_id = self.__convert(row[10])
            speaker_row = self.__look_for_speaker(speaker_id, speaker_sheet)
            if (speaker_row != None):
                self.speakermetadata[speaker_id] = {
                    u'table_person_' + speaker_id: {
                        "id": speaker_id,
                        "Gender": self.__convert(speaker_row[1])
                    }
                }
            else:
                print "### WARN: Speaker with id", speaker_id, "Not found."

            self.metadata[sampleid] = row_metadata


    def ingest_corpus(self):

        print "  converting corpus", self.corpus_dir, "into normalised data in ", self.output_dir
        print "    clearing and creating output location"

        self.clear_output_dir(self.output_dir)

        print "    processing files..."

        dirs = os.walk(self.corpus_dir)

        fileHandler = FileHandler()
        files = fileHandler.getFiles(self.corpus_dir, r'^.+\.wav')
        total = len(files.keys())

        sofar = 0
        for name, path in files.iteritems():
            item_name = name.replace(".wav", "")
            self.__serialise(self.output_dir, item_name, path)
            sofar += 1
            print "   ", sofar, "of", total, "DOC:" + path

        print "   ", total, " Items processed"


    def ingest_document(sourcepath):
        '''
        Ingest a specific source document, from which meta-data annotations and raw data is produced
        '''
        print "Error: calling unsupported operation - ingestDocument(" + sourcepath + ")"
        return None


    def identify_documents(self, documents):
        # should only be one document, which is the display document
        if len(documents) == 1:
            return (None, documents[0]['uri'])
        return (None, None)


    def __serialise(self, outdir, sampleid, source):
        '''
        Function serialises the graphs to disc and returns the object graph to the caller
        '''
        serialiser = Serialiser(outdir)

        if (sampleid in self.metadata):
            meta = {}
            meta.update(self.metadata[sampleid])
            speaker_id = self.metadata[sampleid]["Speaker"]
            meta.update(self.speakermetadata[speaker_id])

            return serialiser.serialise_single_nontext(sampleid, 'MBEP', source, "Audio", get_map(self.corpus_id), meta, [],
                                                       self.identify_documents)
        else:
            print ""
            print "### Error: file '", source, "' with key '", sampleid, "' has no metadata."
            print ""


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

