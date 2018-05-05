## @file
## @brief interactive console

import os,sys

## @defgroup gui GUI
## @{

import wx,wx.stc,threading

## GUI processing thread
class GUI_thread(threading.Thread):
    ## run GUI in background
    def __init__(self):
        threading.Thread.__init__(self)
        ## wx.Application required
        self.app = wx.App()
        ## use only single main window
        self.main = wx.Frame(None,wx.ID_ANY,str(sys.argv))
        ## menu bar
        self.menubar = wx.MenuBar() ; self.main.SetMenuBar(self.menubar)
        ## file menu
        self.file = wx.Menu() ; self.menubar.Append(self.file,'&File')
        ## file/save
        self.save = self.file.Append(wx.ID_SAVE,'&Save')
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
        ## editor area
        self.editor = self.main.control = wx.stc.StyledTextCtrl(self.main)
        self.ReOpen(None)
        ## font scaling Ctrl +/-
        self.editor.CmdKeyAssign(ord('='),wx.stc.STC_SCMOD_CTRL,wx.stc.STC_CMD_ZOOMIN )
        self.editor.CmdKeyAssign(ord('-'),wx.stc.STC_SCMOD_CTRL,wx.stc.STC_CMD_ZOOMOUT)
        ## configure font size
        W,H = wx.GetDisplaySize()
        self.editor.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, \
            wx.Font(H>>4, wx.FONTFAMILY_MODERN, wx.NORMAL, wx.NORMAL))
        ## status bar
        self.status = wx.StatusBar(self.main)
        self.main.SetStatusBar(self.status)
    ## reopen file in editor
    def ReOpen(self,e,filename='src.src'):
        F = open(filename) ; self.editor.SetValue(F.read()) ; F.close()
    ## about event handler
    def About(self,e):
        F = open('README.md') ; wx.MessageBox(F.read(111)) ; F.close()
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
