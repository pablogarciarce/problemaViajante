import json
import random
import math
import statistics
import time
import multiprocessing
from joblib import Parallel, delayed
import julia
from julia.api import Julia

# Inicializa la conexión a Julia
julia.install()
julia_compatible = Julia(compiled_modules=False)

# Define el código de Julia dentro de un string
codigo_julia = """
module MyJuliaModule
    export cruce_pm
    
    function cruce_pm(pareja::Tuple{Vector{Int}, Vector{Int}})
        inicio_segmento = rand(1:length(pareja[1]))
        final_segmento = rand(inicio_segmento+1:length(pareja[1]))
        
        genes_indices_p1 = Dict(gen => idx for (idx, gen) in enumerate(pareja[2]))
        genes_indices_p0 = Dict(gen => idx for (idx, gen) in enumerate(pareja[1]))
        
        h0 = fill(-1, length(pareja[1]))
        h1 = fill(-1, length(pareja[2]))
    
        h0[inicio_segmento:final_segmento] = pareja[1][inicio_segmento:final_segmento]
        h1[inicio_segmento:final_segmento] = pareja[2][inicio_segmento:final_segmento]
    
        for i in union(1:inicio_segmento, final_segmento+1:length(pareja[1]))
            gen_p1 = pareja[2][i]
            gen_p0 = pareja[1][i]
            
            if gen_p1 ∉ h0
                h0[i] = gen_p1
            end
            
            if gen_p0 ∉ h1
                h1[i] = gen_p0
            end
        end
    
        restante0 = [gen for gen in pareja[1] if gen ∉ h0 && gen in h1]
        restante1 = [gen for gen in pareja[2] if gen ∉ h1 && gen in h0]
    
        for gen in restante0
            gen_aux = gen
            while h0[genes_indices_p1[gen_aux]] !== -1
                gen_aux = pareja[1][genes_indices_p1[gen_aux]]
            end
            h0[genes_indices_p1[gen_aux]] = gen
        end
    
        for gen in restante1
            gen_aux = gen
            while h1[genes_indices_p0[gen_aux]] !== -1
                gen_aux = pareja[2][genes_indices_p0[gen_aux]]
            end
            h1[genes_indices_p0[gen_aux]] = gen
        end
    
        return [h0, h1]
    end
end
"""

# Evalúa el código de Julia
julia_compatible.eval(codigo_julia)


# Define la función de cruce parcialmente mapeado en Julia usando PyCall
def cruce_pm_julia(pareja):
    genotipos = (
        [gen + 1 for gen in pareja[0].genotipo],
        [gen + 1 for gen in pareja[1].genotipo])
    # Llama a la función cruce_pm en Julia directamente desde Python
    julia_compatible.eval("@eval Main using .MyJuliaModule")
    genotipos_hijos = julia_compatible.eval("Main.MyJuliaModule.cruce_pm")(genotipos)
    h1 = [gen - 1 for gen in genotipos_hijos[0]]
    h2 = [gen - 1 for gen in genotipos_hijos[1]]
    return [pareja[0].copiar().asignar_genotipo(h1),
            pareja[1].copiar().asignar_genotipo(h2)]


class Individuo:
    def __init__(self, long_gen):
        self.long_gen = long_gen
        self.genotipo = []
        self.valor = None

    def init_aleatorio(self):
        self.genotipo = list(range(self.long_gen))
        random.shuffle(self.genotipo)
        return self

    def asignar_genotipo(self, genotipo):
        self.genotipo = genotipo.copy()
        return self

    def asignar_valor(self, valor):
        self.valor = valor
        return self

    def mutar(self):
        indices = random.sample(range(self.long_gen), 2)
        aux = self.genotipo[indices[0]]
        self.genotipo[indices[0]] = self.genotipo[indices[1]]
        self.genotipo[indices[1]] = aux

    def eval(self, distancias):
        valor = 0
        for i in range(self.long_gen - 1):
            valor += distancias[
                min(self.genotipo[i], self.genotipo[i + 1]),
                max(self.genotipo[i], self.genotipo[i + 1])
            ]
        valor += distancias[
                min(self.genotipo[0], self.genotipo[self.long_gen-1]),
                max(self.genotipo[0], self.genotipo[self.long_gen-1])
            ]
        self.valor = valor

    def copiar(self):
        return Individuo(self.long_gen).asignar_genotipo(self.genotipo).asignar_valor(self.valor)


