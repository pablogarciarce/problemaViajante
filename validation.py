import pandas as pd
import matplotlib.pyplot as plt
import glob
import numpy as np

import xarray as xr


def transformar(num_ciudades=10000):
    files = glob.glob('results/python/' + str(num_ciudades) + 'c*.csv')
    for f in files:
        df = pd.read_csv(f)
        if 'Mejor_ind' in df.columns:
            df = df.drop(columns=['Mejor_ind'])
        elif 'Mejor ind' in df.columns:
            df = df.drop(columns=['Mejor ind'])
        path = '/'.join(['results', f.split('\\')[-1]])
        print(path)
        df.to_csv(path)


def main(num_ciudades):
    files = glob.glob('results/asdf/' + str(num_ciudades) + 'c*.csv')
    arrs = [xr.Dataset.from_dataframe(pd.read_csv(f)).expand_dims(dim={
        "pc": [float(f.split('pc')[1].split('_')[0])],
        "ej": [int(f.split('_e')[1].split('.')[0])]
    }, axis=[0, 1]) for f in files]

    ar = xr.merge(arrs)

    pcs = []
    for pc in ar.coords['pc']:
        ar['Mejor'].sel(pc=pc).mean(dim=['ej'], skipna=False).plot()
        pcs.append(float(pc))
    plt.xlabel('Iteración')
    plt.ylabel('Distancia total recorrida')
    plt.legend(pcs)
    plt.show()

    # plot de la ultima iteracion para el mejor individuo con desviacion estandar
    # es necesario tener en cuenta la parada temprana (no vale con quedarnos con la ultima iteracion)
    dict_valores = {pc/10: [] for pc in range(11)}

    for arr in arrs:
        sin_nan = arr.dropna(dim='index')
        dict_valores[float(sin_nan.coords['pc'])].append(float(sin_nan['Mejor'].sel(index=sin_nan.sizes['index']-1)))

    plt.errorbar(
        dict_valores.keys(),
        [np.mean(val) for val in dict_valores.values()],
        yerr=[np.std(val) for val in dict_valores.values()]
    )
    plt.xlabel('Probabilidad de cruce')
    plt.ylabel('Distancia total recorrida')
    plt.show()


def plot_pc(num_ciudades):
    files = glob.glob('results/' + str(num_ciudades) + 'c*.csv')
    arrs = [xr.Dataset.from_dataframe(pd.read_csv(f)).expand_dims(dim={
        "pc": [float(f.split('pc')[1].split('_')[0])],
        "ej": [int(f.split('_e')[1].split('.')[0])]
    }, axis=[0, 1]) for f in files]

    ar = xr.merge(arrs)

    for pc in ar.coords['pc']:
        print(pc)
        for e in ar.coords['ej']:
            ar['Mejor'].sel(pc=pc).sel(ej=e).plot()
        plt.xlabel('Iteración')
        plt.ylabel('Distancia total recorrida')
        plt.legend(ar.coords['ej'].values)
        plt.show()


if __name__ == '__main__':
    main(100)

