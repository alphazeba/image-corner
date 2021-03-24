

"""
 One-click image sorting/labelling script. Copies or moves images from a folder into subfolders. 
 This script launches a GUI which displays one image after the other and lets the user give different labels
 from a list provided as input to the script. In contrast to original version, version 2 allows for 
 relabelling and keeping track of the labels.
 Provides also short-cuts - press "1" to put into "label 1", press "2" to put into "label 2" a.s.o.

 USAGE:
 run 'python sort_folder_vers2.py' or copy the script in a jupyter notebook and run then

 you need also to provide your specific input (source folder, labels and other) in the preamble
 original Author: Christian Baumgartner (c.baumgartner@imperial.ac.uk)
 changes, version 2: Nestor Arsenov (nestorarsenov_AT_gmail_DOT_com)
 Date: 24. Dec 2018
"""


# Define global variables, which are to be changed by user:

# In[5]:
 # what?

##### added in version 2

# the folder in which the pictures that are to be sorted are stored
# don't forget to end it with the sign '/' !
#input_folder = '/file_path/to/image_folder/'
main_path =  'C:\\Users\\arnho\\Documents\\sudoku\\'
input_folder = main_path + 'aug\\'

# the different folders into which you want to sort the images, e.g. ['cars', 'bikes', 'cats', 'horses', 'shoes']
labels = ["label1"]

# provide either 'copy' or 'move', depending how you want to sort the images into the new folders
# - 'move' starts where you left off last time sorting, no 'go to #pic', works with number-buttons for labeling, no txt-file for tracking after closing GUI, saves memory
# - 'copy' starts always at beginning, has 'go to #pic', doesn't work with number-buttons, has a txt-for tracking the labels after closing the GUI
copy_or_move = 'copy'

# Only relevant if copy_or_move = 'copy', else ignored
# A file-path to a txt-file, that WILL be created by the script. The results of the sorting wil be stored there.
# Don't provide a filepath to an empty file, provide to a non-existing one!
# If you provide a path to file that already exists, than this file will be used for keeping track of the storing.
# This means: 1st time you run this script and such a file doesn't exist the file will be created and populated,
# 2nd time you run the same script, and you use the same df_path, the script will use the file to continue the sorting.
df_path = main_path + 'data\\labels.csv'

# a selection of what file-types to be sorted, anything else will be excluded
file_extensions = ['.jpg', '.png', '.whatever','.jpeg']

# set resize to True to resize image keeping same aspect ratio
# set resize to False to display original image
resize = True

#####


# In[8]:



import pandas as pd
import os
import numpy as np

import argparse
import tkinter as tk
import os
from shutil import copyfile, move
from PIL import ImageTk, Image

