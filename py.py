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
        ## @ingroup nest
        self.nest = []
        
    ## @defgroup dump Dump
    ## @brief objects in human-readable form for debugging
    ## @ingroup sym
    ## @{
    
    ## `print sym` in readable form
    def __repr__(self): return self.dump()
    ## dump object in full tree form
    ## @param[in] depth tree depth for recursive dump
    ## @param[in] onlystack flag used for stack dump (disable `attr{}` dump)
    def dump(self,depth=0,onlystack=False):
        S = '\n'+self.pad(depth)+self.head()
        if not onlystack:
            for i in self.attr:
                S += '\n' + self.pad(depth+1) + self.attr[i].head(prefix='%s = '%i)
        for j in self.nest:
            S += j.dump(depth+1)
        return S
    ## dump object in short header-only `<T:V>` form
    ## @param[in] prefix optional string will be put before `<T:V>`
    def head(self,prefix=''): return '%s<%s:%s>'%(prefix,self.tag,self.val)
    ## pad from left with tabs in tree output
    def pad(self,N): return '\t'*N
    ## @}
    
    ## @defgroup attr Attributes = object slots
    ## @ingroup sym
    ## <b>any object</b> can be used as associative array,
    ## or can have slots to implement OOP mechanics
    ## @{
    
    ## `sym[key]=o` operator
    def __setitem__(self,key,o): self.attr[key] = o ; return self
    ## `sym[key]` fetch object by its name
    def __getitem__(self,key): return self.attr[key]
    ## @}
    
    ## @defgroup nest Nested elements = vector = stack
    ## @ingroup sym
    ## @brief <b>any object</b> can hold nested elements, data in order,
    ## and use it in stack-like way (push/pop/...)
    ## @{
    
    ## push element stack-like
    def push(self,o): self.nest.append(o) ; return self
    ## pop top (end) value
    def pop(self): return self.nest.pop()
    ## @return top element without pop
    def top(self): return self.nest[-1]
    
    ## @}
    
## number
class Num(Sym): pass

## string
class Str(Sym): pass

## vector, can be executed as seqential program /ordered container/  
class Vector(Sym): pass

## wrapper for methods defined in VM 
class Method(Sym):
    ## wrap VM method
    ## @param[in] F method (function)
    def __init__(self,F):
        Sym.__init__(self, F.__name__)
        ## hold pointer to given method
        self.fn = F
    ## callable/executable object
    def __call__(self): self.fn()

## @}

## @defgroup ply Syntax parser (lexer only)
## @ingroup interpret
## using PLY parser generator library
## @{

# PLY library
import ply.lex as lex

## supported token types
tokens = ['SYM','NUM']

## ignored space chars
t_ignore = ' \t\r'

## line comments can start with `#` and `\`
t_ignore_COMMENT = r'[\#\\].*|\(.*?\)'

## count line numbers
def t_newline(t):
    r'\n'
    t.lexer.lineno += 1
    
## numbers
def t_NUM(t):
    r'[\+\-]?[0-9]+(\.[0-9]*)?([eE][\+\-]?[0-9]+)?'
    t.value = Num(t.value) ; return t
    
## symbol lexer rule
def t_SYM(t):
    r'[a-zA-Z0-9_\?\:\;\.\+\-]+'
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
        # fill vocabulary
        self['.'] = Method(self.DROPALL)
        self['?'] = Method(self.PrintStack)
        self[':'] = Method(self.colon)
        self[';'] = Method(self.semicolon)
        ## contains current definition of False (as interepreter mode flag)
        self.COMPILE = False
        # run interpreter
#         self['SRC'] = Str(src)
        self.INTERPRET(src)
    
    ## @defgroup stack Stack operations
    ## @ingroup fvm
    ## @{
    
    ## `DROPALL ( ... -- )` clean data stack
    def DROPALL(self):
        ## `nest[]` in FVM used for data stack
        ## @ingroup nest
        self.nest = []
    
    ## `? ( -- )` print data stack
    def PrintStack(self): print self.dump(onlystack=True)
        
    ## @}
        
    ## @defgroup interpret interpreter/compiler
    ## @ingroup fvm
    ## @{

    ## `: ( -- )` start new word (colon) definition
    def colon(self):
        self.WORD() ; WN = self.pop().val       # fetch word name by forward lexing
        self[WN] = self.COMPILE = Vector(WN)    # can use self name to recurse
    
    ## `; ( -- )` end colon definition
    def semicolon(self): self.COMPILE = False   # close compiling
    
    ## `WORD ( -- wordname )` fetch next word (token) from source code
    ## @returns token will be empty at end of code
    def WORD(self):
        token = self.lexer.token()
        if token: self.push(token.value)    # push parsed object to data stack
        return token                        # PLY token will be empty on EOL
    ## `FIND ( name -- xt|name )` find executable object in vocabulary
    ## @returns found flag or not found name
    def FIND(self):
        o = self.pop() ; WN = o.val         # pop name to be found
        try: self.push(self[WN])            # lookup in vocabulary
        except KeyError:                    # fallback case insensitive
            try: self.push(self[WN])
            except KeyError: raise SyntaxError(o)
    ## `EXECUTE ( xt -- )` run object with executable semantics
    def EXECUTE(self): self.pop()() 
    ## `INTERPRET ( -- )` source code parser/compiler
    def INTERPRET(self,src):
        ## lexer will be used for parsing
        self.lexer = lex.lex()              # construct lexer
        self.lexer.input(src)               # feed source code to lexer
        while True:
            if not self.WORD(): break       # stop on EOF
            if self.top().tag in ['sym']:
                self.FIND()                 # lookup name in definitions
                self.EXECUTE()              # run if found
#             print self
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
#         print ctrl,key
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
