## @file
## @brief interactive console

import os,sys

# we'll use threaded VM/GUI/HTTP to avoid lockups and system falls
import threading,Queue

## @defgroup sym Symbolic object system
## @brief unversal object can hold single data element or work as data container
## @{

## base `Sym`bolic object
class Sym:
    ## construct symbol
    ## @param[in] V single primitive object value
    def __init__(self,V):
        ## type/class tag
        self.tag = self.__class__.__name__.lower()
        ## single object value
        self.val = V
        ## `attr{}`ibutes
        self.attr = {}
        ## `nest[]`ed elements
        self.nest = []
        
    ## @defgroup dump Dump
    ## @brief objects in human-readable form for debugging
    ## @ingroup sym
    ## @{
    
    ## `print sym` in readable form
    def __repr__(self): return self.dump()
    ## dump object in full tree form
    ## @param[in] depth tree depth for recursive dump
    def dump(self,depth=0):
        S = '\n'+self.pad(depth)+self.head()
        for j in self.nest:
            S += j.dump(depth+1)
        return S
    ## dump object in short header-only `<T:V>` form
    ## @param[in] prefix optional string will be put before `<T:V>`
    def head(self,prefix=''):
        return '%s<%s:%s>'%(prefix,self.tag,self.val)
    ## pad from left with tabs in tree output
    def pad(self,N): return '\t'*N
    ## @}
    
    ## @defgroup attr Attributes = object slots
    ## @ingroup sym
    ## <b>any object</b> can be used as associative array,
    ## or can have slots to implement OOP mechanics
    ## @{
    
    ## `sym[key]=o` operator
    def __setitem__(self,key,o):
        self.attr[key] = o ; return self
    ## @}
    
    ## @defgroup nest Nested elements = vector = stack
    ## @ingroup sym
    ## @brief <b>any object</b> can hold nested elements, data in order,
    ## and use it in stack-like way (push/pop/...)
    ## @{
    
    ## push element stack-like
    def push(self,o):
        self.nest.append(o) ; return self
    
    ## @}

## @}

## @defgroup ply Syntax parser (lexer only)
## @ingroup interpret
## using PLY parser generator library
## @{

import ply.lex  as lex

## supported token types
tokens = ['SYM']

## ignored space chars
t_ignore = ' \t\r'

## line comments can start with `#` and `\`
t_ignore_COMMENT = r'[\#\\].*'

## count line numbers
def t_newline(t):
    r'\n'
    t.lexer.lineno += 1
    
## symbol lexer rule
def t_SYM(t):
    r'[a-zA-Z0-9_\?\:\;]+'
    t.value = Sym(t.value) ; return t
    
## lexer error callabck
def t_error(t): raise SyntaxError(t)

## @}

## @defgroup fvm o/FORTH Virtual Machine
## @{

## `o/FORTH` Virtual Machine
class FVM(Sym):
    ## start VM
    ## @param[in] V VM name
    ## @param[in] src source code will be interpreted
    def __init__(self,V,src=''):
        Sym.__init__(self,V)
        self['SRC'] = src
        self.INTERPRET(src)
    
    ## @defgroup interpret interpreter/compiler
    ## @ingroup fvm
    ## @{
        
    ## `WORD ( -- wordname )` fetch next word (token) from source code
    ## @returns token will be empty at end of code
    def WORD(self):
        token = self.lexer.token()
        if token: self.push(token.value)    # push parsed object to data stack
        return token                        # PLY token will be empty on EOL
    ## `INTERPRET ( -- )` source code parser/compiler
    def INTERPRET(self,src):
        ## lexer will be used for parsing
        self.lexer = lex.lex()              # construct lexer
        self.lexer.input(src)               # feed source code to lexer
        while True:
            if not self.WORD(): break       # stop on EOF
            print self
            
    ## @}

## queue will hold source code requests from GUI frontend
SRC = Queue.Queue()

## `o/FORTH` requests processing thread: every command run in separate thread
## (thread will not fail system on errors)
class FVM_thread(threading.Thread):
    ## construct VM will execute FORTH requests from GUI frontend
    def __init__(self):
        threading.Thread.__init__(self)
    ## request queue processing
    def run(self):
        FVM('FORTH',src=SRC.get())

