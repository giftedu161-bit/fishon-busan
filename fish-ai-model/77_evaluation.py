import datetime
import os

import numpy as np
import torch
import yaml

from torch import nn
from tqdm.autonotebook import tqdm

from efficientdet.backbone import EfficientDetBackbone
from efficientdet.loss import FocalLoss_With_KP
from utils.utils import preprocess
from efficientdet.utils import BBoxTransform, ClipBoxes
from typing import Union
from utils.utils import postprocess_with_KP, invert_affine

from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval
import json
import time
import math

from copy import deepcopy

import cv2
from datetime import datetime

use_cuda = True
input_sizes = [512, 640, 768, 896, 1024, 1280, 1280, 1536, 1536]
compound_coef = 2
nms_threshold = 0.2
obj_list = []


class Params:
    def __init__(self, project_file):
        self.params = yaml.safe_load(open(project_file).read())

    def __getattr__(self, item):
        return self.params.get(item, None)

class ModelWithLoss(nn.Module):
    def __init__(self, model, debug=False):
        super().__init__()
        self.criterion = FocalLoss_With_KP()
        self.model = model
        self.debug = debug

    def forward(self, imgs, annotations, obj_list=None):
        _, regression, classification, anchors, regression_kp = self.model(imgs)
        if self.debug:
            cls_loss, reg_loss, reg_kp_loss = self.criterion(classification, regression, anchors, annotations, regression_kp,
                                                imgs=imgs, obj_list=obj_list)
        else:
            cls_loss, reg_loss, reg_kp_loss = self.criterion(classification, regression, anchors, annotations, regression_kp)
        return cls_loss, reg_loss, reg_kp_loss


def evaluate_coco(img_path, set_name, image_ids, coco, model, threshold=0.05, obj_list = []):
    results = []

    regressBoxes = BBoxTransform()
    clipBoxes = ClipBoxes()
    for image_id in tqdm(image_ids):
        image_info = coco.loadImgs(image_id)[0]
        file_name = image_info['file_name']

        if file_name[:4] == 'swim' or file_name[:4] == 'fish':
            if file_name[5:7] == 'rb':
                file_name = 'rb/' + file_name
            elif file_name[5:7] == 'bp':
                file_name = 'bp/' + file_name
            elif file_name[5:7] == 'kr':
                file_name = 'kr/' + file_name
            elif file_name[5:7] == 'of':
                file_name = 'of/' + file_name
            elif file_name[5:7] == 'rs':
                file_name = 'rs/' + file_name

        image_path = img_path + file_name

        ori_imgs, framed_imgs, framed_metas = preprocess(image_path, max_size=input_sizes[compound_coef])
        x = torch.from_numpy(framed_imgs[0])

        if use_cuda:
            x = x.cuda()
        else:
            x = x.float()

        x = x.unsqueeze(0).permute(0, 3, 1, 2)
        features, regression, classification, anchors, regression_kp = model(x)

        preds = postprocess_with_KP(x,
                            anchors, regression, regression_kp, classification,
                            regressBoxes, clipBoxes,
                            threshold, nms_threshold)

        preds = invert_affine(framed_metas, preds)

        ##########
        #display_with_kp(preds, ori_imgs, obj_list, imshow=True, imwrite=False)
        ##########

        if not preds:
            continue


        scores = preds[0]['scores']
        class_ids = preds[0]['class_ids']
        rois = preds[0]['rois']
        kps = preds[0]['kps']

        if rois.shape[0] > 0:
            # x1,y1,x2,y2 -> x1,y1,w,h
            rois[:, 2] -= rois[:, 0]
            rois[:, 3] -= rois[:, 1]

            bbox_score = scores

            for roi_id in range(rois.shape[0]):
                score = float(bbox_score[roi_id])
                label = int(class_ids[roi_id])
                box = rois[roi_id, :]
                kp = kps[roi_id, :]
                image_result = {
                    'image_id': image_id,
                    'category_id': label + 1,
                    'score': float(score),
                    'bbox': box.tolist(),
                    'kp': kp.tolist()
                }

                results.append(image_result)

    if not len(results):
        raise Exception('the model does not provide any valid output, check model architecture and the data input')

    # write output
    filepath = f'{set_name}_bbox_results.json'
    if os.path.exists(filepath):
        os.remove(filepath)
    json.dump(results, open(filepath, 'w'), indent=4)


