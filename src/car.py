class Car:
  def __init__(self, car_id: int, position: int):
    self.id = car_id
    self.position = position
    self.current_time = 0 # Current time for the car to get to the next machine
    self.active = False