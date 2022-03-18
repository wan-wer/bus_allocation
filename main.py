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
    TSP(tkinter.Tk(),carte).mainloop()
