# ga_optimization.py

import random
import numpy as np
from deap import base, creator, tools, algorithms
from production_model import Database, ProductionModel

# ---------------------------
# 1. Initialize the Production Model
# ---------------------------

def initialize_model(db_path):
    db = Database(db_path)
    model = ProductionModel(db)
    return model, db

# ---------------------------
# 2. Define the GA Components
# ---------------------------

def setup_ga(model):
    # Create Fitness and Individual Classes
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))  # Minimization
    creator.create("Individual", list, fitness=creator.FitnessMin)
    
    # Initialize Toolbox
    toolbox = base.Toolbox()
    
    # Attribute Generators
    technology_ids = list(model.technologies['id'])
    toolbox.register("tech_id", random.choice, technology_ids)
    toolbox.register("production_capacity", random.uniform, 0, model.P_max)
    
    # Structure Initializers
    toolbox.register("individual", tools.initCycle, creator.Individual,
                     (toolbox.tech_id, toolbox.production_capacity), n=1)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
    # Fitness Function
    def evaluate_individual(individual):
        solution = tuple(individual)
        return model.fitness_function(solution)
    
    toolbox.register("evaluate", evaluate_individual)
    toolbox.register("mate", tools.cxUniform, indpb=0.5)
    toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=50, indpb=0.2)
    toolbox.register("select", tools.selTournament, tournsize=3)
    
    return toolbox

# ---------------------------
# 3. Run the GA
# ---------------------------

def run_ga(toolbox, model, population_size=50, generations=40, cxpb=0.7, mutpb=0.2):
    # Statistics
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("min", np.min)
    stats.register("max", np.max)
    
    # Hall of Fame to store the best individuals
    hof = tools.HallOfFame(1)
    
    # Initialize Population
    population = toolbox.population(n=population_size)
    
    # Run GA
    algorithms.eaSimple(population, toolbox, cxpb, mutpb, generations, stats=stats, halloffame=hof, verbose=True)
    
    # Retrieve the best solution
    best = hof[0]
    best_cost = model.fitness_function(tuple(best))[0]
    print(f"\nBest Solution: Technology ID = {best[0]}, Production Capacity = {best[1]:.2f} kg/day")
    print(f"Total Cost: {best_cost:.2f} GBP")
    
    return best, best_cost

# ---------------------------
# 4. Main Execution
# ---------------------------

if __name__ == "__main__":
    # Path to your SQLite database
    db_path = '/Users/jackspencer/Documents/Projects/Nanocellulose/nanocellulose_production.db'
    
    # Initialize the production model
    model, db = initialize_model(db_path)
    
    # Setup GA
    toolbox = setup_ga(model)
    
    # Run GA
    best_solution, best_cost = run_ga(toolbox, model)
    
    # Close the database connection
    db.close_connection()