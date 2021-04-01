

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


# Define global variables, which are to be changed by user:

# the folder in which the pictures that are to be sorted are stored
# don't forget to end it with the sign '/' !
#input_folder = '/file_path/to/image_folder/'
main_path =  'C:\\Users\\arnHom\\Documents\\sudoku\\data'
input_folder = 'aug'
# A file-path to a txt-file, that WILL be created by the script. The results of the sorting wil be stored there.
# Don't provide a filepath to an empty file, provide to a non-existing one!
# If you provide a path to file that already exists, than this file will be used for keeping track of the storing.
# This means: 1st time you run this script and such a file doesn't exist the file will be created and populated,
# 2nd time you run the same script, and you use the same df_path, the script will use the file to continue the sorting.
df_path = 'labels2.csv'

# a selection of what file-types to be sorted, anything else will be excluded
file_extensions = ['.jpg', '.png', '.whatever','.jpeg']

# set resize to True to resize image keeping same aspect ratio
# set resize to False to display original image
resize = True

#####
import pandas as pd
import os
import numpy as np

import argparse
import tkinter as tk
from tkinter import filedialog
import os
from shutil import copyfile, move
from PIL import ImageTk, Image

class ImageGui:
    """
    GUI for iFind1 image sorting. This draws the GUI and handles all the events.
    Useful, for sorting views into sub views or for removing outliers from the data.
    """

    def __init__(self, master, paths):
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
        frame = tk.Frame(master)
        frame.grid()

        # Start at the first file name
        self.index = 0
        self.paths = paths

        # initialize current image data.
        self.image_raw = None
        self.image = None
        self.image_panel = tk.Label(frame)
        self.cachedImage = None
        self.cachedImagePath = ""
        self.warpMode = False
        self.corners = np.zeros((2,4))

        # Make buttons
        self.buttons = []
        self.buttons.append(tk.Button(frame, text="prev (a)", width=10, height=1, fg="black", command=lambda : self.move_prev_image()))
        self.buttons.append(tk.Button(frame, text="next (d)", width=10, height=1, fg='black', command=lambda : self.move_next_image()))
        self.buttons.append(tk.Button(frame, text="(s)ave", width = 10, height=1, fg='green', command=lambda : self.save_exit_button()))
        self.buttons.append(tk.Button(frame, text="preview (w)arp", width = 10, height=1, fg='blue', command=lambda : self.handle_warp_toggle()))
        self.buttons.append(tk.Button(frame, text="(r)emove img", width=10,height=1,fg ='red',command=lambda: self.remove_image()))
        # Place buttons in grid
        for ll, button in enumerate(self.buttons):
            button.grid(row=0, column=ll, sticky='we')
            #frame.grid_columnconfigure(ll, weight=1)

        # Add progress label
        progress_string = "%d/%d" % (self.index+1, len(df))
        self.progress_label = tk.Label(frame, text=progress_string, width=10)
        # Place progress label in grid
        self.progress_label.grid(row=1, column=3, sticky='we') # +2, since progress_label is placed after and the additional 2 buttons "next im", "prev im"
        
        # go to box.
        tk.Label(frame, text="go to #pic:").grid(row=1, column=0)
        # listen for typing in the "go to" box.
        self.return_ = tk.IntVar() # return_-> self.index
        self.return_entry = tk.Entry(frame, width=6, textvariable=self.return_)
        self.return_entry.grid(row=1, column=1, sticky='we')
        master.bind('<Return>', self.num_pic_type)
        
        # add the corners display text
        self.corners_label = tk.Label(frame,anchor='w')
        # Place corners label in grid
        self.corners_label.grid(row=3, column=0,columnspan=3, sticky='we') 
        
        # Place the image in grid
        self.image_panel.grid(row=2, column=0, columnspan=5, sticky='we')

        # bind click listener to the image panel
        self.image_panel.bind('<Button-1>',self.image_click)
        master.bind('<KeyRelease>', self.key_pressed)
        # finish  setup by opening the first image.
        self.open_image(0)
        self.set_corner_label()
        
    def add_image_to_data(self):
        global df
        filenames = filedialog.askopenfilenames( initialdir = main_path, title='select files', filetypes = ( ('jpg files', ['*.jpg','*.jpeg']), ('all files','*.*')) )
        toAppend = []
        for f in filenames:
            # copy the file over to main_path + input_folder 
            
            # prepare the names 
            basename = os.path.basename(f)
            newRelativeName = os.path.join(input_folder,basename)
            print(newRelativeName)
            # copy the file over.
            copyfile(f, os.path.join(main_path,newRelativeName))
            
            # add a new row to the df
            newData = [newRelativeName, 0.5,0.5, 0.5,0.5, 0.5,0.5, 0.5,0.5]            
            series = pd.Series(newData, index = df.columns)
            df = df.append(series, ignore_index=True)
        print(len(df))
        self.set_progress_label()
        
    def set_corner_label(self):
        text = ''
        labels = ['top left','top right','bot left','bot right']
        for i in range(4):
            text += labels[i] + '(' + str(self.corners[0,i])+','+ str(self.corners[1,i])+')\n'
        self.corners_label.configure(text=text)
    
    def set_progress_label(self):
        progress_string = "%d/%d" % (self.index+1, len(df))
        self.progress_label.configure(text=progress_string)
    
    def save_exit_button(self):
        self.save()
        # self.master.quit() # i'm not certain that this is really working.
        
    def handle_warp_toggle(self):
        print(self.warpMode)
        self.warpMode = not self.warpMode
        self.set_image(self.cachedImagePath,guide=not self.warpMode,corners=self.corners)
    
    def save(self):
        path = os.path.join(main_path,df_path)
        df.to_csv(os.path.join(main_path,df_path))
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
        data = df.iloc[index].to_numpy()[1:].reshape((2,4),order='F')
        return data
    
    def write_metadata(self,index,data):
        reshaped = data.reshape((1,8),order='F').squeeze()
        current = df.iloc[index].to_numpy()
        current[1:] = reshaped
        df.iloc[index] = current

    def open_image(self,index):
        self.warpMode = False
        self.index = index
        self.set_progress_label()
        
        # we should also load in the meta data for this particular item, if it exists.
        # TODO figure out how the data is being read and written.
        self.corners = self.read_metadata(self.index)
        
        self.set_corner_label()
        self.set_image(df.iloc[self.index].im_path,corners=self.corners)

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
        self.index = self.return_.get() - 1
        self.open_image(self.index)

    def remove_image(self):
        df.drop(index=self.index,inplace=True)
        df.reset_index(drop=True,inplace=True)
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

    @staticmethod
    def _load_image(path):
        """
        Loads and resizes an image from a given path using the Pillow library
        :param path: Path to image
        :return: Resized or original image 
        """
        image = Image.open(os.path.join( main_path,path))
        if(resize):
            max_height = 500
            img = image 
            s = img.size
            ratio = max_height / s[1]
            image = img.resize((int(s[0]*ratio), int(s[1]*ratio)), Image.ANTIALIAS)
        return image

