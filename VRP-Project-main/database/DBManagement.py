from time import sleep

import numpy as np
from bson import json_util

from database import DBConnection as db
from generation.DataGeneration import DataGeneration
from generation.Segment import Segment
from generation.Summit import Summit
from generation.Vehicle import Vehicle

name = 'data_project'

def store_data_generation(data: DataGeneration):
    # Delete data from Gridfs collections
    for collection in db.fs_collections:
        collection.delete_many({})

    # Explicit BSON conversion from JSON.
    json_str = json_util.dumps(data.toJSON())

    # Store new data with Gridfs
    db.fs.put(json_str, encoding='utf-8', filename=name)

def get_stat_from_mongo():
    return db.stat_collection.find()

# get data from mongo and sorting them by numbers of neighbors
def get_stat_from_mongo_sort_by_neighbors():
    return db.stat_collection.find().sort('neighbors')

# get data from mongo and sorting them by numbers of summits
def get_stat_from_mongo_sort_by_summits():
    return db.stat_collection.find().sort('summits')

def get_number_of_stored_stat():
    try:
        stats_count = db.stat_collection.estimated_document_count()
        return stats_count
    except Exception as e:
        print('Error in mongo connection:*', e)
        return 0

def store_stat_to_mongo(stat):
    db.stat_collection.insert_one(stat)

def get_data_generation() -> DataGeneration:
    # Get last data generated
    data_generation = db.fs.get_last_version(name).read()

    # Explicit BSON to JSON conversion.
    json_object = json_util.loads(data_generation)

    # Create an object DataGeneration
    data = DataGeneration(number_of_summit=100, number_of_vehicle=10, max_neighbor=5, number_of_kind_of_item=4,
                          progressbar=False)
    for k, v in json_object.items():
        if k == 'warehouse':
            data.warehouse = v
        elif k == 'data_matrix':
            data.data_matrix = np.array(v)
        elif k == 'data_segment':
            # Convert data segment JSON to object Segment
            data.data_segment = (
                [[Segment(origin=x['origin'], destination=x['destination']) if x != 'null' else None for x in z] for z
                 in v])
        elif k == 'data_vehicles':
            # Convert data segment JSON to object Vehicle
            data.data_vehicles = [Vehicle(kind=x['kind']) for x in v]
        elif k == 'data_summit':
            # Convert data segment JSON to object Summit
            data.data_summit = [Summit(id=x['id']) for x in v]
        else:
            print('Error in data transformation')
    for i in data.warehouse:
        data.data_summit[i].set_warehouse()
    return data
