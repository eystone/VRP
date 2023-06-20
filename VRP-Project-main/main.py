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

        print("Main Menu")
        print('{:.<3s}{:<5}'.format("0", "Exit"))
        print('{:.<3s}{:<5}'.format("1", "Generate a Random Graph to Database"))
        print('{:.<3s}{:<5}'.format("2", "Get Graph from the Database"))
        print('{:.<3s}{:<5}'.format("3", "Calculate Path and print the RoadMap"))
        print('{:.<3s}{:<5}'.format("4", "Generate stat data for studies"))
        print('{:.<3s}{:<5}'.format("5", f"Compute the {dbm.get_number_of_stored_stat()} stat data"))

        while (inp := (input("Enter your choice :"))) not in ["0", "1", "2", "3", "4", "5"]:
            print("Please enter a correct number")
        clearConsole()

        if inp == "0":  # quitter
            print("Program will close in 5 seconds...")
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
            step = int(input("Number of step :"))
            for i in range(10):
                summits = summ
                vehicles = 10
                for j in range(20):
                    neighbors = 3
                    for k in range(10):

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
                        dbm.store_stat_to_mongo(json.loads(json.dumps(bdd_entry)))
               
                        del data.data_segment
                        del data.data_vehicles
                        del data.data_matrix
                        del data.pathfinder
                        #del roadmap_instance
                        del data

                        neighbors += 1
                    vehicles += 1
                summits += step
            print("Statistic Calculation is finished and in MongoDB")
            sleep(10)
        elif inp == "5":
            stat_map = StatMap('statstest')
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

            stat_map.add_txt("Statistics graphs")
            r = Stats.classic_lines_graph(x, y, "Number of summits", "Processing time (in s)", line_names,
                                          "Graph representing the number of summits over the time process.",
                                          True)
            stat_map.add_img(r)
            stat_map.add_txt("This graph describes the time process of the pathfinding ")
            stat_map.add_txt("by the number of summits.")

            # linear regression for number of summit over graph generation time
            b, r = Stats.linear_regression(sm, gn, "Number of summits", "Graph generation time (s)",
                                           "Graph representing a linear regression of \nthe number of summit over graph "
                                           "generation time.",
                                           True)
            stat_map.add_img(r)
            print(f"linear regression fx y ~ {round(b[0], 4)} + {round(b[1], 4)} * x")
            stat_map.add_txt(f"linear regression fx y ~ {round(b[0], 4)} + {round(b[1], 4)} * x")

            # linear regression for number of summit over Pathfinding time with Djikstra.
            b, r = Stats.linear_regression(sm, ptg_dj, "Number of summits", "Pathfinding time with Djikstra (in s)",
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
                                        title='Graph representing a progression of \nnumber of summit over A* pathfinding',
                                        save=True)
            stat_map.add_img(r)
            
            # Save the PDF file
            stat_map.save()
