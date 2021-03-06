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
    
    def kernel(self,s, x):
        return np.exp(-(np.linalg.norm(s-x, axis=1))/1000)
    
    def cal_center(self,in_, center):
        in_ = np.array(in_)
        result = np.sum(self.kernel(in_, center).reshape(-1,1)*in_, axis=0)/np.sum(self.kernel(in_, center))
        return result

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

                new_center = self.cal_center(in_bandwidth, center)
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
        # For every center, we calculate its number of civilians
        self.habitant = dict()
        for center in self.centers_:
            habitant = 0
            for feature in data:
                feature = np.array(feature)
                if np.linalg.norm(center - feature) < self.bandwidth_:
                    habitant += 1
            self.habitant[tuple(center)] = habitant

        
class Ant(object):

    # initialize
    def __init__(self, ID, arrets, gare_centre = 0):
        self.ID = ID                 # ID
        self.arrets = arrets
        self.clean_data()          # random birth place
        self.gare_centre = gare_centre
        self.ant_another = None  # another ant
        

    def clean_data(self):

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
        city_tuple = tuple(self.arrets.location[city_index])
        self.trajet_habitant = self.arrets.habitant[city_tuple] # the sum of numbers of those stops that ant has passed
        self.cout = 0.5*self.total_distance + 0.5*self.trajet_habitant
        
    # add accompanied ant
    def add_another(self, another_ant):
        self.ant_another = another_ant
        if self.path[0] != self.gare_centre:
            self.ant_another.open_table_city[self.path[0]] = False
        
    # next city
    def choice_next_city(self):

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

        for i in range(1, len(self.path)):
            start, end = self.path[i], self.path[i-1]
            temp_distance += self.arrets.distance_graph[start][end]

        end = self.path[0]
        self.total_distance = temp_distance


    # move
    def move(self, next_city):

        self.path.append(next_city)
        self.open_table_city[next_city] = False
        if next_city != self.gare_centre:
            self.ant_another.open_table_city[next_city] = False
        self.total_distance += self.arrets.distance_graph[self.current_city][next_city]
        self.current_city = next_city
        self.move_count += 1
        self.trajet_habitant += self.arrets.habitant[tuple(self.arrets.location[next_city])]
        self.cout = 0.5 * self.total_distance + 0.5 * self.trajet_habitant

    # search path
    def search_path(self):

        self.clean_data()

        while self.move_count < self.arrets.n:
            next_city =  self.choice_next_city()
            self.move(next_city)

        self.__cal_total_distance()

#classe de bus qui sera initialis?? dans classe TSP suivante pour transf??rer les graphes de distance et de ph??romone dans classe ant
class Arret_Bus(object):
    
    def __init__(self,location, distance_graphe, pheromone_graph, habitant):
        self.location = location
        self.distance_graphe = distance_graphe
        self.pheromone_graph = pheromone_graph
        self.n = len(self.location)
        self.habitant = habitant
        
class ZoneAffichage(Canvas):
    
    def __init__(self, parent, w, h, bgcolor, scroll):
        self.__parent = parent
        self.__w = w
        self.__h = h
        Canvas.__init__(self, parent.root, width=w, height=h, bg=bgcolor, scrollregion=scroll)
        
    def OnClick(self,event):
        #si interaction avec canvas est active, alors prendre les coordonnees
        #et envoyer ces coordonnes a la fonction centrale dans classe TSP
        if self.__parent.clickActive == True:
            self.__parent.clickActive = False
            self.__parent.FixCentrale(event.x,event.y)

