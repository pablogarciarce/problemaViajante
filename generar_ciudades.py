import random
import json
import math
import numpy as np


def generar(numero, lado_cuadrado=1000):
    ciudades = []
    for i in range(numero):
        ciudades.append([random.random()*lado_cuadrado, random.random()*lado_cuadrado])
    return ciudades


def guardar(ciudades, numero):
    name = 'C:/Users/pgarc/PycharmProjects/problemaViajante/data/ciudades' + str(numero) + '.json'
    with open(name, 'w') as f:
        json.dump(ciudades, f)
    return name


def generar_distancias():
    cities_path = 'data/ciudades100.json'
    with open(cities_path) as file:
        ciudades = json.load(file)
    array = np.zeros([len(ciudades), len(ciudades)])
    for i in range(len(ciudades)):
        print(i)
        for j in range(len(ciudades)):
            array[i, j] = math.sqrt((ciudades[i][0] - ciudades[j][0]) ** 2 + (ciudades[i][1] - ciudades[j][1]) ** 2)
    name = 'distancias/ciudades100.npy'
    np.save(name, array)


if __name__ == '__main__':
    generar_distancias()
    """
    num = 10
    cities = generar(num)
    nombre = guardar(cities, num)
    with open(nombre) as f:
        cs = json.load(f)
    print(cs)
    """
