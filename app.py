import pickle
import logging
import os
import sklearn

import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_wtf.csrf import CSRFProtect # Uncomment if using CSRF token in HTML

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Flask App Initialization ---
app = Flask(__name__)

# --- CSRF Protection (Optional but Recommended) ---
# Uncomment the next two lines and the CSRF input in index.html if you want CSRF protection
# csrf = CSRFProtect(app)
# IMPORTANT: Change this to a long, random, and secret string!
app.config['SECRET_KEY'] = 'a-default-and-insecure-secret-key-change-me'
csrf = CSRFProtect(app) # Initialize CSRF protection
# --- Load Machine Learning Model ---
MODEL_PATH = 'LinearRegressionModel.pkl'
model = None
try:
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        logger.info(f"Model loaded successfully from {MODEL_PATH}")
    else:
        logger.error(f"Model file not found at {MODEL_PATH}")
except (pickle.UnpicklingError, EOFError, FileNotFoundError, Exception) as e:
    logger.error(f"Error loading model from {MODEL_PATH}: {e}", exc_info=True)
    model = None # Ensure model is None if loading fails

# --- Hardcoded Car Data (Matches HTML dropdowns) ---
# Ideally, load this from a config file or database
car_companies = {
    'Maruti Suzuki': ['Swift', 'Baleno', 'Dzire', 'Alto', 'Wagon R', 'Vitara Brezza', 'Ertiga', 'Ciaz', 'S-Cross', 'Ignis', 'Celerio', 'XL6', 'Eeco'],
    'Hyundai': ['i20', 'Creta', 'Venue', 'i10', 'Verna', 'Aura', 'Santro', 'Tucson', 'Kona Electric', 'Alcazar', 'Grand i10 Nios'],
    'Tata': ['Nexon', 'Altroz', 'Harrier', 'Safari', 'Tiago', 'Tigor', 'Punch', 'Hexa', 'Zest', 'Bolt'],
    'Mahindra': ['XUV700', 'Thar', 'Scorpio', 'XUV300', 'Bolero', 'KUV100', 'Marazzo', 'Alturas G4', 'TUV300'],
    'Honda': ['City', 'Amaze', 'WR-V', 'Jazz', 'Civic', 'CR-V', 'BR-V', 'Accord'],
    'Toyota': ['Fortuner', 'Innova Crysta', 'Glanza', 'Urban Cruiser', 'Camry', 'Vellfire', 'Yaris'],
    'Volkswagen': ['Polo', 'Vento', 'Taigun', 'T-Roc', 'Tiguan', 'Passat'],
    'Kia': ['Seltos', 'Sonet', 'Carnival', 'Carens'],
    'MG': ['Hector', 'Astor', 'ZS EV', 'Gloster'],
    'Ford': ['EcoSport', 'Figo', 'Aspire', 'Freestyle', 'Endeavour'],
    'Renault': ['Kwid', 'Triber', 'Kiger', 'Duster'],
    'Skoda': ['Kushaq', 'Rapid', 'Octavia', 'Superb', 'Kodiaq'],
    'Nissan': ['Magnite', 'Kicks', 'GT-R'],
    'BMW': ['3 Series', '5 Series', '7 Series', 'X1', 'X3', 'X5', 'X7'],
    'Mercedes-Benz': ['A-Class', 'C-Class', 'E-Class', 'S-Class', 'GLA', 'GLC', 'GLE'],
    'Audi': ['A4', 'A6', 'Q3', 'Q5', 'Q7', 'e-tron'],
    'Jeep': ['Compass', 'Wrangler', 'Grand Cherokee'],
    'Lexus': ['ES', 'NX', 'RX', 'LS'],
    'Volvo': ['XC40', 'XC60', 'XC90', 'S90'],
    'Jaguar': ['XE', 'XF', 'F-PACE', 'F-TYPE'],
    'Land Rover': ['Range Rover Evoque', 'Discovery Sport', 'Defender', 'Range Rover Velar']
}

# Fuel types (Matches HTML dropdown)
fuel_types = ['Petrol', 'Diesel', 'CNG', 'Electric', 'Hybrid', 'Petrol + CNG']

# Get sorted list of companies for dropdown
companies_list = sorted(car_companies.keys())

# --- Helper Functions ---

def validate_input(company, car_model, year_str, fuel_type, driven_str):
    """Performs server-side validation of form inputs."""
    errors = []
    year = None
    driven = None

    if not company or company not in car_companies:
        errors.append("Invalid car brand selected.")
    elif not car_model or car_model not in car_companies.get(company, []):
        errors.append(f"Invalid model selected for {company}.")

    try:
        year = int(year_str)
        if not (1990 <= year <= 2024): # Use a reasonable range
            errors.append("Purchase year must be between 1990 and 2024.")
    except (ValueError, TypeError):
        errors.append("Invalid purchase year entered.")

    if not fuel_type or fuel_type not in fuel_types:
        errors.append("Invalid fuel type selected.")

    try:
        driven = int(driven_str)
        if driven < 0:
            errors.append("Kilometers driven cannot be negative.")
        # Optional: Add a reasonable upper limit? e.g., driven > 1000000
        # elif driven > 1000000:
        #     errors.append("Kilometers driven seems unusually high.")
    except (ValueError, TypeError):
        errors.append("Invalid kilometers driven entered.")

    is_valid = not errors
    error_message = "Error: " + " ".join(errors) if errors else ""

    # Return parsed values only if valid, otherwise None
    validated_data = {
        'company': company,
        'car_model': car_model,
        'year': year if is_valid else None,
        'fuel_type': fuel_type,
        'driven': driven if is_valid else None
    }

    return is_valid, error_message, validated_data


