# -*- coding: utf-8 -*-
"""
Created on Sun Mar  6 15:38:41 2022

@author: hp
"""

import random
import copy
import time
import sys
import math
import tkinter
import threading
from functools import reduce
import numpy as np
from tkinter import *
from tkinter import colorchooser
from tkinter import ttk
from tkinter.messagebox import *
from bus_stop import *


#parametres pour algo colinie fourmie
(ALPHA, BETA, RHO, Q) = (1.0, 2.0, 0.2, 100.0)


        
class Ant(object):

    # 初始化
    def __init__(self, ID, arrets):
        self.ID = ID                 # ID
        self.arrets = arrets
        self.__clean_data()          # random birth place


    def __clean_data(self):

        self.path = []               # trail
        self.total_distance = 0.0    # distance of trail
        self.move_count = 0          # movement times
        self.current_city = -1       # current city
        self.open_table_city = [True for i in range(self.arrets.n)] # state of exploration

        city_index = random.randint(0,self.arrets.n-1) # random birth place
        self.current_city = city_index
        self.path.append(city_index)
        self.open_table_city[city_index] = False
        self.move_count = 1

    # next city
    def __choice_next_city(self):

        next_city = -1
        select_citys_prob = [0.0 for i in range(self.arrets.n)]
        total_prob = 0.0

        # the probability to the next city
        for i in range(self.arrets.n):
            if self.open_table_city[i]:
                try :
                    select_citys_prob[i] = pow(self.arrets.pheromone_graph[self.current_city][i], ALPHA) * pow((1.0/self.arrets.distance_graph[self.current_city][i]), BETA)
                    total_prob += select_citys_prob[i]
                except ZeroDivisionError as e:
                    print ('Ant ID: {ID}, current city: {current}, target city: {target}'.format(ID = self.ID, current = self.current_city, target = i))
                    sys.exit(1)

        # choose city
        if total_prob > 0.0:
            temp_prob = random.uniform(0.0, total_prob)
            for i in range(self.arrets.n):
                if self.open_table_city[i]:
                    temp_prob -= select_citys_prob[i]
                    if temp_prob <= 0.0:
                        next_city = i
                        break
        return next_city

    # calculate the total distance
    def __cal_total_distance(self):

        temp_distance = 0.0

        for i in range(1, self.arrets.n):
            start, end = self.path[i], self.path[i-1]
            temp_distance += self.arrets.distance_graph[start][end]

        end = self.path[0]
        self.total_distance = temp_distance


    # move
    def __move(self, next_city):

        self.path.append(next_city)
        self.open_table_city[next_city] = False
        self.total_distance += self.arrets.distance_graph[self.current_city][next_city]
        self.current_city = next_city
        self.move_count += 1

    # search path
    def search_path(self):

        self.__clean_data()

        while self.move_count < self.arrets.n:
            next_city =  self.__choice_next_city()
            self.__move(next_city)

        self.__cal_total_distance()

#classe de bus qui sera initialisé dans classe TSP suivante pour transférer les graphes de distance et de phéromone dans classe ant
class Arret_Bus(object):
    
    def __init__(self,location, distance_graphe, pheromone_graph):
        self.location = location
        self.distance_graphe = distance_graphe
        self.pheromone_graph = pheromone_graph
        self.n = len(self.location)