def _eval(coco_gt, image_ids, pred_json_path):
    # load results in COCO evaluation tool
    coco_pred = coco_gt.loadRes(pred_json_path)

    print('-------------------------------')
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' [UCT+09:00]' + ' Total Results')
    # run COCO evaluation
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' [UCT+09:00]' + ' [BBox]')
    coco_eval = COCOeval(coco_gt, coco_pred, 'bbox')
    coco_eval.params.imgIds = image_ids
    # coco_eval.evaluate()
    # coco_eval.accumulate()
    #

    #for i in range(len())
    evaluate_with_kp(coco_eval)
    accumulate_with_kp(coco_eval)

    coco_eval.stats = np.zeros((3,))
    coco_eval.stats[0] = summarize(coco_eval, 1)
    coco_eval.stats[1] = summarize(coco_eval, 1, iouThr=.5, maxDets=coco_eval.params.maxDets[2])
    coco_eval.stats[2] = summarize(coco_eval, 1, iouThr=.6, maxDets=coco_eval.params.maxDets[2])

    coco_eval.summarize()
    #
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' [UCT+09:00]' + ' [Body Line]')
    #
    summary_kp(coco_eval)

    print('-------------------------------')
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' [UCT+09:00]' + ' Evaluation on Each Category...')

    for key in coco_gt.cats:
        id_index = coco_gt.cats[key]['id'] - 1
        name = coco_gt.cats[key]['name']
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' [UCT+09:00] ' + name + " Result")

        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' [UCT+09:00]' + ' [BBox]')

        coco_eval_each_cat = deepcopy(coco_eval)
        coco_eval_each_cat.eval['counts'][2] = 1
        coco_eval_each_cat.eval['precision'] = deepcopy(coco_eval.eval['precision'][:, :, id_index, :, :])
        coco_eval_each_cat.eval['precision'] = coco_eval_each_cat.eval['precision'].reshape(coco_eval_each_cat.eval['precision'].shape[0],
                                                     coco_eval_each_cat.eval['precision'].shape[1], 1,
                                                     coco_eval_each_cat.eval['precision'].shape[2],
                                                     coco_eval_each_cat.eval['precision'].shape[3])

        coco_eval_each_cat.eval['recall'] = deepcopy(coco_eval.eval['recall'][:, id_index, :, :])
        coco_eval_each_cat.eval['recall'] = coco_eval_each_cat.eval['recall'].reshape(coco_eval_each_cat.eval['recall'].shape[0], 1, coco_eval_each_cat.eval['recall'].shape[1], coco_eval_each_cat.eval['recall'].shape[2])

        coco_eval_each_cat.eval['scores'] = deepcopy(coco_eval.eval['scores'][:, :, id_index, :, :])
        coco_eval_each_cat.eval['scores'] = coco_eval_each_cat.eval['scores'].reshape(coco_eval_each_cat.eval['scores'].shape[0], coco_eval_each_cat.eval['scores'].shape[1], 1, coco_eval_each_cat.eval['scores'].shape[2], coco_eval_each_cat.eval['scores'].shape[3])

        #############

        coco_eval.stats = np.zeros((3,))
        coco_eval_each_cat.stats[0] = summarize(coco_eval_each_cat, 1)
        coco_eval_each_cat.stats[1] = summarize(coco_eval_each_cat, 1, iouThr=.5, maxDets=coco_eval_each_cat.params.maxDets[2])
        coco_eval_each_cat.stats[2] = summarize(coco_eval_each_cat, 1, iouThr=.6, maxDets=coco_eval_each_cat.params.maxDets[2])

        coco_eval_each_cat.summarize()


        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' [UCT+09:00]' + ' [Body Line]')

        summary_kp(coco_eval_each_cat, cat = id_index)

        print('\n')
        print('-------------------------------')

def summarize(coco_eval, ap=1, iouThr=None, areaRng='all', maxDets=100):
    p = coco_eval.params
    iStr = ' {:<18} {} @[ IoU={:<9} | area={:>6s} | maxDets={:>3d} ] = {:0.3f}'
    titleStr = 'Average Precision' if ap == 1 else 'Average Recall'
    typeStr = '(AP)' if ap == 1 else '(AR)'
    iouStr = '{:0.2f}:{:0.2f}'.format(p.iouThrs[0], p.iouThrs[-1]) \
        if iouThr is None else '{:0.2f}'.format(iouThr)

    aind = [i for i, aRng in enumerate(p.areaRngLbl) if aRng == areaRng]
    mind = [i for i, mDet in enumerate(p.maxDets) if mDet == maxDets]
    if ap == 1:
        # dimension of precision: [TxRxKxAxM]
        s = coco_eval.eval['precision']
        # IoU
        if iouThr is not None:
            t = np.where(iouThr == p.iouThrs)[0]
            s = s[t]
        s = s[:, :, :, aind, mind]
    else:
        # dimension of recall: [TxKxAxM]
        s = coco_eval.eval['recall']
        if iouThr is not None:
            t = np.where(iouThr == p.iouThrs)[0]
            s = s[t]
        s = s[:, :, aind, mind]
    if len(s[s > -1]) == 0:
        mean_s = -1
    else:
        mean_s = np.mean(s[s > -1])
    print(iStr.format(titleStr, typeStr, iouStr, areaRng, maxDets, mean_s))
    return mean_s

