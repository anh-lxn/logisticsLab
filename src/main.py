from network import Network
from simulation import Simulation
from car import Car
from utils import *

machine_positions, transport_demand = read_txt_files()

# Network

network = Network(machine_positions, transport_demand)

# Carsn
car1 = Car(car_id=1, position=1)
car2 = Car(car_id=2, position=2)
car3 = Car(car_id=3, position=3)
cars = [car1, car2, car3]


# Simulation
simulation = Simulation(network, cars)
simulation.start_sim()
simulation.show_schedule()
total_fahrten = sum(len(df) - 1 for df in simulation.schedules.values())  # -1 für die Init-Zeile pro Auto
print(f"🚚 Gesamt bearbeitete Fahrten: {total_fahrten}")
print(f"📦 Erwartet laut Transportdemand: {simulation.initial_total_demand}")

