import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class Frame(object):
    def __init__(self,root,row,name,keyList):
        frame = ttk.Labelframe(root,text=name,labelanchor="nw",bootstyle='primary')
        frame.grid(row=row,columnspan=10,padx=10,pady=10,sticky='w')
        self.frame = frame
        self.keyList = keyList
        self.btnList = []
        self.btnVarList = []
        
    def packKeys(self):
        for key in self.keyList:
            v = ttk.IntVar()
            b = ttk.Checkbutton(self.frame,text=key,variable=v,
                                bootstyle='success-outline-toolbutton')
            b.grid(row=1,column=self.keyList.index(key),padx=5,pady=5)
            self.btnVarList.append(v)
            self.btnList.append(b)
    def ChoosenKeys(self):
        choosenKeys =[]
        for i in range(len(self.keyList)):
            if self.btnVarList[i].get():
                choosenKeys.append(self.keyList[i])
        return choosenKeys

