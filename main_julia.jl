using Random
using Statistics
using Distributed
using SharedArrays

using JSON
# using Plots
using DataFrames
using CSV
using NPZ


mutable struct Individuo
    long_gen::Int
    genotipo::Vector{Int}
    valor::Float64  # O el tipo apropiado para tus valores

    function Individuo(long_gen)
        new(long_gen, [], Inf)
    end
end

    function init_aleatorio!(ind::Individuo)
        ind.genotipo = randperm(ind.long_gen)
        return ind
    end

    function asignar_genotipo!(ind::Individuo, genotipo)
        ind.genotipo = copy(genotipo)
        return ind
    end

    function asignar_valor!(ind::Individuo, valor)
        ind.valor = valor
        return ind
    end

    function mutar!(ind::Individuo)
        indices = randperm(ind.long_gen)[1:2]
        aux = ind.genotipo[indices[1]]
        ind.genotipo[indices[1]] = ind.genotipo[indices[2]]
        ind.genotipo[indices[2]] = aux
    end

    function eval!(ind::Individuo, distancias)
        valor = 0
        for i in 1:ind.long_gen-1
            valor += distancias[
                min(ind.genotipo[i], ind.genotipo[i + 1]),
                max(ind.genotipo[i], ind.genotipo[i + 1])
            ]
        end
        valor += distancias[
                min(ind.genotipo[1], ind.genotipo[ind.long_gen]),
                max(ind.genotipo[1], ind.genotipo[ind.long_gen])
            ]
        ind.valor = valor
    end

    function copiar(ind::Individuo)
        return Individuo(ind.long_gen) |> (x -> asignar_genotipo!(x, ind.genotipo)) |> (x -> asignar_valor!(x, ind.valor))
    end


mutable struct Poblacion
    num_individuos::Int
    num_ciudades::Int
    poblacion::Vector{Individuo}
    mejor_individuo::Individuo
            
    function Poblacion(num_individuos, num_ciudades)
        poblacion = [init_aleatorio!(Individuo(num_ciudades)) for _ in 1:num_individuos]
        mejor_individuo = copiar(seleccionar(poblacion))  # Seleccionar el mejor individuo inicial
        new(num_individuos, num_ciudades, poblacion, mejor_individuo)
    end
end
    
    function seleccion_padres!(pop::Poblacion, gamma)
        padres = Individuo[]
        pop.mejor_individuo = copiar(seleccionar(pop.poblacion))
        for i in 1:pop.num_individuos
            torneo_indices = randperm(length(pop.poblacion))[1:gamma]  # Generar índices aleatorios
            torneo = [pop.poblacion[idx] for idx in torneo_indices]  # Seleccionar individuos correspondientes a los índices
            push!(padres, copiar(seleccionar(torneo)))
        end
        pop.poblacion = padres
    end
                                
    function cruce_distr!(pop::Poblacion, prob_cruce)                            
        parejas = emparejar_padres(pop)
        hijos = Individuo[]
        parejas_cruce = Vector{Vector{Individuo}}()
        for pareja in parejas
            if rand() < prob_cruce
                push!(parejas_cruce, pareja)
            else
                append!(hijos, pareja)
            end
        end
        @distributed for i=1:length(parejas_cruce)
            parejas_cruce[i] = cruce_pm(parejas_cruce[i])
        end
        append!(hijos, [h[1] for h in parejas_cruce])
        append!(hijos, [h[2] for h in parejas_cruce])
        pop.poblacion = hijos
    end
                                    
    function cruce_!(pop::Poblacion, prob_cruce)
        parejas = emparejar_padres(pop)
        
        for i=1:length(parejas)
            if rand() < prob_cruce
                try
                    parejas[i] = cruce_pm(parejas[i])
                catch
                    println("ERROR DURANTE EL CRUCE")
                end
            end
        end
        pop.poblacion = append!([par_hijos[1] for par_hijos in parejas], [par_hijos[2] for par_hijos in parejas])
    end
                                    
    function cruce!(pop::Poblacion, prob_cruce)
        parejas = emparejar_padres(pop)
        hijos = Vector{Individuo}()
        
        for pareja in parejas
            if rand() < prob_cruce
                try
                    append!(hijos, cruce_pm(pareja))        
                catch
                    append!(hijos, pareja)
                    println("ERROR DURANTE EL CRUCE")
                end
            else
                append!(hijos, pareja)
            end
        end
        pop.poblacion = hijos
    end

    function emparejar_padres(pop::Poblacion)
        parejas = Vector{Vector{Individuo}}()
        for i in 1:pop.num_individuos ÷ 2
            push!(parejas, [
                copiar(pop.poblacion[2*i-1]),
                copiar(pop.poblacion[2*i])
            ])
        end
        return parejas
    end

    function cruce_pm(pareja)        
        inicio_segmento = rand(1:pareja[1].long_gen)
        final_segmento = rand(inicio_segmento + 1:pareja[1].long_gen)

        h0 = fill(-1, pareja[1].long_gen)
        h1 = fill(-1, pareja[1].long_gen)

        h0[inicio_segmento:final_segmento] .= pareja[1].genotipo[inicio_segmento:final_segmento]
        h1[inicio_segmento:final_segmento] .= pareja[2].genotipo[inicio_segmento:final_segmento]

        for i in setdiff(1:pareja[1].long_gen, inicio_segmento:final_segmento)
            if !(pareja[2].genotipo[i] in h0)
                h0[i] = pareja[2].genotipo[i]
            end
            if !(pareja[1].genotipo[i] in h1)
                h1[i] = pareja[1].genotipo[i]
            end
        end

        restante0 = Set([gen for gen in pareja[1].genotipo if gen ∉ h0 && gen in h1])
        restante1 = Set([gen for gen in pareja[2].genotipo if gen ∉ h1 && gen in h0])

        genes_indices_p1 = Dict(gen => idx for (idx, gen) in enumerate(pareja[2].genotipo))
        genes_indices_p0 = Dict(gen => idx for (idx, gen) in enumerate(pareja[1].genotipo))

        for gen in restante0
            gen_aux = gen
            while h0[genes_indices_p1[gen_aux]] !== -1
                gen_aux = pareja[1].genotipo[genes_indices_p1[gen_aux]]
            end
            h0[genes_indices_p1[gen_aux]] = gen
        end

        for gen in restante1
            gen_aux = gen
            while h1[genes_indices_p0[gen_aux]] !== -1
                gen_aux = pareja[2].genotipo[genes_indices_p0[gen_aux]]
            end
            h1[genes_indices_p0[gen_aux]] = gen
        end

        return [asignar_genotipo!(Individuo(pareja[1].long_gen), h0), asignar_genotipo!(Individuo(pareja[1].long_gen), h1)]
    end

    function mutacion!(pop::Poblacion, prob_mutacion)
        for ind in pop.poblacion
            if rand() < prob_mutacion
                mutar!(ind)
            end
        end
    end

    function seleccion_supervivientes!(pop::Poblacion)
        nuevo_mejor = seleccionar(pop.poblacion)
        if pop.mejor_individuo.valor < nuevo_mejor.valor
            peor = seleccionar(pop.poblacion, false)
            pop.poblacion = [p for p in pop.poblacion if p !== peor]
            push!(pop.poblacion, pop.mejor_individuo)
        end
    end

    function evaluar!(pop::Poblacion, distancias)
        for ind in pop.poblacion
            eval!(ind, distancias)
        end
    end

    function ejecutar_iteracion!(pop::Poblacion, gamma, prob_cruce, prob_mutacion, distancias)
        # t = time()
        seleccion_padres!(pop, gamma)
        cruce!(pop, prob_cruce)
        mutacion!(pop, prob_mutacion)
        evaluar!(pop, distancias)
        seleccion_supervivientes!(pop)
        # println("Tiempo: ", time() - t)
    end

    function media_y_desviacion(pop::Poblacion)
        valores = [ind.valor for ind in pop.poblacion]
        return sum(valores) / length(valores), std(valores)
    end

    function seleccionar(lista_individuos, mejor=true)
        seleccionado = lista_individuos[1]
        for ind in lista_individuos
            if (-1)^(mejor+1) * ind.valor < (-1)^(mejor+1) * seleccionado.valor
                seleccionado = ind
            end
        end
        return seleccionado
    end


