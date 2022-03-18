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

    def number_in_center_area(self, center, data):
        number = 0
        center = np.array(center)
        for feature in data:
            feature = np.array(feature)
            if np.linalg.norm(feature - center) < self.bandwidth_:
                number += 1
        return number

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
        # add the number of points in the area of center
        for index in centers:
            number = self.number_in_center_area(centers[index], data)
            centers[index] = [centers[index], number]
        # sorted centers from the most to the least
        centers_num = sorted(centers.values(), key=lambda tup: tup[1])

        # If the distance between two kernels is less than the bandwidth
        # then we have to remove one because it is a duplicate. Remove the one with fewer points.

        unique = np.ones(len(centers_num), dtype=bool) # to indicate which kernel will be removed
        centers = np.array([np.array(item[0]) for item in centers_num])
        for index, center in enumerate(centers_num):
            if unique[index]:
                # computer kernels(cen) in the area of center i
                for cen in range(len(centers)):
                    if not unique[cen]:
                        pass
                    if np.linalg.norm(centers[cen] - centers[index]) < self.bandwidth_ and cen != index:
                        if center[1] < centers_num[cen][1]:
                            unique[index] = 0
                            break
                        else:
                            unique[cen] = 0
        centers_final = centers[unique]
        self.centers_ = centers_final

        # now we can calculate how many points aren't included
        num_err = 0 # number of points which aren't included
        for feature in data:
            feature = np.array(feature)
            ind = False # to juge if this point will be included: False not included
            for center in self.centers_:
                if np.linalg.norm(center - feature) < self.bandwidth_:
                    ind = True
            if not ind:
                num_err += 1
        self.err_ = num_err

distance_x1 = [
        178, 272, 176, 171, 650, 499, 267, 703, 408, 437, 491, 74, 532, 300, 320, 330, 340,
        700, 710, 720, 705, 680, 690, 670, 650, 666,
        626, 42, 163, 508, 229, 576, 147, 560, 35, 714, 400, 450, 500, 510, 530, 530, 540, 550,
        517, 64, 675, 690, 628, 87, 240, 705, 699, 150, 400, 400, 400, 700, 710, 705, 680,
        614, 36, 482, 666, 597, 209, 201, 492, 294, 100, 150, 5, 10, 15, 20, 25, 30, 40]
distance_y1 = [
        170, 395, 198, 151, 242, 556, 57, 401, 305, 421, 267, 105, 525, 17, 45, 55, 24,
        600, 700, 690, 688, 680, 666, 599, 701, 720,
        244, 330, 141, 380, 153, 442, 528, 329, 232, 48, 10, 30, 50, 450, 480, 510, 600, 499,
        265, 343, 165, 50, 63, 491, 275, 348, 222, 480, 30, 40, 50, 5, 10, 60, 100, 32,
        213, 524, 114, 104, 552, 70, 425, 227, 331, 500, 479, 580, 570, 587, 450, 650, 444]
data1 = list(zip(distance_x1, distance_y1))

distance_x2 = [205, 356, 664, 468, 264, 8, 541, 415, 78, 287, 323, 33, 401, 194, 177, 660, 
               263, 525, 715, 513, 687, 587, 305, 218, 31, 221, 172, 240, 331, 237, 614, 
               333, 22, 722, 179, 628, 81, 517, 296, 593, 329, 390, 372, 460, 528, 773, 409, 
               539, 462, 234, 359, 579, 568, 325]
distance_y2 = [623, 87, 548, 571, 351, 538, 430, 721, 704, 506, 407, 551, 661, 769, 92, 181, 
               155, 651, 714, 92, 351, 380, 63, 731, 153, 396, 710, 628, 170, 775, 685, 677,
               667, 396, 666, 347, 275, 170, 685, 345, 734, 695, 538, 133, 730, 539, 593, 483, 
               230, 689, 638, 709, 212, 746]
data2 = list(zip(distance_x2, distance_y2))

distance_x3 = [333, 200, 742, 121, 314, 126, 98, 530, 338, 425, 205, 478, 718, 587, 37, 676, 
               35, 233, 238, 59, 670, 680, 724, 201, 757, 71, 536, 111, 322, 385, 212, 230,
               241, 179, 389, 291, 318, 481, 390, 704, 545, 530, 798, 744, 14, 252, 209, 595, 
               572, 300, 196, 761, 547, 544, 143, 309, 726, 585, 549, 555, 245, 195, 349, 169, 
               236, 55, 138, 260, 289]
distance_y3 = [547, 271, 135, 570, 183, 417, 366, 675, 176, 626, 365, 249, 239, 479, 585, 33, 
               793, 275, 240, 119, 54, 766, 773, 362, 738, 739, 765, 226, 561, 186, 341, 246, 
               256, 721, 673, 343, 164, 800, 133, 289, 470, 748, 36, 175, 393, 221, 496, 658, 
               420, 799, 392, 545, 0, 575, 611, 387, 60, 205, 73, 785, 462, 704, 46, 37, 745, 
               573, 461, 670, 750]
data3 = list(zip(distance_x3, distance_y3))

distance_x4 = [641, 43, 741, 426, 82, 751, 505, 585, 282, 191, 392, 754, 205, 275, 252, 282, 
               200, 271, 540, 359, 551, 72, 159, 447, 251, 628, 799, 195, 434, 800, 30, 550, 
               316, 761, 458, 140, 95, 175, 144, 50, 776, 194, 545, 405, 773, 453, 696, 426, 
               87, 182, 142, 229, 112, 624, 583, 44, 565, 563, 744, 552, 424, 559, 18, 287, 
               624, 152, 238, 518, 578, 514, 435, 339, 696, 532, 485, 403, 135, 44, 715]
distance_y4 = [382, 667, 764, 133, 46, 669, 103, 442, 279, 662, 709, 392, 606, 519, 721, 564, 
               417, 322, 181, 697, 75, 457, 290, 310, 547, 626, 362, 309, 276, 526, 651, 81, 
               186, 624, 458, 364, 313, 353, 602, 81, 721, 573, 523, 421, 543, 531, 413, 76, 
               714, 383, 465, 97, 158, 510, 260, 270, 516, 330, 744, 511, 547, 720, 798, 205,
               588, 711, 329, 675, 517, 323, 405, 77, 484, 109, 129, 645, 703, 56, 34]
data4 = list(zip(distance_x4, distance_y4))

carte = [data1, data2, data3, data4]

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
    for i in range(len(clf.centers_)):
        ax.scatter(clf.centers_[i][0], clf.centers_[i][1], marker='*', c='k', s=200, zorder=10)
    for i in range(len(data)):
        ax.scatter(data[i][0], data[i][1])
    print(clf.err_)
    plt.show()