def evaluate_with_kp(coco_eval):
    '''
    Run per image evaluation on given images and store results (a list of dict) in self.evalImgs
    :return: None
    '''
    tic = time.time()
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' [UCT+09:00]' + ' Running per image evaluation...')
    p = coco_eval.params
    # add backward compatibility if useSegm is specified in params
    if not p.useSegm is None:
        p.iouType = 'segm' if p.useSegm == 1 else 'bbox'
        print('useSegm (deprecated) is not None. Running {} evaluation'.format(p.iouType))
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' [UCT+09:00]' + ' Evaluate annotation type *{}*'.format(p.iouType))
    p.imgIds = list(np.unique(p.imgIds))
    if p.useCats:
        p.catIds = list(np.unique(p.catIds))
    p.maxDets = sorted(p.maxDets)
    coco_eval.params=p

    coco_eval._prepare()
    # loop through images, area range, max detection number
    catIds = p.catIds if p.useCats else [-1]

    if p.iouType == 'segm' or p.iouType == 'bbox':
        computeIoU = coco_eval.computeIoU
    elif p.iouType == 'keypoints':
        computeIoU = coco_eval.computeOks
    coco_eval.ious = {(imgId, catId): computeIoU(imgId, catId) \
                    for imgId in p.imgIds
                    for catId in catIds}

    evaluateImg = coco_eval.evaluateImg
    maxDet = p.maxDets[-1]

    coco_eval.evalImgs = [evaluateImg_with_kp(coco_eval, imgId, catId, areaRng, maxDet)
                          for catId in catIds
                          for areaRng in p.areaRng
                          for imgId in p.imgIds
                          ]

    coco_eval._paramsEval = deepcopy(coco_eval.params)
    toc = time.time()
    print('DONE (t={:0.2f}s).'.format(toc-tic))

