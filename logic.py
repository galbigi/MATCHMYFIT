import sqlite3
import re      #Input Validation for email
import hashlib #id for chart table picture
import json

class DatabaseManager:
    """Handles all SQLite database connections and CRUD (create, read, update, delete) operations."""
    
    def __init__(self, db_path='smartfit.db'):
        self.db_path = db_path

    def _get_connection(self):
        """Helper method to create a connection """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row #evrey row from the db returns like dictionary
        return conn

    def register_user(self, user_data):
        required_metrics = ['waist', 'chest', 'hip', 'height']
        for metric in required_metrics:
            if user_data.get(metric, 0) <= 0:
                print(f"Validation Failed: {metric} cannot be zero or negative.")
                return False
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            query = '''
            INSERT INTO Users (
                email, full_name, waist_circumference, chest_circumference, 
                hip_circumference, height_cm, inseam_cm, 
                shoulder_width, arm_length, thigh_circumference
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(query, (
                user_data['email'], user_data['full_name'], user_data['waist'],
                user_data['chest'], user_data['hip'], user_data['height'], 
                user_data['inseam'], user_data.get('shoulder'), 
                user_data.get('arm'), user_data.get('thigh')
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_user_measurements(self, email):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE email = ?", (email,))
        user_row = cursor.fetchone()
        conn.close()
        return dict(user_row) if user_row else None

    def login_user(self, email):
        return self.get_user_measurements(email)

    def get_fabric_stretch(self, fabric_name):
        conn = self._get_connection()
        cursor = conn.cursor()
        query = "SELECT stretch_factor FROM Fabrics WHERE fabric_name = ?"
        cursor.execute(query, (fabric_name,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0.0

    def update_user_measurements(self, email, new_measurements):
        conn = self._get_connection()
        cursor = conn.cursor()
        query = '''
        UPDATE Users 
        SET full_name = ?, waist_circumference = ?, chest_circumference = ?, 
            hip_circumference = ?, height_cm = ?, inseam_cm = ?, 
            shoulder_width = ?, arm_length = ?, thigh_circumference = ?
        WHERE email = ?
        '''
        cursor.execute(query, (
            new_measurements['full_name'], new_measurements['waist'], 
            new_measurements['chest'], new_measurements['hip'], 
            new_measurements['height'], new_measurements['inseam'], 
            new_measurements.get('shoulder'), new_measurements.get('arm'), 
            new_measurements.get('thigh'), email
        ))
        conn.commit()
        changes = cursor.rowcount #indicates if changes were done 
        conn.close()
        return changes > 0

    def delete_user(self, email):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Users WHERE email = ?", (email,))
        conn.commit()
        deleted_rows = cursor.rowcount
        conn.close()
        return deleted_rows > 0

    def get_all_fabric_names(self):
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT fabric_name FROM Fabrics")
            results = cursor.fetchall()
            conn.close()
            return [row[0] for row in results]
        except sqlite3.OperationalError:
            return ['Cotton', 'Polyester Blend', 'Stretch Denim']
        
    def save_scan(self, email, category, recommended_size, fabric_type, size_chart_data):
        """Saves a successful scan to the history table."""
        conn = self._get_connection()
        cursor = conn.cursor()
        chart_string = json.dumps(size_chart_data, sort_keys=True)
        chart_hash = hashlib.md5(chart_string.encode()).hexdigest()
        cursor.execute("SELECT user_id FROM Users WHERE email = ?", (email,))
        #we need the first row
        user_row = cursor.fetchone()
        
        if user_row:
            user_id = user_row['user_id']
            cursor.execute('''
            SELECT scan_id FROM Scans_History WHERE user_id = ? AND chart_hash = ?''', (user_id, chart_hash))
            existing_scan = cursor.fetchone()
            if existing_scan:
                cursor.execute('''UPDATE Scans_History SET scan_date = CURRENT_TIMESTAMP, recommended_size = ?, category = ?
                WHERE scan_id = ?
            ''', (recommended_size, category, existing_scan['scan_id']))
            else:
                cursor.execute('''
                INSERT INTO Scans_History (user_id, category, recommended_size, fabric_type, chart_hash)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, category, recommended_size, fabric_type, chart_hash))
            conn.commit()    
        conn.close()
        
    def get_user_history(self, user_id):
        """Fetches the user's scan history using their user_id."""
        conn = self._get_connection()
        cursor = conn.cursor()
        query = '''
            SELECT category as "Category", fabric_type as "Fabric", 
                   recommended_size as "Size", date(scan_date) as "Date"
            FROM Scans_History
            WHERE user_id = ?
            ORDER BY scan_date DESC
        '''
        cursor.execute(query, (user_id,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def add_fabric(self, fabric_name, stretch_factor):
        #only for the tests
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO Fabrics (fabric_name, stretch_factor) VALUES (?, ?)",
                    (fabric_name, stretch_factor)
                )
        except Exception as e:
            print(f"Error adding fabric: {e}")
        



class SizeEngine:
    """The Core Mathematical and AI Comparison Logic."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.categories_mapping = {
            "Tops (Shirts, Jackets, Sweaters)": ["chest_circumference", "shoulder_width", "arm_length"],
            "Bottoms - Pants": ["waist_circumference", "hip_circumference", "inseam_cm", "thigh_circumference"],
            "Bottoms - Skirts": ["waist_circumference", "hip_circumference"],
            "Dresses & Jumpsuits": ["chest_circumference", "waist_circumference", "hip_circumference", "height_cm"],
            "Activewear - Tops (Sports Bras)": ["chest_circumference", "shoulder_width"],
            "Activewear - Bottoms (Leggings)": ["waist_circumference", "hip_circumference", "inseam_cm", "thigh_circumference"]
        }

    def get_garment_categories(self):
        return list(self.categories_mapping.keys())

    def calculate_required_measurement(self, body_measurement, stretch_factor, fit_preference="regular", category="Bottoms (Pants, Skirts)"):
        if "Activewear" in category:
            fit_buffers = {"slim": -4, "regular": -1, "relaxed": 2}
        elif "Bottoms" in category:
            fit_buffers = {"slim": 0, "regular": 2, "relaxed": 5}
        elif "Tops" in category:
            fit_buffers = {"slim": 2, "regular": 4, "relaxed": 8}
        elif "Dresses" in category or "Jumpsuits" in category:
            fit_buffers = {"slim": 0, "regular": 2, "relaxed": 5}
        else:
            fit_buffers = {"slim": 2, "regular": 4, "relaxed": 8}
        
        buffer = fit_buffers.get(fit_preference, 4)
        
        if buffer < 0:
            adjusted_buffer = buffer * (1 + stretch_factor) 
        else:
            adjusted_buffer = buffer * (1 - stretch_factor)
        
        return body_measurement + adjusted_buffer

    def get_relevant_measurements(self, user_profile, selected_category):
        needed_keys = self.categories_mapping.get(selected_category, [])
        return {key: user_profile.get(key) for key in needed_keys} #returns dictionary (e.g {waist:75} )

    def compare_to_chart(self, target_val, measurement_name, size_chart, original_body_val):
        """Range Match"""
        possible_matches = []
        for size_label, dimensions in size_chart.items():
            if measurement_name in dimensions:
                low, high = dimensions[measurement_name]
                if low <= target_val <= high:
                    # In fast fashion, size ranges often overlap. 
                    # We calculate a score to find the most accurate fit among multiple matches.
                    score = abs(low - (original_body_val or target_val))
                    possible_matches.append((score, size_label))
        if possible_matches:
            possible_matches.sort()
            return possible_matches[0][1]
 
        """Nearest Neighbor"""
        distances = []
        for size_label, dimensions in size_chart.items():
            if measurement_name in dimensions:
                low, high = dimensions[measurement_name]
                mid_point = (low + high) / 2.0 
                diff = abs(mid_point - target_val)
                distances.append((diff, size_label))
        
        if distances:
            distances.sort() 
            best_diff, best_size = distances[0]
            if best_diff <= 5.0:
                return best_size

        return "Size Not Found"

    def normalize_label(self, label):
        label = str(label).upper().strip()
        synonyms = {
            "1X": "XL", "2X": "2XL", "XXL": "2XL", "3X": "3XL", "XXXL": "3XL",
            "4X": "4XL", "XXXXL": "4XL", "SMALL": "S", "MEDIUM": "M", 
            "LARGE": "L", "EXTRA LARGE": "XL", "ONE SIZE": "OS", "OS": "OS", 
            "O/S": "OS", "ONESIZE": "OS", "UNISIZE": "OS",
        }
        return synonyms.get(label, label)

    def get_final_recommendation(self, recommendations): #recommendations is dictionary 
        if "Size Not Found" in recommendations.values():
            return "Consult Size Chart"
        valid_sizes = [self.normalize_label(s) for s in recommendations.values()]
        if not valid_sizes:
            return "Consult Size Chart"
        
        if valid_sizes[0].isdigit():
            try:
                numeric_sizes = [int(s) for s in valid_sizes]
                return str(max(numeric_sizes))
            except ValueError:
                pass 

        """list from the smallest size to the biggest"""
        label_order = ["XXS", "XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL", "OS"]
        current_max_idx = -1
        final_label = valid_sizes[0]
        for size in valid_sizes:
            if size in label_order:
                idx = label_order.index(size)
                if idx > current_max_idx:
                    current_max_idx = idx
                    final_label = size
                    
        if final_label == "OS":
            return "One Size Fits All"
        return final_label

    def calculate_weighted_stretch(self, main_fabric_name, main_pct, stretch_type, stretch_pct):
        base_stretch = self.db.get_fabric_stretch(main_fabric_name)
        main_contribution = base_stretch * (main_pct / 100.0)
        
        stretch_multipliers = {
            "None (0%)": 0.0,
            "Spandex / Elastane / Lycra": 0.50,
            "Polyamide / Nylon": 0.25
        }
        stretch_factor = stretch_multipliers.get(stretch_type, 0.0)
        stretch_contribution = stretch_factor * (stretch_pct / 100.0)
        
        return main_contribution + stretch_contribution

    def find_best_size(self, user_profile, garment_category, main_fabric, main_pct, stretch_type, stretch_pct, size_chart, fit_pref="regular"):
        fabric_stretch = self.calculate_weighted_stretch(main_fabric, main_pct, stretch_type, stretch_pct)
        relevant_body_parts = self.get_relevant_measurements(user_profile, garment_category)
        
        point_results = {}

        mandatory_measurements = ["waist_circumference", "chest_circumference", "hip_circumference", "height_cm"]

        for name, body_val in relevant_body_parts.items():
            if not any(name in dimensions for dimensions in size_chart.values()):
                    continue
            if body_val:  
                target = self.calculate_required_measurement(body_val, fabric_stretch, fit_pref, garment_category)
                point_results[name] = self.compare_to_chart(target_val=target, measurement_name=name,size_chart=size_chart, original_body_val=body_val)
            elif name in mandatory_measurements:
                point_results[name]="Size Not Found"
            else:
                continue
        
        if not point_results:
            return {
                "recommendation": "Consult Size Chart",
                "details": {"Error": "No matching measurements found."}
            }

        final_match = self.get_final_recommendation(point_results)
        
        return {
            "recommendation": final_match,
            "details": point_results
        }
def is_valid_email(email):
    pattern = r"^\S+@\S+\.\S+$"
    return re.match(pattern, email) is not None