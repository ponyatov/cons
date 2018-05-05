## @file
## @brief interactive console

## @defgroup gui GUI
## @{

import wx,threading

## GUI processing thread
class GUI_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.app = wx.App()
    def run(self):
        self.app.MainLoop()
gui_thread = GUI_thread()

## @}

if __name__ == '__main__':
    gui_thread.start()
    gui_thread.join()
