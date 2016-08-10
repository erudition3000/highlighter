import argparse, re, sys
from xml.etree import cElementTree as ET
#import cElementTree as ET


#colors are 0:black, 1:red, 2:green, 3:yellow, 4:blue, 5: magenta, 6:cyan, 7:white
#Font colors are in the 30s and background colors are in the 40s
#Add '1; before the color to make it 'bright intensity'
#
#This might help. Run the command: echo -e "testing \033[0;37;41mCOLOR1\033[1;35;44mCOLOR2\033[m"
#This should output testing COLOR1COLOR2 with COLOR1 being white (light gray) text on a red background, and COLOR2 being bold / bright magenta text on a blue background. All subsequent text should be normally colored.

class HighlightSearch():
    defaultForeground = '0'	#black
    defaultBackground = '3'	#yellow
    defaultBrightness = '0'	#Dark
    startTagTemplate = '\e[{0};3{1};4{2}m'
    endTag = r'\e[0m'	#normal
    colorMap = {'black': '0', 'red':'1', 'green':'2', 'yellow':'3', 'blue':'4', 'magenta':'5', 'cyan':'6', 'white':'7'}

    def __init__(self, searchPat):
        self.brightColor = self.defaultBrightness
        
        try:
            self.searchPat = re.compile(searchPat[0])
            self.compileError = False
        except re.error, e:
            sys.stderr.write('ERROR: Invalid regex "{0}"\n    {1}\n'.format(searchPat[0], e))
            self.compileError = True
            
        if len(searchPat)<2:
            self.foreground = self.defaultForeground
        else:
            fg = searchPat[1].lower()
            if 'light-' in fg:
                self.brightColor = 1
                fg = fg.replace('light-','')
            if self.colorMap.has_key(fg):
                self.foreground = self.colorMap[fg]
            else:
                self.foreground = self.defaultForeground
                sys.stderr.write('ERROR: Invalid foreground color "{0}"\n'.format(searchPat[1]))
                self.compileError = True
        
        if len(searchPat)<3:
            self.background = self.defaultBackground
        else:
            bg = searchPat[2].lower()
            if self.colorMap.has_key(bg):
                self.background = self.colorMap[bg]
            else:
                self.background = self.defaultBackground
                sys.stderr.write('ERROR: Invalid background color "{0}"\n'.format(searchPat[2]))
                self.compileError = True
            
    def isError(self):
        return self.compileError
    
    def search(self, text):
       startTag = self.startTagTemplate.format(self.brightColor, self.foreground, self.background)
       (newText,numChanges) = self.searchPat.subn('{0}\g<0>{1}'.format(startTag,self.endTag), text)
       foundMatch = True if numChanges>0 else False
       return (foundMatch, newText)
        
    
    
def parseCommandLine():
    searches = []
    commandLineError = False
    parseError = False
    
    parser = argparse.ArgumentParser(description='Highlight matching text from standard input')
    parser.add_argument('file', nargs='?', default=sys.stdin, type=argparse.FileType('r'), help='Use file instead of stdin for input')
    parser.add_argument('-c', '--config',  action='append', help='Load configuration file to speify search terms')
    parser.add_argument('-s', '--search',  nargs='+', action='append', help='Define a regular expression to search for (and highlight) followed by optional forground and background colors.  Colors can be one of: black, red, green, yellow, blue, magenta, cyan, white')
    parser.add_argument('-m', '--match-only', action='store_true', default=False, help='Only output matching lines')
    
    args = parser.parse_args()
    #print 'args ={0}\n\n'.format(args)

    if args.config:
        for configFile in args.config:
            (configSearches, parseError) = parseConfigurationFile(configFile)
            if parseError:
                break
            searches.extend(configSearches)
            
    if not parseError and args.search:
        for searchArg in args.search:
            hls = HighlightSearch(searchArg)
            if not hls.compileError:
                searches.append(hls)
            else:
                commandLineError = True
                break
            
    if parseError or commandLineError:
        #parser.print_help()
        parser.print_usage()
        sys.exit(1)
    return (parser, args, searches)
            
    

def parseConfigurationFile(configFile):
    searches = []
    parseError = False
    
    try:
        print 'Parsing',configFile
        dom = ET.parse(open(configFile, 'r'))
        root = dom.getroot()
        for searchTag in root.findall('search'):
            (fg,bg) = (None, None)
            searchPat = searchTag.text
            if searchTag.attrib.has_key('fg'):
                fg = searchTag.attrib['fg']
                if searchTag.attrib.has_key('bg'):
                    bg = searchTag.attrib['bg']
            
            searchArg = [searchPat]
            if fg:
                searchArg.append(fg)
            if bg:
                searchArg.append(bg)
            hls = HighlightSearch(searchArg)
            if not hls.compileError:
                searches.append(hls)
            else:
                parseError = True
                break
            
    except ET.ParseError, e:
        sys.stderr.write('ERROR: Parsing file "{0}"\n    {1}\n'.format(configFile, e))
        parseError = True
    except IOError, e:
        sys.stderr.write('ERROR: Parsing file "{0}"\n    {1}\n'.format(configFile, e))
        parseError = True
    
    return (searches, parseError)


    
def main():
    global searches
    
    (parser, args, searches) = parseCommandLine()
    
    if len(searches)==0:
        #parser.error('There are no search patterns defined\n\n')
        sys.stdout.write('ERROR: There are no search patters defined\n\n')
        parser.print_usage()
        
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
    #print 'argv =',sys.argv
    main()