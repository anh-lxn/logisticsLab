import pandas as pd

class Simulation:
  def __init__(self, network, cars: list):
    self.network = network
    self.cars = cars
    self.schedules = { car.id: pd.DataFrame(columns=["Location", "unload", "load"]) for car in cars } # für jedes auto ein schedule
    self.initial_total_demand = self.network.get_total_transport_demands()

  def get_car(self, car_id: int):
    return self.cars[car_id]

  def log_event(self, car_id, location, unload, load):
    """Fügt einen Eintrag zum Fahrplans des Autos hinzu"""
    df = self.schedules[car_id]
    new_row = {"Location": location, "unload": unload, "load": load}
    self.schedules[car_id].loc[len(df)] = new_row

  def show_schedule(self, car_id=None):
    """Zeigt entweder einen bestimmten oder alle Fahrpläne"""
    if car_id is not None:
        print(f"\n🚗 Schedule für Fahrzeug {car_id}:")
        print(self.schedules[car_id])
    else:
        for cid, df in self.schedules.items():
            print(f"\n🚗 Schedule für Fahrzeug {cid}:")
            print(df)

  def find_next_machine_with_open_demands(self, start_machine):
      df = self.network.transport_demand
      # 1️⃣ Aufträge vom aktuellen Standort
      start_demand = df[df["start"] == start_machine].reset_index(drop=True)

      if not start_demand.empty:
          start_demand["distance"] = start_demand["dest"].apply(
              lambda dest: self.network.get_distance_between(start_machine, dest))
          best_row = start_demand.loc[start_demand["distance"].idxmin()]
          return int(best_row["dest"])

      # 2️⃣ Falls keine Aufträge am aktuellen Standort → nächste Startmaschine suchen
      open_starts = df["start"].unique()
      if len(open_starts) == 0:
          return None  # wirklich alles erledigt

      # Distanz zu allen offenen Startmaschinen
      distances = {
          m: self.network.get_distance_between(start_machine, m)
          for m in open_starts
      }

      # 🧭 Nächste Maschine mit offenen Aufträgen (auch weit entfernt!)
      nearest_machine = min(distances, key=distances.get)
      return int(nearest_machine)

  """
  def start_sim(self):
    # Startzustand loggen
    for car in self.cars:
      self.log_event(car.id, car.position, 0, 1)

    while self.network.get_total_transport_demands() > 0: # Solange Aufträge da sind
      # Erteile jedem Auto einen Auftrag der gerade keinen hat
      for car in self.cars:
        # if car has no order
        if car.current_time == 0:
          best_machine = self.find_next_machine_with_open_demands(car.position)
          if best_machine is None:
            continue

          # Auftrag bearbeiten
          self.network.decrease_transport_demand(car.position, best_machine)
          car.current_time = self.network.get_time_between(car.position, best_machine)
          car.position = best_machine
          self.log_event(car.id, car.position, 1, 1)
        else:
          pass


      # Wer kann als nächstes fahren?
      next_car = min(self.cars, key=lambda car: car.current_time)
      min_time = next_car.current_time
      for car in self.cars: # Zeit aller Fahrzeuge um min_time verringern
        car.current_time -= min_time

      print(f"Verbleibende Aufträge: {self.network.get_total_transport_demands()}")
  """
  def start_sim(self, debug=True):
      # Initialisieren: alle Autos aktiv & Startzustand loggen
      for car in self.cars:
          car.active = True
          car.completed_jobs = 0
          self.log_event(car.id, car.position, 0, 1)
          if debug:
              print(f"🚗 Init: Car {car.id} startet an Maschine {car.position}")

      step = 0

      while self.network.get_total_transport_demands() > 0:
          step += 1
          if debug:
              print(f"\n🕒 Schritt {step} | Offene Aufträge: {self.network.get_total_transport_demands()}")

          # 1️⃣ Allen aktiven & freien Autos neue Aufträge geben
          for car in self.cars:
              if not car.active:
                  if debug:
                      print(f"🅿️ Car {car.id}: steht inaktiv bei Maschine {car.position}.")
                  continue

              if car.current_time > 0:
                  if debug:
                      print(f"⏳ Car {car.id}: fährt noch ({car.current_time:.2f}s verbleibend)")
                  continue

              # Auto ist frei → neuen Auftrag suchen
              best_machine = self.find_next_machine_with_open_demands(car.position)

              if best_machine is None:
                  car.active = False
                  if debug:
                      print(f"🛑 Car {car.id}: keine offenen Aufträge mehr. "
                            f"Bleibt an Maschine {car.position}.")
                  continue

              # Fahrtdaten
              travel_time = self.network.get_time_between(car.position, best_machine)
              dist = self.network.get_distance_between(car.position, best_machine)

              # Prüfen, ob echter Auftrag existiert
              df = self.network.transport_demand
              is_real_order = ((df["start"] == car.position) & (df["dest"] == best_machine)).any()

              old_position = car.position
              car.position = best_machine
              car.current_time = travel_time

              # --- Fahrt-Logik ---
              if is_real_order:
                  # ↓ Auftrag ausführen
                  self.network.decrease_transport_demand(old_position, best_machine)
                  car.completed_jobs += 1

                  # Prüfen, ob am Ziel neue Aufträge starten → unload+load = (1,1)
                  has_new_orders = (self.network.transport_demand["start"] == best_machine).any()

                  unload = 1
                  load = 1 if has_new_orders else 0
                  self.log_event(car.id, best_machine, unload, load)

                  if debug:
                      print(f"✅ Car {car.id}: Transport {old_position} → {best_machine} "
                            f"(Distanz={dist:.2f}, Zeit={travel_time:.2f}) | unload={unload}, load={load}")

              else:
                  # 🚗 Nur Transferfahrt (kein echter Auftrag)
                  self.log_event(car.id, best_machine, 1, 0)
                  if debug:
                      print(f"🚗 Car {car.id}: Transferfahrt {old_position} → {best_machine} "
                            f"(Distanz={dist:.2f}, Zeit={travel_time:.2f}) – kein Auftrag")

              # Wenn alles erledigt → abbrechen
              if self.network.get_total_transport_demands() == 0:
                  if debug:
                      print("🟢 Letzter Auftrag abgeschlossen – Simulation endet.")
                  break

          # 2️⃣ Zeit fortschreiben
          next_car = min(self.cars, key=lambda c: c.current_time)
          min_time = next_car.current_time

          if min_time > 0:
              for car in self.cars:
                  car.current_time = max(0, car.current_time - min_time)

              if debug:
                  print(f"⏩ Zeit fortgeschrieben um {min_time:.2f} Einheiten")
                  for car in self.cars:
                      print(f"   └─ Car {car.id}: neue Restzeit {car.current_time:.2f}")

          # 3️⃣ Debug: offene Aufträge
          if debug:
              print("📦 Aktuelle Transportaufträge:")
              if len(self.network.transport_demand) > 0:
                  print(self.network.transport_demand.to_string(index=False))
              else:
                  print("   (Keine offenen Aufträge mehr)")

          # 4️⃣ Fortschritt
          if debug:
              print("📊 Bisher erledigte Aufträge pro Fahrzeug:")
              for car in self.cars:
                  print(f"   └─ Car {car.id}: {car.completed_jobs}")

      # ✅ Simulation beendet
      if debug:
          print("\n✅ Simulation abgeschlossen.")
          total_jobs = sum(car.completed_jobs for car in self.cars)
          print(f"📦 Insgesamt bearbeitete Aufträge: {total_jobs}")
          for car in self.cars:
              status = "aktiv" if car.active else "inaktiv"
              print(f"🚘 Car {car.id}: Endposition {car.position} ({status}) – erledigt: {car.completed_jobs}")
