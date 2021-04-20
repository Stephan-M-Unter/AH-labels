'''
    LabelMe.py - a script to process image annotations.

    Author:             Stephan M. Unter
    Version + Date:     0.1 | 28/01/21

    Description:        This is a quick&dirty script to process the annotation files created with
                        LabelMe (https://github.com/wkentaro/labelme), a software designed to add
                        labelled regions to an image. So far, the script allows for the following
                        actions:
                            1) process annotation files, i.e. read the polygonal areas from the image
                            and save them to a predefined folder structure (default: sorted by label);
                            the processed json will be archived. If there are snippets from earlier
                            attempts, these snippets will be deleted first.
                            2) change resolution of an annotation file (user has to input source ppi and
                            target ppi) - useful if the resolution of an image has changed between labelling
                            and processing
                            3) change folder structure between "labels first" and "annotations first" mode
'''

import sys, os, json
import tkinter as tk
from tkinter import filedialog
import numpy as np
from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None

def process_annotations():
    ### Hardcoded Settings ###
    root = tk.Tk()
    root.withdraw()
    annotations_folder = filedialog.askdirectory(title="Select Folder inlcuding Annotation Files:")+"/"
    snippet_folder = f"{annotations_folder}/Snippets/"
    archive_folder = f"{annotations_folder}/Archive/"

    # initial creation of snippet folder
    if not os.path.isdir(snippet_folder):
        os.makedirs(snippet_folder)
        print("Do you want to save by labels or by annotation?\n")
        print("1) by labels")
        print("2) by annotations\n")
        save_mode = input("Enter number of prefered save mode:\n")
        try:
            save_mode = int(save_mode)
        except:
            print("Error - the user input was not a valid number.")
            sys.exit()
        if save_mode != 1 and save_mode != 2:
            print("Error - the user input was invalid, please select one of the available options.")
            sys.exit()
        if save_mode == 1:
            with open(f"{snippet_folder}/.labels", "w") as f:
                print("Saving by labels activated.")
            f.close()
            save_mode = "labels"
        else:
            with open(f"{snippet_folder}/.papyri", "w") as f:
                print("Saving by annotation activated.")
            f.close()
            save_mode = "annotations"
    else:
        # snippet_folder already exists - determine save mode
        if ".papyri" in os.listdir(snippet_folder):
            save_mode = "annotations"
        elif ".labels" in os.listdir(snippet_folder):
            save_mode = "labels"
        else:
            with open(f"{snippet_folder}/.labels", "w") as f:
                print("Setting save mode to labels first.")
            f.close()
            save_mode = "labels"
    # initial creation of archive folder for used json files
    if not os.path.isdir(archive_folder):
        os.makedirs(archive_folder)

    # returns dict with x, y, width and height of minimal bounding rectangle (mbr)
    def get_bounding_rectangle(list_of_vertices, ratio=1):
        x = 0
        y = 0
        w = 0
        h = 0
        xs = []
        ys = []
        for point in list_of_vertices:
            xs.append(int(point[0]*ratio))
            ys.append(int(point[1]*ratio))
        xs = sorted(xs)
        ys = sorted(ys)
        x = int(xs[0])
        y = int(ys[0])
        w = int(xs[-1] - xs[0])
        h = int(ys[-1] - ys[0])
        return {"type":"mbr", "x": x, "y": y, "w": w, "h": h}

    # # creating folders for new labels
    # def create_folders(snippet_folder, label):
    #     # some replacements for non-alphanumeric characters (like in JSesh codes)
    #     label = label.replace(":", "-")
    #     label = label.replace("&", "-")
    #     label = label.replace("*", "-")
    #     label = label + "/"
    #     if os.path.isdir(snippet_folder+label):
    #         return snippet_folder+label
    #     else:
    #         os.makedirs(snippet_folder+label)
    #         print(f"Created new folder structure for {label}.")
    #         return snippet_folder+label

    # checks all folders for snippets created by the given annotation and removes them
    def remove_old_snippets(snippet_folder, annotation_name):
        labels = [file for file in os.listdir(snippet_folder) if not file.startswith(".")]
        remove_counter = 0
        print(f"Checking {len(os.listdir(snippet_folder))} labels:")
        for label in labels:
            label_folder = f"{snippet_folder}{label}/"
            if not os.path.isdir(label_folder):
                continue
            files = [f"{label_folder}"+file for file in os.listdir(label_folder) if file.startswith(annotation_name[:annotation_name.rfind(".")])]
            for file in files:
                try:
                    os.remove(file)
                    remove_counter += 1
                except:
                    continue
        print(f"{remove_counter} files have been successfully removed.")

    # removing empty label folders
    def clear_empty_folders(snippet_folder):
        label_folders = [f"{snippet_folder}{label}/" for label in os.listdir(snippet_folder) if not label.startswith(".")]
        print(f"Checking {len(label_folders)} labels for empty folders.")
        counter_labels = 0
        for label in label_folders:
            try:
                os.rmdir(label)
                counter_labels += 1
            except:
                continue
        print(f"{counter_labels} labels removed.")


    def create_content_file(snippet_folder):
        files = []
        # create list of all annotation files from file names without duplicates
        for label in os.listdir(snippet_folder):
            if not os.path.isdir(snippet_folder+label):
                continue
            files = sorted(list(set(files + [file[:file.rfind("-")] for file in os.listdir(snippet_folder + label)])))
        # remove old content file
        if "content.txt" in os.listdir(snippet_folder):
            os.remove(snippet_folder+"content.txt")
        # write new content file
        with open(snippet_folder+"content.txt", "w") as f:
            f.write("Snippets have been generated from following annotation files:\n")
            f.write("\n")
            for file in files:
                f.write(file+".json\n")
        f.close()
        print("New content file generated.")

    def save_file(image, mode, snippet_folder, label, annotation, filename, dpi):
        label = label.replace(":", "-")
        label = label.replace("&", "-")
        label = label.replace("*", "-")
        if mode == "labels":
            # make sure label folder exists:
            if not os.path.isdir(f"{snippet_folder}/{label}"):
                os.makedirs(f"{snippet_folder}/{label}")
            image.save(f"{snippet_folder}{label}/{filename}.jpg", dpi=dpi)
        elif mode == "annotations":
            # make sure that annotation folder exists:
            if not os.path.isdir(f"{snippet_folder}/{annotation}"):
                os.makedirs(f"{snippet_folder}/{annotation}")
            # next, make sure that label folder exists:
            if not os.path.isdir(f"{snippet_folder}/{annotation}/{label}"):
                os.makedirs(f"{snippet_folder}/{annotation}/{label}")
            image.save(f"{snippet_folder}{annotation}/{label}/{filename}.jpg", dpi=dpi)
        return

    annotations = [file for file in os.listdir(annotations_folder) if ".json" in file]
    proc_log = {}
    # we iterate over all annotation files, which are the json files provided by scholars
    for annotation in annotations:
        print("*****")
        print(f"Processing {annotation}:")
        print("*****\n")
        with open(annotations_folder+annotation) as f:
            data = json.load(f)

        labels = []

        image_path = data["imagePath"]
        image_path = image_path.replace("\\", "/") # for different operating systems
        if image_path.startswith("./"):
            # relative path, starting in the annotation folder
            image_path = annotations_folder + image_path[image_path.find('/')+1:]
        elif image.path.startswith("../"):
            # relative path, but starts in some folder above annotation folder
            image_path = annotations_folder + image_path[image_path.rfind("../")+1:]
        # in other cases, the image_path already was an absolute path and nothing has to be changed

        name = annotation[:annotation.rfind(".")]
        number_shapes = len(data["shapes"])
        count = 0

        # check if there are resolution changes
        src_ppi = 1
        trg_ppi = 1
        if "srcPPI" in data:
            src_ppi = data["srcPPI"]
        if "targetPPI" in data:
            trg_ppi = data["targetPPI"]
        ratio = trg_ppi / src_ppi

        # remove old entries created by this annotation file
        remove_old_snippets(snippet_folder, annotation)

        # open original image
        dpi = (96,96)
        image = Image.open(image_path).convert("RGBA")
        try:
            dpi = image.info['dpi']
            print(f"DPI in original image: {dpi}")
        except:
            print("DPI information in original image unavailable.")
            print("Output DPI set to (96,96).")
        imageArray = np.asarray(image)

        # next, iterate over all shapes in the file
        for shape in data["shapes"]:
            label = shape["label"]
            if label not in labels:
                labels.append(label)

            shape_name = f"{name}-{count}"

            mbr = get_bounding_rectangle(shape["points"], ratio)
            polygon = [( int(point[0]*ratio), int(point[1]*ratio) ) for point in shape['points']]

            # create polygons and save them to label folder
            maskImage = Image.new("L", (imageArray.shape[1], imageArray.shape[0]), 0)
            ImageDraw.Draw(maskImage).polygon(polygon, outline=1, fill=1)
            mask = np.array(maskImage)

            newImagePolygonArray = np.empty(imageArray.shape, dtype='uint8')
            newImagePolygonArray[:,:,:3] = imageArray[:,:,:3]
            newImagePolygonArray[:,:,3] = mask*255

            # reduce array to snippet dimensions
            newImagePolygonArray = newImagePolygonArray[mbr["y"]:mbr["y"]+mbr["h"],mbr["x"]:mbr["x"]+mbr["w"],:]

            bg = np.array([255, 255, 255])
            alpha = (newImagePolygonArray[:, :, 3] / 255).reshape(newImagePolygonArray.shape[:2] + (1,))
            newImagePolygonArray = ((bg * (1 - alpha)) + (newImagePolygonArray[:, :, :3] * alpha)).astype(np.uint8)

            newImage = Image.fromarray(newImagePolygonArray, "RGB")
            save_file(newImage, save_mode, snippet_folder, label, name, shape_name, dpi)

            print(f"{label} processed. ({count+1}/{number_shapes})                            \r")
            count += 1
            if label not in proc_log:
                proc_log[label] = 1
            else:
                proc_log[label] += 1

        # moved processed annotation file to archive
        os.rename(annotations_folder+annotation, archive_folder+annotation)

    clear_empty_folders(snippet_folder)

    print("*************")
    print("Finished processing, the following labels have been added:\n")
    for label in proc_log:
        print(f"{label}: {proc_log[label]}")
    print("*************\n")

    create_content_file(snippet_folder)

