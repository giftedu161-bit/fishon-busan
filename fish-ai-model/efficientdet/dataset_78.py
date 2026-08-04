import os
import torch
import numpy as np

from torch.utils.data import Dataset, DataLoader
from pycocotools.coco import COCO
import cv2
import random

class CocoDataset_Custom_Fish_78(Dataset):
    def __init__(self, root_dir, set='train2017', coco_file_name=None, transform=None):

        self.root_dir = root_dir
        self.set_name = set
        self.transform = transform

        coco_path = os.path.join(self.root_dir, set, coco_file_name)

        self.coco = COCO(coco_path)
        self.image_ids = self.coco.getImgIds()

        self.load_classes()

        growth_days = np.zeros(1000, dtype=np.int32)

        growth_days_0 = np.zeros(1000, dtype=np.int32)
        growth_days_1 = np.zeros(1000, dtype=np.int32)
        growth_days_2 = np.zeros(1000, dtype=np.int32)
        growth_days_3 = np.zeros(1000, dtype=np.int32)
        growth_days_4 = np.zeros(1000, dtype=np.int32)

        for i in range(len(self.coco.anns)):
            annot = self.load_annotations(i)
            labels = int(annot[0, 6])
            class_idx = int(annot[0, 4])

            growth_days[labels] = growth_days[labels] + 1

            if class_idx == 0:
                growth_days_0[labels] = growth_days[labels] + 1
            elif class_idx == 1:
                growth_days_1[labels] = growth_days[labels] + 1
            elif class_idx == 2:
                growth_days_2[labels] = growth_days[labels] + 1
            elif class_idx == 3:
                growth_days_3[labels] = growth_days[labels] + 1
            elif class_idx == 4:
                growth_days_4[labels] = growth_days[labels] + 1

        f = open("growth_days.txt", "w")

        for i in range(len(growth_days)):
            f.write("{0} {1}\n".format(i, growth_days[i]))
        f.close()

        f = open("growth_days_0.txt", "w")
        for i in range(len(growth_days_0)):
            f.write("{0} {1}\n".format(i, growth_days_0[i]))
        f.close()

        f = open("growth_days_1.txt", "w")
        for i in range(len(growth_days_1)):
            f.write("{0} {1}\n".format(i, growth_days_1[i]))
        f.close()

        f = open("growth_days_2.txt", "w")
        for i in range(len(growth_days_2)):
            f.write("{0} {1}\n".format(i, growth_days_2[i]))
        f.close()

        f = open("growth_days_3.txt", "w")
        for i in range(len(growth_days_3)):
            f.write("{0} {1}\n".format(i, growth_days_3[i]))
        f.close()

        f = open("growth_days_4.txt", "w")
        for i in range(len(growth_days_4)):
            f.write("{0} {1}\n".format(i, growth_days_4[i]))
        f.close()
        #print('[Growth Level Stat]\n1st : {0}, 2nd : {1}, 3rd : {2}'.format(annot_stat[0], annot_stat[1], annot_stat[2]))

        # #Debug
        # for i in range(10):
        #     idx = i
        #     img = self.load_image(idx)
        #     annot = self.load_annotations(idx)
        #
        #     for j in range(annot.shape[0]):
        #         x0 = int(annot[j, 0] + 0.5)
        #         y0 = int(annot[j, 1] + 0.5)
        #         x1 = int(annot[j, 2] + 0.5)
        #         y1 = int(annot[j, 3] + 0.5)
        #         cv2.rectangle(img, (x0, y0), (x1, y1), (0, 0, 255), 3)
        #
        #         x0_0 = int(annot[j, 5] * (x1 - x0) + x0 + 0.5)
        #         y0_0 = int(annot[j, 6] * (y1 - y0) + y0 + 0.5)
        #         x1_0 = int(annot[j, 7] * (x1 - x0) + x0 + 0.5)
        #         y1_0 = int(annot[j, 8] * (y1 - y0) + y0 + 0.5)
        #
        #         x0_1 = int(annot[j, 9] * (x1 - x0) + x0 + 0.5)
        #         y0_1 = int(annot[j, 10] * (y1 - y0) + y0 + 0.5)
        #         x1_1 = int(annot[j, 11] * (x1 - x0) + x0 + 0.5)
        #         y1_1 = int(annot[j, 12] * (y1 - y0) + y0 + 0.5)
        #
        #         cv2.line(img, (x0_0, y0_0), (x1_0, y1_0), (255, 0, 255), 3)
        #         cv2.line(img, (x0_1, y0_1), (x1_1, y1_1), (255, 255, 0), 3)
        #
        #     img = cv2.resize(img, dsize=(int(img.shape[1] / 2 + 0.5), int(img.shape[0] / 2+ 0.5)), interpolation=cv2.INTER_AREA)
        #
        #     cv2.imshow('test', img)
        #     cv2.waitKey(0)

    def load_classes(self):

        # load class names (name -> label)
        categories = self.coco.loadCats(self.coco.getCatIds())
        categories.sort(key=lambda x: x['id'])

        self.classes = {}
        for c in categories:
            self.classes[c['name']] = len(self.classes)

        # also load the reverse (label -> name)
        self.labels = {}
        for key, value in self.classes.items():
            self.labels[value] = key

    def __len__(self):
        return len(self.image_ids)

    def __getitem__(self, idx):

        img = self.load_image(idx)
        annot = self.load_annotations(idx)

        try:
            x0 = int(annot[0, 0])
        except Exception as e:
            print('error')
            print('idx is {0}'.format(idx))
            image_info = self.coco.loadImgs(self.image_ids[idx])[0]
            file_name = image_info['file_name']
            print('file name is ' + file_name)

        x1 = int(annot[0, 2])

        y0 = int(annot[0, 1])
        y1 = int(annot[0, 3])

        ratio = 0.2
        dx = int(((x1 - x0 + 1) * ratio) * 0.5 + 0.5)
        dy = int(((y1 - y0 + 1) * ratio) * 0.5 + 0.5)

        x0 = x0 - dx
        x1 = x1 + dx

        y0 = y0 - dy
        y1 = y1 + dy

        if x0 < 0:
            x0 = 0
        if x1 >= img.shape[1]:
            x1 = img.shape[1] - 1
        if y0 < 0:
            y0 = 0
        if y1 >= img.shape[0]:
            y1 = img.shape[0] - 1

        img = np.copy(img[y0:y1, x0:x1, :])

        # labels = np.empty((1), dtype=int)
        # labels[0] = int(annot[0, 4]) #class
        # labels[1] = int(annot[0, 5]) #maturity

        labels = int(annot[0, 4])

        sample = {'img': img, 'annot': labels}
        if self.transform:
            sample = self.transform(sample)
        return sample

    def load_image(self, image_index):
        image_info = self.coco.loadImgs(int(self.image_ids[image_index]))[0]

        file_name = image_info['file_name']
        #print(file_name)
        if file_name[:6] == './objt':
            file_name = 'images/' + file_name[2:]
        file_name = 'images/' + file_name[2:]
        path = os.path.join(self.root_dir, self.set_name, file_name)
        img = cv2.imread(path)
        if img is None:
            print('empty')
            print(path)

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        #return img.astype(np.float32) / 255.
        return img

    def load_annotations(self, image_index):
        # get ground truth annotations
        annotations_ids = self.coco.getAnnIds(imgIds=self.image_ids[image_index], iscrowd=False)
        annotations = np.zeros((0, 7))

        # some images appear to miss annotations
        if len(annotations_ids) == 0:
            return annotations

        # parse annotations
        coco_annotations = self.coco.loadAnns(annotations_ids)
        for idx, a in enumerate(coco_annotations):

            # some annotations have basically no width / height, skip them
            if a['bbox'][2] < 1 or a['bbox'][3] < 1:
                continue

            annotation = np.zeros((1, 7))
            if len(a['bbox']) != 4:
                print(a['bbox'])
            annotation[0, :4] = a['bbox']
            annotation[0, 4] = a['category_id'] - 1
            diseases_exist = a['diseases_exist']
            if diseases_exist == True:
                annotation[0, 5] = 1
            else:
                annotation[0, 5] = 0

            gd = a['gd']
            annotation[0, 6] = gd
            # bd = a['bd']
            # sl = a['sl']
            #
            # if a['category_id'] == 1:
            #     if sl < 10:
            #         annotation[0, 5] = 0
            #     elif sl < 30:
            #         annotation[0, 5] = 1
            #     else:
            #         annotation[0, 5] = 2
            # elif a['category_id'] == 2:
            #     if sl < 10:
            #         annotation[0, 5] = 0
            #     elif sl < 25:
            #         annotation[0, 5] = 1
            #     else:
            #         annotation[0, 5] = 2
            # elif a['category_id'] == 3:
            #     if sl < 10:
            #         annotation[0, 5] = 0
            #     elif sl < 25:
            #         annotation[0, 5] = 1
            #     else:
            #         annotation[0, 5] = 2
            # elif a['category_id'] == 4:
            #     if sl < 10:
            #         annotation[0, 5] = 0
            #     elif sl < 25:
            #         annotation[0, 5] = 1
            #     else:
            #         annotation[0, 5] = 2
            # elif a['category_id'] == 5:
            #     if sl < 10:
            #         annotation[0, 5] = 0
            #     elif sl < 25:
            #         annotation[0, 5] = 1
            #     else:
            #         annotation[0, 5] = 2

            annotations = np.append(annotations, annotation, axis=0)

        # transform from [x, y, w, h] to [x1, y1, x2, y2]
        annotations[:, 2] = annotations[:, 0] + annotations[:, 2]
        annotations[:, 3] = annotations[:, 1] + annotations[:, 3]

        return annotations


