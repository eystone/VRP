import random
import uuid


class Summit:
    id = 0
    # address = 0
    # warehouse = 1
    kind = 0
    item_to_deliver = {}

    def __init__(self, id):
        self.id = id
        self.kind = 0
        self.item_to_deliver = {"kind": random.randint(0, 3), "qtt": random.randint(1, 5)}

    def set_warehouse(self):
        self.kind = 1

    def toJSON(self):
        """
        serialize the object in json
        """
        return {"id": self.id, "kind": self.kind, "item_to_deliver": self.item_to_deliver}

    def __str__(self):
        if self.kind == 0:
            return f"Summit {self.id}, Adress, items to deliver : {self.item_to_deliver.get('qtt')} of the object kind n°{self.item_to_deliver.get('kind')}"
        else:
            return f"Summit {self.id} DEPOT"

    def str_as_stopover(self):
        return f"Crossroad {self.id}"
