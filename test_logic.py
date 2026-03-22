import unittest
import os
from logic import SizeEngine, DatabaseManager

class TestSizeEngine (unittest.TestCase):
    def setUp(self):
        self.test_db_path = 'test_smartfit.db'
        self.db = DatabaseManager(self.test_db_path)
        conn = self.db._get_connection()
        with conn:
            conn.execute('''
            CREATE TABLE IF NOT EXISTS Fabrics (
                fabric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                fabric_name TEXT UNIQUE NOT NULL,
                stretch_factor REAL NOT NULL 
            )
            ''')
        conn.close() 
        self.engine = SizeEngine(self.db)

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except PermissionError:
                pass 
    def test_calculate_weighted_stretch(self):
        self.db.add_fabric("Cotton", 0.05)
        actual_result=self.engine.calculate_weighted_stretch("Cotton", 90, "Spandex / Elastane / Lycra", 10)
        expected_result=0.095
        self.assertEqual(actual_result, expected_result)
    def test_calculate_weighted_stretch_no_stretch(self):
        self.db.add_fabric("Cotton", 0.05)
        actual_result=self.engine.calculate_weighted_stretch("Cotton", 100, "None (0%)", 0)
        expected_result=0.05
        self.assertEqual(actual_result, expected_result)
    def test_normalize_label_synonyms(self):
        actual_result=self.engine.normalize_label(" extra large ")
        expected_result="XL"
        self.assertEqual(actual_result, expected_result)
    def test_calculate_required_measurement_activewear_slim (self):
        actual_result=self.engine.calculate_required_measurement(100, 0.5, "slim","Activewear - Bottoms (Leggings)")
        expected_result=94
        self.assertEqual(actual_result, expected_result)
    def test_compare_to_chart_overlap(self):
        size_chart = {"S": {"chest_circumference": [80, 92]},"M": {"chest_circumference": [90, 100]}}
        actual_result=self.engine.compare_to_chart(91,"chest_circumference", size_chart,91)
        expected_result="M"
        self.assertEqual(actual_result, expected_result)
    def test_compare_to_chart_closest_start(self):
        size_chart = {"XS": {"chest_circumference": [75, 86]},"S": {"chest_circumference": [80, 92]}}
        actual_result = self.engine.compare_to_chart(85, "chest_circumference", size_chart, 85)
        expected_result="S"
        self.assertEqual(actual_result, expected_result)
    def test_compare_to_chart_Nearest_Neighbor(self):
        size_chart = {"XS": {"chest_circumference": [71, 79]},"S": {"chest_circumference": [80, 89]},"M":{"chest_circumference": [90, 100]}}
        actual_result = self.engine.compare_to_chart(102, "chest_circumference", size_chart, 102)
        expected_result="Size Not Found"
        self.assertEqual(actual_result, expected_result)
    def test_compare_to_chart_Nearest_Neighbor2(self):
        size_chart = {"XS": {"chest_circumference": [91, 93]},"S": {"chest_circumference": [94, 96]},"M":{"chest_circumference": [97, 99]},"L":{"chest_circumference": [100, 102]}}
        actual_result = self.engine.compare_to_chart(104, "chest_circumference", size_chart, 104)
        expected_result="L"
        self.assertEqual(actual_result, expected_result)
    def test_get_final_recommendation_conflict(self):
        recommendations = {"waist_circumference":"S", "hip_circumference":"M","inseam_cm":"XS"}
        actual_result = self.engine.get_final_recommendation(recommendations)
        expected_result="M"
        self.assertEqual(actual_result, expected_result)
    def test_get_final_recommendation_size_not_found(self):
        recommendations = {"waist_circumference":"S", "hip_circumference":"Size Not Found","inseam_cm":"XS"}
        actual_result = self.engine.get_final_recommendation(recommendations)
        expected_result="Consult Size Chart"
        self.assertEqual(actual_result, expected_result)
    def test_get_final_recommendation_numeric(self):
        recommendations = {
            "waist_circumference": "38", 
            "hip_circumference": "42",
            "inseam_cm": "40"
        }
        actual_result = self.engine.get_final_recommendation(recommendations)
        expected_result = "42"
        self.assertEqual(actual_result, expected_result)
    def test_find_best_size_full_flow(self):
        user_profile = {
            "email":"bla1@gmail.com",
            "waist_circumference": 70,
            "hip_circumference": 95,
            "inseam_cm": 75
        }
        size_chart = {
            "S": {"waist_circumference": [68, 72], "hip_circumference": [92, 96]},
            "M": {"waist_circumference": [73, 77], "hip_circumference": [97, 101]}
        }
        self.db.add_fabric("Cotton", 0.0) 
        actual_result = self.engine.find_best_size(
            user_profile, 
            "Bottoms - Pants", 
            "Cotton", 100, "None (0%)", 0, 
            size_chart, 
            fit_pref="regular"
        ).get("recommendation")
        print(actual_result)
        expected_result="M"
        self.assertEqual(actual_result, expected_result)
    def test_find_best_size_missing_measurement(self):
        user_profile = {
            "email": "test@gmail.com",
            "hip_circumference": 95
        }
        
        size_chart = {
            "S": {"waist_circumference": [68, 72], "hip_circumference": [92, 96]},
            "M": {"waist_circumference": [73, 77], "hip_circumference": [97, 101]}
        }
        
        self.db.add_fabric("Cotton", 0.0)
        
        result = self.engine.find_best_size(
            user_profile, 
            "Bottoms - Pants", 
            "Cotton", 100, "None (0%)", 0, 
            size_chart, 
            fit_pref="regular"
        )
    def test_get_final_recommendation_one_size(self):
        recommendations = {
            "chest_circumference": "ONE SIZE",
            "shoulder_width": "O/S"
        }
        actual_result = self.engine.get_final_recommendation(recommendations)
        expected_result = "One Size Fits All"
        self.assertEqual(actual_result, expected_result)
    def test_find_best_size_missing_mandatory_measurement(self):
        user_profile = {
            "email": "test@gmail.com",
            "waist_circumference": 70
        }
        size_chart = {
            "S": {"waist_circumference": [68, 72], "hip_circumference": [92, 96]}
        }
        self.db.add_fabric("Cotton", 0.0) 
        actual_result = self.engine.find_best_size(
            user_profile, 
            "Bottoms - Pants", 
            "Cotton", 100, "None (0%)", 0, 
            size_chart, 
            fit_pref="regular"
        )
        expected_result = "Consult Size Chart"
        self.assertEqual(actual_result["recommendation"], expected_result)


if __name__ == "__main__":
    unittest.main()