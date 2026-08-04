import os

os.environ['KMP_DUPLICATE_LIB_OK']='True'

import torch
import yaml

from efficientdet.backbone import EfficientDetBackbone
from utils.utils import get_last_weights, init_weights
from utils.utils import preprocess_video
from efficientdet.utils import BBoxTransform, ClipBoxes
from typing import Union
from utils.utils import postprocess_with_KP, invert_affine, display_with_kp
from copy import deepcopy

import cv2
from sort import *

class Params:
    def __init__(self, project_file):
        self.params = yaml.safe_load(open(project_file).read())

    def __getattr__(self, item):
        return self.params.get(item, None)

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

def test_video(opt):

    video_src = opt.target_video_path

    params = Params(f'projects/{opt.project}.yml')
    print('Loading training related parameter...on projects/{0}.yml done.'.format(opt.project))
    if params.num_gpus == 0:
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

    obj_list = ['OliveFlounder', 'KoreaRockfish', 'RedSeabream', 'BlackPorgy', 'RockBream']

    use_cuda = True
    use_float16 = False

    threshold = 0.2
    iou_threshold = 0.2

    if torch.cuda.is_available():
        torch.cuda.manual_seed(42)
        print('CUDA is available.')
    else:
        torch.manual_seed(42)

    print('Initializing Dataset...done.')

    model = EfficientDetBackbone(num_classes=len(params.obj_list), compound_coef=opt.compound_coef,
                                 ratios=eval(params.anchors_ratios), scales=eval(params.anchors_scales))

    # load last weights
    if opt.load_weights is not None:
        if opt.load_weights.endswith('.pth'):
            weights_path = opt.load_weights
        else:
            weights_path = get_last_weights(opt.saved_path)

        try:
            ret = model.load_state_dict(torch.load(weights_path), strict=False)
        except RuntimeError as e:
            print(f'[Warning] Ignoring {e}')
            print(
                '[Warning] Don\'t panic if you see this, this might be because you load a pretrained weights with different number of classes. The rest of the weights should be loaded already.')
    else:
        print('[Info] initializing weights...')
        init_weights(model)

    if params.num_gpus > 0:
        model = model.cuda()

    print('Initializing Pretraining Weight...done.')
    model.requires_grad_(False)

    if use_cuda:
        model = model.cuda()
    if use_float16:
        model = model.half()

    cap = cv2.VideoCapture(video_src)

    force_input_size = None  # set None to use default size

    input_sizes = [512, 640, 768, 896, 1024, 1280, 1280, 1536]
    input_size = input_sizes[opt.compound_coef] if force_input_size is None else force_input_size

    # Box
    regressBoxes = BBoxTransform()
    clipBoxes = ClipBoxes()

    frame_num = 0
    model.eval()

    # create instance of SORT
    mot_tracker = Sort()

    while True:
        ret, frame = cap.read()

        if not ret:
            print('video parse error')
            break

        start = time.time()

        frame_num = frame_num + 1
        print('frame num : {0}'.format(frame_num))
        # frame preprocessing
        ori_imgs, framed_imgs, framed_metas = preprocess_video(frame, max_size=input_size, mean = params.mean, std=params.std)

        if use_cuda:
            x = torch.stack([torch.from_numpy(fi).cuda() for fi in framed_imgs], 0)
        else:
            x = torch.stack([torch.from_numpy(fi) for fi in framed_imgs], 0)

        x = x.to(torch.float32 if not use_float16 else torch.float16).permute(0, 3, 1, 2)

        # model predict
        with torch.no_grad():
            _, regression, classification, anchors, regression_kp = model(x)

            out = postprocess_with_KP(x,
                            anchors, regression, regression_kp, classification,
                            regressBoxes, clipBoxes,
                            threshold, iou_threshold)

        # result
        out = invert_affine(framed_metas, out)

        score_thres = 0.85
        out = filtering_overlap(out, score_thres)
        # IoU가 85% 이상이면 score가 낮은거는 지운다
        ######

        #######################################
        out_tracking = []

        for img_idx in range(len(ori_imgs)):
            # # tracking...
            detect_res = np.empty((out[img_idx]['rois'].shape[0], 5))
            for i in range(out[img_idx]['rois'].shape[0]):
                detect_res[i, 0] = out[img_idx]['rois'][i][0]
                detect_res[i, 1] = out[img_idx]['rois'][i][1]
                detect_res[i, 2] = out[img_idx]['rois'][i][2]
                detect_res[i, 3] = out[img_idx]['rois'][i][3]
                detect_res[i, 4] = out[img_idx]['scores'][i]

            track_bbs_ids = mot_tracker.update(detect_res)

            ######
            iouMap = []
            for i in range(track_bbs_ids.shape[0]):
                iouMax = 0
                idx = -1
                for j in range(detect_res.shape[0]):
                    x1 = max(track_bbs_ids[i][0], detect_res[j][0])
                    y1 = max(track_bbs_ids[i][1], detect_res[j][1])
                    x2 = min(track_bbs_ids[i][2], detect_res[j][2])
                    y2 = min(track_bbs_ids[i][3], detect_res[j][3])

                    if x2 - x1 > 0 and y2 - y1:
                        overlapArea = (x2 - x1) * (y2 - y1)
                        areaTracking = (track_bbs_ids[i][2] - track_bbs_ids[i][0]) * (
                                    track_bbs_ids[i][3] - track_bbs_ids[i][1])
                        areaDetection = (detect_res[j][2] - detect_res[j][0]) * (detect_res[j][3] - detect_res[j][1])
                        iou = (overlapArea) / (areaTracking + areaDetection - overlapArea)
                        if iou > iouMax:
                            iouMax = iou
                            idx = j

                iouMap.append([i, idx])

            ######
            out_tracking.append({
                'rois': np.empty((track_bbs_ids.shape[0], 4)),
                'class_ids': np.empty((track_bbs_ids.shape[0]), dtype=np.int64),
                'scores': np.empty((track_bbs_ids.shape[0])),
                'kps': np.empty((track_bbs_ids.shape[0], 8)),
                'ids': np.empty((track_bbs_ids.shape[0]), dtype=np.int64)
            })

            for i in range(track_bbs_ids.shape[0]):
                out_tracking[0]['rois'][i][0] = track_bbs_ids[i, 0]
                out_tracking[0]['rois'][i][1] = track_bbs_ids[i, 1]
                out_tracking[0]['rois'][i][2] = track_bbs_ids[i, 2]
                out_tracking[0]['rois'][i][3] = track_bbs_ids[i, 3]
                out_tracking[0]['ids'][i] = (int)(track_bbs_ids[i, 4])

                out_tracking[0]['class_ids'][i] = (int)(out[img_idx]['class_ids'][iouMap[i][1]])
                out_tracking[0]['scores'][i] = out[img_idx]['scores'][iouMap[i][1]]
                out_tracking[0]['kps'][i] = out[img_idx]['kps'][iouMap[i][1]]

        print("time :", time.time() - start)  # 현재시각 - 시작시간 = 실행 시간

        display_with_kp(out_tracking, ori_imgs, obj_list)

        # show frame by frame
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def filtering_overlap(out, score_thres):
    deletex_bbx_idx = []
    iouMap_detect = []
    for i in range(out[0]['rois'].shape[0]):
        iouMax = 0
        idx = -1
        for j in range(out[0]['rois'].shape[0]):
            if i == j:
                continue
            x1 = max(out[0]['rois'][i][0], out[0]['rois'][j][0])
            y1 = max(out[0]['rois'][i][1], out[0]['rois'][j][1])
            x2 = min(out[0]['rois'][i][2], out[0]['rois'][j][2])
            y2 = min(out[0]['rois'][i][3], out[0]['rois'][j][3])

            if x2 - x1 > 0 and y2 - y1:
                overlapArea = (x2 - x1) * (y2 - y1)
                areaTracking = (out[0]['rois'][i][2] - out[0]['rois'][i][0]) * (
                        out[0]['rois'][i][3] - out[0]['rois'][i][1])
                areaDetection = (out[0]['rois'][j][2] - out[0]['rois'][j][0]) * (
                            out[0]['rois'][j][3] - out[0]['rois'][j][1])
                iou = (overlapArea) / (areaTracking + areaDetection - overlapArea)
                if iou > iouMax:
                    iouMax = iou
                    idx = j

        iouMap_detect.append([i, idx, iouMax])

    out_filtered = deepcopy(out)
    idx_0 = -1
    idx_1 = -1
    iouMapIdx = 0
    cnt = 0
    # iouMapIdx3 = 0
    # while iouMapIdx3 < len(iouMap_detect):
    #     if iouMap_detect[iouMapIdx3][2] > score_thres:
    #         idx_0 = iouMap_detect[iouMapIdx3][0]
    #         idx_1 = iouMap_detect[iouMapIdx3][1]
    #         # cnt = cnt + 1
    #         # if cnt >= 3:
    #         #     print('3 overlaped')
    #     iouMapIdx3 = iouMapIdx3 + 1

    while iouMapIdx < len(iouMap_detect):
        if iouMap_detect[iouMapIdx][2] > 0.85:
            idx_0 = iouMap_detect[iouMapIdx][0]
            idx_1 = iouMap_detect[iouMapIdx][1]
            iouMap_detect.pop(iouMapIdx)

            score_idx_0 = out_filtered[0]['scores'][idx_0]
            score_idx_1 = out_filtered[0]['scores'][idx_1]

            if score_idx_0 > score_idx_1:
                deletex_bbx_idx.append(idx_1)

                idx_del = idx_1
                idx_keep = idx_0
            else:
                deletex_bbx_idx.append(idx_0)

                idx_del = idx_0
                idx_keep = idx_1

            deletex_bbx_idx.append(idx_del)
            iouMapIdx = iouMapIdx - 1

            iouMapIdx2 = 0
            target_idx_to_del = -1
            while iouMapIdx2 < len(iouMap_detect):
                if (len(iouMap_detect) > iouMapIdx2 and len(iouMap_detect) > 0):  # list에 아무것도 없을 때의 케이스 고려
                    if (iouMap_detect[iouMapIdx2][0] == idx_del and iouMap_detect[iouMapIdx2][1] == idx_keep):
                        iouMap_detect.pop(iouMapIdx2)
                        iouMapIdx2 = iouMapIdx2 - 1

                if(len(iouMap_detect) > iouMapIdx2 and len(iouMap_detect) > 0): #list에 아무것도 없을 때의 케이스 고려
                    if (iouMap_detect[iouMapIdx2][0] == idx_del):
                        if iouMap_detect[iouMapIdx2][2] > score_thres:
                            deletex_bbx_idx.append(iouMap_detect[iouMapIdx2][1])
                            iouMap_detect.pop(iouMapIdx2)
                            iouMapIdx2 = iouMapIdx2 - 1

                if (len(iouMap_detect) > iouMapIdx2 and len(iouMap_detect) > 0):  # list에 아무것도 없을 때의 케이스 고려
                    if (iouMap_detect[iouMapIdx2][1] == idx_del):
                        if iouMap_detect[iouMapIdx2][2] > score_thres:
                            deletex_bbx_idx.append(iouMap_detect[iouMapIdx2][0])
                            iouMap_detect.pop(iouMapIdx2)
                            iouMapIdx2 = iouMapIdx2 - 1

                iouMapIdx2 = iouMapIdx2 + 1

        iouMapIdx = iouMapIdx + 1

    for i in range(len(deletex_bbx_idx)):
        target_idx_to_del = deletex_bbx_idx[i]
        out_filtered_idx = 0
        while out_filtered_idx < out_filtered[0]['scores'].shape[0]:
            if out_filtered[0]['rois'][out_filtered_idx][0] == out[0]['rois'][target_idx_to_del][0] and \
                    out_filtered[0]['rois'][out_filtered_idx][1] == out[0]['rois'][target_idx_to_del][1] and \
                    out_filtered[0]['rois'][out_filtered_idx][2] == out[0]['rois'][target_idx_to_del][2] and \
                    out_filtered[0]['rois'][out_filtered_idx][3] == out[0]['rois'][target_idx_to_del][3]:
                out_filtered[0]['scores'] = np.delete(out_filtered[0]['scores'], (out_filtered_idx), axis=0)
                out_filtered[0]['rois'] = np.delete(out_filtered[0]['rois'], (out_filtered_idx), axis=0)
                out_filtered[0]['kps'] = np.delete(out_filtered[0]['kps'], (out_filtered_idx), axis=0)
                out_filtered[0]['class_ids'] = np.delete(out_filtered[0]['class_ids'], (out_filtered_idx), axis=0)
                out_filtered_idx = out_filtered_idx - 1
            out_filtered_idx = out_filtered_idx + 1

    out = deepcopy(out_filtered)
    return out


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


import easydict

#'test_video/swim_of_2021-01-07-09-20_00-00.MP4'
#'test_video/swim_rs_2021-01-07-09-45_00-00.MP4'
#'test_video/swim_rs_2021-01-07-10-40_00-00.MP4'
#'test_video/swim_kr_2020-12-18-10-04_00-00.MP4'
# "load_weights": "trained_weight/20210109_efficientdet-d2_299_66300.pth",

opt = easydict.EasyDict({
    "target_video_path": 'test_video/test.mp4', #Target Video Path
    "compound_coef": 2,  #EfficientNet 의 compound coefficient
    "project": "fish_77",  #Project 이름 설정. ./projects 파일 내의 {project}.yml 파일과 연관
    "load_weights": "trained_weight/20210222_efficientdet-d2_29_203900.pth", #학습 완료된 weight
})

if __name__ == '__main__':
    print(opt.project)
    print('Start the test script')
    test_video(opt)










