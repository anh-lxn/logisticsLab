import pandas as pd
import os
import time

class Simulation:
  def __init__(self, network, cars: list):
    self.network = network
    self.cars = cars
    self.schedules = { car.id: pd.DataFrame(columns=["Location", "unload", "load"]) for car in cars } # für jedes auto ein schedule
    self.temp_df = self.network.transport_demand.copy()

    self.initial_total_demand = self.network.get_total_transport_demands()
    # 1️⃣ Pfad definieren
    git_dir = os.getcwd()
    data_dir = os.path.join(git_dir, 'data')
    self.schedule_path = os.path.join(data_dir, "schedule.txt")

  def get_car(self, car_id: int):
    return self.cars[car_id]

  def log_event(self, car_id, location, unload, load):
    """Fügt einen Eintrag zum Fahrplans des Autos hinzu"""
    df = self.schedules[car_id]
    new_row = {"Location": location, "unload": unload, "load": load}
    self.schedules[car_id].loc[len(df)] = new_row

  def change_last_event(self, car_id):
    df = self.schedules[car_id]
    if df.empty:
        return
    last_idx = df.index[-1]
    old_position = df.loc[last_idx, "Location"]
    df.loc[last_idx, ["Location", "unload", "load"]] = [old_position, 1, 0]

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
  def _is_real_order(self, start, dest):
    df = self.network.transport_demand
    return ((df["start"] == start) & (df["dest"] == dest)).any()

  def _has_new_from(self, start):
    df = self.network.transport_demand
    return (df["start"] == start).any()

  def _advance_time(self):
    # kleinste positive Restzeit aller TRAVEL-Autos
    active_times = [c.current_time for c in self.cars if getattr(c, "state", "IDLE") == "TRAVEL" and c.current_time > 0]
    if not active_times:
        return 0.0
    dt = min(active_times)
    for c in self.cars:
        if getattr(c, "state", "IDLE") == "TRAVEL":
            c.current_time = max(0.0, c.current_time - dt)
    return dt

  def decrease_temp_demand(self, start_machine, dest_machine, amount=1):
    condition = (self.temp_df["start"] == start_machine) & (self.temp_df["dest"] == dest_machine) # Zeile bei der es True ist
    self.temp_df.loc[condition, "number"] -= amount
    self._update_temp_demand()

  def _update_temp_demand(self): # static
    self.temp_df = self.temp_df[self.temp_df["number"] != 0].reset_index(drop=True) # updating so there is no 0 demand in the dataframe

  def get_total_temp_demands(self):
    return self.temp_df["number"].sum()

  def _finalize_line_to_unload_only(self, car):
    # letzte Log-Zeile auf (unload=1, load=0) setzen
    self.change_last_event(car.id)

  def _debug_cars(self):
    for c in self.cars:
        print(f"   └─ Car {c.id}: state={getattr(c, 'state', '?')}, pos={c.position}, t={c.current_time:.2f}, active={c.active}, jobs={getattr(c, 'completed_jobs', 0)}")

  def print_summary(self, title="✅ Simulation abgeschlossen."):
    """Zeigt Endstatistik, alle Fahrpläne (Schedules) und speichert kombinierten Fahrplan."""
    print(f"\n{title}")
    total_jobs = sum(getattr(c, "completed_jobs", 0) for c in self.cars)
    print(f"📦 Insgesamt bearbeitete Aufträge: {total_jobs}\n")

    # 🔹 Fahrzeug-Zusammenfassung
    for c in self.cars:
        status = "aktiv" if getattr(c, "active", False) else "inaktiv"
        print(
            f"🚘 Car {c.id}: "
            f"Endposition {c.position} "
            f"({status}) – erledigt: {getattr(c, 'completed_jobs', 0)}"
        )

    # 🔹 Fahrpläne (Schedules) je Fahrzeug ausgeben
    for cid, df in self.schedules.items():
        print(f"\n📋 Schedule für Fahrzeug {cid}:")
        if df.empty:
            print("   (Keine Einträge)")
        else:
            print(df.to_string(index=False))

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

    if debug:
        print("\n🚀 Starte Simulation ...")
        print(f"📦 Anfangs-Aufträge: {self.network.get_total_transport_demands()}")

    # Init
    for car in self.cars:
        car.active = True
        car.completed_jobs = 0
        car.state = "IDLE"     # neu: expliziter Zustand
        car.leerfahrt = False
        car.current_time = getattr(car, "current_time", 0.0)
        self.log_event(car.id, car.position, car.unload, car.load)
        if debug:
            print(f"   ➕ Init: Car {car.id} @ {car.position} (unload={car.unload}, load={car.load})")
    step = 0


    while self.network.get_total_transport_demands() > 0 or any(c.state == "TRAVEL" for c in self.cars):
        time.sleep(0.5)
        if self.network.get_total_transport_demands() > len(self.cars):
            #if step == 5:
            #   break
            step += 1
            if debug:
                print(f"\n===================== 🕒 SCHRITT {step} =====================")
                print(f"📦 Offene Aufträge (vor Phase A): {self.network.get_total_transport_demands()}")
                self._debug_cars()

            # A) Ankünfte verarbeiten
            for car in self.cars:
                if not car.active:
                    continue
                if car.state == "TRAVEL" and car.current_time == 0:
                    # Ankunft: Auftrag ausführen, wenn real
                    if car.leerfahrt:
                        # Leerfahrt: nur loggen (unload=1, load je nach deiner Logik =0)
                        car.unload = 0
                        car.load = 1
                        self.log_event(car.id, car.position, car.unload, car.load)
                        if debug:
                            print(f"📝 Leerfahrt angekommen: Car {car.id} → {car.position} (unload={car.unload}, load={car.load})")
                    else:
                        # Realer Auftrag
                        self.network.decrease_transport_demand(car.old_position, car.position)
                        car.completed_jobs += 1
                        self.log_event(car.id, car.position, car.unload, car.load)
                        if debug:
                            print(f"📦 Auftrag erledigt: {car.old_position} → {car.position} (Car {car.id})")

                    # Nach Ankunft: entscheiden ob es weitergeht
                    if self.network.get_total_transport_demands() == 0:
                        # keine Aufträge mehr → finalisieren und stoppen
                        self._finalize_line_to_unload_only(car)
                        car.active = False
                        car.state = "DONE"
                        if debug:
                            print(f"🟢 Letzter Auftrag durch Car {car.id} → Simulation terminiert Fahrzeuge.")
                        continue
            # D) Status
            if debug:
                print("\n📋 Offene Transportaufträge (Ende Schritt):")
                if len(self.network.transport_demand) > 0:
                    print(self.network.transport_demand.to_string(index=False))
                else:
                    print("   (Keine offenen Aufträge mehr)")

            # B) Aufträge zuweisen (nur IDLE & active & t==0)
            for car in self.cars:
                if not car.active or car.current_time > 0:
                    continue

                # ✅ sonst ganz normal Auftrag suchen
                dest = self.find_next_machine_with_open_demands(car.position)
                if dest is None:
                    self._finalize_line_to_unload_only(car)
                    car.active = False
                    car.state = "DONE"
                    if debug:
                        print(f"🛑 Car {car.id}: keine offenen Aufträge mehr → bleibt an {car.position}")
                    continue

                # Fahrt zuweisen
                travel_time = self.network.get_time_between(car.position, dest)
                dist = self.network.get_distance_between(car.position, dest)
                real = self._is_real_order(car.position, dest)

                car.old_position = car.position
                car.position = dest
                car.current_time = travel_time
                car.leerfahrt = not real
                car.unload = 1
                car.load = 1 if real else 0
                car.state = "TRAVEL"

                if debug:
                    if real:
                        print(f"✅ Assign REAL: Car {car.id}: {car.old_position} → {dest} (d={dist:.2f}, t={travel_time:.2f})")
                    else:
                        print(f"🚗 Assign LEER: Car {car.id}: {car.old_position} → {dest} (d={dist:.2f}, t={travel_time:.2f})")


            # C) Zeit fortschreiben
            dt = self._advance_time()
            if debug and dt > 0:
                print(f"\n⏩ Zeit fortgeschrieben um {dt:.2f}")
                self._debug_cars()


            # Schleifenbedingung checkt oben erneut:
            # - wenn keine Aufträge mehr da UND niemand TRAVEL → Ende


        else:
           time.sleep(1)
           for car in self.cars:
                if car.current_time > 0:
                    self._debug_cars()
                    self._advance_time()
                    self.print_summary()
                    self.log_event(car.id, car.position, car.unload, car.load)
                else:
                   self._debug_cars()
                   self.print_summary()



    # Ende: Sicherheits-Finalisierung
    for car in self.cars:
        if car.active and car.state != "TRAVEL":
            self._finalize_line_to_unload_only(car)
        car.active = False if car.state != "TRAVEL" else car.active