def change_json_resolution():
    # input of json file
    root = tk.Tk()
    root.withdraw()
    filepath = filedialog.askopenfilename(filetypes=[("JSON-File", '.json')])
    filename = os.path.basename(filepath)
    filestem = filename[:filename.rfind(".")]
    folder = filepath[:-len(filename)]
    print(f"Selected file: {filepath}")

    # input of source and target resolution
    src_ppi = input("What is the source resolution in ppi?\n")
    target_ppi = input("What is the target resolution in ppi?\n")
    # TODO make sure that only numbers are allowed
    src_ppi = int(src_ppi)
    target_ppi = int(target_ppi)
    ratio = target_ppi / src_ppi

    with open(filepath) as f:
        data = json.load(f)

    for idx, shape in enumerate(data["shapes"]):
        for idy, point in enumerate(shape["points"]): 
            data["shapes"][idx]["points"][idy] = [coord*ratio for coord in point]

    with open(f"{folder}/{filestem}_{target_ppi}ppi.json", "w") as output:
        json.dump(data, output)

def restructure_folder():
    root = tk.Tk()
    root.withdraw()
    snippet_dir = filedialog.askdirectory()

    print(f"Selected directory: {snippet_dir}")

    content = os.listdir(snippet_dir)
    mode = "ltp"
    if ".papyri" in content:
        mode = "ptl"

    main_content = [file for file in content if os.path.isdir(f"{snippet_dir}/{file}")]

    files = []

    for folder in main_content:
        if mode == "ltp":
            # label mode, i.e. main_content consists of label folders, all files directly under that
            files = files + [f"{snippet_dir}/{folder}/{file}" for file in os.listdir(f"{snippet_dir}/{folder}") if not file.startswith(".")]
        else:
            # papyrus mode, i.e. there are first papyrus folders, then label folders, then the files
            subfolders = [subfolder for subfolder in os.listdir(f"{snippet_dir}/{folder}") if os.path.isdir(f"{snippet_dir}/{folder}/{subfolder}")]
            for subfolder in subfolders:
                files = files + [f"{snippet_dir}/{folder}/{subfolder}/{file}" for file in os.listdir(f"{snippet_dir}/{folder}/{subfolder}") if not file.startswith(".")]

    for file in files:
        file = file.replace("\\", "/")

        folder = file[:file.rfind("/")]
        name = file[file.rfind("/")+1:file.rfind("-")]
        filename = file[file.rfind("/")+1:]
        # extension = file[file.rfind(".")+1:]
        label = file[:file.rfind("/")]
        label = label[label.rfind("/")+1:]

        if mode == "ltp":
            # first, check if the papyrus folder already exists
            if not os.path.isdir(f"{snippet_dir}/{name}"):
                os.makedirs(f"{snippet_dir}/{name}")
            # second, check if the label folder exists
            if not os.path.isdir(f"{snippet_dir}/{name}/{label}"):
                os.makedirs(f"{snippet_dir}/{name}/{label}")
            # move file from original label folder to new papyrus-label folder
            os.rename(file, f"{snippet_dir}/{name}/{label}/{filename}")
        else:
            # first, check if the label folder already exists
            if not os.path.isdir(f"{snippet_dir}/{label}"):
                os.makedirs(f"{snippet_dir}/{label}")
            # next move file from original folder to new label folder
            os.rename(file, f"{snippet_dir}/{label}/{filename}")

        # check if original folder is empty, if so, remove it:
        if len(os.listdir(folder)) == 0:
            os.removedirs(folder)

    # last, add control file
    if ".papyri" in content:
        os.remove(f"{snippet_dir}/.papyri")
        with open(f"{snippet_dir}/.labels", "w") as f:
            print("Folders changed to label mode.")
        f.close()
    else:
        os.remove(f"{snippet_dir}/.labels")
        with open(f"{snippet_dir}/.papyri", "w") as f:
            print("Folders changed to papyrus mode.")
        f.close()

print("Welcome to the LableMe Processor - a quick&dirty tool written to")
print("cut out predefined label regions from images, redefine annotation files")
print("or restructure resulting folders.\n")

print("Please select what you would like to do:\n")
print("1) Process annotation files and create snippets.")
print("2) Change resolution of an annotational .json file.")
print("3) Restructure snippet folder.\n")

user_mode = input("Please enter the number of your desired task:\n")

# ensuring correctness of user input
try:
    user_mode = int(user_mode)
except:
    print("Error - please restart the script and enter a valid number.")
    sys.exit()
if user_mode < 1 or user_mode > 3:
    print("Error - please restart the script and select one of the available numbers.")
    sys.exit()

if user_mode == 1:
    process_annotations()
elif user_mode == 2:
    change_json_resolution()
elif user_mode == 3:
    restructure_folder()