def collater(data):
    imgs = [s['img'] for s in data]
    annots = [s['annot'] for s in data]

    imgs = torch.from_numpy(np.stack(imgs, axis=0))
    annots = torch.as_tensor(annots)

    # max_num_annots = max(annot.shape[0] for annot in annots)
    #
    # if max_num_annots > 0:
    #
    #     annot_padded = torch.ones((len(annots), max_num_annots, 13)) * -1
    #
    #     for idx, annot in enumerate(annots):
    #         if annot.shape[0] > 0:
    #             annot_padded[idx, :annot.shape[0], :] = annot
    # else:
    #     annot_padded = torch.ones((len(annots), 1, 13)) * -1

    imgs = imgs.permute(0, 3, 1, 2)

    return {'img': imgs, 'annot': annots}


class Resizer(object):
    """Convert ndarrays in sample to Tensors."""
    
    def __init__(self, img_size=512):
        self.img_size = img_size

    def __call__(self, sample):
        image, annots = sample['img'], sample['annot']
        height, width, _ = image.shape
        if height > width:
            scale = self.img_size / height
            resized_height = self.img_size
            resized_width = int(width * scale)
        else:
            scale = self.img_size / width
            resized_height = int(height * scale)
            resized_width = self.img_size

        image = cv2.resize(image, (resized_width, resized_height), interpolation=cv2.INTER_LINEAR)

        new_image = np.zeros((self.img_size, self.img_size, 3))
        new_image[0:resized_height, 0:resized_width] = image

        if type(annots) is int:
            annots_np = np.array([annots])
            annots_ret = torch.from_numpy(annots_np)
            annots_ret = annots
        else:
            annots_ret = torch.from_numpy(annots)

        return {'img': torch.from_numpy(new_image).to(torch.float32), 'annot': annots_ret}


