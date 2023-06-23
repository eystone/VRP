import os
import uuid

import networkx as nx
import numpy as np
from matplotlib import pyplot as plt
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from generation.DataGeneration import DataGeneration


def remove_img(fn):
    os.remove(f'{fn}.jpg')


def matrix_to_img(matrix, summit) -> str:
    # Generate the figure
    G2 = matrix.to_di_graph()
    plt.figure()
    options = {
        'node_color': 'yellow',
        'node_size': 120,
        'edge_color': 'tab:grey',
        'with_labels': False,
    }
    # Set node size by type
    node_sizes = [300 if x.kind == 1 else 120 for x in summit]
    # Set color map
    cmap = ['darkorange' if x.kind == 1 else 'dodgerblue' for x in summit]
    # Draw the graph and specify our characteristics
    lbl = ['Dépot' if x.kind == 1 else f'{summit.index(x)}' for x in summit]
    nx.draw(G2, with_labels=True, node_color=cmap,
            node_size=node_sizes, font_size=8, font_weight="bold", width=1,
            edgecolors='gray', labels={i: lbl[i] for i in range(len(lbl))})
    fn = str(uuid.uuid4())[:6]
    plt.savefig(f'graphs/{fn}.jpg', format='jpg')
    plt.close()
    return fn


class RoadMap:
    file_name = "random_name"

    def __init__(self, file_name):
        self.file_name = file_name

    def generate(self, data: DataGeneration):

        c = canvas.Canvas(f"{self.file_name}.pdf")

        c.drawString(100, 800, "Roadmap")
        c.drawString(100, 780, "Summits, Arrays, and Depot generation")
        fn = matrix_to_img(data.data_matrix, data.data_summit)
        c.drawImage(f'graphs/{fn}.jpg', 0, 760 - 4 * inch, height=4 * inch, preserveAspectRatio=True, mask='auto')
        offset = 740 - 4 * inch
        for smt in data.data_summit:
            c.drawString(100, offset, str(smt))
            if offset - 20 < 20:
                c.showPage()
                offset = 800
            else:
                offset -= 20

        for vh in data.data_vehicles:
            c.showPage()
            c.drawString(100, 800, f"Roadmap for the vehicle {vh.id}")
            offset = 780
            idx = 0
            for i, stop in enumerate(vh.full_itinerary):
                smt = data.data_summit[stop]
                if i == 0:
                    c.drawString(100, offset, f"Stop n° {i} : {smt}")
                else:
                    if smt.id == vh.itinerary[idx] or smt.id == data.warehouse[vh.kind]:
                        c.drawString(100, offset, f"Stop n° {i} : {smt}")
                        idx += 1
                    else:
                        c.drawString(100, offset, f"Stop n° {i} : {smt.str_as_stopover()}")
                if offset - 20 < 20:
                    c.showPage()
                    offset = 800
                else:
                    offset -= 20
        c.save()
