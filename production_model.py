# production_model.py

import sqlite3
import pandas as pd
import numpy as np

class Database:
    def __init__(self, db_path):
        """
        Initialize the database connection.

        :param db_path: Path to the SQLite database file.
        """
        self.conn = sqlite3.connect(db_path)
    
    def fetch_technologies(self):
        """
        Fetch technology data from the Technologies table.

        :return: pandas DataFrame containing technologies data.
        """
        query = "SELECT * FROM Technologies"
        technologies = pd.read_sql_query(query, self.conn)
        return technologies
    
    def fetch_materials(self):
        """
        Fetch material data from the Materials table.

        :return: pandas DataFrame containing materials data.
        """
        query = "SELECT * FROM Materials"
        materials = pd.read_sql_query(query, self.conn)
        return materials
    
    def fetch_quality_metrics(self):
        """
        Fetch quality metrics data from the QualityMetrics table.

        :return: pandas DataFrame containing quality metrics data.
        """
        query = "SELECT * FROM QualityMetrics"
        quality_metrics = pd.read_sql_query(query, self.conn)
        return quality_metrics
    
    def close_connection(self):
        """
        Close the database connection.
        """
        self.conn.close()

class ProductionModel:
    def __init__(self, db: Database):
        """
        Initialize the production model with data from the database.

        :param db: An instance of the Database class.
        """
        self.technologies = db.fetch_technologies()
        self.materials = db.fetch_materials()
        self.quality_metrics = db.fetch_quality_metrics()
        
        # Calculate Biomass Procurement and Preprocessing Cost per kg
        self.C_B = self.materials['cost'].sum()  # Sum if multiple materials are used
        
        # Extract Quality Metrics by metric name for clarity
        metrics = self.quality_metrics.set_index('metric')['threshold'].to_dict()
        self.Q_min = metrics.get('Q_min', 400.0)  # Default value if not found
        self.E_max = metrics.get('E_max', 2500.0)
        self.P_max = metrics.get('P_max', 1000.0)
        self.C_E = metrics.get('C_E', 0.15)
        
    def calculate_quality(self, technology_id, y):
        """
        Calculate the quality index based on the selected technology and production parameters.

        :param technology_id: ID of the selected technology.
        :param y: Daily production capacity (kg/day).
        :return: Quality index (Q).
        """
        # Placeholder function: define actual quality calculation based on technology
        # For demonstration, assume Q is a function of technology efficiency and production capacity
        tech = self.technologies[self.technologies['id'] == technology_id].iloc[0]
        Q = tech['efficiency_factor'] * y  # Example formula
        return Q
    
    def objective_function(self, solution):
        """
        Calculate the total production cost for a given solution.

        :param solution: Tuple containing (technology_id, y)
        :return: Total cost (float)
        """
        technology_id, y = solution
        tech = self.technologies[self.technologies['id'] == technology_id].iloc[0]
        
        C_Ti = tech['capital_cost']
        C_Oi = tech['operational_cost']
        E_i = tech['energy_consumption_rate']
        
        # Total Capital Cost: Assume capital cost is a one-time cost; for GA, it might be treated differently
        # Here, we include it in the daily cost for simplicity
        total_capital_cost = C_Ti  # Could be amortized over time
        
        # Total Operational Cost
        total_operational_cost = C_Oi * y  # Assuming operational cost scales with production
        
        # Total Energy Cost
        total_energy_cost = self.C_E * E_i * y
        
        # Total Biomass Cost
        total_biomass_cost = self.C_B * y
        
        # Total Cost
        total_cost = total_capital_cost + total_operational_cost + total_energy_cost + total_biomass_cost
        return total_cost
    
    def is_feasible(self, solution):
        """
        Check if a given solution satisfies all constraints.

        :param solution: Tuple containing (technology_id, y)
        :return: Tuple (is_feasible: bool, penalty: float)
        """
        technology_id, y = solution
        tech = self.technologies[self.technologies['id'] == technology_id].iloc[0]
        
        # Production Capacity Constraint
        capacity_feasibility = y <= self.P_max
        
        # Energy Consumption Constraint
        energy_consumption = tech['energy_consumption_rate'] * y
        energy_feasibility = energy_consumption <= self.E_max
        
        # Quality Standards Constraint
        Q = self.calculate_quality(technology_id, y)
        quality_feasibility = Q >= self.Q_min
        
        # Non-Negativity Constraint
        non_negativity = y >= 0
        
        # Check all constraints
        is_feasible = all([capacity_feasibility, energy_feasibility, quality_feasibility, non_negativity])
        
        # Calculate penalty for infeasible solutions (if any)
        penalty = 0
        if not capacity_feasibility:
            penalty += (y - self.P_max) * 1000  # Arbitrary penalty multiplier
        if not energy_feasibility:
            penalty += (energy_consumption - self.E_max) * 1000
        if not quality_feasibility:
            penalty += (self.Q_min - Q) * 1000
        if not non_negativity:
            penalty += (-y) * 1000  # y should be >=0
        
        return is_feasible, penalty
    
    def fitness_function(self, solution):
        """
        Calculate the fitness of a solution for the Genetic Algorithm.

        :param solution: Tuple containing (technology_id, y)
        :return: Fitness value (float)
        """
        total_cost = self.objective_function(solution)
        is_feasible, penalty = self.is_feasible(solution)
        
        if is_feasible:
            return total_cost,
        else:
            # Penalize infeasible solutions by adding a large penalty
            return total_cost + penalty,

# The following block is removed/commented out to prevent execution during import
# if you wish to run it independently, uncomment it.

# if __name__ == "__main__":
#     # Path to your SQLite database
#     db_path = 'nanocellulose_production.db'
    
#     # Initialize the database connection
#     db = Database(db_path)
    
#     # Initialize the production model
#     model = ProductionModel(db)
    
#     # Example solution: (technology_id, y)
#     example_solution = (1, 500)  # Replace with actual technology ID and production capacity
    
#     # Calculate fitness
#     fitness = model.fitness_function(example_solution)
#     print(f"Fitness (Total Cost): {fitness[0]:.2f} GBP")
    
#     # Check feasibility
#     is_feasible, penalty = model.is_feasible(example_solution)
#     print(f"Is Feasible: {is_feasible}")
#     if not is_feasible:
#         print(f"Penalty: {penalty:.2f}")
    
#     # Close the database connection
#     db.close_connection()