class ImageGui:
    """
    GUI for iFind1 image sorting. This draws the GUI and handles all the events.
    Useful, for sorting views into sub views or for removing outliers from the data.
    """

    def __init__(self, master, labels, paths):
        """
        Initialise GUI
        :param master: The parent window
        :param labels: A list of labels that are associated with the images
        :param paths: A list of file paths to images
        :return:
        """

        # So we can quit the window from within the functions
        self.master = master

        # Extract the frame so we can draw stuff on it
        frame = tk.Frame(master)

        # Initialise grid
        frame.grid()

        # Start at the first file name
        self.index = 0
        self.paths = paths
        self.labels = labels
        #### added in version 2
        self.sorting_label = 'unsorted'
        ####
        
        self.corners = np.zeros((2,4))

        # Number of labels and paths
        self.n_labels = len(labels)
        self.n_paths = len(paths)

        # Set empty image container
        self.image_raw = None
        self.image = None
        self.image_panel = tk.Label(frame)
        self.cachedImage = None
        self.cachedImagePath = ""

        # Make buttons
        self.buttons = []
        for label in labels:
            self.buttons.append(
                    tk.Button(frame, text=label, width=10, height=2, fg='blue', command=lambda l=label: self.vote(l))
            )
            
        ### added in version 2
        self.buttons.append(tk.Button(frame, text="prev im", width=10, height=1, fg="green", command=lambda l=label: self.move_prev_image()))
        self.buttons.append(tk.Button(frame, text="next im", width=10, height=1, fg='green', command=lambda l=label: self.move_next_image()))
        self.buttons.append(tk.Button(frame, text="save quit", width = 10, height=1, fg='red', command=lambda l=label: self.save_exit_button()))
        ###
        
        # Add progress label
        progress_string = "%d/%d" % (self.index+1, self.n_paths)
        self.progress_label = tk.Label(frame, text=progress_string, width=10)
        
        # Place buttons in grid
        for ll, button in enumerate(self.buttons):
            button.grid(row=0, column=ll, sticky='we')
            #frame.grid_columnconfigure(ll, weight=1)

        # Place progress label in grid
        self.progress_label.grid(row=1, column=self.n_labels+2, sticky='we') # +2, since progress_label is placed after
                                                                            # and the additional 2 buttons "next im", "prev im"
            
        #### added in version 2
        # Add sorting label
        sorting_string = "poop"# os.path.split(df.sorted_in_folder[self.index])[-2] # this will not work.
        self.sorting_label = tk.Label(frame, text=("in folder: %s" % (sorting_string)), width=15)
        # add the corners display text
        self.corners_label = tk.Label(frame, text=str(self.corners))
        
        # Place typing input in grid, in case the mode is 'copy'
        if copy_or_move == 'copy':
            tk.Label(frame, text="go to #pic:").grid(row=1, column=0)

            self.return_ = tk.IntVar() # return_-> self.index
            self.return_entry = tk.Entry(frame, width=6, textvariable=self.return_)
            self.return_entry.grid(row=1, column=1, sticky='we')
            master.bind('<Return>', self.num_pic_type)
        ####
        
        # Place sorting label in grid
        self.corners_label.grid(row=2, column=self.n_labels+1, sticky='we') # +2, since progress_label is placed after
                                                                            # and the additional 2 buttons "next im", "prev im"
        # Place the image in grid
        self.image_panel.grid(row=2, column=0, columnspan=self.n_labels+1, sticky='we')

        # bind click listener to the image panel
        self.image_panel.bind('<Button-1>',self.image_click)

        # key bindings (so number pad can be used as shortcut)
        # make it not work for 'copy', so there is no conflict between typing a picture to go to and choosing a label with a number-key
        if copy_or_move == 'move':
            for key in range(self.n_labels):
                master.bind(str(key+1), self.vote_key)
        self.open_image(0)
    
    def save_exit_button(self):
        self.save()
        # self.master.quit() # i'm not certain that this is really working.
        
    
    def save(self):
        df.to_csv(df_path)

    def image_click(self,event):
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
        self.corners_label.configure(text=str(self.corners))

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
        self.index = index
        progress_string = "%d/%d" % (self.index+1, self.n_paths)
        self.progress_label.configure(text=progress_string)
        
        #### added in version 2
        # i'm not sure what this is for.
        sorting_string = "poop"# os.path.split(df.sorted_in_folder[self.index])[-2] #shows the last folder in the filepath before the file
        test = "in folder: %s" % (sorting_string)
        self.sorting_label.configure(text=("what"))
        ####

        # we should also load in the meta data for this particular item, if it exists.
        # TODO figure out how the data is being read and written.
        self.corners = self.read_metadata(self.index)
        
        self.corners_label.configure(text=str(self.corners))
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
            

        self.image_raw = image
        self.image = ImageTk.PhotoImage(image)
        self.image_panel.configure(image=self.image)

    # for moving the next image ( happens when you click a sort button. )
    def show_next_image(self):
        """
        Displays the next image in the paths list and updates the progress display
        """
        self.move_next_image()
    
    ### for moving to the previous image (attached to a button)       
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

    def vote(self, label):
        """
        Processes a vote for a label: Initiates the file copying and shows the next image
        :param label: The label that the user voted for
        """
        """
        ##### added in version 2
        # check if image has already been sorted (sorted_in_folder != 0)
        if df.sorted_in_folder[self.index] != df.im_path[self.index]:
            # if yes, use as input_path the current location of the image
            input_path = df.sorted_in_folder[self.index]
            root_ext, file_name = os.path.split(input_path)
            root, _ = os.path.split(root_ext)
        else:
            # if image hasn't been sorted use initial location of image
            input_path = df.im_path[self.index]
            root, file_name = os.path.split(input_path)
        #####
        """
        self.write_metadata(self.index,self.corners)
        
        # what is root and file_name used for? it doesn't really look like it gets use?????
        
        # we don't actually want to be moving anything anymore.
        """
        #input_path = self.paths[self.index]
        if copy_or_move == 'copy':
            self._copy_image(label, self.index)
        if copy_or_move == 'move':
            self._move_image(label, self.index)
        """
        self.show_next_image()

    def vote_key(self, event):
        """
        Processes voting via the number key bindings.
        :param event: The event contains information about which key was pressed
        """
        pressed_key = int(event.char)
        label = self.labels[pressed_key-1]
        self.vote(label)
    
    #### added in version 2
    def num_pic_type(self, event):
        """Function that allows for typing to what picture the user wants to go.
        Works only in mode 'copy'."""
        # -1 in line below, because we want images bo be counted from 1 on, not from 0
        self.index = self.return_.get() - 1
        self.open_image(self.index)

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
        image = Image.open(path)
        if(resize):
            max_height = 500
            img = image 
            s = img.size
            ratio = max_height / s[1]
            image = img.resize((int(s[0]*ratio), int(s[1]*ratio)), Image.ANTIALIAS)
        return image

    @staticmethod
    def _copy_image(label, ind):
        """
        Copies a file to a new label folder using the shutil library. The file will be copied into a
        subdirectory called label in the input folder.
        :param input_path: Path of the original image
        :param label: The label
        """
        root, file_name = os.path.split(df.sorted_in_folder[ind])
        # two lines below check if the filepath contains as an ending a folder with the name of one of the labels
        # if so, this folder is being cut out of the path
        if os.path.split(root)[1] in labels:
            root = os.path.split(root)[0]
            os.remove(df.sorted_in_folder[ind])
            
        output_path = os.path.join(root, label, file_name)
        print("file_name =",file_name)
        print(" %s --> %s" % (file_name, label))
        copyfile(df.im_path[ind], output_path)
        
        # keep track that the image location has been changed by putting the new location-path in sorted_in_folder    
        df.loc[ind,'sorted_in_folder'] = output_path
        #####
        
        df.to_csv(df_path)

    @staticmethod
    def _move_image(label, ind):
        """
        Moves a file to a new label folder using the shutil library. The file will be moved into a
        subdirectory called label in the input folder. This is an alternative to _copy_image, which is not
        yet used, function would need to be replaced above.
        :param input_path: Path of the original image
        :param label: The label
        """
        root, file_name = os.path.split(df.sorted_in_folder[ind])
        # two lines below check if the filepath contains as an ending a folder with the name of one of the labels
        # if so, this folder is being cut out of the path
        if os.path.split(root)[1] in labels:
            root = os.path.split(root)[0]
        output_path = os.path.join(root, label, file_name)
        print("file_name =",file_name)
        print(" %s --> %s" % (file_name, label))
        move(df.sorted_in_folder[ind], output_path)
            
        # keep track that the image location has been changed by putting the new location-path in sorted_in_folder    
        df.loc[ind,'sorted_in_folder'] = output_path
        #####


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
#     # Make input arguments
#     parser = argparse.ArgumentParser()
#     parser.add_argument('-f', '--folder', help='Input folder where the *tif images should be', required=True)
#     parser.add_argument('-l', '--labels', nargs='+', help='Possible labels in the images', required=True)
#     args = parser.parse_args()

