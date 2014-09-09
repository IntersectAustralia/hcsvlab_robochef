import os.path
import xlrd

from hcsvlab_robochef import utils
from hcsvlab_robochef.ingest_base import IngestBase
from hcsvlab_robochef.mbep.rdf import mbepMap
from hcsvlab_robochef.utils.serialiser import *
from hcsvlab_robochef.utils.statistics import *
from hcsvlab_robochef.utils.filehandler import FileHandler


class MbepIngest(IngestBase):

    metadata = {}
    speakermetadata = {}
    META_DEFAULTS = {'language': 'eng'}

    def setMetaData(self, filename):
        """
        Set the spreadsheet file from which pixar metadata is read.  This data will
        be combined with the pathnames to the documents themselves.
        """

        wb = xlrd.open_workbook(filename)
        sheet = wb.sheet_by_index(2)
        tags = map(self.__convert, sheet.row(0))

        speakerSheet = wb.sheet_by_index(3)


        for row in [sheet.row(i) for i in range(1, sheet.nrows)]:
            sampleid = self.__convert(row[0]).replace(".wav", "")
            row_metadata = { 'sampleid': sampleid }
            row_metadata.update(self.META_DEFAULTS)
            for idx in range(1, sheet.ncols):
                propertyName = tags[idx].strip()
                propertyValue = self.__convert(row[idx]).strip()
                row_metadata[propertyName] = propertyValue

            # Collect speaker metadata
            speakerId = self.__convert(row[10])
            speakerRow = self.__lookForSpeaker(speakerId, speakerSheet)
            if (speakerRow != None):
                self.speakermetadata[speakerId] = {
                    u'table_person_' + speakerId: {
                        "id":speakerId,
                        "Gender":self.__convert(speakerRow[1])
                    }
                }
            else:
                print "### WARN: Speaker with id", speakerId, "Not found."

            self.metadata[sampleid] = row_metadata

    def ingestCorpus(self, srcdir, outdir):

        print "  converting corpus", srcdir, "into normalised data in ", outdir
        print "    clearing and creating output location"
      
        self.clear_output_dir(outdir)

        print "    processing files..."

        dirs = os.walk(srcdir)

        fileHandler = FileHandler()
        files = fileHandler.getFiles(srcdir, r'^.+\.wav')
        total = len(files.keys())

        sofar = 0
        for name, path in files.iteritems():
            item_name = name.replace(".wav", "")
            self.__serialise(outdir, item_name, path)
            sofar += 1
            print "   ", sofar, "of", total, "DOC:" + path

        print "   ", total, " Items processed"


    def ingestDocument(sourcepath):
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
            speakerId = self.metadata[sampleid]["Speaker"]
            meta.update(self.speakermetadata[speakerId])

            return serialiser.serialise_single_nontext(sampleid, 'MBEP', source, "Audio", mbepMap, meta, [], self.identify_documents)
        else:
            print ""
            print "### Error: file '", source, "' with key '", sampleid, "' has no metadata."
            print ""

    def __lookForSpeaker(self, speakerId, speakerSheet):
        ''' Function  iterates the speakers sheet looking for speakerId '''
        for row in [speakerSheet.row(i) for i in range(1, speakerSheet.nrows)]:
            currentId = self.__convert(row[0])
            if currentId == speakerId:
                return row
        return None


    def __convert(self, cell):
        ''' There are no float values in the Excel sheet. Cut hem here to int before converting to unicode. '''
        if cell.ctype in (2, 3, 4):
            return unicode(int(cell.value))
        return cell.value
