import logging

from hcsvlab_robochef.cooee.ingest import *
from hcsvlab_robochef.ace.ingest import *
from hcsvlab_robochef.ice.ingest import *
from hcsvlab_robochef.monash.ingest import *
from hcsvlab_robochef.griffith.ingest import *
from hcsvlab_robochef.md.ingest import *
from hcsvlab_robochef.auslit.ingest import *
from hcsvlab_robochef.braided.ingest import *
from hcsvlab_robochef.art.ingest import *
from hcsvlab_robochef.paradisec.ingest import *
from hcsvlab_robochef.eopas_test.ingest import *
from hcsvlab_robochef.avozes.ingest import *
from hcsvlab_robochef.pixar.ingest import *
from hcsvlab_robochef.austalk.ingest import *
from hcsvlab_robochef.rirusyd.ingest import *
from hcsvlab_robochef.mbep.ingest import *
from hcsvlab_robochef.jakartan_indonesian.ingest import *
from hcsvlab_robochef.llc.ingest import *
from hcsvlab_robochef.trove.ingest import *


def main():
    """
    Primary application entry point
    """
    corpora = utils.getCorporaArgs(sys.argv)

    print "cpr: corpora conversion tool\n"

    # NOTE: Configure the logger and the configuration manager
    configmanager.configinit()
    logging.basicConfig(filename='hcsvlab_robochef.log', level=logging.INFO, format='%(asctime)s %(message)s')

    corpus_basedir = configmanager.get_config("CORPUS_BASEDIR", "../input/")
    output_dir = configmanager.get_config("CORPUS_OUTPUTDIR", "../output/")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for c in corpora:
        # TODO: all these hard coded variables should be parameterised to vars set in the config.ini
        if c == "art":
            print "converting ART"
            art = ARTIngest()
            art.setMetaData(corpus_basedir + "ART/ART-corpus-catalogue.xls")
            art.ingestCorpus(corpus_basedir + "ART", output_dir + "art")
            art.create_collection_manifest(output_dir + "art", "turtle")

        elif c == "cooee":
            print "converting COOEE"
            cooee = CooeeIngest()
            cooee.setMetaData(corpus_basedir + "COOEE/COOEE.XLS")
            cooee.copy_collection_metadata(corpus_basedir, output_dir, "cooee.n3", "cooee.n3")
            cooee.ingestCorpus(corpus_basedir + "COOEE/data", output_dir + "cooee")
            cooee.create_collection_manifest(output_dir + "cooee", "turtle")

        elif c == "ace":
            print "converting ace"
            ace = ACEIngest()
            ace.setMetaData(corpus_basedir + "ace/Manual")
            ace.copy_collection_metadata(corpus_basedir, output_dir, "ace.n3", "ace.n3")
            ace.ingestCorpus(corpus_basedir + "ace", output_dir + "ace")
            ace.create_collection_manifest(output_dir + "ace", "turtle")

        elif c == "ice":
            print "converting ice"
            ice = ICEIngest()
            ice.copy_collection_metadata(corpus_basedir, output_dir, "ice.n3", "ice.n3")
            ice.ingest(os.path.join(corpus_basedir, "ICE"), os.path.join(output_dir, "ice"))
            ice.create_collection_manifest(output_dir + "ice", "turtle")

        elif c == "monash":
            print "converting monash"
            monash = MonashIngest()
            monash.copy_collection_metadata(corpus_basedir, output_dir, "monash.n3", "monash.n3")
            monash.ingestCorpus(corpus_basedir + "Monash Corpus of Australian English/Transcripts-sanitised",
                                output_dir + "monash")
            monash.create_collection_manifest(output_dir + "monash", "turtle")

        elif c == "griffith":
            print "converting griffith"
            griffith = GriffithIngest()
            griffith.setMetaData(corpus_basedir + "griffith/metadata")
            griffith.copy_collection_metadata(corpus_basedir, output_dir, "gcsause.n3", "gcsause.n3")
            griffith.ingestCorpus(corpus_basedir + "griffith", output_dir + "gcsause")
            griffith.create_collection_manifest(output_dir + "gcsause", "turtle")

        elif c == "md":
            print "converting mitchell & delbridge"
            md = MDIngest()
            md.setMetaData(corpus_basedir + "MD/flatfilesrc.txt")
            md.copy_collection_metadata(corpus_basedir, output_dir, "md.n3", "mitcheldelbridge.n3")
            md.ingestCorpus(corpus_basedir + "MD", output_dir + "mitcheldelbridge")
            md.create_collection_manifest(output_dir + "mitcheldelbridge", "turtle")

        elif c == "auslit":
            print "converting auslit"
            auslit = AuslitIngest()
            auslit.copy_collection_metadata(corpus_basedir, output_dir, "austlit.n3", "austlit.n3")
            auslit.ingestCorpus(corpus_basedir + "AusLit", output_dir + "austlit")
            auslit.create_collection_manifest(output_dir + "austlit", "turtle")

        elif c == "braided":
            print "converting braided channels"
            braided = BraidedIngest()
            braided.copy_collection_metadata(corpus_basedir, output_dir, "braided_channels.n3", "braidedchannels.n3")
            braided.ingestCorpus(corpus_basedir + "braided_channels", output_dir + "braidedchannels")
            braided.create_collection_manifest(output_dir + "braidedchannels", "turtle")

        elif c == "paradisec":
            print "converting paradisec"
            paradisec = ParadisecIngest()

            metadata_path = output_dir + "paradisec"
            paradisec.ingestCorpus(corpus_basedir + "paradisec", metadata_path)

            for item in os.listdir(metadata_path):
                subdir = os.path.join(metadata_path, item)
                if os.path.isdir(subdir):
                    paradisec.create_collection_manifest(subdir, "turtle")

        elif c == "eopas_test":
            print "converting eopas_test"
            eopas = EopasTestIngest()
            eopas.ingestCorpus(corpus_basedir + "eopas_test", output_dir + "eopas_test")
            eopas.create_collection_manifest(output_dir + "eopas_test", "turtle")

        elif c == "avozes":
            print "converting avozes"
            avozes = AvozesIngest()
            avozes.setMetaData(corpus_basedir + "avozes/Avozes.xls")
            avozes.ingestCorpus(corpus_basedir + "avozes", output_dir + "avozes")
            avozes.create_collection_manifest(output_dir + "avozes", "turtle")

        elif c == "pixar":
            print "converting Pixar Film Excerpts"
            pixar = PixarIngest()
            pixar.setMetaData(corpus_basedir + "pixar/PixarFilmExcerpts.xls")
            pixar.copy_collection_metadata(corpus_basedir, output_dir, "pixar.n3", "pixar.n3")
            pixar.ingestCorpus(corpus_basedir + "pixar", output_dir + "pixar")
            pixar.create_collection_manifest(output_dir + "pixar", "turtle")

        elif c == "austalk":
            print "converting austalk"
            austalk = AustalkIngest()

            metadata_path = os.path.join(output_dir, "austalk/metadata")
            if not os.path.exists(metadata_path):
                os.mkdir(metadata_path)

            austalk.ingestCorpus(corpus_basedir, metadata_path)
            for item in os.listdir(metadata_path):
                subdir = os.path.join(metadata_path, item)
                if os.path.isdir(subdir):
                    austalk.create_collection_manifest(subdir, "turtle")

        elif c == "rirusyd":
            print "converting Room Impulse Response"
            rir = RirIngest()
            rir.setMetaData(corpus_basedir + "rirusyd/room_impulse_responses.xlsx")
            rir.copy_collection_metadata(corpus_basedir, output_dir, "rirusyd.n3", "rirusyd.n3")
            rir.ingestCorpus(corpus_basedir + "rirusyd", output_dir + "rirusyd")
            rir.create_collection_manifest(output_dir + "rirusyd", "turtle")

        elif c == "mbep":
            print "converting Macquarie Battery of Emotional Prosody"
            mbep = MbepIngest()
            mbep.setMetaData(corpus_basedir + "mbep/mq_emotional.xlsx")
            mbep.copy_collection_metadata(corpus_basedir, output_dir, "mbep.n3", "mbep.n3")
            mbep.ingestCorpus(corpus_basedir + "mbep", output_dir + "mbep")
            mbep.create_collection_manifest(output_dir + "mbep", "turtle")

        elif c == "jakartan_indonesian":
            print "converting Jakartan Idonesian"
            jakartan = JakartanIndonesianIngest()
            jakartan.setMetaData(corpus_basedir + "jakartan_indonesian/JakartanIndonesian-modified.xlsx")
            jakartan.copy_collection_metadata(corpus_basedir, output_dir, "jakartan_indonesian.n3", "jakartan_indonesian.n3")
            jakartan.ingestCorpus(corpus_basedir + "jakartan_indonesian", output_dir + "jakartan_indonesian")
            jakartan.create_collection_manifest(output_dir + "jakartan_indonesian", "turtle")

        elif c == "llc":
            print "converting LLC"
            llc = LLCIngest()
            llc.setMetaData(corpus_basedir + "LLC/LectureCorpus_OnlineFiles_Mar25 2014.xlsx")
            llc.copy_collection_metadata(corpus_basedir, output_dir, "llc.n3", "llc.n3")
            llc.ingestCorpus(corpus_basedir + "LLC", output_dir + "llc")
            llc.create_collection_manifest(output_dir + "llc", "turtle")

        elif c == "trove":
            print "converting Trove"
            trove = TroveIngest()
            trove.ingestCorpus(corpus_basedir + "trove", output_dir + "trove")
            trove.create_collection_manifest(output_dir + "trove", "turtle")

if __name__ == "__main__":
    main()
