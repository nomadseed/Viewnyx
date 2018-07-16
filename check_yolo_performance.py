# -*- coding: utf-8 -*-
"""
Created on Thu Jul 12 14:52:06 2018

given the benchmark annotation, compare the result of yolo with it, return 
TP/FP/TN/FN, as well as percision and recall.


@author: Wen Wen
"""

import argparse
import cv2
import os
import time
import numpy as np
import json

def getIoU(bbx_benchmark,bbx_detect):
    """
    calculate Intersection over Union of two bounding boxes
    return 0 if no intersection
    
    """
    
    # get the cordinates of intersecting square
    x_inter_1=max(bbx_benchmark['x'],bbx_detect['x'])
    y_inter_1=max(bbx_benchmark['y'],bbx_detect['y'])
    x_inter_2=min(bbx_benchmark['x']+bbx_benchmark['width'],bbx_detect['x']+bbx_detect['width'])
    y_inter_2=min(bbx_benchmark['y']+bbx_benchmark['height'],bbx_detect['y']+bbx_detect['height'])
    
    # get intersect area
    inter_area = max(0, x_inter_2 - x_inter_1) * max(0, y_inter_2 - y_inter_1)
    
    # get bbx area
    benchmark_area = bbx_benchmark['width'] * bbx_benchmark['height']
    detect_area=bbx_detect['width'] * bbx_detect['height']
    
    # calculate IoU
    iou = inter_area / float(benchmark_area + detect_area - inter_area)
    
    # for debugging, check the result
    '''
    print('benchmark:(x1,y1)=',bbx_benchmark['x'],bbx_benchmark['y'],' (x2,y2)=',bbx_benchmark['x']+bbx_benchmark['width'],bbx_benchmark['y']+bbx_benchmark['height'])
    print('detect:(x1,y1)=',bbx_detect['x'],bbx_detect['y'],'(x2,y2)=',bbx_detect['x']+bbx_detect['width'],bbx_detect['y']+bbx_detect['height'])
    print('intersection area:',inter_area)
    print('benchmark area:',benchmark_area)
    print('detect area:',detect_area)
    print('IoU=',iou,'\n')
    '''
    
    
    return iou

