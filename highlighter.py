import argparse, re, sys
# fileinput

searches = []

class HighlightSearch():
    defaultForeground = 'Black'
    defaultBackground = 'Yellow'
    def __init__(self, searchPat):
        try:
            self.searchPat = re.compile(searchPat)
            self.compileError = False
        except re.error, e:
            sys.stderr.write('ERROR: Invalid regex "{0}"\n    {1}\n'.format(searchPat, e))
            self.compileError = True
            
    def isError(self):
        return self.compileError
    
    def search(self, text):
       (newText,numChanges) = self.searchPat.subn('<Start>\g<0><Stop>', text)
       foundMatch = True if numChanges>0 else False
       return (foundMatch, newText)
        
    
    
        
        
        

def parseConfigurationFile(configFile):
    return None
    
    
def BuildSearch(searchLine):
    pass

    
def main():
    global searches
    
    parser = argparse.ArgumentParser(description='Highlight matching text from standard input')
    #parser.add_argument('filename', nargs='?', help='Use file instead of stdin for input')
    parser.add_argument('file', nargs='?', default=sys.stdin, type=argparse.FileType('r'), help='Use file instead of stdin for input')
    #parser.add_argument('filename', nargs='?', default=None, help='Use file instead of stdin for input')
    parser.add_argument('-c', '--config',  action='append', help='Load configuration file to speify search terms')
    parser.add_argument('-s', '--search',  action='append', help='Define a regular expression to search for (and highlight)')
    parser.add_argument('-m', '--match-only', action='store_true', default=False, help='Only output matching lines')
    
    args = parser.parse_args()
    print 'args ={0}\n\n'.format(args)

    if args.config:
        for configFile in args.config:
            configSearches = parseConfigurationFile(configFile)
            
    if args.search:
        for search in args.search:
            hls = HighlightSearch(search)
            searches.append(hls)
            
    if len(searches)==0:
        parser.error('There are no search patterns defined\n\n')
    else:
        for line in args.file:
        
            foundMatch = False
            for search in searches:
                (lineMatch,line) = search.search(line)
                if lineMatch:
                    foundMatch = True
            if not args.match_only or foundMatch:
                sys.stdout.write(line)
                    
                
            


if __name__ == '__main__':
	main()