def evaluateImg_with_kp(coco_eval, imgId, catId, aRng, maxDet):
    '''
    perform evaluation for single category and image
    :return: dict (single image results)
    '''
    p = coco_eval.params
    if p.useCats:
        gt = coco_eval._gts[imgId,catId]
        dt = coco_eval._dts[imgId,catId]
    else:
        gt = [_ for cId in p.catIds for _ in coco_eval._gts[imgId,cId]]
        dt = [_ for cId in p.catIds for _ in coco_eval._dts[imgId,cId]]
    if len(gt) == 0 and len(dt) ==0:
        return None

    for g in gt:
        if g['ignore'] or (g['area']<aRng[0] or g['area']>aRng[1]):
            g['_ignore'] = 1
        else:
            g['_ignore'] = 0

    # sort dt highest score first, sort gt ignore last
    gtind = np.argsort([g['_ignore'] for g in gt], kind='mergesort')
    gt = [gt[i] for i in gtind]
    dtind = np.argsort([-d['score'] for d in dt], kind='mergesort')
    dt = [dt[i] for i in dtind[0:maxDet]]
    iscrowd = [int(o['iscrowd']) for o in gt]
    # load computed ious
    ious = coco_eval.ious[imgId, catId][:, gtind] if len(coco_eval.ious[imgId, catId]) > 0 else coco_eval.ious[imgId, catId]

    T = len(p.iouThrs)
    G = len(gt)
    D = len(dt)
    gtm  = np.zeros((T,G))
    dtm  = np.zeros((T,D))
    gtIg = np.array([g['_ignore'] for g in gt])
    dtIg = np.zeros((T,D))

    gtm  = np.ones((T,G)) * -1
    dtm  = np.ones((T,D)) * -1
    dtIg = np.ones((T, D)) * -1

    if not len(ious)==0:
        for tind, t in enumerate(p.iouThrs):
            for dind, d in enumerate(dt):
                # information about best match so far (m=-1 -> unmatched)
                iou = min([t,1-1e-10])
                m   = -1
                for gind, g in enumerate(gt):
                    # if this gt already matched, and not a crowd, continue
                    if gtm[tind,gind]>0 and not iscrowd[gind]:
                        continue
                    # if dt matched to reg gt, and on ignore gt, stop
                    if m>-1 and gtIg[m]==0 and gtIg[gind]==1:
                        break
                    # continue to next gt unless better match made
                    if ious[dind,gind] < iou:
                        continue
                    # if match successful and best so far, store appropriately
                    iou=ious[dind,gind]
                    m=gind
                # if match made store id of match for both dt and gt
                if m ==-1:
                    continue
                dtIg[tind,dind] = gtIg[m]
                dtm[tind,dind]  = gt[m]['id']
                gtm[tind,m]     = d['id']
    # set unmatched detections outside of area range to ignore
    a = np.array([d['area']<aRng[0] or d['area']>aRng[1] for d in dt]).reshape((1, len(dt)))
    dtIg = np.logical_or(dtIg, np.logical_and(dtm==0, np.repeat(a,T,0)))

    # calculate kp error based on
    # gtm
    gtm_kp_error = np.ones((T,G)) * -1
    for iou_idx in range(gtm.shape[0]):
        for obj_idx in range(gtm.shape[1]):
            if gtm[iou_idx, obj_idx] == -1:
                continue
            gt_obj_idx = int(gt[obj_idx]['id'])
            dt_obj_idx = int(gtm[iou_idx, obj_idx])
            gt_info = coco_eval.cocoGt.loadAnns(gt_obj_idx)
            dt_info = coco_eval.cocoDt.loadAnns(dt_obj_idx)

            #gt_kp = [gt_info[0]['keypoints1'][0], gt_info[0]['keypoints1'][1], gt_info[0]['keypoints1'][2], gt_info[0]['keypoints1'][3], gt_info[0]['keypoints2'][0], gt_info[0]['keypoints2'][1], gt_info[0]['keypoints2'][2], gt_info[0]['keypoints2'][3]]
            gt_kp = [gt_info[0]['keypoints'][0], gt_info[0]['keypoints'][1], gt_info[0]['keypoints'][2],
                     gt_info[0]['keypoints'][3], gt_info[0]['keypoints'][4], gt_info[0]['keypoints'][5],
                     gt_info[0]['keypoints'][6], gt_info[0]['keypoints'][7]]

            dt_kp = np.copy(dt_info[0]['kp'])

            for j in range(int(len(dt_kp)/2)):
                dt_kp[2 * j + 0] = (int)(dt_info[0]['bbox'][0] + 0.5) + (int)(dt_info[0]['bbox'][2] * dt_kp[2 * j + 0] + 0.5)
                dt_kp[2 * j + 1] = (int)(dt_info[0]['bbox'][1] + 0.5) + (int)(dt_info[0]['bbox'][3] * dt_kp[2 * j + 1] + 0.5)

            error = math.sqrt((gt_kp[0] - dt_kp[0]) * (gt_kp[0] - dt_kp[0]) + (gt_kp[1] - dt_kp[1]) * (gt_kp[1] - dt_kp[1])) + math.sqrt((gt_kp[2] - dt_kp[2]) * (gt_kp[2] - dt_kp[2]) + (gt_kp[3] - dt_kp[3]) * (gt_kp[3] - dt_kp[3])) + math.sqrt((gt_kp[4] - dt_kp[4]) * (gt_kp[4] - dt_kp[4]) + (gt_kp[5] - dt_kp[5]) * (gt_kp[5] - dt_kp[5])) + math.sqrt((gt_kp[6] - dt_kp[6]) * (gt_kp[6] - dt_kp[6]) + (gt_kp[7] - dt_kp[7]) * (gt_kp[7] - dt_kp[7]))
            error = error / (4 * (int)(dt_info[0]['bbox'][3]))

            gtm_kp_error[iou_idx, obj_idx] = error

            # ##Debug
            # gt_img_name = coco_eval.cocoGt.loadImgs(gt_info[0]['image_id'])[0]['file_name']
            # dt_img_name = coco_eval.cocoGt.loadImgs(dt_info[0]['image_id'])[0]['file_name']
            #
            # gt_img_path = opt.data_path + '/' + opt.project + '/val/' + gt_img_name[5:7] + '/' + gt_img_name
            # dt_img_path = opt.data_path + '/' + opt.project + '/val/' + dt_img_name[5:7] + '/' + dt_img_name
            #
            # gt_img = cv2.imread(gt_img_path)
            # dt_img = cv2.imread(dt_img_path)
            #
            # cv2.rectangle(gt_img, ((int)(gt_info[0]['bbox'][0] + 0.5), (int)(gt_info[0]['bbox'][1] + 0.5)), ((int)(gt_info[0]['bbox'][0] + gt_info[0]['bbox'][2] + 0.5), (int)(gt_info[0]['bbox'][1] + gt_info[0]['bbox'][3] + 0.5)), (0, 0, 255), 3)
            # cv2.rectangle(gt_img, ((int)(dt_info[0]['bbox'][0] + 0.5), (int)(dt_info[0]['bbox'][1] + 0.5)), ((int)(dt_info[0]['bbox'][0] + dt_info[0]['bbox'][2] + 0.5), (int)(dt_info[0]['bbox'][1] + dt_info[0]['bbox'][3] + 0.5)), (255, 0, 0), 2)
            #
            # cv2.line(gt_img, ((int)(gt_kp[0] + 0.5), (int)(gt_kp[1] + 0.5)), ((int)(gt_kp[2] + 0.5), (int)(gt_kp[3] + 0.5)), (0, 0, 255), 3)
            # cv2.line(gt_img, ((int)(gt_kp[4] + 0.5), (int)(gt_kp[5] + 0.5)), ((int)(gt_kp[6] + 0.5), (int)(gt_kp[7] + 0.5)), (0, 0, 255), 3)
            #
            # cv2.line(gt_img, ((int)(dt_kp[0] + 0.5), (int)(dt_kp[1] + 0.5)), ((int)(dt_kp[2] + 0.5), (int)(dt_kp[3] + 0.5)), (255, 0, 0), 2)
            # cv2.line(gt_img, ((int)(dt_kp[4] + 0.5), (int)(dt_kp[5] + 0.5)), ((int)(dt_kp[6] + 0.5), (int)(dt_kp[7] + 0.5)), (255, 0, 0), 2)
            #
            # cv2.imwrite('test.png', gt_img)
            #

            # dtm
    dtm_kp_error = np.ones((T,D)) * -1
    for iou_idx in range(dtm.shape[0]):
        for obj_idx in range(dtm.shape[1]):
            if dtm[iou_idx, obj_idx] == -1:
                continue
            gt_obj_idx = int(dtm[iou_idx, obj_idx])
            dt_obj_idx = int(dt[obj_idx]['id'])
            gt_info = coco_eval.cocoGt.loadAnns(gt_obj_idx)
            dt_info = coco_eval.cocoDt.loadAnns(dt_obj_idx)

            gt_kp = [gt_info[0]['keypoints'][0], gt_info[0]['keypoints'][1], gt_info[0]['keypoints'][2],
                     gt_info[0]['keypoints'][3], gt_info[0]['keypoints'][4], gt_info[0]['keypoints'][5],
                     gt_info[0]['keypoints'][6], gt_info[0]['keypoints'][7]]
            dt_kp = np.copy(dt_info[0]['kp'])

            for j in range(int(len(dt_kp) / 2)):
                dt_kp[2 * j + 0] = (int)(dt_info[0]['bbox'][0] + 0.5) + (int)(
                    dt_info[0]['bbox'][2] * dt_kp[2 * j + 0] + 0.5)
                dt_kp[2 * j + 1] = (int)(dt_info[0]['bbox'][1] + 0.5) + (int)(
                    dt_info[0]['bbox'][3] * dt_kp[2 * j + 1] + 0.5)

            error = math.sqrt((gt_kp[0] - dt_kp[0]) * (gt_kp[0] - dt_kp[0]) + (gt_kp[1] - dt_kp[1]) * (
                        gt_kp[1] - dt_kp[1])) + math.sqrt(
                (gt_kp[2] - dt_kp[2]) * (gt_kp[2] - dt_kp[2]) + (gt_kp[3] - dt_kp[3]) * (
                            gt_kp[3] - dt_kp[3])) + math.sqrt(
                (gt_kp[4] - dt_kp[4]) * (gt_kp[4] - dt_kp[4]) + (gt_kp[5] - dt_kp[5]) * (
                            gt_kp[5] - dt_kp[5])) + math.sqrt(
                (gt_kp[6] - dt_kp[6]) * (gt_kp[6] - dt_kp[6]) + (gt_kp[7] - dt_kp[7]) * (gt_kp[7] - dt_kp[7]))
            error = error / (4 * (int)(dt_info[0]['bbox'][3]))

            dtm_kp_error[iou_idx, obj_idx] = error

            # ##Debug
            # gt_img_name = coco_eval.cocoGt.loadImgs(gt_info[0]['image_id'])[0]['file_name']
            # dt_img_name = coco_eval.cocoGt.loadImgs(dt_info[0]['image_id'])[0]['file_name']
            #
            # gt_img_path = opt.data_path + '/' + opt.project + '/val/' + gt_img_name[5:7] + '/' + gt_img_name
            # dt_img_path = opt.data_path + '/' + opt.project + '/val/' + dt_img_name[5:7] + '/' + dt_img_name
            #
            # gt_img = cv2.imread(gt_img_path)
            # dt_img = cv2.imread(dt_img_path)
            #
            # cv2.rectangle(gt_img, ((int)(gt_info[0]['bbox'][0] + 0.5), (int)(gt_info[0]['bbox'][1] + 0.5)), ((int)(gt_info[0]['bbox'][0] + gt_info[0]['bbox'][2] + 0.5), (int)(gt_info[0]['bbox'][1] + gt_info[0]['bbox'][3] + 0.5)), (0, 0, 255), 3)
            # cv2.rectangle(gt_img, ((int)(dt_info[0]['bbox'][0] + 0.5), (int)(dt_info[0]['bbox'][1] + 0.5)), ((int)(dt_info[0]['bbox'][0] + dt_info[0]['bbox'][2] + 0.5), (int)(dt_info[0]['bbox'][1] + dt_info[0]['bbox'][3] + 0.5)), (255, 0, 0), 2)
            #
            # cv2.line(gt_img, ((int)(gt_kp[0] + 0.5), (int)(gt_kp[1] + 0.5)), ((int)(gt_kp[2] + 0.5), (int)(gt_kp[3] + 0.5)), (0, 0, 255), 3)
            # cv2.line(gt_img, ((int)(gt_kp[4] + 0.5), (int)(gt_kp[5] + 0.5)), ((int)(gt_kp[6] + 0.5), (int)(gt_kp[7] + 0.5)), (0, 0, 255), 3)
            #
            # cv2.line(gt_img, ((int)(dt_kp[0] + 0.5), (int)(dt_kp[1] + 0.5)), ((int)(dt_kp[2] + 0.5), (int)(dt_kp[3] + 0.5)), (255, 0, 0), 2)
            # cv2.line(gt_img, ((int)(dt_kp[4] + 0.5), (int)(dt_kp[5] + 0.5)), ((int)(dt_kp[6] + 0.5), (int)(dt_kp[7] + 0.5)), (255, 0, 0), 2)
            #
            # cv2.imwrite('test.png', gt_img)



    # store results for given image and category
    return {
            'image_id':     imgId,
            'category_id':  catId,
            'aRng':         aRng,
            'maxDet':       maxDet,
            'dtIds':        [d['id'] for d in dt],
            'gtIds':        [g['id'] for g in gt],
            'dtMatches':    dtm,
            'gtMatches':    gtm,
            'dtScores':     [d['score'] for d in dt],
            'dtm_kp_error': dtm_kp_error,
            'gtm_kp_error': gtm_kp_error,
            'gtIgnore':     gtIg,
            'dtIgnore':     dtIg,
        }

