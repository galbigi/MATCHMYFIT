import json
import os
from PIL import Image
from dotenv import load_dotenv
from google import genai 

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")


client = genai.Client(api_key=api_key)

def analyze_size_chart(image):
    """
    Sends the image to Gemini Vision using the NEW google-genai SDK.
    """
    prompt = """
    You are an expert at extracting clothing size charts from images.
    
    CRITICAL INSTRUCTION:
    First, analyze the image. If the image does NOT contain a clothing size chart (for example, if it's a picture of an animal, a landscape, a person, or random text), you MUST return EXACTLY this JSON and nothing else:
    {"error": "not_a_size_chart"}
    
    If it DOES contain a size chart, extract the measurements into a JSON format as follows:
    
    1. MAPPING: Use EXACTLY these keys (if the measurement exists in the chart): 
       'chest_circumference', 'waist_circumference', 'hip_circumference', 
       'inseam_cm', 'shoulder_width', 'arm_length', 'thigh_circumference', 'height_cm'.
    
    2. DATA FORMAT: For every measurement, return a LIST with two numbers [min, max].
       - If the chart shows a range (e.g., "86-90"), return [86, 90].
       - If the chart shows a single number (e.g., "90"), return [90, 90].
       - If units are inches, convert to cm (val * 2.54) before putting in the list.
    
   3. CRITICAL RULES FOR FAST FASHION CHARTS & HEBREW TRANSLATIONS:
        - Skirts & Dresses (No Inseam): If the garment is a Skirt or Dress, DO NOT map "Length" (אורך) to "inseam_cm". Inseam is strictly for pants.
        - Hip vs. Thigh Translation: The Hebrew words "ירך" or "גודל ירך" are often incorrect translations for "Hip". Map them to "hip_circumference". Only map to "thigh_circumference" if the word is explicitly plural "ירכיים" or "היקף ירכיים".
        - Elastic Bands: If you see a large range for a measurement (e.g., Waist 62.0-90.0), extract the HIGHER number of the range as the maximum stretch capacity.
        - FLAT MEASUREMENTS VS. BABY SIZES (CRITICAL): If a chart provides "Flat Measurements" (half-circumference), you MUST multiply the values by 2 for Chest, Waist, and Hips. 
            * How to know? Look at the size labels. If the size labels are for adults (e.g., S, M, L, 34, 38, 40) AND the circumference values are impossibly small (e.g., under 55cm), it is a FLAT measurement -> multiply by 2.
            * ARMPIT/CHEST ADJUSTMENT (CHEST ONLY): If the extracted 'chest_circumference' for an ADULT size (after doubling) is 86cm or less, it is likely an armpit-level measurement. In this case, ADD 7cm ONLY to the 'chest_circumference' value. DO NOT add this adjustment to waist, hips, or any other measurement.
            * If the size labels are clearly for babies/kids (e.g., 0-3M, 6M, 2T, 4Y, 110cm), DO NOT multiply by 2 and DO NOT add the 5cm adjustment.
        
         
    4. LABEL STANDARDIZATION:
        - Use '3XL' instead of 'XXXL'.
        - Use '4XL' instead of 'XXXXL'.
        - Use single letters 'S', 'M', 'L' instead of 'Small', 'Medium', 'Large'.
            
    5. RETURN: Return ONLY a JSON object where keys are the size labels (e.g., "S", "M").
    
    6. ERROR HANDLING: If the image does NOT contain a size chart or is unreadable, 
       return ONLY this JSON: {"error": "no_chart_found"}.
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash', 
        contents=[prompt, image]
    )
    return response.text

def parse_ai_response(raw_text):
    """
    Cleans the AI text response and converts it to a Python dictionary.
    """
    try:
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        if "error" in data:
            return None
            
        return data
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return None

def analyze_clothing_reviews(reviews_text):
    """
    Sends the customer reviews to Gemini using the NEW google-genai SDK.
    """
    prompt = f"""
    You are an expert fashion fit analyst. 
    Read the following customer reviews (which may contain typos, missing spaces, bad grammar, and irrelevant info).
    
    YOUR TASK:
    1. Ignore all irrelevant noise (shipping, colors, complaints about the courier, etc.).
    2. Focus ONLY on sizing and fit.
    3. Determine the overall sizing trend and identify if there are specific problem areas in the garment.
    
    OUTPUT FORMAT:
    You MUST return ONLY a valid JSON object. Do not add any conversational text, explanations, or markdown formatting (like ```json).
    Use exactly this structure:
    {{
        "overall_fit": "runs_small" | "true_to_size" | "runs_large" | "mixed" | "unknown",
        "problem_area": "string describing specific tight/loose areas (e.g., 'tight in shoulders') or null if none",
        "confidence_score": integer from 1 to 100 representing how clear the trend is
    }}

    Reviews to analyze:
    ---
    {reviews_text}
    ---
    """
    response = client.models.generate_content(
        model='gemini-2.5-flash', 
        contents=prompt
    )
    return response.text