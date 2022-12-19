import json
import random
import matplotlib.pyplot as plt
from genetic_alg import distancia


def main(cities_path):
    with open(cities_path) as f:
        ciudades = json.load(f)
    sol = []
    indices_restantes = list(range(len(ciudades)))
    sol.append(indices_restantes.pop(
        random.sample(indices_restantes, 1)[0])
    )
    for i in range(len(ciudades)-1):
        mejor_indice = None
        menor_dist = 10000
        for indice in indices_restantes:
            if distancia(ciudades[indice], ciudades[sol[i]]) < menor_dist:
                mejor_indice = indice
                menor_dist = distancia(ciudades[indice], ciudades[sol[i]])
        sol.append(mejor_indice)
        indices_restantes.remove(mejor_indice)

    ciudad_x = [ciudad[0] for ciudad in ciudades]
    ciudad_y = [ciudad[1] for ciudad in ciudades]
    plt.figure()
    plt.scatter(ciudad_x, ciudad_y)
    plt.plot(
        [ciudad_x[ind] for ind in sol],
        [ciudad_y[ind] for ind in sol]
    )

    # calculamos su valor
    valor = 0
    for i in range(len(ciudades) - 1):
        valor += distancia(ciudades[sol[i]], ciudades[sol[i + 1]])
    valor += distancia(ciudades[sol[0]], ciudades[sol[len(ciudades) - 1]])
    print("El valor de la función de adaptación es ", valor)
    plt.show()


if __name__ == '__main__':
    main('data/ciudades10.json')
