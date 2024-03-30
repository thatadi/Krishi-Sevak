from flask import Blueprint , render_template,request,flash
from flask_login import login_required,current_user
from .models import Farm
from . import db
from pandas import DataFrame , isna
import joblib
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

views = Blueprint('views',__name__)
current_dir = os.path.dirname(__file__)

# Path to the model file
model_file_path = os.path.join(current_dir, 'model.pkl')

# Load the trained model
model = joblib.load(model_file_path)
crops = ['rice', 'maize', 'chickpea', 'kidneybeans', 'pigeonpeas',
       'mothbeans', 'mungbean', 'blackgram', 'lentil', 'pomegranate',
       'banana', 'mango', 'grapes', 'watermelon', 'muskmelon', 'apple',
       'orange', 'papaya', 'coconut', 'cotton', 'jute', 'coffee']
data = {
    'crop': ['rice', 'maize', 'chickpea', 'kidneybeans', 'pigeonpeas', 'mothbeans', 'mungbean', 'blackgram', 'lentil', 'pomegranate',
       'banana', 'mango', 'grapes', 'watermelon', 'muskmelon', 'apple',
       'orange', 'papaya', 'coconut', 'cotton', 'jute', 'coffee'],
    'land_preparation': [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
    'sowing': [2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 2, 2, 2, 0, 2, 2, 0, 2, 2, 2],
    'vegetative_growth': [75, 75, 52, 52, 75, 52, 52, 52, 52, 0, 0, 0, 75, 45, 45, 0, 75, 75, 0, 75, 75, 75],
    'flowering_pollination': [8, 8, 8, 8, 8, 8, 8, 8, 8, 0, 0, 0, 8, 5, 5, 0, 8, 8, 0, 15, 15, 8],
    'fruit_development': [37, 37, 37, 37, 37, 37, 37, 37, 37, 0, 0, 0, 45, 35, 35, 0, 45, 45, 0, 45, 45, 45],
    'ripening': [130, 130, 120, 120, 150, 120, 120, 120, 120, 0, 0, 0, 150, 90, 90, 0, 150, 150, 0, 180, 180, 180],
    'harvesting_days': [5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 5, 3, 3, 0, 5, 5, 0, 5, 5, 5],
    'starting_months': ['June', 'June', 'October', 'June', 'June', 'June', 'June', 'June', 'October', None, None, None, 'February', 'March', 'March', None, 'October', 'June', None, 'June', 'June', 'June'],
    'ending_months': ['November', 'November', 'April', 'November', 'November', 'November', 'November', 'November', 'April', None, None, None, 'October', 'September', 'September', None, 'April', 'November', None, 'November', 'November', 'November']
}

df = pd.DataFrame(data)

# Function to convert month names to month numbers
def month_name_to_number(name):
    return datetime.strptime(name, "%B").month if name is not None else None

# Function to calculate dates based on current month and crop

def calculate_dates(row, start_date=None):  # Accepts optional start_date
        current_date = datetime.now().date() if start_date is None else start_date
        current_month = current_date.month
        current_year = current_date.year
            

        # Convert starting and ending months to their respective integer representations
        starting_month = month_name_to_number(row['starting_months'])
        ending_month = month_name_to_number(row['ending_months'])

        # If current month is same as starting month, take current date as starting date
        if starting_month is not None and current_month == starting_month:
            start_date = current_date
        # If current month is after starting month, start from starting month of next year
        elif starting_month is not None and current_month > starting_month:
            start_date = datetime(current_year + 1, starting_month, 1).date()
        # If current month is before starting month, start from the 1st date of the starting month
        elif starting_month is not None:
            start_date = datetime(current_year, starting_month,1 ).date()

        dates = {'crop': row['crop'], 'land_preparation': start_date}
        if start_date is not None:
            for phase in ['sowing', 'vegetative_growth', 'flowering_pollination', 'fruit_development', 'ripening', 'harvesting_days']:
                start_date += timedelta(days=row[phase])
                dates[phase] = start_date.strftime('%Y-%m-%d')
        return pd.Series(dates)


def generate_schedule_for_crop(df, crop_name, start_date):
    # Filter the DataFrame for the specific crop
    crop_df = df[df['crop'] == crop_name]

    # Apply function to calculate dates for the specific crop
    date_df = crop_df.apply(calculate_dates, axis=1)

    return date_df



@views.route('/')
def base():
    return render_template('base.html')
@views.route('/tnc')
def tnc():
    return render_template('tnc.html')

@views.route('/prediction',methods=['GET','POST'])
@login_required
def prediction():
     if request.method  == 'POST':
        nitrogen=request.form.get('param1') 
        phosphorous=request.form.get('param2') 
        potassium=request.form.get('param3') 
        temperature=request.form.get('param4') 
        humidity=request.form.get('param5') 
        ph=request.form.get('param6')
        
        new_farm=Farm(nitrogen=nitrogen,phosphorous=phosphorous, potassium=potassium,temperature=temperature,ph=ph,humidity=humidity,user_id=current_user.id)
        db.session.add(new_farm)
        db.session.commit()

        flash('Information submitted',category='success')
        parameters = [float(request.form[f'param{i}']) for i in range(1, 8)]

            # Reshape parameters as needed for prediction
        features_2d = np.array([parameters])

            # Make predictions
        predictions = model.predict(features_2d)

            # Handle prediction results based on model output format:
        if len(predictions.shape) == 1:  # Single class prediction (binary)
                predicted_class_index = int(predictions[0])
                predicted_crop = crops[predicted_class_index] if predicted_class_index >= 0 else 'No Crop Predicted'
        else:  # Assuming multi-class prediction (probability distribution)
                predicted_class_index = np.argmax(predictions, axis=1)[0]
                predicted_crop = crops[predicted_class_index]
                specific_start_date = datetime.now().date()

    # Predicted crop (For example, 'maize')
                specific_crop = predicted_crop
                specific_start_date = datetime.now().date()
            
                schedule = generate_schedule_for_crop(df, specific_crop, specific_start_date)
            
                return render_template('prediction.html', result=predicted_crop, schedule=schedule)
       
     return render_template('prediction.html',user=current_user,result=None)

@views.route('/home')
@login_required
def home():
     return render_template('home.html')

@views.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    if request.method == 'POST':
        predicted_crop = request.form.get('crop')
        specific_crop = predicted_crop
        specific_start_date = datetime.now().date()

        schedule = generate_schedule_for_crop(df, specific_crop, specific_start_date)

        # Ensure a valid response is always returned, even if schedule is empty
        if isinstance(schedule, pd.DataFrame) and not schedule.empty:
            return render_template('schedule.html', schedule=schedule)
        else:
            return render_template('schedule.html', schedule=None)  # Return a valid response even if schedule is empty

    # Explicitly return a response for GET requests as well
    return render_template('schedule.html', schedule=None)  # Pass schedule=None for initial display
