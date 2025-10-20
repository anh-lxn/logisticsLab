from car import Car
from utils import calculate_least_distance_route

car1 = Car(id=1, location=10)

car1.print_status()
dest_machine, _ = calculate_least_distance_route(car1.get_location())
car1.move_to(dest_machine)
car1.print_status()


