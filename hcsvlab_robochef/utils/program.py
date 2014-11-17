import os


def getCorporaArgs(argsv):
  """
  Gets the list of live corpora from the command line arguments.  Will give
  all corpora for no arguemnts and will return whatever arguments were given
  otherwise

  >>> getCorporaArgs([])
  []
  >>> getCorporaArgs(["main"])
  ['cooee', 'ace', 'ice', 'monash', 'griffith', 'md', 'auslit', 'braided', 'paradisec']
  >>> getCorporaArgs(['main', 'one'])
  ['one']
  """
  corpra = []
  if (len(argsv) == 1):
    corpra = ["cooee", "ace", "ice", "monash", 'griffith', 'md', 'auslit', 'art', 'braided']
  else:
    corpra = argsv[1:]
  return corpra

def listFiles(res, dir, rec=True, ignore_list=[]):
  """
  Recursively lists all files in a given directory.
  ignore_list specifies a list of names for directories which are ignored when listing directory contents.
  """
  more = []
  for i in os.listdir(dir):
    # Only process files or directories if they are not in the ignore list.
    if not (i in ignore_list):
      if os.path.isfile(os.path.join(dir, i)):
        res[:0] = [os.path.join(dir, i)]
      else:
        more[:0] = [i]

  if (rec):
    for j in more:
      listFiles(res, os.path.join(dir, j), rec, ignore_list)
