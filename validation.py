import pandas as pd
import matplotlib.pyplot as plt
import glob
import xarray as xr


def main(num_ciudades):
    files = glob.glob('results/' + str(num_ciudades) + 'c*.csv')
    arrs = [xr.Dataset.from_dataframe(pd.read_csv(f)).expand_dims(dim={
        "pc": [float(f.split('pc')[1].split('_')[0])],
        "ej": [int(f.split('_e')[1].split('.')[0])]
    }, axis=[0, 1]) for f in files]

    ar = xr.merge(arrs)

    pcs = []
    for pc in ar.coords['pc']:
        ar['Mejor'].sel(pc=pc).mean(dim=['ej']).plot()
        pcs.append(float(pc))
    plt.legend(pcs)
    plt.show()
    # print(ar['Mejor'].sel(index=9999).mean(dim=['ej']))


if __name__ == '__main__':
    main(100)

