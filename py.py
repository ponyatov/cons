## @file
## @brief interactive console

import os,sys

## @defgroup gui GUI
## @{

import wx,threading

## GUI processing thread
class GUI_thread(threading.Thread):
    ## run GUI in background
    def __init__(self):
        threading.Thread.__init__(self)
        # wx.Application required
        self.app = wx.App()
        # use only single main window
        self.main = wx.Frame(None,wx.ID_ANY,str(sys.argv))
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
