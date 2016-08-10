#!/usr/bin/python
import argparse, re, sys
from xml.etree import cElementTree as ET

#Looks at each line of stdin and adds ANSI color escape sequences to regular expressions
#defined on the comand-line or in a config file.  To specify colors use standard color 
#names: black, red, green, yellow, blue, magenta, cyan, white

class HighlightSearch():
    defaultForeground = '0'     #black
    defaultBackground = '3'     #yellow
    defaultBrightness = '0'     #Dark
    startTagFgBgTemplate = '\e[{0};3{1};4{2}m'
    startTagFgTemplate = '\e[{0};3{1}m'
    startTagBgTemplate = '\e[4{0}m'
    endTag = r'\e[0m'   #back to terminal default
    colorMap = {'black': '0', 'red':'1', 'green':'2', 'yellow':'3', 'blue':'4', 'magenta':'5', 'cyan':'6', 'white':'7'}

    def __init__(self, searchPat, fg=None, bg=None):
        self.brightColor = self.defaultBrightness
        self.foreground = None
        self.background = None
        
        try:
            self.searchPat = re.compile(searchPat)
            self.compileError = False
        except re.error, e:
            sys.stderr.write('ERROR: Invalid regex "{0}"\n    {1}\n'.format(searchPat, e))
            self.compileError = True
            
        if fg:
            fg = fg.lower()
            if 'light-' in fg:
                self.brightColor = 1
                fg = fg.replace('light-','')
            if self.colorMap.has_key(fg):
                self.foreground = self.colorMap[fg]
            else:
                self.foreground = self.defaultForeground
                sys.stderr.write('ERROR: Invalid foreground color "{0}"\n'.format(fg))
                self.compileError = True
        elif bg is None:    #if no FG or BG then set default FG
            self.foreground = self.defaultForeground
        
        if bg:
            bg = bg.lower()
            if self.colorMap.has_key(bg):
                self.background = self.colorMap[bg]
            else:
                self.background = self.defaultBackground
                sys.stderr.write('ERROR: Invalid background color "{0}"\n'.format(bg))
                self.compileError = True
        elif fg is None:        #if no FG or BG then set default BG
            self.background = self.defaultBackground
            
    def isError(self):
        return self.compileError
    
    def search(self, text):
        if self.foreground and self.background:
            startTag = self.startTagFgBgTemplate.format(self.brightColor, self.foreground, self.background)
        elif self.foreground:
            startTag = self.startTagFgTemplate.format(self.brightColor, self.foreground)
        else:
            startTag = self.startTagBgTemplate.format(self.background)
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
            searchPat = searchArg[0]
            fg = searchPat[1] if len(searchArg)>1 else None
            bg = searchPat[2] if len(searchArg)>2 else None
            hls = HighlightSearch(searchPat, fg, bg)
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
        dom = ET.parse(open(configFile, 'r'))
        root = dom.getroot()
        for searchTag in root.findall('search'):
            (fg,bg) = (None, None)
            searchPat = searchTag.text
            if searchTag.attrib.has_key('fg'):
                fg = searchTag.attrib['fg']
            if searchTag.attrib.has_key('bg'):
                bg = searchTag.attrib['bg']
            
            hls = HighlightSearch(searchPat, fg, bg)
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