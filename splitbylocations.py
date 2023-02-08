import sys
import json
import numpy as np
from math import radians
from sklearn.metrics.pairwise import haversine_distances
from sklearn.cluster import AgglomerativeClustering


def load_image_locations(file_path):
    imlocs = None
    with open(file_path, 'r') as file_stream:
        imlocs = json.load(file_stream)
    return imlocs

def prepare_distance_matrix(imlocs):
    # copy location info into numpy matrix
    locs = np.zeros((len(imlocs), 2), dtype=np.double)
    for idx, loc in enumerate(imlocs):
        locs[idx, 0] = loc[1]
        locs[idx, 1] = loc[2]

    # transform angles to radians and prepare distance matrix, in kilometers
    vrad = np.vectorize(radians, [np.double])
    distmat_km = haversine_distances(vrad(locs))*6371.0
    return distmat_km

def clasterize_distance_thres(imlocs, distmat, thres, prefix):
    aclust = AgglomerativeClustering(n_clusters=None, linkage='average', affinity='precomputed', distance_threshold=thres)
    aclust.fit(distmat)

    clustmap = {}
    for label, imloc in zip(aclust.labels_, imlocs):
        clust_name = '{}_{}'.format(prefix, label)
        if clust_name in clustmap:
            clustmap[clust_name].append(imloc[0])
        else:
            clustmap[clust_name] = [imloc[0]]
    return clustmap

def main():
    imlocs_path = 'dumps/imlocs.json'

    imlocs = load_image_locations(imlocs_path)
    print(f'info: preparing distance matrix...', file=sys.stderr)
    distmat = prepare_distance_matrix(imlocs)
    print(f'info: prepared distance matrix', file=sys.stderr)

    print(f'info: cluster for 10 km...', file=sys.stderr)
    clustmap_10km = clasterize_distance_thres(imlocs, distmat, 10.0, 'cluster10km')
    print(f'info: cluster for 1 km...', file=sys.stderr)
    clustmap_1km = clasterize_distance_thres(imlocs, distmat, 1.0, 'cluster1km')
    print(f'info: done clusters', file=sys.stderr)

    with open('dumps/clustmap_10km.json', 'w') as file_stream:
        json.dump(clustmap_10km, file_stream)

    with open('dumps/clustmap_1km.json', 'w') as file_stream:
        json.dump(clustmap_1km, file_stream)


if __name__ == '__main__':
    main()