def accumulate_with_kp(coco_eval, p = None):
    '''
    Accumulate per image evaluation results and store the result in self.eval
    :param p: input params for evaluation
    :return: None
    '''
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' [UCT+09:00]' + ' Accumulating evaluation results...')
    tic = time.time()
    if not coco_eval.evalImgs:
        print('Please run evaluate() first')
    # allows input customized parameters
    if p is None:
        p = coco_eval.params
    p.catIds = p.catIds if p.useCats == 1 else [-1]
    T           = len(p.iouThrs)
    R           = len(p.recThrs)
    K           = len(p.catIds) if p.useCats else 1
    A           = len(p.areaRng)
    M           = len(p.maxDets)
    precision   = -np.ones((T,R,K,A,M)) # -1 for the precision of absent categories
    recall      = -np.ones((T,K,A,M))
    scores      = -np.ones((T,R,K,A,M))

    # create dictionary for future indexing
    _pe = coco_eval._paramsEval
    catIds = _pe.catIds if _pe.useCats else [-1]
    setK = set(catIds)
    setA = set(map(tuple, _pe.areaRng))
    setM = set(_pe.maxDets)
    setI = set(_pe.imgIds)
    # get inds to evaluate
    k_list = [n for n, k in enumerate(p.catIds)  if k in setK]
    m_list = [m for n, m in enumerate(p.maxDets) if m in setM]
    a_list = [n for n, a in enumerate(map(lambda x: tuple(x), p.areaRng)) if a in setA]
    i_list = [n for n, i in enumerate(p.imgIds)  if i in setI]
    I0 = len(_pe.imgIds)
    A0 = len(_pe.areaRng)
    # retrieve E at each category, area range, and max number of detections
    for k, k0 in enumerate(k_list):
        Nk = k0*A0*I0
        for a, a0 in enumerate(a_list):
            Na = a0*I0
            for m, maxDet in enumerate(m_list):
                E = [coco_eval.evalImgs[Nk + Na + i] for i in i_list]
                E = [e for e in E if not e is None]
                if len(E) == 0:
                    continue
                dtScores = np.concatenate([e['dtScores'][0:maxDet] for e in E])

                # different sorting method generates slightly different results.
                # mergesort is used to be consistent as Matlab implementation.
                inds = np.argsort(-dtScores, kind='mergesort')
                dtScoresSorted = dtScores[inds]

                dtm  = np.concatenate([e['dtMatches'][:,0:maxDet] for e in E], axis=1)[:,inds]
                dtIg = np.concatenate([e['dtIgnore'][:,0:maxDet]  for e in E], axis=1)[:,inds]
                gtIg = np.concatenate([e['gtIgnore'] for e in E])
                npig = np.count_nonzero(gtIg==0 )
                if npig == 0:
                    continue
                tps = np.logical_and(               dtm,  np.logical_not(dtIg) )
                fps = np.logical_and(np.logical_not(dtm), np.logical_not(dtIg) )

                tp_sum = np.cumsum(tps, axis=1).astype(dtype=np.float)
                fp_sum = np.cumsum(fps, axis=1).astype(dtype=np.float)
                for t, (tp, fp) in enumerate(zip(tp_sum, fp_sum)):
                    tp = np.array(tp)
                    fp = np.array(fp)
                    nd = len(tp)
                    rc = tp / npig
                    pr = tp / (fp+tp+np.spacing(1))
                    q  = np.zeros((R,))
                    ss = np.zeros((R,))

                    if nd:
                        recall[t,k,a,m] = rc[-1]
                    else:
                        recall[t,k,a,m] = 0

                    # numpy is slow without cython optimization for accessing elements
                    # use python array gets significant speed improvement
                    pr = pr.tolist(); q = q.tolist()

                    for i in range(nd-1, 0, -1):
                        if pr[i] > pr[i-1]:
                            pr[i-1] = pr[i]

                    inds = np.searchsorted(rc, p.recThrs, side='left')
                    try:
                        for ri, pi in enumerate(inds):
                            q[ri] = pr[pi]
                            ss[ri] = dtScoresSorted[pi]
                    except:
                        pass
                    precision[t,:,k,a,m] = np.array(q)
                    scores[t,:,k,a,m] = np.array(ss)
    coco_eval.eval = {
        'params': p,
        'counts': [T, R, K, A, M],
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'precision': precision,
        'recall':   recall,
        'scores': scores,
    }
    toc = time.time()
    print('DONE (t={:0.2f}s).'.format( toc-tic))


