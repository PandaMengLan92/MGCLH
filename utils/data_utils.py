import os
import torch
import itertools
import numpy as np
from PIL import Image
from torch.utils.data import Dataset
import torchvision.transforms as transforms
from torch.utils.data.sampler import Sampler


NO_LABEL = -1

class DataSetWarpper(Dataset):
    """Enable dataset to output index of sample
    """
    def __init__(self, dataset, num_classes):
        self.dataset = dataset
        self.num_classes = num_classes

    def __getitem__(self, index):
        sample, label = self.dataset[index]
        return sample, label, index

    def __len__(self):
        return len(self.dataset)

class TransformTwice:

    def __init__(self, transform):
        self.transform = transform

    def __call__(self, inp):
        out1 = self.transform(inp)
        out2 = self.transform(inp)
        return out1, out2

class TransformWeakStrong:

    def __init__(self, trans1, trans2):
        self.transform1 = trans1
        self.transform2 = trans2

    def __call__(self, inp):
        out1 = self.transform1(inp)
        out2 = self.transform2(inp)
        return out1, out2


class TwoStreamBatchSampler(Sampler):
    """Iterate two sets of indices
    """
    def __init__(self, primary_indices, secondary_indices, batch_size, secondary_batch_size):
        self.primary_indices = primary_indices
        self.primary_batch_size = batch_size - secondary_batch_size
        self.secondary_indices = secondary_indices
        self.secondary_batch_size = secondary_batch_size

        assert len(self.primary_indices) >= self.primary_batch_size > 0
        assert len(self.secondary_indices) >= self.secondary_batch_size > 0

    def __iter__(self):
        primary_iter = iterate_once(self.primary_indices)
        secondary_iter = iterate_eternally(self.secondary_indices)
        return (
            secondary_batch + primary_batch
            for (primary_batch, secondary_batch)
            in zip(grouper(primary_iter, self.primary_batch_size),
                   grouper(secondary_iter, self.secondary_batch_size))
        )

    def __len__(self):
        return len(self.primary_indices) // self.primary_batch_size

def iterate_once(iterable):
    return np.random.permutation(iterable)

def iterate_eternally(indices, is_shuffle=True):
    shuffleFunc = np.random.permutation if is_shuffle else lambda x: x
    def infinite_shuffles():
        while True:
            yield shuffleFunc(indices)
    return itertools.chain.from_iterable(infinite_shuffles())

def grouper(iterable, n):
    args = [iter(iterable)]*n
    return zip(*args)

def encode_onehot(labels, num_classes=10):
    """
    进行编码0/1/2/转换成one_hot 编码
    :param labels: label n*1
    :param num_classes: num_classes 10
    :return: one_hot code n*10
    """
    onehot_labels = torch.zeros([labels.size(0), num_classes], dtype=torch.float)
    for i in range(labels.size(0)):
        onehot_labels[i, labels[i]] = 1
    return onehot_labels

def Similarity_Matrix(labels, num_classes=10):
    """
    根据 label 生成 S 矩阵
    :return: S n*n
    """
    onehot = encode_onehot(labels, num_classes)
    Matrix = onehot @ onehot.t()

    return Matrix

def Pairwise_Matrix(label1,label2, num_classes=10):
    """
    根据 label 生成 S 矩阵
    :return: S n*n
    """
    onehot1 = encode_onehot(label1, num_classes)
    onehot2 = encode_onehot(label2, num_classes)
    Matrix = onehot1 @ onehot2.t()

    return Matrix


