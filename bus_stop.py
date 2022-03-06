# -*- coding:utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt

def kernel(s, x):
    return np.exp(-(np.linalg.norm(s-x, axis=1))/1000)

#calculate new center
def cal_center(in_, center):
    in_ = np.array(in_)
    result = np.sum(kernel(in_, center).reshape(-1,1)*in_, axis=0)/np.sum(kernel(in_, center))
    return result

class MeanShift(object):
    def __init__(self, bandwidth=4):
        #bandwidth represent radius
        self.bandwidth_ = bandwidth

    def fit(self, data):
        data = np.array(data)
        centers = {}
        # regard every point as a center
        for i in range(len(data)):
            centers[i] = np.array(data[i])
            # print(centers)
        while True:
            new_centers = []
            for i in centers:
                in_bandwidth = []
                # put every point near point i in_bandwidth
                center = centers[i]
                for feature in data:
                    feature = np.array(feature)
                    if np.linalg.norm(feature - center) < self.bandwidth_:
                        in_bandwidth.append(feature)

                new_center = cal_center(in_bandwidth, center)
                new_centers.append(tuple(new_center))

            uniques = sorted(list(set(new_centers)))
            prev_centers = dict(centers)
            centers = {}
            for i in range(len(uniques)):
                centers[i] = np.array(uniques[i])

            optimzed = True
            for i in centers:
                if not np.linalg.norm(centers[i] - prev_centers[i]) < np.exp(-15):
                    optimzed = False
                    if not optimzed:
                        break
            if optimzed:
                break

        self.centers_ = centers


if __name__ == '__main__':
    distance_x = [
        178, 272, 176, 171, 650, 499, 267, 703, 408, 437, 491, 74, 532, 300, 320, 330, 340,
        700, 710, 720, 705, 680, 690, 670, 650, 666,
        626, 42, 163, 508, 229, 576, 147, 560, 35, 714, 400, 450, 500, 510, 530, 530, 540, 550,
        517, 64, 675, 690, 628, 87, 240, 705, 699, 150, 400, 400, 400, 700, 710, 705, 680,
        614, 36, 482, 666, 597, 209, 201, 492, 294, 100, 150, 5, 10, 15, 20, 25, 30, 40]
    distance_y = [
        170, 395, 198, 151, 242, 556, 57, 401, 305, 421, 267, 105, 525, 17, 45, 55, 24,
        600, 700, 690, 688, 680, 666, 599, 701, 720,
        244, 330, 141, 380, 153, 442, 528, 329, 232, 48, 10, 30, 50, 450, 480, 510, 600, 499,
        265, 343, 165, 50, 63, 491, 275, 348, 222, 480, 30, 40, 50, 5, 10, 60, 100, 32,
        213, 524, 114, 104, 552, 70, 425, 227, 331, 500, 479, 580, 570, 587, 450, 650, 444]
    data = list(zip(distance_x, distance_y))
    fig = plt.figure()
    ax = fig.add_subplot(111)
    clf = MeanShift(bandwidth=200)
    clf.fit(data)
    print(clf.centers_)
    for i in clf.centers_:
        ax.scatter(clf.centers_[i][0], clf.centers_[i][1], marker='*', c='k', s=200, zorder=10)
    for i in range(len(data)):
        ax.scatter(data[i][0], data[i][1])
    plt.show()