def summary_kp(coco_eval, p = None, cat = -1):
    '''
    Accumulate per image evaluation results and store the result in self.eval
    :param p: input params for evaluation
    :return: None
    '''
    print('Accumulating evaluation results...')
    tic = time.time()
    if not coco_eval.evalImgs:
        print('Please run evaluate() first')
    # allows input customized parameters
    if p is None:
        p = coco_eval.params
    p.catIds = p.catIds if p.useCats == 1 else [-1]
    T           = len(p.iouThrs)
    R           = len(p.recThrs)
    K           = len(p.catIds) if p.useCats else 1
    A           = len(p.areaRng)
    M           = len(p.maxDets)
    kp_accuracy      = -np.ones((T,K,A,M))

    # create dictionary for future indexing
    _pe = coco_eval._paramsEval
    catIds = _pe.catIds if _pe.useCats else [-1]
    setK = set(catIds)
    setA = set(map(tuple, _pe.areaRng))
    setM = set(_pe.maxDets)
    setI = set(_pe.imgIds)
    # get inds to evaluate
    k_list = [n for n, k in enumerate(p.catIds)  if k in setK]
    m_list = [m for n, m in enumerate(p.maxDets) if m in setM]
    a_list = [n for n, a in enumerate(map(lambda x: tuple(x), p.areaRng)) if a in setA]
    i_list = [n for n, i in enumerate(p.imgIds)  if i in setI]
    I0 = len(_pe.imgIds)
    A0 = len(_pe.areaRng)
    # retrieve E at each category, area range, and max number of detections
    for k, k0 in enumerate(k_list):
        Nk = k0*A0*I0
        for a, a0 in enumerate(a_list):
            Na = a0*I0
            for m, maxDet in enumerate(m_list):
                E = [coco_eval.evalImgs[Nk + Na + i] for i in i_list]
                E = [e for e in E if not e is None]
                E = [e for e in E if np.sum(e['dtm_kp_error']) != e['dtm_kp_error'].shape[0]*e['dtm_kp_error'].shape[1]*-1]
                if len(E) == 0:
                    continue

                for t in range(len(p.iouThrs)):
                    cnt = 0
                    mean_kp_error = 0
                    for e in E:
                        for obj_idx in range(e['dtm_kp_error'].shape[1]):
                            if e['dtm_kp_error'][t, obj_idx] != -1:
                                mean_kp_error = mean_kp_error + e['dtm_kp_error'][t, obj_idx]
                                cnt = cnt + 1
                    if cnt != 0:
                        mean_kp_error = mean_kp_error / cnt
                    kp_accuracy[t, k, a, m] = mean_kp_error


    if cat == -1:
        coco_eval.eval['kp_accuracy'] = kp_accuracy
    else:
        coco_eval.eval['kp_accuracy'] = deepcopy(kp_accuracy[:, cat, :, :])
        coco_eval.eval['kp_accuracy'] = coco_eval.eval['kp_accuracy'].reshape(kp_accuracy.shape[0],
                                                     1,
                                                     kp_accuracy.shape[2],
                                                     kp_accuracy.shape[3])

        kp_accuracy = deepcopy(kp_accuracy[:, cat, :, :])
        kp_accuracy = kp_accuracy.reshape(kp_accuracy.shape[0], 1, kp_accuracy.shape[1], kp_accuracy.shape[2])

    acc_0 = 0
    cnt_0 = 0
    for idx_1 in range(kp_accuracy.shape[1]):
        for idx_2 in range(kp_accuracy.shape[2]):
            for idx_3 in range(kp_accuracy.shape[3]):
                for idx_0 in range(kp_accuracy.shape[0]):
                    acc_0 = acc_0 + kp_accuracy[idx_0, idx_1, idx_2, idx_3]
                    cnt_0 = cnt_0 + 1
    acc_0 = acc_0 / cnt_0

    acc_1 = 0
    cnt_1 = 0
    for idx_1 in range(kp_accuracy.shape[1]):
        for idx_2 in range(kp_accuracy.shape[2]):
            for idx_3 in range(kp_accuracy.shape[3]):
                acc_1 = acc_1 + kp_accuracy[0, idx_1, idx_2, idx_3]
                cnt_1 = cnt_1 + 1
    acc_1 = acc_1 / cnt_1

    acc_2 = 0
    cnt_2 = 0
    for idx_1 in range(kp_accuracy.shape[1]):
        for idx_2 in range(kp_accuracy.shape[2]):
            for idx_3 in range(kp_accuracy.shape[3]):
                acc_2 = acc_2 + kp_accuracy[7, idx_1, idx_2, idx_3]
                cnt_2 = cnt_2 + 1
    acc_2 = acc_2 / cnt_2

    print('Total Length Normalized Accuracy @[ IoU=0.50:0.95\t| area=\tall] = {0}'.format(acc_0))
    print('Total Length Normalized Accuracy @[ IoU=0.50\t| area=\tall] = {0}'.format(acc_1))
    print('Total Length Normalized Accuracy @[ IoU=0.75\t| area=\tall] = {0}'.format(acc_2))

    toc = time.time()
    print('DONE (t={:0.2f}s).'.format( toc-tic))


