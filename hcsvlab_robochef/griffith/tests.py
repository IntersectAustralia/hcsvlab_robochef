# coding: utf-8
import unittest
import doctest

from hcsvlab_robochef.griffith.ingest import *
from hcsvlab_robochef.griffith import ingest
from hcsvlab_robochef.rdf.map import *


def unittests():
  res = doctest.DocTestSuite(ingest)
  res.addTest(unittest.makeSuite(UnitTest))
  return res


class UnitTest(unittest.TestCase):

  configmanager.configinit()
  corpus_basedir = configmanager.get_config("CORPUS_BASEDIR", "../input/")
  griffith = GriffithIngest()
  # griffith.setMetaData(corpus_basedir + "griffith/metadata")

  def test_meta_extract(self):
     # We do not assert anything here, we call this to make sure it runs and does not fall over
    self.griffith.setMetaData(self.corpus_basedir + "griffith/metadata")
  
  
  def testPossibleLine(self):
	  res = self.griffith._GriffithIngest__possibleLine().parseString("91 hi\n")[0]
	  self.assertEqual(res, " hi")
	  
	  res = self.griffith._GriffithIngest__possibleLine().parseString("91 \n")[0]
	  self.assertEqual(res, " ")
	
	
  def testSimpleAnnotation(self):
    res = self.griffith._GriffithIngest__markupParser().parseString("hi:there")[0]
    self.assertEqual(res.text, "hithere")
    self.assertEqual(res.anns, [Annotation("elongation", "", 2, 2)])
    
    res = self.griffith._GriffithIngest__markupParser().parseString("what(.)the")[0]
    self.assertEqual(res.text, "what the")
    self.assertEqual(res.anns, [Annotation("micropause", "", 4, 5)])

    res = self.griffith._GriffithIngest__markupParser().parseString("what(1.2)the")[0]
    self.assertEqual(res.text, "what the")
    self.assertEqual(res.anns, [Annotation("pause", "1.2", 4, 5)])


  def testManyAnnotations(self):
    res = self.griffith._GriffithIngest__markupParser().parseString("hi:there(.)chap")[0]
    self.assertEqual(res.text, "hithere chap")
    self.assertEqual(res.anns, [Annotation("elongation", "", 2, 2), Annotation("micropause", "", 7, 8)])

    res = self.griffith._GriffithIngest__markupParser().parseString("hi(1.3):there(.)chap")[0]
    self.assertEqual(res.text, "hi there chap")
    self.assertEqual(res.anns, [Annotation("pause", "1.3", 2, 3),Annotation("elongation", "", 3, 3), Annotation("micropause", "", 8, 9)])

    res = self.griffith._GriffithIngest__markupParser().parseString("hi(1.3):there(.)::c:hap")[0]
    self.assertEqual(res.text, "hi there chap")
    self.assertEqual(res.anns, [Annotation("pause", "1.3", 2, 3),Annotation("elongation", "", 3, 3), Annotation("micropause", "", 8, 9),Annotation("elongation", "", 9, 9),Annotation("elongation", "", 9, 9),Annotation("elongation", "", 10, 10)])

    
  def testNestedAnnotations(self):
    res = self.griffith._GriffithIngest__markupParser().parseString("what >the fast >really fast<<")[0]
    self.assertEqual(res.text, "what the fast really fast")
    self.assertEqual(res.anns, [Annotation("speed", "compressed", 14, 25), Annotation("speed", "compressed", 5, 25)])

  
  def testSpeakerParser(self):
    res = self.griffith._GriffithIngest__ourSpeakerParser().parseString("J: Hi there")[0]
    self.assertEqual(res.text, "Hi there")
    self.assertEqual(res.anns, [Annotation("speaker", "J", 0, 8)])
    
    res = self.griffith._GriffithIngest__ourSpeakerParser().parseString("J: Hi there\nK: Hello")[0]
    self.assertEqual(res.text, "Hi there\nHello")
    self.assertEqual(res.anns, [Annotation("speaker", "J", 0, 8), Annotation("speaker", "K", 9,14)])
    
    res = self.griffith._GriffithIngest__ourSpeakerParser().parseString("        J:    Nicky are you coming to uni on\n          Monday to listen to Jacqui's presentation?")[0]
    self.assertEqual(res.text, "Nicky are you coming to uni on\n          Monday to listen to Jacqui's presentation")
    self.assertEqual(res.anns, [Annotation("intonation", "rising", 82, 82), Annotation("speaker", "J", 0, 82)])

    res = self.griffith._GriffithIngest__ourSpeakerParser().parseString("        J:    Nicky are you coming to uni on\n          Monday to listen to Jacqui's presentation?            (.)")[0]
    self.assertEqual(res.text, "Nicky are you coming to uni on\n          Monday to listen to Jacqui's presentation ")
    self.assertEqual(res.anns, [Annotation("intonation", "rising", 82, 82),Annotation("micropause", "", 82, 83), Annotation("speaker", "J", 0, 83)])
  
    body, anns = self.griffith._GriffithIngest__extractAnnotations("        J:    Nicky are you coming to uni on\n          Monday to listen to Jacqui's presentation?            (.)")
    self.assertEqual(body, "Nicky are you coming to uni on\n          Monday to listen to Jacqui's presentation ")
    self.assertEqual(anns, [Annotation("intonation", "rising", 82, 82),Annotation("micropause", "", 82, 83), Annotation("speaker", "J", 0, 83)])


  def testSpeakerParserWithTurnPreceededWithPipe(self):
    body, anns = self.griffith._GriffithIngest__extractAnnotations("|J: Hi there")
    
    self.assertEqual(body, "Hi there")
    self.assertEqual(anns, [Annotation("speaker", "J", 0, 8)])


  def testSpeakerParserWithTurnPreceededWithMultiplePipe(self):
     body, anns = self.griffith._GriffithIngest__extractAnnotations("|J: |Hi there  |")

     self.assertEqual(body, "Hi there")
     self.assertEqual(anns, [Annotation("speaker", "J", 0, 8)])
       
  
  def testOneParticularDocumentGCSAusE22(self):  
    (text, body, meta, anns) = self.griffith.ingestDocument(self.corpus_basedir + 'griffith/GCSAusE22.doc')
    self.assertEqual(anns[0], Annotation("elongation", "", 1, 1))
  
    (meta_graph, ann_graph) = self.griffith._GriffithIngest__serialise(self.corpus_basedir + 'griffith/',
                                                                       '/tmp', self.corpus_basedir + 'griffith/GCSAusE22.doc',
                                                                       'GCSAusE22.doc', text, body, meta, anns)
  
    root_id = griffMap.item_uri(meta['sampleid'])
    
    # Assert that the root sample as a title which is mandatory
    self.assertTrue((root_id, DC.title, Literal("GCSAusE22")) in meta_graph)   
    
  
  def testOneParticularDocumentGCSAusE01(self):
    
    (text, body, meta, anns) = self.griffith.ingestDocument(self.corpus_basedir + 'griffith/GCSAusE01.doc')
    
    # Has 2 participants only
    self.assertTrue(meta.has_key('table_person_Participant_1'))
    self.assertTrue(meta.has_key('table_person_Participant_2'))
    self.assertFalse(meta.has_key('table_person_Participant_3'))

    # Is comprised of two documents one Text, the other Audio
    self.assertTrue(meta.has_key('table_document_GCSAusE01#Text'))
    self.assertFalse(meta.has_key('table_document_GCSAusE01#Audio'))
    
    self.assertTrue(meta['table_document_GCSAusE01#Text'].has_key('Title'))
       
       
  def testFullData(self):
    data = """
    Transcript Coversheet
    |                      |Data                                        |
    |Title                 |GCSAusE18                                   |
    |Number of people      |2                                           |
    |Description           |A transcribed conversation between two      |
    |                      |female classmates that occurred before class|
    |                      |in a tutorial room.                         |
    |Participants          |Nicky (32, Australia, female, L1 English,   |
    |                      |AU,                                         |
    |                      |Undergraduate, Student/Waitress)            |
    |                      |Judith (59, Australia, female, L1 English,  |
    |                      |AU,                                         |
    |                      |Undergraduate, Student/Secondary teacher)   |
    |Date of recording     |April 2009                                  |
    |Place of recording    |Brisbane                                    |
    |Length of recording   |8 minutes 0 seconds                         |
    |Contributor of        |Jessica Park                                |
    |recording             |                                            |
    |Length of transcript  |1,825 words, 9,914 characters (with spaces),|
    |                      |267 lines(0:00-5:17)                        |
    |Number of pages       |9                                           |
    |Transcribers          |Jessica Park (April 2009)                   |
    |                      |Yasuhisa Watanabe (June 2009)               |
    |Date transcription    |7 October 2009                              |
    |last modified         |                                            |
    |Creator               |Michael Haugh                               |
    1      J:    Nicky are you coming to uni on
    2            Monday to listen to Jacqui's presentation?
    3            (.)
    """
    
    topTable = self.griffith.parseTopTable(data)['topTable']
    body = self.griffith.parseBody(data)["body"]
    
    body, anns = self.griffith._GriffithIngest__extractAnnotations(body)    
    self.assertEqual(body, "Nicky are you coming to uni on\n            Monday to listen to Jacqui's presentation ")
    self.assertEqual(anns, [Annotation("intonation", "rising", 84, 84),Annotation("micropause", "", 84, 85), Annotation("speaker", "J", 0, 85)])
    self.assertEqual(topTable["Title"], "GCSAusE18")
    self.assertEqual(topTable["Number of people"], "2")
    self.assertEqual(topTable["Date of recording"], "April 2009")
    self.assertEqual(topTable["Length of recording"], "8 minutes 0 seconds")
    self.assertEqual(topTable["Transcribers"], "Jessica Park (April 2009) Yasuhisa Watanabe (June 2009)")
    self.assertEqual(topTable["last modified"], "")
    
    dataPlus = data + u"""4	N:	Ye:s I will be here, (0.8) u:m and that will 
      5		also be good too cause I've got this other
      6		assignment,\xb0 oh >did I-\xb0 < I told you about that 
      7		didn't I,=the one (.) fo:r (0.3) u:m
      """
    
    topTable = self.griffith.parseTopTable(dataPlus)['topTable']
    body = self.griffith.parseBody(dataPlus)["body"]
    body, anns = self.griffith._GriffithIngest__extractAnnotations(body)


  def testFullDataWithAdditionalPipes(self):
    data = unicode("""
    Transcript Coversheet
    |                      |Data                                        |
    |Title                 |GCSAusE18                                   |
    |Number of people      |2                                           |
    |Description           |A transcribed conversation between two      |
    |                      |female classmates that occurred before class|
    |                      |in a tutorial room.                         |
    |Participants          |Nicky (32, Australia, female, L1 English,   |
    |                      |AU,                                         |
    |                      |Undergraduate, Student/Waitress)            |
    |                      |Judith (59, Australia, female, L1 English,  |
    |                      |AU,                                         |
    |                      |Undergraduate, Student/Secondary teacher)   |
    |Date of recording     |April 2009                                  |
    |Place of recording    |Brisbane                                    |
    |Length of recording   |8 minutes 0 seconds                         |
    |Contributor of        |Jessica Park                                |
    |recording             |                                            |
    |Length of transcript  |1,825 words, 9,914 characters (with spaces),|
    |                      |267 lines(0:00-5:17)                        |
    |Number of pages       |9                                           |
    |Transcribers          |Jessica Park (April 2009)                   |
    |                      |Yasuhisa Watanabe (June 2009)               |
    |Date transcription    |7 October 2009                              |
    |last modified         |                                            |
    |Creator               |Michael Haugh                               |
    
    
    |1   |J:       |mmm um: (1.5) are you superstitious?                       |
    |2   |         |(3.0)                                                      |
    |3   |C:       |yes and no:. there’s a >bloo:dy bird<                      |
    |4   |         |(hh)ther(hh)e.                                             |
    """, errors='ignore')
    
    topTable = self.griffith.parseTopTable(data)['topTable']
    body = self.griffith.parseBody(data)["body"]
    
    body, anns = self.griffith._GriffithIngest__extractAnnotations(body)    
    self.assertEqual(body, u'mmm um  are you superstitious \nyes and no theres a bloody bird                      \n            hhtherhhe')

  def testGCSAusE18(self):
    raw = u"""N:	so it's the whole course (.) that's 
        in the same boat=
	=so [she] doesn't (.) have to and it's her- 
J:	    [yeah]
N:	she [is the convenor (0.5) so:
J:	     [yeah
          """
    body, at =  self.griffith._GriffithIngest__extractAnnotations(raw)
    self.assertEqual(body, u"so it's the whole course   that's \n        in the same boat\n        so she doesn't   have to and it's her-\nyeah\nshe is the convenor   so\nyeah")
