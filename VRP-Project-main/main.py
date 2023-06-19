import json
import os
import time
from time import sleep

from database import DBManagement as dbm
from generation.DataGeneration import DataGeneration
from pathfinding.PathFinding import average_weight
from pdf.RoadMap import RoadMap
from pdf.StatMap import StatMap
from statistic import Stats
import pandas as pd

def clearConsole(): os.system('cls' if os.name in ('nt', 'dos') else 'clear')

if __name__ == '__main__':
    data = None

    while True:

        print("What do you want to do?")
        print('{:.<3s}{:<5}'.format("0", "Exit"))
        print('{:.<3s}{:<5}'.format("1", "Random Graph to DB"))
        print('{:.<3s}{:<5}'.format("2", "Get Graph from the DB"))
        print('{:.<3s}{:<5}'.format("3", "Calculate Path + print RoadMap"))
        print('{:.<3s}{:<5}'.format("4", "Generate stat data for studies"))
        print('{:.<3s}{:<5}'.format("5", f"Compute the {dbm.get_number_of_stored_stat()} stat data"))

        while (inp := (input("Enter your choice :"))) not in ["0", "1", "2", "3", "4", "5"]:
            print("Please enter a correct number")
        clearConsole()

        if inp == "0":  # quitter
            print("It will close in 5 seconds...")
            sleep(5)
            quit(0)

        elif inp == "1":  # Generate + store
            data = DataGeneration(number_of_summit=500, number_of_vehicle=10, max_neighbor=5, number_of_kind_of_item=4)
            clearConsole()
            print("Loading in MongoDB")
            dbm.store_data_generation(data)

        elif inp == "2":  # Load from DB
            print("Getting data from MongoDB")
            data = dbm.get_data_generation()
            # data.display()
            clearConsole()

        elif inp == "3":  # Pathfinding + RoadMap
            if data is not None:
                print("Path calculation, please wait")
                start = time.time()
                data.pathfinder.do(data, "dj", 10)
                end = time.time()
                print(end - start)
                clearConsole()
                print('Generation of the pdf, please wait')
                roadmap_instance = RoadMap('test')
                roadmap_instance.generate(data)
            else:
                print("The data is not loaded, please generate or import it (1 or 2)\n")

        elif inp == "4":  # stat mode
            summ = int(input("Number of summit : "))
            step = int(input("step :"))
            for i in range(5):
                summits = summ
                vehicles = 10
                for j in range(10):
                    neighbors = 3
                    for k in range(5):

                        bdd_entry = {"summits": summits, "vehicles": vehicles, "neighbors": neighbors}
                        #generation
                        start = time.time()
                        data = DataGeneration(number_of_summit=summits, number_of_vehicle=vehicles,
                                              max_neighbor=neighbors,
                                              number_of_kind_of_item=4)
                        end = time.time()
                        print(f"i:{i}\tj:{j}\t{k}")
                        bdd_entry['generation'] = end - start
                        #Djikstra
                        start = time.time()
                        data.pathfinder.do(data, "Djistra", 10)
                        end = time.time()
                        bdd_entry['pathfinding_dj'] = end - start
                        bdd_entry['average_weight_dj'] = average_weight(data)
                        #AStar
                        start = time.time()
                        data.pathfinder.do(data, "Astar", 10)
                        end = time.time()
                        bdd_entry['pathfinding_astar'] = end - start
                        bdd_entry['average_weight_astar'] = average_weight(data)
               
                        del data.data_segment
                        del data.data_vehicles
                        del data.data_matrix
                        del data.pathfinder
                        #del roadmap_instance
                        del data

                        dbm.store_stat_to_mongo(json.loads(json.dumps(bdd_entry)))
                        print("Stored to MongoDB")
                        neighbors += 1
                    vehicles += 1
                summits += step
            print("Statistic Calculation is finished and put in the MongoDB")
            sleep(10)
        elif inp == "5":
            stat_map = StatMap('statstest')
            # fig = plt.figure()
            # ax = plt.axes(projection='3d')
            # ax.scatter3D(x, y, z, c=z, cmap='BrBG_r')
            stats = dbm.get_stat_from_mongo()
            with_dj = {}
            with_astar = {'smt': [], 'pfas': [], 'pfdj': [], 'nei': []}
            sm = []
            gn = []
            ng = []
            ptg_dj = []
            avg_w_dj = []
            ptg_astar = []
            sm_astar = []
            ng_astar = []
            for x in stats:
                sm.append(x['summits'])
                gn.append(x["generation"])
                ng.append(x['neighbors'])
                ptg_dj.append(x['pathfinding_dj'])
                avg_w_dj.append(x['average_weight_dj'])
                try:
                    if x['pathfinding_astar']:
                        with_astar['smt'].append(x['summits'])
                        with_astar['pfas'].append(x['pathfinding_astar'])
                        with_astar['pfdj'].append(x['pathfinding_dj'])
                        with_astar['nei'].append(x['neighbors'])

                except Exception as e:
                    pass

            # number of summit over Pathfinding time
            x = [[], []]
            y = [[], []]
            line_names = [[], []]
            f = pd.DataFrame(with_astar).groupby(['smt'])['pfdj'].mean()
            for i in f.index:
                x[0].append(i)
                y[0].append(f[i])
                line_names[0] = "Pathfinding with Djikstra"
            f = pd.DataFrame(with_astar).groupby(['smt'])['pfas'].mean()
            for i in f.index:
                x[1].append(i)
                y[1].append(f[i])
                line_names[1] = "Pathfinding with A*"

            stat_map.add_txt("1. Execution time analysis")
            r = Stats.classic_lines_graph(x, y, "Number of summits", "Pathfinding time (in s)", line_names,
                                          "Graph representing number of summit over Pathfinding time.",
                                          True)
            stat_map.add_img(r)
            stat_map.add_txt("With this graph we can compare the pathfinding algorithm by their respective")
            stat_map.add_txt("mean execution time.")

            # linear regression for number of summit over graph generation time
            b, r = Stats.linear_regression(sm, gn, "Number of summits", "Graph generation time (s)",
                                           "Graph representing a linear regression of \nnumber of summit over graph "
                                           "generation time.",
                                           True)
            stat_map.add_img(r)
            print(f"linear regression fx y ~ {round(b[0], 4)} + {round(b[1], 4)} * x")
            stat_map.add_txt(f"linear regression fx y ~ {round(b[0], 4)} + {round(b[1], 4)} * x")

            # linear regression for number of summit over Pathfinding time with Djikstra.
            b, r = Stats.linear_regression(sm, ptg_dj, "Number of summits", "Pathfinding time with Djikstra (s)",
                                           "Graph representing a linear regression of \nnumber of summit over Pathfinding time with Djikstra.",
                                           True)
            print(f"linear regression fx y ~ {round(b[0], 4)} + {round(b[1], 4)} * x")
            stat_map.add_img(r)
            stat_map.add_txt(f"linear regression fx y ~ {round(b[0], 4)} + {round(b[1], 4)} * x")

            # linear regression for number of summit over Pathfinding time with a*.
            b, r = Stats.linear_regression(with_astar['smt'], with_astar['pfas'], "Number of summits",
                                           "Pathfinding time with A* (s)",
                                           "Graph representing a linear regression of \nnumber of summit over Pathfinding time with A*.",
                                           True)
            print(f"linear regression fx y ~ {round(b[0], 4)} + {round(b[1], 4)} * x")
            stat_map.add_img(r)
            stat_map.add_txt(f"linear regression fx y ~ {round(b[0], 4)} + {round(b[1], 4)} * x")

            # plotting pathfinding Dijkstra
            r = Stats.stats_pathfinding(sm=sm, ng=ng, ptg=ptg_dj,
                                        title='Graph representing a progression of \nnumber of summit over Dijkstra pathfinding',
                                        save=True)
            stat_map.add_img(r)

            # plotting pathfinding A star
            r = Stats.stats_pathfinding(sm=with_astar['smt'], ng=with_astar['nei'], ptg=with_astar['pfas'],
                                        title='Graph representing a progression of \nnumber of summit over A star pathfinding',
                                        save=True)
            stat_map.add_img(r)
            stat_map.next_page()
            stat_map.add_txt("2. Influence of neighbors and summits")
            # Plotting of the dj fix summits
            r = Stats.stat_dj_fix_summits(True)
            stat_map.add_img(r)
            stat_map.add_txt("We had a graph with a defined number of summits (500) and we can see that")
            stat_map.add_txt("when we add neighbors (even a small amount), the execution time grows instantly.")

            # Plotting of the dj fix neighbors
            r = Stats.stat_dj_fix_neighbors(True)
            stat_map.add_img(r)
            stat_map.add_txt("We had a graph with a defined number of neighbors (3) and we can see that when we ")
            stat_map.add_txt("add summits the execution time grows but we need a large amount of summits to")
            stat_map.add_txt("influence the execution time ")
            stat_map.add_txt(" ")
            stat_map.add_txt("The conclusion we can make is that the number of neighbors influences more the")
            stat_map.add_txt("execution time of the algorithm than the number of summits")
            # Save the PDF file
            stat_map.save()