## @}

## @defgroup gui GUI
## @{

import wx,wx.stc

## GUI processing thread
class GUI_thread(threading.Thread):
    ## run GUI in background
    def __init__(self):
        threading.Thread.__init__(self)
        ## wx.Application required
        self.app = wx.App()
        ## use only single main window
        self.main = wx.Frame(None,wx.ID_ANY,str(sys.argv))
        ## menu
        self.SetupMenu()
        ## editor area
        self.SetupEditor()
        ## status bar
        self.status = wx.StatusBar(self.main) ; self.main.SetStatusBar(self.status)
    ## condifure menu
    def SetupMenu(self):
        ## menu bar
        self.menubar = wx.MenuBar() ; self.main.SetMenuBar(self.menubar)
        ## file menu
        self.file = wx.Menu() ; self.menubar.Append(self.file,'&File')
        ## file/save
        self.save = self.file.Append(wx.ID_SAVE,'&Save')
        self.main.Bind(wx.EVT_MENU, self.onSave, self.save)
        ## file/export
        self.export = self.file.Append(wx.ID_CONVERT,'Ex&port') 
        self.file.AppendSeparator()
        ## file/exit
        self.exit = self.file.Append(wx.ID_EXIT,'E&xit')
        self.main.Bind(wx.EVT_MENU, lambda e:self.main.Close(), self.exit)
        ## help menu
        self.help = wx.Menu() ; self.menubar.Append(self.help,'&Help')
        ## help/about
        self.about = self.help.Append(wx.ID_ABOUT,'&About\tF1')
        self.main.Bind(wx.EVT_MENU, self.About, self.about)
    ## configure editor
    def SetupEditor(self):
        ## editor: use StyledText widget with rich syntax coloring
        self.editor = self.main.control = wx.stc.StyledTextCtrl(self.main)
        self.ReOpen(None)
        ## configure font size
        W,H = self.main.GetClientSize()
        self.editor.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, \
            wx.Font(H>>3, wx.FONTFAMILY_MODERN, wx.NORMAL, wx.NORMAL))
        ## left margin with line numbers
        self.editor.SetMargins(5,0)
        self.editor.SetMarginType(1,wx.stc.STC_MARGIN_NUMBER)
        self.editor.SetMarginWidth(1,55)
        # bind keys
        ## font scaling Ctrl +/-
        self.editor.CmdKeyAssign(ord('='),wx.stc.STC_SCMOD_CTRL,wx.stc.STC_CMD_ZOOMIN )
        self.editor.CmdKeyAssign(ord('-'),wx.stc.STC_SCMOD_CTRL,wx.stc.STC_CMD_ZOOMOUT)
        ## run code on Ctrl-Enter
        self.editor.Bind(wx.EVT_CHAR,self.onChar)
    ## event handler: process keyboard events
    def onChar(self,e):
        key = e.GetKeyCode() ; ctrl = e.CmdDown() ; shift = e.ShiftDown()
        if key == 13 and ( ctrl or shift ): self.ProcessCommand()
        else: e.Skip()
    ## start command processing from selected text
    def ProcessCommand(self):
        SRC.put ( self.editor.GetSelectedText() )   # put to queue
        FVM_thread().start()                        # run worker
    ## save handler
    def onSave(self,e):
        F = open(self.filename,'w') ; F.write( self.editor.GetValue() ) ; F.close()
    ## reopen file in editor
    def ReOpen(self,e,filename='src.src'):
        ## save used file name
        self.filename = filename
        F = open(filename) ; self.editor.SetValue(F.read()) ; F.close()
    ## about event handler
    def About(self,e):
        F = open('README.md') ; wx.MessageBox(F.read()) ; F.close()
    ## activate GUI elements only on thread start
    ## (interpreter system can run in headless mode) 
    def run(self):
        self.main.Show()
        self.app.MainLoop()
## GUI thread sigleton
gui_thread = GUI_thread()

## @}

if __name__ == '__main__':
    gui_thread.start()
    gui_thread.join()