class TSP(object):

    def __init__(self, root, carte, width =800, height = 800): 

        self.root = root
        ww = 700
        wh = 650
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - ww) / 2
        y = (sh - wh) / 2
        self.root.geometry("%dx%d+%d+%d" % (ww, wh, x, y))
        self.width = width      
        self.height = height
        self.carte = carte
        self.villes = self.carte[0]
        self.root.configure(bg="wheat")
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
        self.__boutonArrets = Button(self.barreOutils, text='Cr??er arr??ts')
        self.__boutonArrets.pack(side = LEFT, padx=5,pady=5)
        self.__boutonCentral = Button(self.barreOutils, text='Choisir Centrale')
        self.__boutonCentral.pack(side = LEFT, padx=5,pady=5)
        self.__boutonSearch = Button(self.barreOutils, text='Calculer lignes')
        self.__boutonSearch.pack(side = LEFT,padx=5, pady=5)
        self.__label_cout = Label(self.barreOutils,text = '')
        self.__label_cout.pack(side = TOP,padx=5,pady=5)

        
        #Fonctions des boutons
        self.__boutonInit.config(command = self.new)
        self.__boutonArrets.config(command = self.arret_bus)
        self.__boutonCentral.config(command = self.active)
        self.__boutonSearch.config(command = self.search_path)

        # tkinter.Canvas
        self.canvas = ZoneAffichage(self, self.width, self.height, 'tan', (0, 0, 800, 1000))
        self.canvas.pack(side = TOP,padx = 5,pady = 5, expand=True, fill=BOTH)
        self.clickActive = False
        self.canvas.bind('<Button-1>', self.canvas.OnClick)
        self.title("Allocation de bus")
        hbar = tkinter.Scrollbar(self.canvas, orient=HORIZONTAL)
        hbar.pack(side=BOTTOM, fill=X)
        hbar.config(command=self.canvas.xview)
        vbar = tkinter.Scrollbar(self.canvas, orient=VERTICAL)
        vbar.pack(side=RIGHT, fill=Y)
        vbar.config(command=self.canvas.yview)
        self.canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.__r = 5 #rayons des villes et arrets traces
        self.__lock = threading.RLock()     

        self.new()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def title(self, s):

        self.root.title(s)

    def new(self, evt = None):

        # arreter le calcul en cours
        self.__lock.acquire()
        self.__running = False
        self.__lock.release()

        self.clear()     # eliminer les donnees
        self.arrets = [] #liste des arrets
        self.nodes = []  #liste des figures de villes(appartements)
        self.nodes2 = [] #liste des figures des arrets de bus
        self.ants = [] #liste des fourmis
        self.centrale = []
        self.__label_cout.config(text = '')

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
        self.__boutonCentral.config(state = DISABLED)
        
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
        
    #changer de carte
    def select_carte(self):
        self.villes = self.carte[self.radioVar.get()]
        self.new()
        
    # lier des noeuds par ordre
    # dessiner la premiere ligne de bus
    def line(self, order, couleur,largeur):
        # eliminer le trait d'avant
        self.canvas.delete("line")
        def line2(i1, i2):
            p1, p2 = self.arrets.location[i1], self.arrets.location[i2]
            self.canvas.create_line(p1[0],p1[1],p2[0],p2[1], fill = couleur, tags = "line", width = largeur)
            return i2

        reduce(line2, order, order[0])  #lier tous les points dans order un par un
    # dessiner la deuxieme ligne de bus
    def line_2(self, order, couleur, largeur):
        def line2(i1, i2):
            p1, p2 = self.arrets.location[i1], self.arrets.location[i2]
            self.canvas.create_line(p1[0], p1[1]-2, p2[0], p2[1]-2, fill=couleur, tags="line", width=largeur)
            return i2

        reduce(line2, order, order[0])  # lier tous les points dans order un par un
    def arret_bus(self):
        # create a serie of bandwidth then choose
        # the one whose error is the smallest
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
        self.arrets = Arret_Bus(clf.centers_,[],[],clf.habitant)
        for i in range(len(self.arrets.location)):
            x = self.arrets.location[i][0]
            y = self.arrets.location[i][1]
            node_horizontal = self.canvas.create_line(x-self.__r*2, y+self.__r*2, x+self.__r*2, y-self.__r*2, 
                    fill = "ForestGreen", tags = "node",width=2)
            node_vertical = self.canvas.create_line(x-self.__r*2, y-self.__r*2, x+self.__r*2, y+self.__r*2, 
                    fill = "ForestGreen",tags = "node",width=2)
                    
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
        self.__boutonCentral.config(state = NORMAL)
                
    def active(self):
        #activer l'interaction en clique avec le canvas
        self.clickActive = True
        self.__boutonSearch.config(state = DISABLED)
        self.clear()
        self.centrale = []
        self.__label_cout.config(text = '')
        self.centrale_index = -1
        for i in range(len(self.villes)):
            x = self.villes[i][0]
            y = self.villes[i][1]
            # dessiner les noeuds de rayon self.__r
            self.canvas.create_oval(x - self.__r,
                    y - self.__r, x + self.__r, y + self.__r,
                    fill = "#F5DEB3",      
                    outline = "#000000",   
                    tags = "node",
                )
            
        for i in range(len(self.arrets.location)):
            x = self.arrets.location[i][0]
            y = self.arrets.location[i][1]
            node_horizontal = self.canvas.create_line(x-self.__r*2, y+self.__r*2, x+self.__r*2, y-self.__r*2, 
                    fill = "ForestGreen", tags = "node",width=2)
            node_vertical = self.canvas.create_line(x-self.__r*2, y-self.__r*2, x+self.__r*2, y+self.__r*2, 
                    fill = "ForestGreen",tags = "node",width=2)
        
        
        
    def FixCentrale(self,x,y):
        autour = []
        for i in range (self.arrets.n):
            if abs(x-self.arrets.location[i][0]) <= 2*self.__r and abs(y-self.arrets.location[i][1]) <= 2*self.__r:
                autour.append(i)
        #s'il y a exactement un arret autour de clique
        if len(autour)==1:
            self.centrale = self.arrets.location[autour[0]]
            self.canvas.create_line(self.centrale[0]-self.__r*2, self.centrale[1]+self.__r*2, self.centrale[0]+self.__r*2, self.centrale[1]-self.__r*2, 
                    fill = "Red", tags = "node",width=2.5)
            self.canvas.create_line(self.centrale[0]-self.__r*2, self.centrale[1]-self.__r*2, self.centrale[0]+self.__r*2, self.centrale[1]+self.__r*2, 
                    fill = "Red",tags = "node",width=2.5)
            self.__boutonSearch.config(state = NORMAL)
        #s'il n'y a pas d'arret assez proche de clique
        if len(autour)==0:
            #reactive l'interaction avec canvas pour que l'utilisateur puisse choisir a nouveau le centrale
            self.clickActive = True
            tkinter.messagebox.showinfo(title='Echec',message='Pas de arret d??tect?? aux alentours de clique. Veuillez r??essayer !')

    # calculer des lignes de bus par colonie fourmie
    def search_path(self, evt=None):
        self.__boutonSearch.config(state = DISABLED)
        self.__boutonCentral.config(state = DISABLED)
        self.__label_cout.config(text = '')
        self.__lock.acquire()
        self.__running = True
        self.__lock.release()
        self.centrale_index = -1
        for index, center in enumerate(self.arrets.location):
            if (np.array(center) == np.array(self.centrale)).all():
                self.centrale_index = index
                break

        self.ants = [Ant(ID, self.arrets, self.centrale_index) for ID in
                     range(ant_num)]  # initialisation colonie fourmie, the first colony
        self.ants2 = [Ant(ID, self.arrets, self.centrale_index) for ID in range(ant_num, 2 * ant_num)]  # the second colony