def aspectaware_resize_padding(image, width, height, interpolation=None, means=None):
    old_h, old_w, c = image.shape
    if old_w > old_h:
        new_w = width
        new_h = int(width / old_w * old_h)
    else:
        new_w = int(height / old_h * old_w)
        new_h = height

    canvas = np.zeros((height, height, c), np.float32)
    if means is not None:
        canvas[...] = means

    if new_w != old_w or new_h != old_h:
        if interpolation is None:
            image = cv2.resize(image, (new_w, new_h))
        else:
            image = cv2.resize(image, (new_w, new_h), interpolation=interpolation)

    padding_h = height - new_h
    padding_w = width - new_w

    if c > 1:
        canvas[:new_h, :new_w] = image
    else:
        if len(image.shape) == 2:
            canvas[:new_h, :new_w, 0] = image
        else:
            canvas[:new_h, :new_w] = image

    return canvas, new_w, new_h, old_w, old_h, padding_w, padding_h,



def preprocess_video(*frame_from_video, max_size=512, mean=(0.406, 0.456, 0.485), std=(0.225, 0.224, 0.229)):
    ori_imgs = frame_from_video

    normalized_imgs = [(img / 255 - mean) / std for img in ori_imgs]

    imgs_meta = [aspectaware_resize_padding(img, max_size, max_size,
                                            means=None, interpolation=cv2.INTER_LINEAR) for img in normalized_imgs]
    framed_imgs = [img_meta[0] for img_meta in imgs_meta]
    framed_metas = [img_meta[1:] for img_meta in imgs_meta]

    return ori_imgs, framed_imgs, framed_metas