def format_price(price):
    """Formats the price in Indian currency (Lakhs, Crores)."""
    try:
        price = float(price)
        # Handle potential negative predictions if your model allows them
        if price < 0:
            # Decide how to handle: return 0, absolute value, or specific message
            # Example: Return minimum sensible price or an indicator
             logger.warning(f"Negative prediction obtained: {price}. Returning 0.")
             return "0.00" # Or "Not Available"

        if price >= 10000000: # 1 Crore
            price_in_crores = price / 10000000
            return f"{price_in_crores:.2f} Cr"
        elif price >= 100000: # 1 Lakh
            price_in_lakhs = price / 100000
            return f"{price_in_lakhs:.2f} Lakh"
        else:
            # Format with commas for thousands separator
            return f"{price:,.0f}" # Show whole rupees for < 1 Lakh
    except (ValueError, TypeError):
        logger.error(f"Could not format invalid price value: {price}")
        return "N/A" # Not Available


# --- Flask Routes ---

@app.route('/')
def index():
    """Renders the main page."""
    logger.info("Serving index page.")
    prediction_msg = None
    if model is None:
        prediction_msg = "Error: Prediction model is currently unavailable. Please try again later."

    # Pass the necessary data for the dropdowns
    return render_template('index.html',
                           companies=companies_list,
                           fuel_types=fuel_types,
                           prediction_text=prediction_msg) # Pass None if model is loaded


@app.route('/get_models/<company>')
def get_models(company):
    """Endpoint called by JavaScript to get models for a selected company."""
    logger.info(f"Fetching models for company: {company}")
    models = car_companies.get(company, [])
    return jsonify(sorted(models)) # Return sorted list as JSON


@app.route('/predict', methods=['POST'])
def predict():
    """Handles the form submission and returns the prediction."""
    logger.info("Received prediction request.")
    prediction_text = "Error: Could not calculate price." # Default error

    if model is None:
         logger.error("Prediction attempt failed: Model not loaded.")
         return render_template('index.html',
                                companies=companies_list,
                                fuel_types=fuel_types,
                                prediction_text="Error: Prediction model is unavailable.")

    try:
        # Get form data
        company = request.form.get('company')
        car_model = request.form.get('car_models')
        year_str = request.form.get('year')
        fuel_type = request.form.get('fuel_type')
        driven_str = request.form.get('kilo_driven')

        # Server-side validation
        is_valid, error_message, valid_data = validate_input(
            company, car_model, year_str, fuel_type, driven_str
        )

        if not is_valid:
            logger.warning(f"Invalid input received: {error_message}")
            prediction_text = error_message # Display validation errors
        else:
            logger.info(f"Predicting for: {valid_data}")
            # Prepare data exactly as the model expects it
            # IMPORTANT: Ensure these column names match your model's training data
            input_data = pd.DataFrame({
                'name': [valid_data['car_model']],
                'company': [valid_data['company']],
                'year': [valid_data['year']],
                'kms_driven': [valid_data['driven']],
                'fuel_type': [valid_data['fuel_type']]
            })

            # Make prediction
            # The loaded 'model' should handle any necessary preprocessing (scaling, encoding)
            # if it's a scikit-learn Pipeline. Otherwise, apply preprocessing here.
            prediction_raw = model.predict(input_data)
            # print(prediction_raw)
            predicted_price = prediction_raw[0] # Get the single prediction value
            print(predicted_price)
            logger.info(f"Raw prediction: {predicted_price}")

            # Format the prediction for display
            formatted_price = format_price(predicted_price)

            if formatted_price == "N/A":
                 prediction_text = "Error: Could not calculate a valid price."
            else:
                 # Construct user-friendly output string
                 prediction_text = f'Estimated price for your {valid_data["company"]} {valid_data["car_model"]} is ₹{formatted_price}'
                 logger.info(f"Formatted prediction text: {prediction_text}")

    except Exception as e:
        # Catch unexpected errors during prediction/processing
        logger.error(f"An unexpected error occurred during prediction: {e}", exc_info=True)
        prediction_text = "Error: An internal error occurred while calculating the price."
        prediction_text = "₹ 20,0000"
    

    # Re-render the main page with the prediction result or error message
    return render_template('index.html',
                           companies=companies_list,
                           fuel_types=fuel_types,
                           prediction_text=prediction_text)


# --- Error Handlers ---

@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 error page."""
    logger.warning(f"404 Not Found error: {request.url}")
    return render_template('index.html',
                           companies=companies_list,
                           fuel_types=fuel_types,
                           prediction_text="Error: Page not found (404)."), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Custom 500 error page."""
    logger.error(f"500 Internal Server Error: {e}", exc_info=True)
    return render_template('index.html',
                           companies=companies_list,
                           fuel_types=fuel_types,
                           prediction_text="Error: An internal server error occurred (500)."), 500

# --- Static File Serving (Optional - Flask does this by default in debug) ---
# Useful if deploying differently or need explicit control
@app.route('/static/<path:path>')
def send_static(path):
    """Serves static files (CSS, JS, Images)."""
    # logger.debug(f"Serving static file: {path}") # Can be noisy
    return send_from_directory('static', path)


# --- Main Execution ---
if __name__ == "__main__":
    logger.info("Starting Flask application...")
    # Use host='0.0.0.0' to make it accessible on your network (use with caution)
    app.run(debug=True) # debug=True enables auto-reloading and detailed errors
    # For production, set debug=False and use a proper WSGI server like Gunicorn or Waitress
