from utils import get_transport_demands, calculate_least_distance_route


class Car:
  def __init__(self, id, location):
      self.id = id
      self.location = location # Maschinen ID bei dem das Auto ist
      self.load = True
      self.unload = False
      self.time = 0.0
      self.speed = 1

  def get_id(self):
      return self.id
  def get_location(self):
      return self.location
  def get_load_info(self):
      return self.load
  def get_unload_info(self):
      return self.unload
  def get_time(self):
      return self.time
  def set_load(self, load_status):
      self.load = load_status
  def set_unload(self, unload_status):
      self.unload = unload_status

  def calculate_time(self):
      _, distance = calculate_least_distance_route(self.location)
      travel_time = round(distance / self.speed, 2)
      self.time += travel_time

  def move_to(self, machine_position):
      self.location = machine_position
      self.calculate_time()
      self.print_status()

  def print_status(self):
      print(f"Car ID: {self.id}, Location: {self.location}, Load: {self.load}, Unload: {self.unload}, Time: {self.time}")


