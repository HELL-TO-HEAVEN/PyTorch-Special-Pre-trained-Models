# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 16:04:34 2018

@author: ZHAO Yuzhi
"""

import os
import numpy as np
import torch
from torchvision import transforms
from PIL import Image
from skimage import color

# read a txt expect EOF
def text_readlines(filename):
    # Try to read a txt file and return a list.Return [] if there was a mistake.
    try:
        file = open(filename, 'r')
    except IOError:
        error = []
        return error
    content = file.readlines()
    # This for loop deletes the EOF (like \n)
    for i in range(len(content)):
        content[i] = content[i][:len(content[i]) - 1]
    file.close()
    return content

# save a list to a txt
def text_save(content, filename, mode='a'):
    # Try to save a list variable in txt file.
    file = open(filename, mode)
    for i in range(len(content)):
        file.write(str(content[i]) + '\n')
    file.close()

# VGG-16 accuracy for one image
# input: one imgpath, a VGG-16 model and the ground truth label
# output: top1 and top5 accuracy (0 or 1)
def get_lab(img):
    # pre-processing, let all the images are in RGB color space
    img = img.resize((224, 224), Image.ANTIALIAS).convert('RGB')        # PIL Image RGB: R [0, 255], G [0, 255], B [0, 255], order [H, W, C]
    img = np.array(img)                                                 # numpy RGB: R [0, 255], G [0, 255], B [0, 255], order [H, W, C]
    # convert RGB to Lab, finally get Tensor
    lab = color.rgb2lab(img).astype(np.float32)                         # skimage Lab: L [0, 100], a [-128, 127], b [-128, 127], order [H, W, C]
    lab = transforms.ToTensor()(lab)                                    # Tensor Lab: L [0, 100], a [-128, 127], b [-128, 127], order [C, H, W]
    # normaization
    lab[[0], ...] = lab[[0], ...] / 50 - 1.0                            # L, normalized to [-1, 1]
    lab[[1, 2], ...] = lab[[1, 2], ...] / 110.0                         # a and b, normalized to [-1, 1], approximately
    return lab

def Classification_Acuuracy(imgpath, model, label):
    # Read the images
    img = Image.open(imgpath)
    target = get_lab(img)
    target = target.unsqueeze_(dim = 0)
    target = target.cuda()

    # Evaluate the accuracy
    out = model(target)
    out = torch.softmax(out, 1)
    maxk = max((1, 5))
    _, pred = out.topk(maxk, 1, True, True)
    pred_top5 = pred.cpu().numpy().squeeze()

    # Compare the result and label; -1 because targetlist is from 1~1000
    label = int(label) - 1
    if pred_top5[0] == label:
        top1 = 1
    else:
        top1 = 0
    top5 = 0
    for i in range(len(pred_top5)):
        if pred_top5[i] == label:
            top5 = 1

    return top1, top5

# VGG-16 accuracy for dataset
def Dset_Acuuracy(vgg16, imglist, targetlist, basepath):
    # Define the list saving the accuracy
    top1list = []
    top5list = []
    top1ratio = 0
    top5ratio = 0

    # Compute the accuracy
    for i in range(len(imglist)):
        # Full imgpath
        imgname = imglist[i]
        imgpath = basepath + imgname
        # Seek for the index; index = i
        # Compute the top-1 and top-5 accuracy
        top1, top5 = Classification_Acuuracy(imgpath, vgg16, targetlist[i])
        top1list.append(top1)
        top5list.append(top5)
        top1ratio = top1ratio + top1
        top5ratio = top5ratio + top5
        print('The %dth image: top1: %d, top5: %d' % (i, top1, top5))
    top1ratio = top1ratio / len(imglist)
    top5ratio = top5ratio / len(imglist)

    return top1list, top5list, top1ratio, top5ratio

if __name__ == "__main__":
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"

    # Pre-trained VGG-16
    vgg16 = torch.load('./LabVGG16_FC/LabVGG16_FC_BN_epoch125_batchsize32.pth').cuda()
    vgg16.eval()
    # Read all names
    imglist = text_readlines('ILSVRC2012_val_name.txt')
    # Define target list of validation set 50000 images (index: 0~49999)
    targetlist = text_readlines('imagenet_2012_validation_scalar.txt')
    # Define imgpath
    basepath = 'C:\\Users\\ZHAO Yuzhi\\Desktop\\dataset\\ILSVRC2012_val_256\\'
    # Define the name you want to save as
    base = 'epoch 125 / LabVGG16_FC'

    top1list, top5list, top1ratio, top5ratio = Dset_Acuuracy(vgg16, imglist, targetlist, basepath)

    print('The overall results for %s: top1ratio: %f, top5ratio: %f' % (base, top1ratio, top5ratio))