def make_folder(directory):
    """
    Make folder if it doesn't already exist
    :param directory: The folder destination path
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        

# The main bit of the script only gets exectured if it is directly called
if __name__ == "__main__":

###### Commenting out the initial input and puting input into preamble
# TODO seems it would probably be a good idea to allow this stuff to function again.
#     # Make input arguments
#     parser = argparse.ArgumentParser()
#     parser.add_argument('-f', '--folder', help='Input folder where the *tif images should be', required=True)
#     parser.add_argument('-l', '--labels', nargs='+', help='Possible labels in the images', required=True)
#     args = parser.parse_args()

#     # grab input arguments from args structure
#     input_folder = args.folder
#     labels = args.labels
    
    # Put all image file paths into a list
    paths = []
    
    file_names = [fn for fn in sorted(os.listdir( os.path.join(main_path,input_folder )))
                  if any(fn.endswith(ext) for ext in file_extensions)]
    paths = [os.path.join(input_folder,file_name) for file_name in file_names]
    
    try:
        test = os.path.join(main_path, df_path)
        print(test)
        df = pd.read_csv(os.path.join(main_path, df_path),header=0,index_col=0)
    except FileNotFoundError: # if it doesn't exist generate a blank one.    
        print('created a new data file');
        df = pd.DataFrame(columns=["im_path", 'tlx','tly','trx','try','blx','bly','brx','bry'])
        defaultValues = np.ones((len(paths),1))*0.5;
        df.im_path = paths
        for name in df.columns:
            if name != 'im_path':
                df[name] = defaultValues
    
# Start the GUI
root = tk.Tk()
app = ImageGui(root, paths)
root.mainloop()

