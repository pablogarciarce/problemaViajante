import json
import random
import matplotlib.pyplot as plt
import numpy as np


def main(dist_path):
    distancias = np.load(dist_path)
    sol = []
    indices_restantes = list(range(distancias.shape[0]))
    sol.append(indices_restantes.pop(
        random.sample(indices_restantes, 1)[0])
    )
    for i in range(distancias.shape[0]-1):
        mejor_indice = None
        menor_dist = 10000
        for indice in indices_restantes:
            if distancias[indice, sol[i]] < menor_dist:
                mejor_indice = indice
                menor_dist = distancias[indice, sol[i]]
        sol.append(mejor_indice)
        indices_restantes.remove(mejor_indice)

    # calculamos su valor
    valor = 0
    for i in range(distancias.shape[0] - 1):
        valor += distancias[sol[i], sol[i + 1]]
    valor += distancias[sol[0], sol[distancias.shape[0] - 1]]
    print("El valor de la función de adaptación es ", valor)


if __name__ == '__main__':
    main('distancias/ciudades10000.npy')