mutable struct RunSimulation
    num_individuos::Int
    num_ciudades::Int
    gamma_torneo::Int
    prob_cruce::Float64
    prob_mutacion::Float64
    max_ite::Int
    individuos::Poblacion
    distancias::Array{Float64, 2}
    
    function RunSimulation(config_path, distancias_path)
        config = JSON.parsefile(config_path)
        new(config["num_individuos"], config["num_ciudades"], config["gamma_torneo"], config["prob_cruce"], config["prob_mutacion"],
            config["max_ite"], Poblacion(config["num_individuos"], config["num_ciudades"]), 
            npzread(distancias_path))
    end
end
    
    function simulate_probs(run_sim::RunSimulation, probs_cruce, ejecuciones, paciencia=100)
        for prob in probs_cruce
            for ej in ejecuciones
                path = "results/julia/$(run_sim.num_ciudades)ciudades_pc$(prob)_e$(ej).csv"
                df = DataFrame(Mejor=[], Media=[], Std=[], Mejor_ind=String[])
                run_sim.individuos = Poblacion(run_sim.num_individuos, run_sim.num_ciudades)
                evaluar!(run_sim.individuos, run_sim.distancias)
                mejor_media = Inf
                cont_paciencia = 0
                for i in 1:run_sim.max_ite
                    ejecutar_iteracion!(run_sim.individuos, run_sim.gamma_torneo, prob, run_sim.prob_mutacion, run_sim.distancias)
                    media_desviacion = media_y_desviacion(run_sim.individuos)
                    push!(df, [run_sim.individuos.mejor_individuo.valor, media_desviacion..., string(run_sim.individuos.mejor_individuo.genotipo)])
                    println("Prob ", prob, " Ejecucion ", ej, " Iteracion ", i, " Media ", media_desviacion[1])
                    if media_desviacion[1] < mejor_media
                        mejor_media = media_desviacion[1]
                        cont_paciencia = 0
                    else
                        cont_paciencia += 1
                        if cont_paciencia > paciencia
                            break
                        end
                    end
                    if i % 1000 == 0
                        CSV.write(path, df)
                    end
                end
            end
        end
    end


conf_path = "config.json"
distancias_path = "distancias/ciudades100.npy"

sim = RunSimulation(conf_path, distancias_path)
simulate_probs(sim, range(0.0, step=0.1, stop=1.0), [0,1,2,3,4])