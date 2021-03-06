from __future__ import division

from model import *
from utils.utils import *
from dataset_process.sl_datasets import *

import os
import sys
import time
import datetime
import argparse
import cv2
from PIL import Image

import torch
from torch.utils.data import DataLoader
from torchvision import datasets
from torch.autograd import Variable

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.ticker import NullLocator

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image_folder", type=str, default="data/test", help="path to dataset")
    parser.add_argument("--model_def", type=str, default="config/yolov3.cfg", help="path to model definition file")
    parser.add_argument("--weights_path", type=str, default="checkpoints/yolov3_ckpt_219.pth", help="path to weights file")
    parser.add_argument("--class_path", type=str, default="config/sldata.names", help="path to class label file")
    parser.add_argument("--conf_thres", type=float, default=0.9, help="object confidence threshold")
    parser.add_argument("--nms_thres", type=float, default=0.4, help="iou thresshold for non-maximum suppression")
    parser.add_argument("--batch_size", type=int, default=4, help="size of the batches")
    parser.add_argument("--n_cpu", type=int, default=0, help="number of cpu threads to use during batch generation")
    parser.add_argument("--img_size", type=int, default=512, help="size of each image dimension")
    parser.add_argument("--checkpoint_model", type=str, help="path to checkpoint model")
    opt = parser.parse_args()
    print(opt)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    os.makedirs("output", exist_ok=True)

    # Set up model
    model = Darknet(opt.model_def, img_size=opt.img_size).to(device)

    if opt.weights_path.endswith(".weights"):
        # Load darknet weights
        model.load_darknet_weights(opt.weights_path)
    else:
        # Load checkpoint weights
        model.load_state_dict(torch.load(opt.weights_path))

    model.eval()  # Set in evaluation mode

    dataloader = DataLoader(
        ImageFolder(opt.image_folder, img_size=opt.img_size),
        batch_size=opt.batch_size,
        shuffle=False,
        num_workers=opt.n_cpu,
    )

    classes = load_classes(opt.class_path)  # Extracts class labels from file

    Tensor = torch.cuda.FloatTensor if torch.cuda.is_available() else torch.FloatTensor

    imgs = []  # Stores image paths
    img_detections = []  # Stores detections for each image index

    print("\nPerforming object detection:")
    prev_time = time.time()
    for batch_i, (img_paths, input_imgs) in enumerate(dataloader):
        # Configure input
        input_imgs = np.concatenate((input_imgs,input_imgs,input_imgs),axis=1)
        input_imgs = Variable(torch.from_numpy(input_imgs).to(device))

        # Get detections
        with torch.no_grad():
            detections = model(input_imgs)
            detections = non_max_suppression(detections, opt.conf_thres, opt.nms_thres)

        # Log progress
        current_time = time.time()
        inference_time = datetime.timedelta(seconds=current_time - prev_time)
        prev_time = current_time
        print("\t+ Batch %d, Inference Time: %s" % (batch_i, inference_time))

        # Save image and detections
        imgs.extend(img_paths)
        img_detections.extend(detections)



    print("\nSaving images:")
    # Iterate through images and save plot of detections
    for img_i, (path, detections) in enumerate(zip(imgs, img_detections)):
        # predict_txt = 'F:\Projects\yolov3\yolov3SL\data\\train_val138\predict\\' + path.split('\\')[-1].split('.')[0] + '.txt'

        print("(%d) Image: '%s'" % (img_i, path))
        img_cv = cv2.imread(path)

        # Draw bounding boxes and labels of detections
        if detections is not None:
            # Rescale boxes to original image
            detections = rescale_boxes(detections, opt.img_size, img_cv.shape[:2])
            unique_labels = detections[:, -1].cpu().unique()
            n_cls_preds = len(unique_labels)
            for x1, y1, x2, y2, conf, cls_conf, cls_pred in detections:
                #
                # f = open(predict_txt, 'w+')
                # s = '{:.5f} {:.5f} {:.5f} {:.5f} {:.5f}'.format(x1.item(),y1.item(),x2.item()
                #                                            ,y2.item(),cls_conf.item())
                # f.write(s)

                print("\t+ Label: %s, Conf: %.5f" % (classes[int(cls_pred)], cls_conf.item()))


                # Create a Rectangle in cv2_img

                cv2.rectangle(img_cv, (x1, y1), (x2, y2), (255, 255, 255), thickness=1)
                text = classes[int(cls_pred)] + ':' + str(cls_conf.item())
                cv2.putText(img_cv, text, (x1, y1), cv2.FONT_HERSHEY_COMPLEX, 0.3, (0, 255, 0),
                            thickness=1)

                filename = path.split("/")[-1].split(".")[0]
                save_path = 'F:\Projects\yolov3\sl-master\output\\' + filename + '.png'
                print(save_path)
                cv2.imwrite(save_path, img_cv)  # save picture
