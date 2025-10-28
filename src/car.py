class Car:
  def __init__(self, car_id: int, position: int):
    self.id = car_id
    self.old_position = position
    self.position = position
    self.leerfahrt = False
    self.completed_jobs = 0

    self.unload = 0
    self.load = 1