#        for i in range(ant_num):
#            self.ants[i].add_another(self.ants2[i])
#            self.ants2[i].add_another(self.ants[i])

        self.best_ant = Ant(-1, self.arrets)
        self.best_ant.cout = 1 << 31
        self.best_ant2 = Ant(-2, self.arrets)
        self.best_ant2.cout = 1 << 31
        self.iter = 1  # initialisation nombre iteration
        # the smaller the value of the cout is, the better the ant is. 
        cout_best = 1 << 31

        while self.__running:
            for index_ant in range(ant_num):
                ant1 = self.ants[index_ant]
                ant2 = self.ants2[index_ant]
                ant1.clean_data()
                ant2.clean_data()
                ant1.add_another(ant2)
                ant2.add_another(ant1)
                while np.any(ant1.open_table_city) or np.any(ant2.open_table_city):
                    # if both ant1 and ant2 can move
                    if np.any(ant1.open_table_city) and np.any(ant2.open_table_city):
                        # we choose the ant acoording to its cout(ant.cout), the more cout the ant has,
                        # the less possible it is to be chosen
                        ant1_cout = ant1.cout
                        ant2_cout = ant2.cout
                        ant_chosen = np.random.choice([1, 2], 1, [1 / ant1_cout, 1 / ant2_cout])[0]
                        if ant_chosen == 1:
                            ant_chosen = ant1
                        else:
                            ant_chosen = ant2
                    # only ant1 can move
                    elif np.any(ant1.open_table_city):
                        ant_chosen = ant1
                    # only ant2 can move
                    else:
                        ant_chosen = ant2
                    next_city = ant_chosen.choice_next_city()
                    ant_chosen.move(next_city)
                # mise ?? jour de meilleure solution
                # if the civilians that two bus transport is more balanced,
                # the cout is better
                cout_this_time = ant1.total_distance + ant2.total_distance\
                                        - 1/(1/ant1.trajet_habitant+1/ant2.trajet_habitant)
                if cout_this_time < cout_best:
                    self.best_ant = copy.deepcopy(ant1)
                    self.best_ant2 = copy.deepcopy(ant2)
                    cout_best = self.best_ant.total_distance + self.best_ant2.total_distance \
                                       - 1 /(1 / self.best_ant.trajet_habitant + 1 / self.best_ant2.trajet_habitant)
                    self.__label_cout.config(text = 'Co??t de solution : %.2f'%(cout_best))
            # MAJ de ph??romone
            self.__update_pheromone_gragh()
            # lier des points
            self.line(self.best_ant.path, "ForestGreen", 1)
            self.line_2(self.best_ant2.path, "#a52a2a", 1)
            # mise a jour de canvas
            self.canvas.update()
            self.iter += 1
            if self.iter >= 400:
                self.__running = False
                self.line(self.best_ant.path, "ForestGreen", 3)
                self.line_2(self.best_ant2.path, "#a52a2a", 3)
        self.__boutonSearch.config(state = NORMAL)
        self.__boutonCentral.config(state = NORMAL)


    # MAJ de pheromone
    def __update_pheromone_gragh(self):

        # pheromone de chaque fourmie
        temp_pheromone = [[0.0 for col in range(self.n)] for raw in range(self.n)]
        for ant in self.ants:
            for i in range(1, len(ant.path)):
                start, end = ant.path[i - 1], ant.path[i]
                # laisser de pheromone entre deux arrets voisins, inversement proportionnel a la distence
                temp_pheromone[start][end] += Q / ant.total_distance
                temp_pheromone[end][start] = temp_pheromone[start][end]
        for ant in self.ants2:
            for i in range(1, len(ant.path)):
                start, end = ant.path[i - 1], ant.path[i]
                # laisser de pheromone entre deux arrets voisins, inversement proportionnel a la distence
                temp_pheromone[start][end] += Q / ant.total_distance
                temp_pheromone[end][start] = temp_pheromone[start][end]

        # MAJ pheromone de tous les arrets
        for i in range(self.n):
            for j in range(self.n):
                self.arrets.pheromone_graph[i][j] = self.arrets.pheromone_graph[i][j] * RHO + temp_pheromone[i][j]

    # main loop
    def mainloop(self):
        self.root.mainloop()
        
        
if __name__ == '__main__':
    #parametres pour algo colinie fourmie
    (ALPHA, BETA, RHO, Q) = (1.0, 2.0, 0.15, 100.0)
    ant_num = 50
    #fenetre
    TSP(tkinter.Tk(),carte).mainloop()