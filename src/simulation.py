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

    def finalize_schedules(self, debug=True):
        # Fall 1️⃣: Falsches Laden rückwirkend korrigieren
        for car_id, df in self.schedules.items():
            df = df.reset_index(drop=True)

            for i in range(len(df) - 1):
                current_load = df.loc[i, "load"]
                next_unload = df.loc[i + 1, "unload"]

                # Wenn das nächste Ziel unload == 0 hat → aktuelles load war falsch
                if current_load == 1 and next_unload == 0:
                    df.loc[i, "load"] = 0
                    if debug:
                        print(f"🔧 Korrigiere Car {car_id}: Zeile {i} – "
                            f"Location {df.loc[i, 'Location']} → load auf 0 gesetzt "
                            f"(wegen unload=0 bei {df.loc[i+1, 'Location']})")

            # Fall 2️⃣: Letzte Zeile entfernen, wenn (unload, load) == (1,1) oder (0,1)
            if not df.empty:
                last_unload = df.loc[df.index[-1], "unload"]
                last_load = df.loc[df.index[-1], "load"]

                if (last_unload, last_load) in [(1, 1), (0, 1)]:
                    if debug:
                        print(f"🗑️ Entferne letzte Zeile von Car {car_id}: "
                            f"Location {df.loc[df.index[-1], 'Location']} "
                            f"(unload={last_unload}, load={last_load})")
                    df = df.iloc[:-1]
            self.schedules[car_id] = df

    def combine_schedules_preserve_order(self, save=True, debug=True):
        """
        Kombiniert alle Fahrplans (Schedules) zu einer großen Tabelle,
        ohne die Reihenfolge der Einträge oder Indizes zu verändern.
        """
        combined_list = []

        for car_id, df in self.schedules.items():
            # Kopie mit Fahrzeug-ID hinzufügen, aber Originalreihenfolge behalten
            temp = df.copy()
            temp["VehicleId"] = car_id
            temp["OriginalIndex"] = df.index  # zur Sicherheit behalten
            combined_list.append(temp)

            if debug:
                print(f"📋 Fahrzeug {car_id}: {len(df)} Einträge hinzugefügt.")

        # Hintereinander anhängen – Reihenfolge bleibt stabil
        combined = pd.concat(combined_list, ignore_index=True)

        # Optionale Spaltenreihenfolge
        combined = combined[["VehicleId", "Location", "unload", "load"]]

        if save:
            os.makedirs(os.path.dirname(self.schedule_path), exist_ok=True)
            combined.to_csv(self.schedule_path, sep=";", index=False)
            if debug:
                print(f"\n💾 Alle Schedules kombiniert gespeichert unter: {self.schedule_path}")

        return combined



    def start_sim(self, debug=True):
        # 1️⃣ Initialisierung
        for car in self.cars:
            car.active = True
            car.completed_jobs = 0
            self.log_event(car.id, car.position, 0, 1)  # Startpunkt loggen
            if debug:
                print(f"   ➕ Init: Car {car.id} startet an Maschine {car.position}")

        step = 0
        while self.network.get_total_transport_demands() > 0:
            #time.sleep(0.5)
            for car in self.cars:
                if self.network.get_total_transport_demands() == 0:
                    break
                if not car.active:
                    continue

                # --- Nächsten sinnvollen Zielpunkt finden ---
                next_machine = self.find_next_machine_with_open_demands(car.position)
                if next_machine is None:
                    car.active = False

                # --- Prüfen, ob reale Lieferung oder Leerfahrt ---
                is_real = self._is_real_order(car.position, next_machine)
                distance = self.network.get_distance_between(car.position, next_machine)
                car.old_position = car.position
                car.position = next_machine

                if is_real:
                # Reale Lieferung
                    self.network.decrease_transport_demand(car.old_position, next_machine)
                    car.completed_jobs += 1
                    temp_machine = self.find_next_machine_with_open_demands(car.position)
                    is_real_next = self._is_real_order(car.position, temp_machine)

                    if is_real_next:
                        self.log_event(car.id, next_machine, 1, 1)
                    else:
                        self.log_event(car.id, next_machine, 1, 0)

                    action = "REAL"

                else:
                    # Leerfahrt
                    self.log_event(car.id, next_machine, 0, 1)
                    action = "LEER"
                 # Update Fahrzeugposition
                if debug:
                    print(f"🚗 Car {car.id}: {action} – {car.old_position} → {next_machine}")

                    # Debug: aktueller Stand

            if debug:
                print("\n📋 Offene Aufträge (nach Schritt):")
                if len(self.network.transport_demand) > 0:
                    print(self.network.transport_demand.to_string(index=False))
                else:
                    print("   (keine offenen Aufträge mehr)")
         # 3️⃣ Simulation abgeschlossen
        self.finalize_schedules()
        self.combine_schedules_preserve_order()
        if debug:
            print("\n✅ Simulation abgeschlossen.")
            for c in self.cars:
                status = "aktiv" if getattr(c, "active", False) else "inaktiv"
                print(f"🚘 Car {c.id}: Endposition {c.position} ({status}) – erledigt: {c.completed_jobs}")