class RandomFlipX(object):
    """Convert ndarrays in sample to Tensors."""

    def __call__(self, sample, flip_x=0.5):
        if np.random.rand() < flip_x:
            image, annots = sample['img'], sample['annot']
            image = image[:, ::-1, :]

            sample = {'img': image, 'annot': annots}

        return sample

class GaussianBlur(object):

    def __init__(self, kernel_size=9):
        self.kernel_size = kernel_size

    def __call__(self, sample):
        image, annots = sample['img'], sample['annot']

        kernel_size = random.randrange(self.kernel_size)
        if kernel_size % 2 ==0:
            kernel_size = kernel_size + 1
        image = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0.5)

        return {'img': image, 'annot': annots}


class RandomHSV(object):

    def __init__(self, d_h=5, d_s=10, d_v=10):
        self.d_h = d_h
        self.d_s = d_s
        self.d_v = d_v

    def __call__(self, sample):
        image, annots = sample['img'], sample['annot']

        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        #h, s, v = cv2.split(hsv)

        h_p = random.randrange(0, 100)
        if h_p < 20:
            d_h = random.randrange(-self.d_h, self.d_h)
            hsv[:, :, 0] = hsv[:, :, 0] + d_h
            hsv[:, :, 0] = np.clip(hsv[:, :, 0], 0, 180)

        h_s = random.randrange(0, 100)
        if h_s < 20:
            d_s = random.randrange(-self.d_s, self.d_s)
            hsv[:, :, 1] = hsv[:, :, 1] + d_s
            hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)

        h_v = random.randrange(0, 100)
        if h_v < 20:
            d_h = random.randrange(-self.d_v, self.d_v)
            hsv[:, :, 2] = hsv[:, :, 2] + d_h
            hsv[:, :, 2] = np.clip(hsv[:, :, 2], 0, 255)

        #final_hsv = cv2.merge((h, s, v))
        image = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

        return {'img': image, 'annot': annots}


class RandomNoise(object):

    def __init__(self, weight = 50):
        self.weight = weight
    def __call__(self, sample):
        image, annots = sample['img'], sample['annot']
        h, w, c = image.shape
        noise = np.random.randint(0, 50, (h, w))  # design jitter/noise here
        zitter = np.zeros_like(image)
        zitter[:, :, 1] = noise

        image = cv2.add(image, zitter)

        return {'img': image, 'annot': annots}



class Normalizer(object):

    def __init__(self, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]):
        self.mean = np.array([[mean]])
        self.std = np.array([[std]])

    def __call__(self, sample):
        image, annots = sample['img'], sample['annot']

        return {'img': ((image.astype(np.float32)/255. - self.mean) / self.std), 'annot': annots}
