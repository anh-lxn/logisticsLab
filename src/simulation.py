import pandas as pd
import os
import random
import numpy as np


class Simulation:
    def __init__(self, network, cars, schedule_name="schedule.txt", seed=30, k=3, save=True):
        self.network = network
        self.cars = cars
        self.k = k # Number of possible next machines to choose from
        self.total_empty_runs = 0
        self.save = save

        # Schedule for each car
        self.schedules = { car.id: pd.DataFrame(columns=["Location", "unload", "load"]) for car in cars }

        self.schedule_name = schedule_name
        # Output path
        self.git_dir = os.path.dirname(os.getcwd())
        self.data_dir = os.path.join(self.git_dir, 'data')
        self.schedule_path = os.path.join(self.data_dir, self.schedule_name)

        # Random Seeds
        random.seed(seed)
        np.random.seed(seed)

    # --------------------------------------------------------
    # Helper Methods
    # --------------------------------------------------------
    def _is_real_order(self, start, dest):
        """Prüft, ob es keine leere Fahrt ist."""
        df = self.network.transport_demand
        return ((df["start"] == start) & (df["dest"] == dest)).any()

    def log_event(self, car_id, location, unload, load):
        """Fügt einen Eintrag zum Fahrplans des Autos hinzu."""
        df = self.schedules[car_id]
        new_row = {"Location": location, "unload": unload, "load": load}
        self.schedules[car_id].loc[len(df)] = new_row

    def show_leerfahrten(self):
        """Gibt die Anzahl der Leerfahrten pro Auto und insgesamt aus."""
        for car in self.cars:
            print(f"Car {car.id}: Anzahl leehrer Fahrten = {car.empty_runs}")
        print(f"Gesamte Leerfahrten: {self.total_empty_runs}")

    def show_schedule(self, car_id=None):
        """Zeigt entweder einen bestimmten oder alle Fahrpläne an."""
        if car_id is not None:
            print(f"\nSchedule für Fahrzeug {car_id}:")
            print(self.schedules[car_id])
        else:
            for cid, df in self.schedules.items():
                print(f"\nSchedule für Fahrzeug {cid}:")
                print(df)

    # --------------------------------------------------------
    # Randomized Greedy Selection
    # --------------------------------------------------------
    def find_next_machine_randomly(self, start_machine):
        df = self.network.transport_demand

        # 1. Aufträge vom aktuellen Standort
        start_demand = df[df["start"] == start_machine].reset_index(drop=True)
        if not start_demand.empty:
            start_demand["distance"] = start_demand["dest"].apply(lambda dest: self.network.get_distance_between(start_machine, dest))
            start_demand = start_demand.sort_values("distance")
            candidates = start_demand.head(self.k)
            best_row = candidates.sample(1).iloc[0]
            return int(best_row["dest"])

        # 2. Falls keine Aufträge am Standort → nächste Startmaschine suchen
        open_starts = df["start"].unique()
        if len(open_starts) == 0:
            return None
        distances = { m: self.network.get_distance_between(start_machine, m) for m in open_starts } # Distanzen berechnen
        sorted_machines = sorted(distances.items(), key=lambda x: x[1])
        candidates = sorted_machines[:self.k]
        next_machine = random.choice(candidates)[0] # zufällige Maschine auswählen
        return int(next_machine)

    # --------------------------------------------------------
    # Postprocessing
    # --------------------------------------------------------

    def finalize_schedules(self):
        """Korrigiert den finalen Fahrplan jedes Autos."""
        for car_id, df in self.schedules.items():
            df = df.reset_index(drop=True)

            # Fall 1: Falsches Laden rückwirkend korrigieren
            for i in range(len(df) - 1):
                current_load = df.loc[i, "load"]
                next_unload = df.loc[i + 1, "unload"]
                # Wenn das nächste Ziel unload == 0 hat -> aktuelles load war falsch
                if current_load == 1 and next_unload == 0:
                    df.loc[i, "load"] = 0

            # Fall 2: Letzte Zeile entfernen, wenn (unload, load) == (1,1) oder (0,1)
            if not df.empty:
                last_unload = df.loc[df.index[-1], "unload"]
                last_load = df.loc[df.index[-1], "load"]
                if (last_unload, last_load) in [(1, 1), (0, 1)]:
                    df = df.iloc[:-1]

            self.schedules[car_id] = df


    def combine_schedules_preserve_order(self, save=True, withEmptyRuns=True):
        """Kombiniert alle Fahrplans (Schedules) zu einer großen Tabelle."""
        combined_list = []

        for car_id, df in self.schedules.items():

            # Kopie erzeugen
            temp = df.copy()
            temp["VehicleId"] = car_id
            temp["OriginalIndex"] = df.index  # zur Sicherheit behalten
            combined_list.append(temp)

        # Hintereinander anhängen
        combined = pd.concat(combined_list, ignore_index=True)

        # Optionale Spaltenreihenfolge
        combined = combined[["VehicleId", "Location", "unload", "load"]]

        if save:
            if withEmptyRuns:
                for car_id, df in self.schedules.items():
                    combined["emptyRuns"] = self.total_empty_runs

            os.makedirs(os.path.dirname(self.schedule_path), exist_ok=True)
            combined.to_csv(self.schedule_path, sep=";", index=False)
            print(f"{self.schedule_name} gespeichert unter: {self.schedule_path}")


        return combined

    # --------------------------------------------------------
    # Hauptsimulation
    # --------------------------------------------------------
    def start_sim(self, display=True):
        # 1. Initialisierung
        for car in self.cars:
            car.active = True
            car.completed_jobs = 0
            self.log_event(car.id, car.position, 0, 1)  # Startpunkt loggen

        # 2. Simulation durchführen
        print("Starte Simulation...")
        while self.network.get_total_transport_demands() > 0:
            for car in self.cars:
                if self.network.get_total_transport_demands() == 0:
                    break
                if not car.active:
                    continue

                # Nächsten sinnvollen Zielpunkt finden
                next_machine = self.find_next_machine_randomly(car.position)
                if next_machine is None:
                    car.active = False

                # Prüfen, ob reale Lieferung oder Leerfahrt
                is_real = self._is_real_order(car.position, next_machine)
                car.old_position = car.position
                car.position = next_machine

                # Verarbeitung reale Lieferung
                if is_real:

                    self.network.decrease_transport_demand(car.old_position, next_machine)
                    car.completed_jobs += 1
                    temp_machine = self.find_next_machine_randomly(car.position)
                    is_real_next = self._is_real_order(car.position, temp_machine)

                    if is_real_next:
                        self.log_event(car.id, next_machine, 1, 1)
                    else:
                        self.log_event(car.id, next_machine, 1, 0)

                 # Verarbeitung Leerfahrt
                else:
                    self.log_event(car.id, next_machine, 0, 1)
                    car.empty_runs += 1
                    self.total_empty_runs += 1

        # 3. Simulation Postprocessing
        print("Simulation beendet.")
        self.finalize_schedules()
        self.combine_schedules_preserve_order(save=self.save)
        if display: self.show_leerfahrten()