def checkSingleImage(imgname,annos_benchmark,annos_detect,totalperformance,IOUthresh):
    # check every detected bbx, add the result to currentperformance
    performance=totalperformance
    # special case 1: no detected, but benchmark has cars, all false negative
    if len(annos_detect)==0:
        if len(annos_benchmark)!=0:
            for bbx in annos_benchmark:
                if bbx['category'].lower()=='leading':
                    performance['leading']['fn']+=1
                    performance['overall']['fn']+=1
                elif bbx['category'].lower()=='sideways':
                    # no benchmark for leading car, tn
                    performance['overall']['fn']+=1
                    
    # special case 2: no benchmark, but detected, all false positive
    elif len(annos_benchmark)==0:
        if len(annos_detect)!=0:
            for bbx in annos_detect:
                if bbx['category'].lower()=='leading':
                    performance['leading']['fp']+=1
                    performance['overall']['fp']+=1
                elif bbx['category'].lower()=='sideways':
                    # no detection for leading car, tn
                    performance['overall']['fp']+=1
        
    # common case: both benchmark and detected file has bbx, calculate IoU
    else:
        benchlist=[] # to store the matched bbx
        detectlist=[] # to store the matched bbx
        for i in range(len(annos_benchmark)):
            # calculate IoU bbx in detect and bbx in benchmark            
            for j in range(len(annos_detect)):
                iou=getIoU(annos_benchmark[i],annos_detect[j])
                # true positive
                if iou>=IOUthresh:
                    if annos_benchmark[i]['category'].lower()==annos_detect[j]['category'].lower():
                        performance['leading']['tp']+=1
                        performance['overall']['tp']+=1
                    else:
                        # tp for overall
                        performance['overall']['tp']+=1
                        if annos_detect[j]['category'].lower()=='leading': 
                            # fp for leading car
                            performance['leading']['fp']+=1
                        elif annos_detect[j]['category'].lower()=='sideways':
                            # fn for leading car
                            performance['leading']['fn']+=1
                    
                    # mark the matched bbx in benchmark
                    benchlist.append(i)  
                    detectlist.append(j)
                    # go to next benchmark if already have one match
        '''
        print('imgname',imgname)
        print('bench',benchlist,'bench len',len(annos_benchmark))
        print('detect',detectlist,'detect len',len(annos_detect),'\n')
        '''
        
        # find the unmatched in benchmark, fn
        for i in range(len(annos_benchmark)):
            # if matched, skip
            if i in benchlist:
                continue
            else:
                performance['overall']['fn']+=1
                if annos_benchmark[i]['category']=='leading':
                    # miss a leading car in detection
                    performance['leading']['fn']+=1
        
        # find the unmatched in detect, fp
        for i in range(len(annos_detect)):
            # if matched, skip
            if i in detectlist:
                continue
            else:
                performance['overall']['fp']+=1
                if annos_detect[i]['category']=='leading':
                    # miss a leading car in detection
                    performance['leading']['fp']+=1
                
    
    return performance

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, 
                        default='FrameImages/', 
                        help="File path of input data")
    parser.add_argument('--IoU',type=float,default=0.5,help='percentage of IoU')
    args = parser.parse_args()
    
    filepath=args.file_path
    folderdict=os.listdir(filepath)
    IOUthresh=args.IoU
    
    # initial the numbers for performance
    totalperformance={'leading':{'tp':0, 'fp':0, 'tn':0, 'fn':0},
                      'overall':{'tp':0, 'fp':0, 'tn':0, 'fn':0}}
    
    for foldername in folderdict:
        jsonpath=filepath+foldername+'/'
        # load the json files
        # path for new dataset:jsonpath+'annotation_'+foldername+'_with_leading.json'
        # path for old dataset:jsonpath+'annotationfull_'+foldername+'.json'
        if not os.path.exists(jsonpath+'annotationfull_'+foldername+'.json'):
            continue   
        else:
            benchmark=json.load(open(jsonpath+'annotationfull_'+foldername+'.json'))
            detected=json.load(open(jsonpath+'annotation_'+foldername+'.json'))
        
        for imgname in detected:
            # if not detected
            if len(detected[imgname])==0:
                annos_detect={}
            else:
                annos_detect=detected[imgname]['annotations']
            
            # if no such a benchmark
            if benchmark.get(imgname)==None:
                annos_benchmark={}
            else:
                annos_benchmark=benchmark[imgname]['annotations']
            
            # calculate performance
            totalperformance=checkSingleImage(imgname,annos_benchmark,annos_detect,totalperformance,IOUthresh)
    
    # calculate precision, recall and missrate
    precision_leading=totalperformance['leading']['tp']/(totalperformance['leading']['tp']+totalperformance['leading']['fp'])
    precision_overall=totalperformance['overall']['tp']/(totalperformance['overall']['tp']+totalperformance['overall']['fp'])
    
    recall_leading=totalperformance['leading']['tp']/(totalperformance['leading']['tp']+totalperformance['leading']['fn'])
    recall_overall=totalperformance['overall']['tp']/(totalperformance['overall']['tp']+totalperformance['overall']['fn'])
    
    missrate_leading=totalperformance['leading']['fn']/(totalperformance['leading']['tp']+totalperformance['leading']['fn'])
    missrate_overall=totalperformance['overall']['fn']/(totalperformance['overall']['tp']+totalperformance['overall']['fn'])
    
    print('IoU threshold:',IOUthresh,'\n')
    
    print('overall performance on detecting cars:')
    print(totalperformance['overall'])
    print('precision:',precision_overall)
    print('recall:',recall_overall)
    print('miss rate:',missrate_overall,'\n')
    
    print('performance on detecting leading cars:')
    print(totalperformance['leading'])
    print('precision:',precision_leading)
    print('recall:',recall_leading)
    print('miss rate:',missrate_leading,'\n')
    
    
    
    
    
    
""" End of file """