class Poblacion:
    def __init__(self, num_individuos, num_ciudades, distancias):
        self.num_individuos = num_individuos
        self.num_ciudades = num_ciudades
        self.poblacion = [Individuo(num_ciudades).init_aleatorio() for _ in range(num_individuos)]
        self.evaluar(distancias)
        self.mejor_individuo = seleccionar(self.poblacion).copiar()

    def seleccion_padres(self, gamma):
        padres = []
        for i in range(self.num_individuos):
            torneo = random.sample(self.poblacion, gamma)
            padres.append(seleccionar(torneo).copiar())
        self.poblacion = padres

    def cruce(self, prob_cruce):
        parejas = self.emparejar_padres()
        hijos = []
        parejas_cruce = []
        for pareja in parejas:
            if random.random() < prob_cruce:
                parejas_cruce.append(pareja)
            else:
                hijos = hijos + pareja
        # num_cores = multiprocessing.cpu_count()
        extra_hijos = Parallel(n_jobs=8)(delayed(self.cruce_pm)(p) for p in parejas)
        hijos = hijos + [h[0] for h in extra_hijos] + [h[1] for h in extra_hijos]
        self.poblacion = hijos

    def cruce_julia(self, prob_cruce):
        parejas = self.emparejar_padres()
        hijos = []
        parejas_cruce = []
        for pareja in parejas:
            if random.random() < prob_cruce:
                parejas_cruce.append(pareja)
            else:
                hijos = hijos + pareja
        # Llamada a la función de cruce parcialmente mapeado en Julia
        julia_compatible.eval("using .MyJuliaModule")
        # num_cores = multiprocessing.cpu_count()
        # extra_hijos = Parallel(n_jobs=8)(delayed(cruce_pm_julia)(p) for p in parejas_cruce)
        try:
            extra_hijos = [cruce_pm_julia(p.copy()) for p in parejas_cruce]
        except:
            print('ERROR DE JULIA DURANTE EL CRUCE')
            extra_hijos = parejas_cruce

        hijos = hijos + [h[0] for h in extra_hijos] + [h[1] for h in extra_hijos]
        self.poblacion = hijos

    def emparejar_padres(self):
        parejas = []
        for i in range(int(len(self.poblacion) / 2)):
            parejas.append([
                self.poblacion[2 * i].copiar(),
                self.poblacion[2 * i + 1].copiar()
            ])
        return parejas

    def cruce_pm(self, pareja):
        inicio_segmento = random.randint(0, self.num_ciudades - 1)
        final_segmento = random.randint(inicio_segmento + 1, self.num_ciudades)

        h0 = [None] * self.num_ciudades
        h1 = [None] * self.num_ciudades
        # se asignan los segmentos
        h0[inicio_segmento:final_segmento] = pareja[0].genotipo[inicio_segmento:final_segmento]
        h1[inicio_segmento:final_segmento] = pareja[1].genotipo[inicio_segmento:final_segmento]

        # se asigna la parte que no esta en ningun segmento
        for i in set(range(inicio_segmento)) | set(range(final_segmento, self.num_ciudades)):
            if pareja[1].genotipo[i] not in h0:
                h0[i] = pareja[1].genotipo[i]
            if pareja[0].genotipo[i] not in h1:
                h1[i] = pareja[0].genotipo[i]

        # se asigna el resto, pertenecientes al segmento del otro padre
        restante0 = [gen for gen in pareja[0].genotipo if gen not in h0 and gen in h1]
        restante1 = [gen for gen in pareja[1].genotipo if gen not in h1 and gen in h0]

        genes_indices_p1 = {gen: idx for idx, gen in enumerate(pareja[1].genotipo)}
        genes_indices_p0 = {gen: idx for idx, gen in enumerate(pareja[0].genotipo)}

        for gen in restante0:
            gen_aux = gen
            while h0[genes_indices_p1[gen_aux]] is not None:
                gen_aux = pareja[0].genotipo[genes_indices_p1[gen_aux]]
            h0[genes_indices_p1[gen_aux]] = gen
        for gen in restante1:
            gen_aux = gen
            while h1[genes_indices_p0[gen_aux]] is not None:
                gen_aux = pareja[1].genotipo[genes_indices_p0[gen_aux]]
            h1[genes_indices_p0[gen_aux]] = gen

        return [Individuo(self.num_ciudades).asignar_genotipo(h0), Individuo(self.num_ciudades).asignar_genotipo(h1)]

    def mutacion(self, prob_mutacion):
        for ind in self.poblacion:
            if random.random() < prob_mutacion:
                ind.mutar()

    def seleccion_supervivientes(self):
        nuevo_mejor = seleccionar(self.poblacion)
        if self.mejor_individuo.valor < nuevo_mejor.valor:
            self.poblacion.remove(seleccionar(self.poblacion, mejor=False))
            self.poblacion.append(self.mejor_individuo.copiar())
        else:
            self.mejor_individuo = nuevo_mejor.copiar()

    def evaluar(self, distancias):
        for ind in self.poblacion:
            ind.eval(distancias)

    def ejecutar_iteracion(self, gamma, prob_cruce, prob_mutacion, distancias):
        t = time.time()
        self.seleccion_padres(gamma)
        self.cruce_julia(prob_cruce)
        self.mutacion(prob_mutacion)
        self.evaluar(distancias)
        self.seleccion_supervivientes()
        print('Tiempo iteración: ', time.time() - t)

    def media_y_desviacion(self):
        valores = [ind.valor for ind in self.poblacion]
        return sum(valores) / len(valores), statistics.stdev(valores)


def seleccionar(lista_individuos, mejor=True):
    seleccionado = lista_individuos[0]
    for ind in lista_individuos:
        if (-1)**(mejor+1) * ind.valor < (-1)**(mejor+1) * seleccionado.valor:
            seleccionado = ind
    return seleccionado