# function for display
def display(preds, imgs, obj_list):
    for i in range(len(imgs)):
        if len(preds[i]['rois']) == 0:
            return imgs[i]

        for j in range(len(preds[i]['rois'])):
            if float(preds[i]['scores'][j]) > 0.2:
                (x1, y1, x2, y2) = preds[i]['rois'][j].astype(np.int)
                cv2.rectangle(imgs[i], (x1, y1), (x2, y2), (255, 255, 0), 2)
                obj = obj_list[preds[i]['class_ids'][j]]
                score = float(preds[i]['scores'][j])

                cv2.putText(imgs[i], '{}, {:.3f}'.format(obj, score),
                            (x1, y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (255, 255, 0), 2)

                if 'ids' in preds[i].keys():
                    id = float(preds[i]['ids'][j])
                    cv2.putText(imgs[i], 'id: {}'.format((int)(id)),
                                (x1, y2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                                (0, 0, 255), 3)
        return imgs[i]

def invert_affine(metas: Union[float, list, tuple], preds):
    for i in range(len(preds)):
        if len(preds[i]['rois']) == 0:
            continue
        else:
            if metas is float:
                preds[i]['rois'][:, [0, 2]] = preds[i]['rois'][:, [0, 2]] / metas
                preds[i]['rois'][:, [1, 3]] = preds[i]['rois'][:, [1, 3]] / metas
            else:
                new_w, new_h, old_w, old_h, padding_w, padding_h = metas[i]
                preds[i]['rois'][:, [0, 2]] = preds[i]['rois'][:, [0, 2]] / (new_w / old_w)
                preds[i]['rois'][:, [1, 3]] = preds[i]['rois'][:, [1, 3]] / (new_h / old_h)
    return preds

def evaluation(opt):
    params = Params(f'projects/{opt.project}.yml')

    SET_NAME = params.test_set
    TEST_GT = opt.data_path + '/' + opt.project + '/' + SET_NAME + '/' + 'test.json'

    TEST_IMGS = opt.data_path + '/' + opt.project + '/' + SET_NAME + '/'

    #MAX_IMAGES = 10000
    coco_gt = COCO(TEST_GT)
    image_ids = coco_gt.getImgIds()
    print(TEST_GT)
    len(image_ids)

    obj_list = params.obj_list

    if not os.path.exists(f'{SET_NAME}_bbox_results.json'):
        model = EfficientDetBackbone(compound_coef=opt.compound_coef, num_classes=len(params.obj_list),
                                     ratios=eval(params.anchors_ratios), scales=eval(params.anchors_scales))
        model.load_state_dict(torch.load(opt.weights, map_location=torch.device('cuda:0')))
        model.requires_grad_(False)
        model.eval()

        if params.num_gpus > 0:
            model = model.cuda()

        evaluate_coco(TEST_IMGS, SET_NAME, image_ids, coco_gt, model, obj_list = obj_list)

    _eval(coco_gt, image_ids, f'{SET_NAME}_bbox_results.json')

import easydict
opt = easydict.EasyDict({
    "compound_coef": 2, #EfficientNet 의 compound coefficient
    "project": "fish_77", #Project 이름 설정. ./projects 파일 내의 {project}.yml 파일과 연관
    "weights": f'trained_weight/20210221_efficientdet-d2_14_97700.pth', #학습 완료된 weight
    "data_path": "E:/Research/Databases/object/fish",  #evaluation을 할 데이터가 위치한 폴더 위치
    "nms_threshold": 0.2, #evaluation을 할 때의 threshold
    "cuda": True, #cuda 사용 유무
    "device": 0 #device index
})

if __name__ == '__main__':
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' [UCT+09:00]' + ' Start the evaluation script')

    nms_threshold = opt.nms_threshold

    evaluation(opt)






