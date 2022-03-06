# -*- coding: utf-8 -*-
"""
Created on Sat Mar  5 14:41:56 2022

@author: hp
"""

import numpy as np
import math

# -*- coding:utf-8 -*-
import numpy as np
from matplotlib import pyplot
from mpl_toolkits.mplot3d import Axes3D
from sklearn.datasets.samples_generator import make_blobs

def gaussian_kernal(s,x,c):
    return np.exp(-c*abs(s-x))

class MeanShift(object):
    def __init__(self, bandwidth=4):
        self.bandwidth_ = bandwidth

    def fit(self, data):
        centers = {}
        # initialement prendre chaque point comme centre
        for i in range(len(data)):
            centers[i] = data[i]
            # print(centers)
        while True:
            new_centers = []
            for i in centers:
                in_bandwidth = []
                #pour chaque centre, prendre un point, si distance < bandwidth, on le met dans in_bandwidth
                center = centers[i]
                x_numerateur = 0
                x_denominateur = 0
                y_numerateur = 0
                y_denominateur = 0
                for feature in data:
                    if np.linalg.norm(feature - center) < self.bandwidth_:
                        in_bandwidth.append(feature)
                        x_numerateur += gaussian_kernal(feature[0],center[0],0.5)*feature[0]
                        x_denominateur += gaussian_kernal(feature[0],center[0],0.5)
                        y_numerateur += gaussian_kernal(feature[1],center[1],0.5)*feature[1]
                        y_denominateur += gaussian_kernal(feature[1],center[1],0.5)

                new_center = [np.round(x_numerateur/x_denominateur,3), np.round(y_numerateur/y_denominateur,3)]
                new_centers.append(tuple(new_center))
            uniques = sorted(list(set(new_centers)))
            prev_centers = dict(centers)
            centers = {}
            for i in range(len(uniques)):
                centers[i] = np.array(uniques[i])
            optimzed = True
            for i in centers:
                if not np.array_equal(centers[i], prev_centers[i]):
                    optimzed = False
                    if not optimzed:
                        break
            if optimzed:
                break

        self.centers_ = centers


if __name__ == '__main__':
    fig = pyplot.figure()
    ax = fig.add_subplot(111)
    centers = [[2, 1], [6, 6], [10, 12],[4,21],[8,17]]
    x, _ = make_blobs(n_samples=69 , centers=centers, cluster_std=1)
    clf = MeanShift()
    clf.fit(x)
    print(clf.centers_)
    for i in clf.centers_:
        ax.scatter(clf.centers_[i][0], clf.centers_[i][1], marker='*', c='k', s=200, zorder=10)

    for i in range(len(x)):
        ax.scatter(x[i][0], x[i][1])

    pyplot.show()