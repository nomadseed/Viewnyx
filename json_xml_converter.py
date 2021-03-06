# -*- coding: utf-8 -*-
"""
Created on Thu Jul  5 15:55:31 2018

convert the annotation of viewnyx dataset from json to xml, or opposite

@author: Wen Wen
"""
import sys
import os
import json
import argparse
import numpy as np

from lxml import etree
import xml.etree.ElementTree as ET


def jsonRead(filename):
    return json.load(open(filename))

def convertJson2Xml(jsondata, imagepath):
    """
    to convert json annotation (one json per folder) into xml (one xml per image)
    Input:
        jsondata: annotation for all images under a single folder
        imagepath: to know the folder name and to save the xml file
    
    """
    
    totalfile=len(jsondata)
    print(str(totalfile)+' files in the json '+imagepath)
    cnt = 0
    
    for imagename in jsondata:
        # for each image
        root=ET.Element('annotation')
        ET.SubElement(root,'folder').text=imagepath.split('/')[-2]
        ET.SubElement(root,'filename').text=jsondata[imagename]['name']
        ET.SubElement(root, 'datasetname').text  = 'Viewnyx part 1'
        sub = ET.SubElement(root, "size")
        ET.SubElement(sub, "width").text  = str(jsondata[imagename]['width'])
        ET.SubElement(sub, "height").text  = str(jsondata[imagename]['height'])
        ET.SubElement(sub, "depth").text  = '3'
        ET.SubElement(root, "segmented").text='0'
        
        # save each bounding box in the image
        for bbx in jsondata[imagename]['annotations']:
            obj = ET.SubElement(root, "object")
            ET.SubElement(obj, "name").text  = bbx['label'].lower() # change it to lower letters
            ET.SubElement(obj, "pose").text  = 'left'
            ET.SubElement(obj, 'heading').text = bbx['category']
            ET.SubElement(obj,'id').text = str(bbx['id'])
            ET.SubElement(obj, "truncated").text  = '0'
            ET.SubElement(obj, "difficult").text  = '0'
            bndbox = ET.SubElement(obj,'bndbox')
            ET.SubElement(bndbox, "xmin").text = str(bbx['x'])
            ET.SubElement(bndbox, "ymin").text = str(bbx['y'])
            ET.SubElement(bndbox, "xmax").text = str(bbx['x']+bbx['width'])
            ET.SubElement(bndbox, "ymax").text = str(bbx['y']+bbx['height'])
        
        # save the xml file for current image with pretty printing
        
        xmlstr=ET.tostring(root) # return a binary string if encoding is default
        tree=etree.fromstring(xmlstr)
        xmlstr=etree.tostring(tree,pretty_print=True) # reform the xml string with pretty printing
        with open(imagepath+imagename.replace('jpg','xml'),'wb') as savefile:
            savefile.write(xmlstr)
            
        if ((10*cnt)%totalfile) <= 1:
            print(100*cnt/totalfile, '%')
        cnt+=1        
    
def getImageList(filepath,keyword_with='jpg',keyword_without='o'):
    '''
    find all the specified images under a folder
    Input:
        filepath: path of file
        keyword_with: if this word appears in the name, choose it
        keyword_without: if this word appears in the name, ignore it
        
    Example:
        getImageList('./','jpg','flipped')
    
    '''
    filelist=os.listdir(filepath)
    newlist=[]
    for i in range(0,len(filelist)):
        if keyword_with in filelist[i] and keyword_without not in filelist[i]:
            newlist.append(filelist[i])
    return newlist
    
    
if __name__ == '__main__':
    # pass the parameters
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, 
                        default='./testframes/', 
                        help="File path of input data (default './testframes/')")
    
    args = parser.parse_args()
    
    # set the work directory 
    filepath=args.file_path

    # go to one folder
    folderlist=os.listdir(filepath)
    for i in folderlist:
        # operations below are in same folder
        if '.' in i:
            continue # it's not a folder but a file
        imagepath=filepath+i+'/'
        # get image list
        imagelist=getImageList(imagepath,'jpg','o')
        # get json data, there are filenames in those data
        jsonname = imagepath+'annotationfull_'+imagepath.split('/')[-2]+'.json'
        try:    
            jsondata = jsonRead(jsonname)   
        except:
            print('failed to open', jsonname, '------- json doesnt exist')
            continue
        
        # convert one json file into many xml file corresponding to the image names
        string=convertJson2Xml(jsondata, imagepath)
        
        

""" End of File """
