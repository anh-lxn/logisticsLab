from network import Network
from simulation import Simulation
from car import Car
from utils import read_txt_files

machine_positions, transport_demand = read_txt_files()

# Network

network = Network(machine_positions, transport_demand)

# Carsn
car1 = Car(car_id=1, position=1)
#car2 = Car(car_id=2, position=2)
#car3 = Car(car_id=3, position=3)
#car4 = Car(car_id=4, position=4)
#car5 = Car(car_id=5, position=5)
#car6 = Car(car_id=6, position=6)
#car7 = Car(car_id=7, position=7)
#car8 = Car(car_id=8, position=8)
#car9 = Car(car_id=9, position=9)
#car10 = Car(car_id=10, position=10)
#cars = [car1, car2, car3, car4, car5, car6, car7, car8, car9, car10]
cars = [car1]


# Simulation
simulation = Simulation(network, cars)
simulation.start_sim()
simulation.show_schedule()
total_fahrten = sum(len(df) - 1 for df in simulation.schedules.values())  # -1 für die Init-Zeile pro Auto
print(f"🚚 Gesamt bearbeitete Fahrten: {total_fahrten}")
print(f"📦 Erwartet laut Transportdemand: {simulation.initial_total_demand}")