class TSP(object):

    def __init__(self, root, carte, width =800, height = 1000): 

        self.root = root                               
        self.width = width      
        self.height = height
        self.carte = carte
        self.villes = self.carte[0]
        
        #Creation de Menu
        menubar = tkinter.Menu(root)
        menubar.add_command(label="Quitter", command=self.quite)

        #radioButtons pour selectionner des cartes
        self.radioVar = IntVar()
        carteMenu = Menu(menubar, tearoff=False)
        for i in range (len(self.carte)-1):
            carteMenu.add_radiobutton(label="Carte %d"%(i), variable=self.radioVar, value=i, command=self.select_carte)
        carteMenu.add_radiobutton(label="Carte %d"%(len(self.carte)-1), variable=self.radioVar, value=len(self.carte)-1, command=self.select_carte)
        menubar.add_cascade(label='Cartes', menu=carteMenu)
        self.root.config(menu=menubar)
        #Creation BarreOutil
        self.barreOutils = tkinter.Frame(root)
        self.barreOutils.pack(side= TOP)

        
        #Creation et placement des boutons

        self.__boutonInit = Button(self.barreOutils, text='Initialisation')
        self.__boutonInit.pack(side = LEFT,padx=5, pady=5)
        self.__boutonArrets = Button(self.barreOutils, text='Créer arrêts')
        self.__boutonArrets.pack(side = LEFT, padx=5,pady=5)
        self.__boutonSearch = Button(self.barreOutils, text='Calculer lignes')
        self.__boutonSearch.pack(side = LEFT,padx=5, pady=5)
        self.__boutonArreter = Button(self.barreOutils, text='Arreter')
        self.__boutonArreter.pack(side = LEFT,padx=5, pady=5)
        
        #Fonctions des boutons
        self.__boutonInit.config(command = self.new)
        self.__boutonArrets.config(command = self.arret_bus)
        self.__boutonSearch.config(command = self.search_path)
        self.__boutonArreter.config(command = self.stop)
        # tkinter.Canvas
        self.canvas = tkinter.Canvas(
                root,
                width = self.width,
                height = self.height,
                bg = "#EBEBEB",           
                xscrollincrement = 1,
                yscrollincrement = 1,
            )

        self.canvas.pack(side = TOP,expand = tkinter.YES, fill = tkinter.BOTH,padx = 5,pady = 5)
        self.title("Allocation de bus")
        

        self.__r = 5 #rayons des villes et arrets traces
        self.__lock = threading.RLock()     

        self.new()

      

    def title(self, s):

        self.root.title(s)

    def new(self, evt = None):

        # arreter le calcul en cours
        self.__lock.acquire()
        self.__running = False
        self.__lock.release()

        self.clear()     # eliminer les donnees
        self.nodes = []  #liste des figures de villes(appartements)
        self.nodes2 = [] #liste des figures des arrets de bus

        # initialisation des villes
        for i in range(len(self.villes)):
            x = self.villes[i][0]
            y = self.villes[i][1]
            # dessiner les noeuds de rayon self.__r
            node = self.canvas.create_oval(x - self.__r,
                    y - self.__r, x + self.__r, y + self.__r,
                    fill = "#F5DEB3",      
                    outline = "#000000",   
                    tags = "node",
                )
            self.nodes.append(node)
        
        self.__boutonArrets.config(state = NORMAL)
        self.__boutonSearch.config(state = DISABLED)
    
    #fonction pour changer de carte
    def select_carte(self):
        self.villes = self.carte[self.radioVar.get()]
        self.new()
    # lier des noeuds par ordre
    def line(self, order, couleur,largeur):
        # eliminer le trait d'avant
        self.canvas.delete("line")
        def line2(i1, i2):
            p1, p2 = self.arrets.location[i1], self.arrets.location[i2]
            self.canvas.create_line(p1[0],p1[1],p2[0],p2[1], fill = couleur, tags = "line", width = largeur)
            return i2

        reduce(line2, order, order[0])  #lier tous les points dans order un par un

    # nettoyer canvas
    def clear(self):
        for item in self.canvas.find_all():
            self.canvas.delete(item)
            
        # quitter application
    def quite(self):
        self.__lock.acquire()
        self.__running = False
        self.__lock.release()
        self.root.destroy()
        sys.exit()

    # arreter le calcul en cours
    def stop(self):
        self.__lock.acquire()
        self.__running = False
        self.__lock.release()
            
    def arret_bus(self):
        # create a serie of bandwidth then choose the one whose error is the smallest
        band_serie = np.linspace(60, 200, 10)
        clf_best = MeanShift(bandwidth=200)
        clf_best.fit(self.villes)
        band_best = 200
        for band in band_serie:
            clf = MeanShift(bandwidth=band)
            clf.fit(self.villes)
            if clf_best.err_ > clf.err_:
                clf_best = clf
                band_best = band
        clf = MeanShift(bandwidth=band_best)
        clf.fit(self.villes)
        self.arrets = clf.centers_
        self.arrets = Arret_Bus(clf.centers_,[],[])
        for i in range(len(self.arrets.location)):
            x = self.arrets.location[i][0]
            y = self.arrets.location[i][1]
            # dessiner les noeuds de rayon self.__r
            #node = self.canvas.create_rectangle(x - self.__r,
            #        y - self.__r, x + self.__r, y + self.__r,
            #        fill = "#FF7F50",      
            #        outline = "#000000",   
            #        tags = "node",
            #    )
            node_horizontal = self.canvas.create_line(x-self.__r*3, y+self.__r*3, x+self.__r*3, y-self.__r*3, 
                    fill = "blue", tags = "node")
            node_vertical = self.canvas.create_line(x-self.__r*3, y-self.__r*3, x+self.__r*3, y+self.__r*3, 
                    fill = "blue",tags = "node")
                    
            self.nodes2.append([node_vertical,node_horizontal])
        self.n = len(self.arrets.location) #nombre d'arrets
        
        #des donnes pour l'algorithme colonie fourmie
        self.arrets.distance_graph = [ [0.0 for col in range(self.n)] for raw in range(self.n)]
        self.arrets.pheromone_graph = [ [1.0 for col in range(self.n)] for raw in range(self.n)]
        # initialisation des diatances entre les arrets et les ferromones
        for i in range(self.n):
            for j in range(self.n):
                temp_distance = pow((self.arrets.location[i][0] - self.arrets.location[j][0]), 2) + pow((self.arrets.location[i][1] - self.arrets.location[j][1]), 2)
                temp_distance = pow(temp_distance, 0.5)
                self.arrets.distance_graph[i][j] =float(int(temp_distance + 0.5))
                self.arrets.pheromone_graph[i][j] = 1.0
        
        self.__boutonArrets.config(state = DISABLED)
        self.__boutonSearch.config(state = NORMAL)
                

    # calculer des lignes de bus par colonie fourmie
    def search_path(self, evt = None):

        
        self.__lock.acquire()
        self.__running = True
        self.__lock.release()

        self.ants = [Ant(ID,self.arrets) for ID in range(ant_num)]  # initialisation colonie fourmie
        self.best_ant = Ant(-1,self.arrets)                          
        self.best_ant.total_distance = 1 << 31            
        self.iter = 1       # initialisation nombre iteration
        
        while self.__running:
            
            for ant in self.ants:
                #chercher une voie
                ant.search_path()
               #comparer avec la meilleure fourmie actuelle
                if ant.total_distance < self.best_ant.total_distance:
                    # mise à jour de meilleure solution
                    self.best_ant = copy.deepcopy(ant)
            # MAJ de phéromone
            self.__update_pheromone_gragh()
            # lier des points
            self.line(self.best_ant.path,"#000000",1)
            # mise a jour de canvas
            self.canvas.update()
            self.iter += 1
            if self.iter >= 400:
                self.__running = False
                self.line(self.best_ant.path,'blue',3)

    # MAJ de pheromone
    def __update_pheromone_gragh(self):

        # pheromone de chaque fourmie
        temp_pheromone = [[0.0 for col in range(self.n)] for raw in range(self.n)]
        for ant in self.ants:
            for i in range(1,self.n):
                start, end = ant.path[i-1], ant.path[i]
                # laisser de pheromone entre deux arrets voisins, inversement proportionnel a la distence
                temp_pheromone[start][end] += Q / ant.total_distance
                temp_pheromone[end][start] = temp_pheromone[start][end]

        # MAJ pheromone de tous les arrets
        for i in range(self.n):
            for j in range(self.n):
                self.arrets.pheromone_graph[i][j] = self.arrets.pheromone_graph[i][j] * RHO + temp_pheromone[i][j]

    # 主循环
    def mainloop(self):
        self.root.mainloop()
        
        
if __name__ == '__main__':


    ant_num = 50
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
    TSP(tkinter.Tk(),carte).mainloop()
