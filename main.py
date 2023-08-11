from genetic_alg import Poblacion

import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import time


class RunSimulation:
    def __init__(self, config_path, cities_path=None, distancias_path=None):
        with open(config_path) as f:
            config = json.load(f)
        self.num_individuos = config['num_individuos']
        self.num_ciudades = config['num_ciudades']
        self.gamma_torneo = config['gamma_torneo']
        self.prob_cruce = config['prob_cruce']
        self.prob_mutacion = config['prob_mutacion']
        self.max_ite = config['max_ite']

        self.individuos = Poblacion(self.num_individuos, self.num_ciudades)
        with open(cities_path) as f:
            self.ciudades = json.load(f)

        self.distancias = np.load(distancias_path)

    def simulate(self, paciencia=10):
        mejor = []
        media = []
        stdev = []
        self.individuos.evaluar(self.distancias)
        mejor_media = np.inf
        cont_paciencia = 0
        for i in range(self.max_ite):
            print(i)
            self.individuos.ejecutar_iteracion(self.gamma_torneo, self.prob_cruce, self.prob_mutacion, self.distancias)
            mejor.append(self.individuos.mejor_individuo.valor)
            media_y_desviacion = self.individuos.media_y_desviacion()
            print(media_y_desviacion[0])
            media.append(media_y_desviacion[0])
            stdev.append(media_y_desviacion[1])
            if media_y_desviacion[0] < mejor_media:
                mejor_media = media_y_desviacion[0]
                cont_paciencia = 0
            else:
                cont_paciencia += 1
                if cont_paciencia > paciencia:
                    break
        plt.plot(mejor)
        plt.errorbar(range(len(mejor)), media, yerr=stdev)
        plt.show()
        print(mejor[len(mejor)-1])
        self.representar_solucion(self.individuos.mejor_individuo)

    def simulate_probs(self, probs_cruce, ejecuciones, paciencia=10):
        for prob in probs_cruce:
            print('Probabilidad de cruce: ', prob)
            for ej in ejecuciones:
                print('EJECUCION ', ej)
                df = pd.DataFrame(index=range(self.max_ite), columns=['Mejor', 'Media', 'Std', 'Mejor ind'])
                self.individuos = Poblacion(self.num_individuos, self.num_ciudades)
                self.individuos.evaluar(self.distancias)
                mejor_media = np.inf
                cont_paciencia = 0
                for i in range(self.max_ite):
                    print(i)
                    self.individuos.ejecutar_iteracion(self.gamma_torneo, prob, self.prob_mutacion, self.distancias)
                    media_desviacion = self.individuos.media_y_desviacion()
                    df.iloc[i] = [
                        self.individuos.mejor_individuo.valor,
                        *media_desviacion,
                        self.individuos.mejor_individuo.genotipo
                             ]
                    print(media_desviacion[0])
                    if media_desviacion[0] < mejor_media:
                        mejor_media = media_desviacion[0]
                        cont_paciencia = 0
                    else:
                        cont_paciencia += 1
                        if cont_paciencia > paciencia:
                            break
                path = 'results/' + str(self.num_ciudades) + 'ciudades_pc' + str(prob) + '_e' + str(ej) + '.csv'
                df.to_csv(path)

    def representar_solucion(self, individuo):
        ciudad_x = [ciudad[0] for ciudad in self.ciudades]
        ciudad_y = [ciudad[1] for ciudad in self.ciudades]
        plt.figure()
        plt.scatter(ciudad_x, ciudad_y)
        plt.plot(
            [ciudad_x[ind] for ind in individuo.genotipo],
            [ciudad_y[ind] for ind in individuo.genotipo]
        )
        plt.show()


if __name__ == '__main__':
    conf_path = 'config.json'
    path_ciudades = 'data/ciudades10000.json'
    distancias_path = 'distancias/ciudades10000.npy'

    # RunSimulation(conf_path, path_ciudades, distancias_path).simulate(paciencia=2)

    RunSimulation(conf_path, path_ciudades, distancias_path).simulate_probs(
        np.linspace(1, 0, 11),
        [3]
    )


