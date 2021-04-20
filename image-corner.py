

"""
allows simple quadrant single feature mapping.  
designed for identifying corners in an image.
 USAGE:
 run 'python sort_folder_vers2.py' or copy the script in a jupyter notebook and run then

 you need also to provide your specific input (source folder, labels and other) in the preamble
 original Author: Christian Baumgartner (c.baumgartner@imperial.ac.uk)
 changes, version 2: Nestor Arsenov (nestorarsenov_AT_gmail_DOT_com)
 image-corner: alphazeba
"""
# a selection of what file-types to be sorted, anything else will be excluded
file_extensions = ['.jpg', '.png', '.whatever','.jpeg']

# set resize to True to resize image keeping same aspect ratio
# set resize to False to display original image
resize = True
#####
import pandas as pd
import os
import numpy as np
import argparse # do we need this?
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import os
from shutil import copyfile, move
from PIL import ImageTk, Image

class ImageGui:
    """
    GUI for iFind1 image sorting. This draws the GUI and handles all the events.
    Useful, for sorting views into sub views or for removing outliers from the data.
    """
    
    def buildMainView(self):
        self.deleteCurrentFrame()
        
        self.frame = tk.Frame(self.master)
        self.frame.grid()
        # Start at the first file name
        self.index = 0
        
        # initialize current image data.
        self.image_raw = None
        self.image = None
        self.image_panel = tk.Label(self.frame)
        self.cachedImage = None
        self.cachedImagePath = ""
        self.warpMode = False
        self.corners = np.zeros((2,4))

        # Make buttons
        self.buttons = []
        
        menu = tk.Menu(self.master)
        
        fileMenu = tk.Menu(menu)
        editMenu = tk.Menu(menu)
        viewMenu = tk.Menu(menu)
        
        menu.add_cascade(label='file', menu=fileMenu)
        menu.add_cascade(label='edit', menu=editMenu)
        menu.add_cascade(label='view', menu=viewMenu)
        
        fileMenu.add_command(label='(s)ave',command=self.save_exit_button)
        fileMenu.add_separator()
        fileMenu.add_command(label='open project', command=self.openProject)
        fileMenu.add_command(label='new project', command=self.newProject)
        fileMenu.add_separator()
        fileMenu.add_command(label='close project', command = self.closeProject)
        fileMenu.add_command(label='export project', command=self.exportProject)
        
        editMenu.add_command(label='(r)emove image',command=self.remove_image)
        editMenu.add_separator()
        editMenu.add_command(label='imp(o)rt images',command=self.add_image_to_data)
        
        viewMenu.add_command(label='preview (w)arp', command=self.handle_warp_toggle)
        
        self.master.configure(menu=menu)
        
        self.buttons.append(tk.Button(self.frame, text="prev (a)", width=10, height=1, fg="black", command=lambda : self.move_prev_image()))
        self.buttons.append(tk.Button(self.frame, text="next (d)", width=10, height=1, fg='black', command=lambda : self.move_next_image()))
        # Place buttons in grid
        for ll, button in enumerate(self.buttons):
            button.grid(row=1, column=ll, sticky='we')

        # Add progress label
        progress_string = "%d/%d" % (self.index+1, len(self.df))
        self.progress_label = tk.Label(self.frame, text=progress_string, width=10)
        # Place progress label in grid
        self.progress_label.grid(row=2, column=3, sticky='we') # +2, since progress_label is placed after and the additional 2 buttons "next im", "prev im"
        
        # go to box.
        tk.Label(self.frame, text="go to #pic:").grid(row=2, column=0)
        # listen for typing in the "go to" box.
        self.return_ = tk.IntVar() # return_-> self.index
        self.return_entry = tk.Entry(self.frame, width=6, textvariable=self.return_)
        self.return_entry.grid(row=2, column=1, sticky='we')
        self.master.bind('<Return>', self.num_pic_type)
        
        # add the corners display text
        self.corners_label = tk.Label(self.frame,anchor='w')
        # Place corners label in grid
        self.corners_label.grid(row=4, column=0,columnspan=3, sticky='we') 
        
        # Place the image in grid
        self.image_panel.grid(row=3, column=0, columnspan=5, sticky='we')

        # bind click listener to the image panel
        self.image_panel.bind('<Button-1>',self.image_click)
        self.master.bind('<KeyRelease>', self.key_pressed)
        # finish  setup by opening the first image.
        self.open_image(0)
        self.set_corner_label()
        
    def buildIntroView(self):
        self.deleteCurrentFrame()
        
        self.frame = tk.Frame(root)
        self.frame.grid()
        
        emptyMenu = tk.Menu(self.master)
        self.master.configure(menu=emptyMenu)

        openButton = tk.Button(self.frame, text='open project', command=self.openProject)
        openButton.grid(row=0,column=0,sticky='we')

        newButton = tk.Button(self.frame, text='new project', command = self.newProject)
        newButton.grid(row=0, column=1, sticky='we')
        
    def exportProject(self):
        exportString = simpledialog.askstring(title='export project', prompt='seperated by a dash; enter just a single number if exporting from the beginning; enter nothing to export everything')
        rangeToExport = range(len(self.df))
        if exportString != '':
            # we will need to actually parse the string.
            try: # in the event it is only a single string entered.
                rangeToExport = range(int(exportString)-1)
            except: # otherwise, the user should have entered 2 numbers seperated by a '-'
                nums = exportString.split('-')
                print(nums)
                rangeToExport = range(int(nums[0])-1,int(nums[1])-1) # subtracting 1 because user facing numbers start at 1 while internal are 0 based.
        
        print(rangeToExport)
        destinationPath = filedialog.askdirectory(title='choose a folder to export data too')
        if path =='':
            print("didn't export the project")
            return
        
        # copy the files over.
        for index in rangeToExport:
            fileName = self.df.iloc[index].im_path # maybe we should consider removing any of the fancy foldering type stuff out of the way? 
            # if there is the potential for some folder existing, maybe we should check whether there is a folder in the path and then create the folders to make sure it can be copied over.
            copyfile( os.path.join(self.main_path, fileName ), os.path.join( destinationPath, fileName ) )
        
        # now we need to make a new df with the copied over files in it.
        newDf = df.iloc[rangeToExport]
        newDf.to_csv(destinationPath) # save the new df over to the location
        
        # then maybe we should open up the new project?
        # or maybe we should tell the user that they are still in the old project so that they know whats up.
        result = messagebox.showinfo("Export complete","your export has been exported to "+destinationPath+".  The original project is still open, if you would like to edit the export, please open it now")
        
        
        
        # otherwise, we are ready to begin moving stuff into the new folder.
        # we can duplicate the current project over there. and then we would need to start movign the photos over ther.edit
        # we would need to make sure that we are only duplicating the portion of the dataframe that is within the range though.
        
    def openProject(self):
        path = filedialog.askopenfilename(title='Open project', filetypes = ( ('csv files', ['*.csv']), ('all files','*.*')) )
        if path == '':
            print("didn't open a project")
            return
        # what is returned if someone exits?
        print('the path: "',path,'"')
        # now we need to break the basename off of the rest of the directory
        path, basename = os.path.split(path)
        self.df_path = basename
        self.main_path = path
        self.df = pd.read_csv( os.path.join(self.main_path, self.df_path) , header =0, index_col=0)
        
        self.buildMainView()

    def newProject(self):
        path = filedialog.askdirectory(title='Set folder for new project (the one with your images in it)')
        if path == '':
            print("didn't create a project")
            return
        print('the path: "',path,'"')
        self.main_path = path
        self.df_path = 'labels.csv'
        
        # Put all image file paths into a list
        paths = []
        
        file_names = [fn for fn in sorted(os.listdir( self.main_path))
                      if any(fn.endswith(ext) for ext in file_extensions)]
        paths = [file_name for file_name in file_names]

        print('created a new data file')
        self.df = pd.DataFrame(columns=["im_path", 'tlx','tly','trx','try','blx','bly','brx','bry'])
        defaultValues = np.ones((len(paths),1))*0.5
        self.df.im_path = paths
        for name in self.df.columns:
            if name != 'im_path':
                self.df[name] = defaultValues
                
        self.buildMainView()
        
    def closeProject(self):
        self.df = None
        self.buildIntroView()

    def deleteCurrentFrame(self):
        if self.frame != None:
            self.frame.destroy()
            self.frame = None

    def __init__(self, master):
        """
        Initialise GUI
        :param master: The parent window
        :param labels: A list of labels that are associated with the images
        :param paths: A list of file paths to images
        :return:
        """
        # gui stuff.
        # So we can quit the window from within the functions
        self.master = master
        master.title("image-corner")
        self.frame = None
        self.main_path =  'C:\\Users\\arnHom\\Documents\\sudoku\\data'
        self.df_path = 'labels.csv'
        # move to the first view.
        self.buildIntroView()
        self.df = None
        
    def add_image_to_data(self):
        filenames = filedialog.askopenfilenames( initialdir = self.main_path, title='select files', filetypes = ( ('jpg files', ['*.jpg','*.jpeg']), ('all files','*.*')) )
        for f in filenames:
            # copy the file over to main_path + input_folder 
            # prepare the names 
            basename = os.path.basename(f)
            newRelativeName = basename
            print(newRelativeName)
            # copy the file over.
            copyfile(f, os.path.join(self.main_path,newRelativeName))
            # add a new row to the self.df
            newData = [newRelativeName, 0.5,0.5, 0.5,0.5, 0.5,0.5, 0.5,0.5]
            series = pd.Series(newData, index = self.df.columns)
            self.df = self.df.append(series, ignore_index=True)
        print(len(self.df))
        self.set_progress_label()
        
    def set_corner_label(self):
        text = ''
        labels = ['top left','top right','bot left','bot right']
        for i in range(4):
            text += labels[i] + '(' + str(self.corners[0,i])+','+ str(self.corners[1,i])+')\n'
        self.corners_label.configure(text=text)
    
    def set_progress_label(self):
        progress_string = "%d/%d" % (self.index+1, len(self.df))
        self.progress_label.configure(text=progress_string)
    
    def save_exit_button(self):
        self.save()
        # self.master.quit() # i'm not certain that this is really working.
        
    def handle_warp_toggle(self):
        print(self.warpMode)
        self.warpMode = not self.warpMode
        self.set_image(self.cachedImagePath,guide=not self.warpMode,corners=self.corners)
    
    def save(self):
        path = os.path.join(self.main_path,self.df_path)
        self.df.to_csv(path)
        print('saved file at ',path)

    # handles the hotkeys.
    def key_pressed(self,event):
        if event.char == 'a':
            self.move_prev_image()
        elif event.char == 'd':
            self.move_next_image()
        elif event.char == 'w':
            self.handle_warp_toggle()
        elif event.char == 's':
            self.save_exit_button()
        elif event.char == 'r':
            self.remove_image()
        elif event.char == 'o':
            self.add_image_to_data()
        
    def image_click(self,event):
        if self.warpMode:
            print('ignoring click while in warpmode')
            return
        image = self.image_raw
        halfSize = np.array(image.size)/2
        x,y= event.x,event.y
        quadrant = -1
        if y < halfSize[1]:
            if x < halfSize[0]:
                quadrant = 0
            else:
                quadrant = 1
        else: # x>= 
            if x < halfSize[0]:
                quadrant = 2
            else:
                quadrant = 3
        x = (x%halfSize[0])/halfSize[0]
        y = (y%halfSize[1])/halfSize[1]

        self.corners[:,quadrant] = [x,y]
        self.set_image(self.cachedImagePath,corners=self.corners)
        self.write_metadata(self.index,self.corners)
        self.set_corner_label()

        print(event.x)

        print(event)
                
    def read_metadata(self,index):
        # formats the data as as a 2x4 array 
        #
        #   topleft, topright, botleft,botright
        # x    n        n         n       n
        # y    n        n         n       n
        data = self.df.iloc[index].to_numpy()[1:].reshape((2,4),order='F')
        return data
    
    def write_metadata(self,index,data):
        reshaped = data.reshape((1,8),order='F').squeeze()
        current = self.df.iloc[index].to_numpy()
        current[1:] = reshaped
        self.df.iloc[index] = current

    def open_image(self,index):
        self.warpMode = False
        self.index = index
        self.set_progress_label()
        
        # we should also load in the meta data for this particular item, if it exists.
        # TODO figure out how the data is being read and written.
        self.corners = self.read_metadata(self.index)
        
        self.set_corner_label()
        self.set_image(self.df.iloc[self.index].im_path,corners=self.corners)

    def set_image(self, path, guide=True,corners=np.zeros((2,4))):
        """
        Helper function which sets a new image in the image view
        :param path: path to that image
        """
        image = None
        if(path == self.cachedImagePath):
            print('recovered image from cache')
            image = self.cachedImage.copy()
        else:
            print('loaded image from disk')
            image = self._load_image(path)
            self.cachedImagePath = path
            self.cachedImage = image.copy()
        print(image.size)   

        # paint on the guid
        if guide:
            size = image.size
            halfSize = np.array(size)/2
            vx = int(size[0]/2)
            hy = int(size[1]/2)
            pxls = image.load()
            width = 5
            halfWidth = int(width/2)

            for x in range(size[0]):
                for i in range(width):
                    y = hy + i-halfWidth
                    pxls[x,y] = self._invertPixel(pxls[x,y])

            for y in range(size[1]):
                for i in range(width):
                    x = vx + i-halfWidth
                    pxls[x,y] = self._invertPixel(pxls[x,y])
            
            # highlight the corners.
            multipliers = np.array([[0,0],[1,0],[0,1],[1,1]])
            for i in range(4):
                multiplier = multipliers[i,:].squeeze()
                corner = corners[:,i].squeeze()
                drawSpot = corner*halfSize+multiplier*halfSize
                for ix in range(width):
                    for iy in range(width):
                        x = ix+drawSpot[0]-halfWidth
                        y = iy+drawSpot[1]-halfWidth
                        pxls[x,y] = self._invertPixel(pxls[x,y])
        else:
            # lets show off the warped version!
            image = self.perspectiveWarp(image,corners)

        self.image_raw = image
        self.image = ImageTk.PhotoImage(image)
        self.image_panel.configure(image=self.image)
    
    # for moving to the previous image (attached to a button)       
    def move_prev_image(self):
        """
        Displays the prev image in the paths list AFTER BUTTON CLICK,
        doesn't update the progress display
        """
        if self.index > 0:
            self.open_image(self.index-1)
        else:
            print("already at 0 can't move back any further")
    
    # for moving to the next image (attached to a button)
    def move_next_image(self):
        """
        Displays the next image in the paths list AFTER BUTTON CLICK,
        doesn't update the progress display
        """
        self.open_image(self.index+1)
    
    def num_pic_type(self, event):
        """Function that allows for typing to what picture the user wants to go.
        Works only in mode 'copy'."""
        # -1 in line below, because we want images bo be counted from 1 on, not from 0
        self.master.focus() # this steals focus from the intvar widget, so the use doesn't accidentally keep typing in it.
        self.index = self.return_.get() - 1
        self.open_image(self.index)

    def remove_image(self):
        self.df.drop(index=self.index,inplace=True)
        self.df.reset_index(drop=True,inplace=True)
        self.open_image(self.index)
        
    def getCornersInWorldSpace(self,corners):
        width = 5
        halfWidth = int(width/2)
        # highlight the corners.
        offset = np.array([[0,0],[1,0],[0,1],[1,1]]).transpose()
        return (corners+offset)/2

    def perspectiveWarp(self,image,corners):
        size = image.size
        srcPxls = image.copy().load()
        pxls = image.load()
        realCorners = self.getCornersInWorldSpace(corners) * np.array(size).reshape((2,1))
        for y in range(size[1]):
            fy = y/size[1]
            left = self.tween(realCorners[:,0],realCorners[:,2],fy)
            right = self.tween(realCorners[:,1],realCorners[:,3],fy)
            for x in range(size[0]):
                fx = x/size[0]
                rmpos = self.tween(left,right,fx).squeeze()
                ix = max(min(int(rmpos[0]),size[0]),0)
                iy = max(min(int(rmpos[1]),size[1]),0)
                pxls[x,y] = srcPxls[ix,iy]
        return image
        
    @staticmethod
    def tween(avec,bvec, amt):
        dif = bvec-avec
        return avec+dif*amt

    @staticmethod
    def _invertPixel(pxl):
        r,g,b = pxl
        pxl = (255-r,int((255-g)/2),int((255-b)/2))
        return pxl

    def _load_image(self, path):
        """
        Loads and resizes an image from a given path using the Pillow library
        :param path: Path to image
        :return: Resized or original image 
        """
        image = Image.open(os.path.join(self.main_path,path))
        if(resize):
            max_height = 500
            img = image 
            s = img.size
            ratio = max_height / s[1]
            image = img.resize((int(s[0]*ratio), int(s[1]*ratio)), Image.ANTIALIAS)
        return image



        
# boot program.
root = tk.Tk()
app = ImageGui(root)
root.mainloop()

    

    