#     # grab input arguments from args structure
#     input_folder = args.folder
#     labels = args.labels
    
    # Make folder for the new labels
    for label in labels:
        make_folder(os.path.join(input_folder, label))

    # Put all image file paths into a list
    paths = []
#     for file in os.listdir(input_folder):
#         if file.endswith(".tif") or file.endswith(".tiff"):

#             path = os.path.join(input_folder, file)
#             paths.append(path).

    ######## added in version 2
    file_names = [fn for fn in sorted(os.listdir(input_folder))
                  if any(fn.endswith(ext) for ext in file_extensions)]
    paths = [input_folder+file_name for file_name in file_names]
    
    
    try:
        df = pd.read_csv(df_path,header=0,index_col=0)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["im_path", 'tlx','tly','trx','try','blx','bly','brx','bry'])
        defaultValues = np.ones((len(paths),1))*0.5;
        df.im_path = paths
        for name in df.columns:
            if name != 'im_path':
                df[name] = defaultValues
        
    """
    if copy_or_move == 'copy':
        try:
            df = pd.read_csv(df_path, header=0)
            # Store configuration file values
        except FileNotFoundError:
            df = pd.DataFrame(columns=["im_path", 'sorted_in_folder'])
            df.im_path = paths
            df.sorted_in_folder = paths
    if copy_or_move == 'move':
        df = pd.DataFrame(columns=["im_path", 'sorted_in_folder'])
        df.im_path = paths
        df.sorted_in_folder = paths
    """
    #######
    
# Start the GUI
root = tk.Tk()
app = ImageGui(root, labels, paths)
root.mainloop()

