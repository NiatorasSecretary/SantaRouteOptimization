"""
Weihnachtsmann Routenplanung
Berechnet die optimale Route unter Berücksichtigung von Kapazitäts- und Zeitbeschränkungen
"""

import pandas as pd
import numpy as np
from geopy.distance import geodesic
from datetime import datetime
import os


class SantaRouteOptimizer:
    """Optimiert die Route des Weihnachtsmannes"""
    
    NORTH_POLE = (90.0, 0.0)
    COAL_ARTICLE_ID = 0
    
    def __init__(self, children_file, gifts_file, sleigh_specs_file):
        """
        Initialisiert den Routenoptimierer
        
        Args:
            children_file: Pfad zur Kinder-CSV
            gifts_file: Pfad zur Geschenk-CSV
            sleigh_specs_file: Pfad zur Schlittenspezifikations-CSV
        """
        self.children_df = self._load_children(children_file)
        self.gifts_df = self._load_gifts(gifts_file)
        self.sleigh_specs = self._load_sleigh_specs(sleigh_specs_file)
        
        self.max_weight = self.sleigh_specs['maximum weight']
        self.max_volume = self.sleigh_specs['maximum volume']
        self.speed_kmh = self.sleigh_specs['speed (km/h)']
        self.time_per_stop_min = self.sleigh_specs['time per stop (min)']
        self.max_time_hours = 7
        
    def _load_children(self, filepath):
        """Lädt Kinderdaten aus CSV"""
        df = pd.read_csv(filepath, sep=';', decimal=',')
        return df
    
    def _load_gifts(self, filepath):
        """Lädt Geschenkdaten aus CSV"""
        df = pd.read_csv(filepath, sep=';', decimal=',')
        return df
    
    def _load_sleigh_specs(self, filepath):
        """Lädt Schlittenspezifikationen aus CSV"""
        df = pd.read_csv(filepath, sep=';', decimal=',')
        specs = {}
        for _, row in df.iterrows():
            specs[row['meta data']] = float(row['value'])
        return specs
    
    def assign_gifts(self):
        """Weist Kindern Geschenke zu - unartige Kinder bekommen Kohle (Artikel-ID 0)"""
        self.children_df['assigned_article'] = self.children_df.apply(
            lambda row: row['wish'] if row['naughty'] == 0 else self.COAL_ARTICLE_ID,
            axis=1
        )
        
        self.children_df = self.children_df.merge(
            self.gifts_df, 
            left_on='assigned_article', 
            right_on='article',
            how='left'
        )
    
    def calculate_distance(self, coord1, coord2):
        """
        Berechnet die Entfernung zwischen zwei Koordinaten in km
        
        Args:
            coord1: Tuple (latitude, longitude)
            coord2: Tuple (latitude, longitude)
            
        Returns:
            Entfernung in Kilometern
        """
        return geodesic(coord1, coord2).kilometers
    
    def optimize_route(self):
        """
        Optimiert die Route mit Greedy-Algorithmus (Nearest Neighbor)
        unter Berücksichtigung von Kapazitäts- und Zeitbeschränkungen
        
        Returns:
            Liste von Dictionaries mit Stop-Informationen
        """
        self.assign_gifts()
        
        route = []
        unvisited = set(self.children_df['child'].tolist())
        current_position = self.NORTH_POLE
        current_cargo = {}
        total_time = 0
        
        while unvisited:
            best_child = None
            best_distance = float('inf')
            
            for child_id in unvisited:
                child = self.children_df[self.children_df['child'] == child_id].iloc[0]
                child_coords = (child['latitude'], child['longitude'])
                article_id = int(child['assigned_article'])
                
                distance_to_child = self.calculate_distance(current_position, child_coords)
                
                can_deliver = article_id in current_cargo and current_cargo[article_id] > 0
                
                if can_deliver and distance_to_child < best_distance:
                    best_distance = distance_to_child
                    best_child = child_id
            
            if best_child is None:
                undeliverable = []
                for child_id in list(unvisited):
                    child = self.children_df[self.children_df['child'] == child_id].iloc[0]
                    
                    if (child['weight'] > self.max_weight or 
                        child['volume'] > self.max_volume):
                        undeliverable.append(child_id)
                        print(f"WARNUNG: Kind {child_id} kann nicht beliefert werden (Geschenk zu groß/schwer)")
                
                for child_id in undeliverable:
                    unvisited.remove(child_id)
                
                if not unvisited:
                    break
                
                return_distance = self.calculate_distance(current_position, self.NORTH_POLE)
                total_time += return_distance / self.speed_kmh
                
                articles_to_load = self.calculate_loading(unvisited)
                route.append({'type': 'refuel', 'articles': articles_to_load})
                
                current_position = self.NORTH_POLE
                current_cargo = articles_to_load.copy()
            else:
                child = self.children_df[self.children_df['child'] == best_child].iloc[0]
                child_coords = (child['latitude'], child['longitude'])
                article_id = int(child['assigned_article'])
                
                route.append({'type': 'delivery', 'child_id': best_child})
                unvisited.remove(best_child)
                
                current_cargo[article_id] -= 1
                if current_cargo[article_id] == 0:
                    del current_cargo[article_id]
                
                travel_distance = self.calculate_distance(current_position, child_coords)
                current_position = child_coords
                
                total_time += travel_distance / self.speed_kmh
                total_time += self.time_per_stop_min / 60.0
        
        final_return_distance = self.calculate_distance(current_position, self.NORTH_POLE)
        total_time += final_return_distance / self.speed_kmh
        
        route.append({'type': 'refuel', 'articles': {}})
        
        if total_time > self.max_time_hours:
            print(f"WARNUNG: Gesamtzeit {total_time:.2f}h überschreitet das Limit von {self.max_time_hours}h!")
            print(f"Geschwindigkeit müsste mindestens {total_time/self.max_time_hours * self.speed_kmh:.0f} km/h betragen.")
        else:
            print(f"Route erfolgreich berechnet! Gesamtzeit: {total_time:.2f}h")
        
        return route
    
    def calculate_loading(self, unvisited_children):
        """
        Berechnet welche Geschenke beim Nachfüllen geladen werden sollen
        unter Berücksichtigung der Kapazitätsbeschränkungen
        
        Args:
            unvisited_children: Set der noch nicht besuchten Kind-IDs
            
        Returns:
            Dictionary {article_id: count}
        """
        needed_articles = {}
        for child_id in unvisited_children:
            child = self.children_df[self.children_df['child'] == child_id].iloc[0]
            article_id = int(child['assigned_article'])
            needed_articles[article_id] = needed_articles.get(article_id, 0) + 1
        
        loaded_articles = {}
        current_weight = 0
        current_volume = 0
        
        for article_id, needed_count in sorted(needed_articles.items()):
            gift = self.gifts_df[self.gifts_df['article'] == article_id].iloc[0]
            
            max_by_weight = int((self.max_weight - current_weight) / gift['weight'])
            max_by_volume = int((self.max_volume - current_volume) / gift['volume'])
            max_can_load = min(max_by_weight, max_by_volume, needed_count)
            
            if max_can_load > 0:
                loaded_articles[article_id] = max_can_load
                current_weight += max_can_load * gift['weight']
                current_volume += max_can_load * gift['volume']
        
        return loaded_articles
    
    def export_route(self, route, output_file):
        """
        Exportiert die Route als CSV (Semikolon-getrennt, Komma als Dezimaltrennzeichen)
        Format: stop, article, pieces
        
        Args:
            route: Liste von Stop-Dictionaries
            output_file: Pfad zur Ausgabedatei
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        rows = []
        for stop in route:
            if stop['type'] == 'delivery':
                rows.append({
                    'stop': stop['child_id'],
                    'article': '',
                    'pieces': ''
                })
            elif stop['type'] == 'refuel':
                if stop['articles']:
                    for article_id, count in sorted(stop['articles'].items()):
                        rows.append({
                            'stop': 0,
                            'article': article_id,
                            'pieces': count
                        })
                else:
                    rows.append({
                        'stop': 0,
                        'article': '',
                        'pieces': ''
                    })
        
        route_df = pd.DataFrame(rows)
        route_df.to_csv(output_file, sep=';', decimal=',', index=False)
        
        deliveries = sum(1 for s in route if s['type'] == 'delivery')
        refuels = sum(1 for s in route if s['type'] == 'refuel' and s['articles'])
        
        print(f"Route gespeichert in: {output_file}")
        print(f"Anzahl Zeilen: {len(rows)}")
        print(f"Anzahl Kinder beliefert: {deliveries}")
        print(f"Anzahl Nachfüllstops: {refuels}")
    
    def print_statistics(self, route):
        """Gibt detaillierte Statistiken zur Route aus"""
        print("\n=== ROUTENSTATISTIK ===")
        
        total_distance = 0
        current_pos = self.NORTH_POLE
        nice_count = 0
        naughty_count = 0
        stop_count = 0
        refuel_count = 0
        
        for stop in route:
            if stop['type'] == 'refuel':
                distance = self.calculate_distance(current_pos, self.NORTH_POLE)
                total_distance += distance
                current_pos = self.NORTH_POLE
                if stop['articles']:
                    refuel_count += 1
            else:
                child_id = stop['child_id']
                child = self.children_df[self.children_df['child'] == child_id].iloc[0]
                child_coords = (child['latitude'], child['longitude'])
                distance = self.calculate_distance(current_pos, child_coords)
                total_distance += distance
                current_pos = child_coords
                stop_count += 1
                
                if child['naughty'] == 0:
                    nice_count += 1
                else:
                    naughty_count += 1
        
        total_time = total_distance / self.speed_kmh
        total_time += stop_count * (self.time_per_stop_min / 60.0)
        
        print(f"Gesamtdistanz: {total_distance:.2f} km")
        print(f"Anzahl Stopps: {stop_count}")
        print(f"Anzahl Nachfüllstops: {refuel_count}")
        print(f"Gesamtzeit (inkl. Stopps): {total_time:.2f} Stunden")
        print(f"Brav: {nice_count} Kinder")
        print(f"Unartig (Kohle): {naughty_count} Kinder")
        print(f"Zeitlimit: {self.max_time_hours} Stunden - {'EINGEHALTEN ✓' if total_time <= self.max_time_hours else 'ÜBERSCHRITTEN ✗'}")
        print("=" * 40)


def main():
    """Hauptfunktion"""
    print("=" * 60)
    print("  WEIHNACHTSMANN ROUTENPLANUNG 2025")
    print("=" * 60)
    
    optimizer = SantaRouteOptimizer(
        children_file='sample_data/sample_input.csv',
        gifts_file='sample_data/articles.csv',
        sleigh_specs_file='sample_data/sleigh_specs.csv'
    )
    
    print(f"\nSchlitten-Spezifikationen:")
    print(f"  Max. Gewicht: {optimizer.max_weight} kg")
    print(f"  Max. Volumen: {optimizer.max_volume} m³")
    print(f"  Geschwindigkeit: {optimizer.speed_kmh} km/h")
    print(f"  Zeit pro Stopp: {optimizer.time_per_stop_min} min")
    print(f"  Zeitfenster: {optimizer.max_time_hours} Stunden (22:00 - 07:00)")
    
    print(f"\nAnzahl Kinder: {len(optimizer.children_df)}")
    print("\nBerechne optimale Route...")
    
    route = optimizer.optimize_route()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'output/route_{timestamp}.csv'
    
    optimizer.export_route(route, output_file)
    optimizer.print_statistics(route)
    
    print(f"\n✓ Routenberechnung abgeschlossen!")


if __name__ == "__main__":
    main()
