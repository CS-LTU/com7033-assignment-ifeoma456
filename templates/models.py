import sqlite3
import pandas as pd
import numpy as np
import pickle
import os
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StrokeHypertensionPredictor:
    """Machine Learning model for stroke/hypertension prediction"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoders = {}
        self.model_path = 'models/stroke_model.pkl'
        self.scaler_path = 'models/scaler.pkl'
        self.encoders_path = 'models/label_encoders.pkl'
        self.load_models()
    
    def load_models(self):
        """Load trained model, scaler, and label encoders"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                print("✓ Stroke model loaded")
            
            if os.path.exists(self.scaler_path):
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                print("✓ Scaler loaded")
            
            if os.path.exists(self.encoders_path):
                with open(self.encoders_path, 'rb') as f:
                    self.label_encoders = pickle.load(f)
                print("✓ Label encoders loaded")
                
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
    
    def train_model(self):
        """Placeholder for training new models - models are pre-trained"""
        logger.info("Models are pre-trained and ready to use")
        return True
    
    def preprocess_patient_data(self, patient_data):
        """Preprocess patient data for prediction"""
        try:
            # Create DataFrame
            df = pd.DataFrame([patient_data])
            
            # Handle BMI
            if 'bmi' in df.columns:
                df['bmi'] = pd.to_numeric(df['bmi'], errors='coerce')
                df['bmi'] = df['bmi'].fillna(28.5)
            
            # Encode categorical variables
            categorical_columns = ['gender', 'ever_married', 'work_type', 'Residence_type', 'smoking_status']
            for col in categorical_columns:
                if col in df.columns and col in self.label_encoders:
                    try:
                        df[col] = self.label_encoders[col].transform(df[col].astype(str))
                    except:
                        df[col] = 0
            
            # Select features in correct order
            feature_columns = [
                'gender', 'age', 'hypertension', 'heart_disease', 'ever_married',
                'work_type', 'Residence_type', 'avg_glucose_level', 'bmi', 'smoking_status'
            ]
            
            X = df[feature_columns].values.astype(float)
            
            # Scale features
            if self.scaler:
                X_scaled = self.scaler.transform(X)
                return X_scaled
            return X
        
        except Exception as e:
            logger.error(f"Error preprocessing patient data: {str(e)}")
            return None
    
    def extract_patient_medical_features(self, patient_id):
        """
        Extract patient's medical features from HMS database.
        These will be used as ADDITIONAL INPUT FEATURES for the model.
        
        Returns dict with patient history features:
        - stored_hypertension: 0/1 from patient record
        - stored_heart_disease: 0/1 from patient record
        - avg_historical_glucose: Average glucose from assessments
        - avg_historical_bmi: Average BMI from assessments
        - visit_frequency: How often patient comes to clinic
        - assessment_count: Number of previous assessments
        - days_as_patient: How long patient in system
        - risk_trajectory: Historical risk trend (0-1 scale)
        """
        features = {
            'has_stored_hypertension': 0,
            'has_stored_heart_disease': 0,
            'avg_historical_glucose': 100,  # Default normal
            'avg_historical_bmi': 25,       # Default normal
            'visit_frequency': 0,            # New patient
            'assessment_count': 0,           # No assessments
            'days_as_patient': 0,            # New patient
            'risk_trajectory': 0.5,          # Neutral
        }
        
        if not patient_id:
            return features
        
        try:
            conn = sqlite3.connect('hospital.db')
            conn.row_factory = sqlite3.Row
            
            # Get patient's stored medical conditions
            patient = conn.execute(
                "SELECT * FROM patients WHERE id = ?",
                (patient_id,)
            ).fetchone()
            
            if patient:
                # Extract stored diagnoses (if columns exist)
                features['has_stored_hypertension'] = int(patient.get('hypertension', 0) or 0)
                features['has_stored_heart_disease'] = int(patient.get('heart_disease', 0) or 0)
                
                # Calculate days as patient
                if patient.get('created_at'):
                    created = datetime.fromisoformat(patient['created_at'])
                    days_diff = (datetime.now() - created).days
                    features['days_as_patient'] = min(days_diff / 365.0, 1.0)  # Normalize to 0-1
            
            # Get assessment history
            assessments = conn.execute(
                """SELECT * FROM health_assessments 
                   WHERE patient_id = ? 
                   ORDER BY created_at DESC LIMIT 20""",
                (patient_id,)
            ).fetchall()
            
            if assessments:
                features['assessment_count'] = len(assessments)
                
                # Calculate averages from recent assessments
                glucoses = [float(a['avg_glucose_level']) for a in assessments if a['avg_glucose_level']]
                bmis = [float(a['bmi']) for a in assessments if a['bmi']]
                risks = [float(a['risk_score']) for a in assessments if a['risk_score']]
                
                if glucoses:
                    features['avg_historical_glucose'] = sum(glucoses) / len(glucoses)
                if bmis:
                    features['avg_historical_bmi'] = sum(bmis) / len(bmis)
                
                # Calculate visit frequency (assessments per month)
                if features['days_as_patient'] > 0:
                    months = max(features['days_as_patient'] * 12, 0.1)  # Avoid division by zero
                    features['visit_frequency'] = min(len(assessments) / months, 5.0) / 5.0  # Normalize to 0-1
                
                # Calculate risk trajectory
                if len(risks) >= 2:
                    latest_risk = risks[0]
                    oldest_risk = risks[-1]
                    # 0 = improving, 0.5 = stable, 1.0 = worsening
                    risk_change = latest_risk - oldest_risk
                    if risk_change > 20:
                        features['risk_trajectory'] = 1.0  # Worsening
                    elif risk_change < -20:
                        features['risk_trajectory'] = 0.0  # Improving
                    else:
                        features['risk_trajectory'] = 0.5  # Stable
            
            # Get appointment frequency
            appointments = conn.execute(
                """SELECT COUNT(*) as count FROM appointments 
                   WHERE patient_id = ?""",
                (patient_id,)
            ).fetchone()
            
            if appointments and appointments['count']:
                # Already factored into visit_frequency
                pass
            
            conn.close()
            
            logger.info(f"Patient {patient_id} features: {features}")
            return features
            
        except Exception as e:
            logger.error(f"Error extracting patient medical features: {str(e)}")
            return features
    
    def enhance_form_data_with_patient_history(self, form_data, patient_id=None):
        """
        ENHANCED APPROACH: Intelligently blend form data with patient history.
        This creates richer input that considers the patient's medical background.
        
        Strategy:
        - If form value is provided, use it (user is entering current data)
        - If patient history exists, use it as confidence indicator
        - Weight the combination based on recency and reliability
        """
        try:
            enhanced_data = form_data.copy()
            
            if not patient_id:
                return enhanced_data
            
            # Get patient's historical medical features
            patient_features = self.extract_patient_medical_features(patient_id)
            
            # Enhance with stored diagnoses
            # If patient has stored hypertension, this influences the prediction
            if patient_features['has_stored_hypertension'] and form_data.get('hypertension', 0) == 0:
                # Patient had hypertension before, likely still relevant
                enhanced_data['hypertension_confidence'] = 0.8
            
            if patient_features['has_stored_heart_disease'] and form_data.get('heart_disease', 0) == 0:
                # Patient had heart disease, likely still relevant
                enhanced_data['heart_disease_confidence'] = 0.8
            
            # Blend form glucose with historical average
            current_glucose = form_data.get('avg_glucose_level', patient_features['avg_historical_glucose'])
            if patient_features['assessment_count'] > 0:
                # Weight current 60%, history 40%
                enhanced_data['avg_glucose_level'] = (current_glucose * 0.6 + patient_features['avg_historical_glucose'] * 0.4)
                enhanced_data['glucose_reliability'] = min(0.5 + patient_features['assessment_count'] * 0.1, 1.0)
            
            # Blend form BMI with historical average
            current_bmi = form_data.get('bmi', patient_features['avg_historical_bmi'])
            if patient_features['assessment_count'] > 0:
                # Weight current 60%, history 40%
                enhanced_data['bmi'] = (current_bmi * 0.6 + patient_features['avg_historical_bmi'] * 0.4)
                enhanced_data['bmi_reliability'] = min(0.5 + patient_features['assessment_count'] * 0.1, 1.0)
            
            # Add all patient features for logging/analysis
            enhanced_data['patient_features'] = patient_features
            
            logger.info(f"Enhanced form data with patient history: {enhanced_data}")
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Error enhancing form data: {str(e)}")
            return form_data
    
    def get_combined_patient_data(self, form_data, patient_id=None):
        """
        Combine form input with patient database history for enhanced prediction.
        Uses form data as primary, enriched with:
        1. Patient's stored medical history
        2. Historical average metrics from previous assessments
        3. Trend analysis (improving/stable/worsening)
        4. Smart blending of current vs historical data
        """
        try:
            # STEP 1: Enhance form data with patient history (NEW Option 2 approach)
            combined_data = self.enhance_form_data_with_patient_history(form_data, patient_id)
            patient_medical_info = None
            
            if patient_id:
                conn = sqlite3.connect('hospital.db')
                conn.row_factory = sqlite3.Row
                
                # Get patient record and their stored medical history
                patient = conn.execute(
                    "SELECT * FROM patients WHERE id = ?",
                    (patient_id,)
                ).fetchone()
                
                if patient:
                    # Store patient medical info for use in trend analysis
                    patient_medical_info = dict(patient)
                    
                    # Get previous assessments for historical averages and trends
                    prev_assessments = conn.execute(
                        """SELECT * FROM health_assessments 
                           WHERE patient_id = ? 
                           ORDER BY created_at DESC LIMIT 10""",
                        (patient_id,)
                    ).fetchall()
                    
                    if prev_assessments:
                        # Calculate metrics from previous assessments
                        prev_glucoses = []
                        prev_bmis = []
                        prev_risks = []
                        
                        for assessment in prev_assessments:
                            try:
                                if assessment['avg_glucose_level']:
                                    prev_glucoses.append(float(assessment['avg_glucose_level']))
                                if assessment['bmi']:
                                    prev_bmis.append(float(assessment['bmi']))
                                if assessment['risk_score']:
                                    prev_risks.append(float(assessment['risk_score']))
                            except:
                                pass
                        
                        # Add historical glucose analysis
                        if prev_glucoses:
                            combined_data['historical_avg_glucose'] = sum(prev_glucoses) / len(prev_glucoses)
                            current_glucose = combined_data.get('avg_glucose_level', 0)
                            
                            # Trend detection
                            if current_glucose > combined_data['historical_avg_glucose'] * 1.2:
                                combined_data['glucose_trend'] = 'increasing'
                                combined_data['glucose_change'] = current_glucose - combined_data['historical_avg_glucose']
                            elif current_glucose < combined_data['historical_avg_glucose'] * 0.8:
                                combined_data['glucose_trend'] = 'decreasing'
                                combined_data['glucose_change'] = current_glucose - combined_data['historical_avg_glucose']
                            else:
                                combined_data['glucose_trend'] = 'stable'
                                combined_data['glucose_change'] = current_glucose - combined_data['historical_avg_glucose']
                        
                        # Add historical BMI analysis
                        if prev_bmis:
                            combined_data['historical_avg_bmi'] = sum(prev_bmis) / len(prev_bmis)
                            current_bmi = combined_data.get('bmi', 0)
                            
                            if current_bmi > combined_data['historical_avg_bmi'] * 1.1:
                                combined_data['bmi_trend'] = 'increasing'
                                combined_data['bmi_change'] = current_bmi - combined_data['historical_avg_bmi']
                            elif current_bmi < combined_data['historical_avg_bmi'] * 0.9:
                                combined_data['bmi_trend'] = 'decreasing'
                                combined_data['bmi_change'] = current_bmi - combined_data['historical_avg_bmi']
                            else:
                                combined_data['bmi_trend'] = 'stable'
                                combined_data['bmi_change'] = current_bmi - combined_data['historical_avg_bmi']
                        
                        # Add risk trend analysis
                        if len(prev_risks) >= 2:
                            latest_risk = prev_risks[0]
                            previous_risk = prev_risks[1]
                            combined_data['previous_risk_score'] = latest_risk
                            combined_data['risk_change'] = latest_risk - previous_risk
                            
                            if latest_risk - previous_risk > 15:
                                combined_data['risk_trajectory'] = 'worsening'
                            elif latest_risk - previous_risk < -15:
                                combined_data['risk_trajectory'] = 'improving'
                            else:
                                combined_data['risk_trajectory'] = 'stable'
                        elif prev_risks:
                            combined_data['previous_risk_score'] = prev_risks[0]
                    
                    # Add patient's stored medical flags
                    combined_data['patient_age_category'] = 'senior' if int(patient.get('age', 0)) > 60 else 'adult' if int(patient.get('age', 0)) > 30 else 'young'
                    combined_data['has_patient_record'] = True
                
                conn.close()
            
            combined_data['patient_medical_info'] = patient_medical_info
            return combined_data
        
        except Exception as e:
            logger.error(f"Error combining patient data: {str(e)}")
            return form_data
    
    def predict(self, patient_data):
        """Predict stroke/hypertension risk"""
        try:
            if self.model is None:
                return None
            
            X_scaled = self.preprocess_patient_data(patient_data)
            if X_scaled is None:
                return None
            
            prediction = int(self.model.predict(X_scaled)[0])
            probability = self.model.predict_proba(X_scaled)[0]
            
            # Base risk score from model
            risk_score = float(probability[1] * 100)
            
            # ENHANCED: Adjust risk score based on historical trends
            adjusted_risk = risk_score
            trend_notes = []
            
            # Check for worsening glucose levels
            if 'glucose_trend' in patient_data:
                if patient_data['glucose_trend'] == 'increasing':
                    adjusted_risk += 5  # Increase risk if glucose is rising
                    trend_notes.append("⚠️ Glucose levels increasing from historical average")
                elif patient_data['glucose_trend'] == 'decreasing':
                    adjusted_risk = max(adjusted_risk - 3, 0)  # Decrease if improving
                    trend_notes.append("✓ Glucose levels improving from historical average")
            
            # Check for worsening BMI
            if 'bmi_trend' in patient_data:
                if patient_data['bmi_trend'] == 'increasing':
                    adjusted_risk += 3
                    trend_notes.append("⚠️ BMI increasing from historical average")
                elif patient_data['bmi_trend'] == 'decreasing':
                    adjusted_risk = max(adjusted_risk - 2, 0)
                    trend_notes.append("✓ BMI improving from historical average")
            
            # Compare with previous risk score
            if 'previous_risk_score' in patient_data:
                prev_risk = patient_data['previous_risk_score']
                risk_change = adjusted_risk - prev_risk
                if risk_change > 15:
                    trend_notes.append("⚠️ ALERT: Significant increase in risk since last assessment")
                    adjusted_risk = min(adjusted_risk + 2, 100)
                elif risk_change < -15:
                    trend_notes.append("✓ Significant improvement since last assessment")
            
            # Cap adjusted risk at 100
            adjusted_risk = min(adjusted_risk, 100)
            adjusted_risk = max(adjusted_risk, 0)
            
            # Determine risk level based on adjusted risk
            if adjusted_risk >= 75:
                risk_level = "HIGH RISK"
                risk_color = "danger"
            elif adjusted_risk >= 50:
                risk_level = "MODERATE RISK"
                risk_color = "warning"
            elif adjusted_risk >= 25:
                risk_level = "LOW RISK"
                risk_color = "info"
            else:
                risk_level = "MINIMAL RISK"
                risk_color = "success"
            
            return {
                'prediction': 'Has Stroke/Hypertension' if prediction == 1 else 'No Stroke/Hypertension',
                'risk_level': risk_level,
                'risk_color': risk_color,
                'confidence': float(probability[prediction] * 100),
                'risk_score': adjusted_risk,  # Use adjusted risk score
                'base_risk_score': risk_score,  # Include base score for comparison
                'probability_no_condition': float(probability[0] * 100),
                'probability_has_condition': float(probability[1] * 100),
                'trend_notes': trend_notes,  # Include historical trend information
                'historical_avg_glucose': patient_data.get('historical_avg_glucose'),
                'historical_avg_bmi': patient_data.get('historical_avg_bmi'),
                'previous_risk_score': patient_data.get('previous_risk_score')
            }
        
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            return None
    
    def get_patient_assessment_history(self, patient_id):
        """Get patient's previous health risk assessments"""
        try:
            conn = sqlite3.connect('hospital.db')
            conn.row_factory = sqlite3.Row
            
            assessments = conn.execute(
                """SELECT * FROM health_assessments 
                   WHERE patient_id = ? 
                   ORDER BY created_at DESC 
                   LIMIT 10""",
                (patient_id,)
            ).fetchall()
            
            conn.close()
            return [dict(row) for row in assessments] if assessments else []
        except Exception as e:
            logger.error(f"Error retrieving assessment history: {str(e)}")
            return []
    
    def get_patient_health_history(self, patient_id):
        """Get patient's medical history from database"""
        try:
            conn = sqlite3.connect('hospital.db')
            conn.row_factory = sqlite3.Row
            
            patient = conn.execute(
                "SELECT * FROM patients WHERE id = ?",
                (patient_id,)
            ).fetchone()
            
            conn.close()
            
            if not patient:
                return None
            
            return {
                'patient_id': patient['id'],
                'first_name': patient['first_name'],
                'last_name': patient['last_name'],
                'gender': patient['gender'],
                'date_of_birth': patient['date_of_birth'],
                'medical_history': patient['medical_history'],
                'created_at': patient['created_at']
            }
        except Exception as e:
            logger.error(f"Error retrieving patient health history: {str(e)}")
            return None
    
    def get_risk_trend(self, patient_id):
        """Calculate risk trend (improving/stable/worsening) from assessment history"""
        try:
            assessments = self.get_patient_assessment_history(patient_id)
            
            if len(assessments) < 2:
                return {"trend": "No History", "direction": "neutral", "change": 0}
            
            # Get latest and previous assessment
            latest = assessments[0]['risk_score']
            previous = assessments[1]['risk_score']
            
            change = latest - previous
            
            if change > 10:
                trend = "Worsening"
                direction = "up"
            elif change < -10:
                trend = "Improving"
                direction = "down"
            else:
                trend = "Stable"
                direction = "neutral"
            
            return {
                "trend": trend,
                "direction": direction,
                "change": round(change, 2),
                "previous_risk": round(previous, 2),
                "latest_risk": round(latest, 2)
            }
        except Exception as e:
            logger.error(f"Error calculating risk trend: {str(e)}")
            return {"trend": "Unable to calculate", "direction": "unknown", "change": 0}
    
    def save_assessment(self, patient_id, form_data, prediction_result):
        """Save assessment result to database for history tracking"""
        try:
            conn = sqlite3.connect('hospital.db')
            
            conn.execute('''
                INSERT INTO health_assessments (
                    patient_id, gender, age, hypertension, heart_disease,
                    ever_married, work_type, residence_type, avg_glucose_level,
                    bmi, smoking_status, risk_level, risk_score, confidence,
                    probability_no_condition, probability_has_condition
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient_id,
                form_data.get('gender'),
                int(form_data.get('age', 0)),
                1 if form_data.get('hypertension') else 0,
                1 if form_data.get('heart_disease') else 0,
                form_data.get('ever_married'),
                form_data.get('work_type'),
                form_data.get('Residence_type'),
                float(form_data.get('avg_glucose_level', 0)),
                float(form_data.get('bmi', 0)),
                form_data.get('smoking_status'),
                prediction_result.get('risk_level'),
                prediction_result.get('risk_score'),
                prediction_result.get('confidence'),
                prediction_result.get('probability_no_condition'),
                prediction_result.get('probability_has_condition')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving assessment: {str(e)}")
            return False


class PatientHealthModel:
    """Patient health analytics model"""
    
    @staticmethod
    def get_patient_health_analytics(patient_id):
        """Get comprehensive health analytics for a patient"""
        try:
            conn = sqlite3.connect('hospital.db')
            conn.row_factory = sqlite3.Row
            
            # Get patient info
            patient = conn.execute(
                "SELECT * FROM patients WHERE id = ?",
                (patient_id,)
            ).fetchone()
            
            if not patient:
                return None
            
            # Get appointment history
            appointments = conn.execute(
                "SELECT COUNT(*) FROM appointments WHERE patient_id = ?",
                (patient_id,)
            ).fetchone()[0]
            
            # Get billing info
            total_bills = conn.execute(
                "SELECT COUNT(*) FROM billing WHERE patient_id = ?",
                (patient_id,)
            ).fetchone()[0]
            
            outstanding_bills = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM billing WHERE patient_id = ? AND status = 'Unpaid'",
                (patient_id,)
            ).fetchone()[0]
            
            conn.close()
            
            return {
                'patient': dict(patient),
                'appointments': appointments,
                'total_bills': total_bills,
                'outstanding_bills': outstanding_bills
            }
        
        except Exception as e:
            logger.error(f"Error getting patient health analytics: {str(e)}")
            return None
    
    @staticmethod
    def get_all_patients_summary():
        """Get summary of all patients"""
        try:
            conn = sqlite3.connect('hospital.db')
            conn.row_factory = sqlite3.Row
            
            patients = conn.execute(
                "SELECT * FROM patients ORDER BY created_at DESC"
            ).fetchall()
            
            conn.close()
            
            return [dict(p) for p in patients]
        
        except Exception as e:
            logger.error(f"Error getting patients summary: {str(e)}")
            return []


class DoctorAnalytics:
    """Analytics and insights for doctors"""
    
    @staticmethod
    def get_doctor_dashboard_stats():
        """Get statistics for doctor dashboard"""
        try:
            conn = sqlite3.connect('hospital.db')
            
            total_patients = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
            active_appointments = conn.execute(
                "SELECT COUNT(*) FROM appointments WHERE status = 'Scheduled'"
            ).fetchone()[0]
            recent_patients = conn.execute(
                "SELECT COUNT(*) FROM patients WHERE date(created_at) = date('now')"
            ).fetchone()[0]
            pending_bills = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM billing WHERE status = 'Unpaid'"
            ).fetchone()[0]
            
            conn.close()
            
            return {
                'total_patients': total_patients,
                'active_appointments': active_appointments,
                'recent_patients': recent_patients,
                'pending_bills': pending_bills
            }
        
        except Exception as e:
            logger.error(f"Error getting doctor dashboard stats: {str(e)}")
            return {}
    
    @staticmethod
    def get_high_risk_patients():
        """Get patients predicted as high risk"""
        try:
            predictor = StrokeHypertensionPredictor()
            conn = sqlite3.connect('hospital.db')
            conn.row_factory = sqlite3.Row
            
            patients = conn.execute("SELECT * FROM patients").fetchall()
            conn.close()
            
            high_risk_patients = []
            
            for patient in patients:
                try:
                    # Map gender values
                    gender = patient['gender']
                    if gender and gender.lower().startswith('f'):
                        gender = 'Female'
                    else:
                        gender = 'Male'
                    
                    patient_data = {
                        'gender': gender,
                        'age': calculate_age(patient['date_of_birth']),
                        'hypertension': 0,
                        'heart_disease': 0,
                        'ever_married': 'Yes',
                        'work_type': 'Private',
                        'Residence_type': 'Urban',
                        'avg_glucose_level': 100.0,
                        'bmi': 25.0,
                        'smoking_status': 'never smoked'
                    }
                    
                    result = predictor.predict(patient_data)
                    if result and ('HIGH' in result['risk_level'] or 'MODERATE' in result['risk_level']):
                        high_risk_patients.append({
                            'patient': dict(patient),
                            'prediction': result
                        })
                except Exception as e:
                    logger.error(f"Error processing patient: {str(e)}")
                    continue
            
            return high_risk_patients
        except Exception as e:
            logger.error(f"Error getting high risk patients: {str(e)}")
            return []


# Global instances
stroke_predictor = StrokeHypertensionPredictor()
patient_health_model = PatientHealthModel()
doctor_analytics = DoctorAnalytics()


def get_model_stats():
    """Get model performance statistics"""
    return {
        'model_status': 'Ready' if stroke_predictor.model else 'Not Loaded',
        'last_trained': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'model_type': 'Stroke/Hypertension Prediction',
        'features': 10
    }


def calculate_age(date_of_birth):
    """Calculate age from date of birth"""
    try:
        from datetime import datetime
        dob = datetime.strptime(date_of_birth, '%Y-%m-%d')
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except:
        return 30  # Default age


# ============================================================================
# OPTION C: DOCTOR SYSTEM - Complete Doctor Management
# ============================================================================

class DoctorProfile:
    """Doctor profile management and data model"""
    
    def __init__(self, db_path='hospital.db'):
        self.db_path = db_path
    
    def get_or_create_profile(self, user_id, specialization='General Practice'):
        """Get existing doctor profile or create new one"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM doctors WHERE user_id = ?', (user_id,))
            profile = cursor.fetchone()
            
            if not profile:
                cursor.execute('''
                    INSERT INTO doctors (user_id, specialization, license_number)
                    VALUES (?, ?, ?)
                ''', (user_id, specialization, f'LIC-{user_id}-{datetime.now().timestamp()}'))
                conn.commit()
                logger.info(f"Created doctor profile for user_id: {user_id}")
                cursor.execute('SELECT * FROM doctors WHERE user_id = ?', (user_id,))
                profile = cursor.fetchone()
            
            return dict(profile) if profile else None
        except Exception as e:
            logger.error(f"Error managing doctor profile: {str(e)}")
            return None
        finally:
            conn.close()
    
    def update_profile(self, doctor_id, **kwargs):
        """Update doctor profile information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            allowed_fields = ['specialization', 'contact_number', 'qualification', 
                            'experience_years', 'consultation_fee', 'bio', 'availability_status']
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if updates:
                set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
                values = list(updates.values()) + [doctor_id]
                cursor.execute(f'UPDATE doctors SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?', values)
                conn.commit()
                logger.info(f"Updated doctor profile: {doctor_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating doctor profile: {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_profile_by_id(self, doctor_id):
        """Get full doctor profile with stats"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM doctors WHERE id = ?', (doctor_id,))
            profile = cursor.fetchone()
            
            if profile:
                profile_dict = dict(profile)
                # Add stats
                cursor.execute('SELECT COUNT(*) as total_patients FROM doctor_patient_assignments WHERE doctor_id = ? AND status = "active"', (doctor_id,))
                profile_dict['total_patients'] = cursor.fetchone()['total_patients']
                
                cursor.execute('SELECT COUNT(*) as total_actions FROM doctor_activity_logs WHERE doctor_id = ?', (doctor_id,))
                profile_dict['total_actions'] = cursor.fetchone()['total_actions']
                
                return profile_dict
            return None
        except Exception as e:
            logger.error(f"Error fetching doctor profile: {str(e)}")
            return None
        finally:
            conn.close()
    
    def get_all_doctors(self):
        """Get all doctor profiles with basic stats"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT d.*, u.email, u.full_name,
                    COUNT(DISTINCT dpa.patient_id) as patient_count,
                    COUNT(DISTINCT dal.id) as activity_count
                FROM doctors d
                LEFT JOIN users u ON d.user_id = u.id
                LEFT JOIN doctor_patient_assignments dpa ON d.id = dpa.doctor_id
                LEFT JOIN doctor_activity_logs dal ON d.id = dal.doctor_id
                GROUP BY d.id
                ORDER BY d.created_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching all doctors: {str(e)}")
            return []
        finally:
            conn.close()


class DoctorActivityLogger:
    """Track and log all doctor actions"""
    
    def __init__(self, db_path='hospital.db'):
        self.db_path = db_path
    
    def log_activity(self, doctor_id, action_type, details=None, patient_id=None):
        """Log a doctor activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO doctor_activity_logs (doctor_id, action_type, details, patient_id)
                VALUES (?, ?, ?, ?)
            ''', (doctor_id, action_type, details, patient_id))
            conn.commit()
            logger.info(f"Logged activity: {action_type} for doctor_id: {doctor_id}")
            return True
        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_doctor_activities(self, doctor_id, limit=50):
        """Get recent activities for a doctor"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT dal.*, p.name as patient_name
                FROM doctor_activity_logs dal
                LEFT JOIN patients p ON dal.patient_id = p.id
                WHERE dal.doctor_id = ?
                ORDER BY dal.timestamp DESC
                LIMIT ?
            ''', (doctor_id, limit))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching activities: {str(e)}")
            return []
        finally:
            conn.close()
    
    def get_activity_summary(self, doctor_id):
        """Get activity statistics for a doctor"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT action_type, COUNT(*) as count
                FROM doctor_activity_logs
                WHERE doctor_id = ?
                GROUP BY action_type
                ORDER BY count DESC
            ''', (doctor_id,))
            summary = {row['action_type']: row['count'] for row in cursor.fetchall()}
            return summary
        except Exception as e:
            logger.error(f"Error fetching activity summary: {str(e)}")
            return {}
        finally:
            conn.close()
    
    def get_all_activities(self, limit=100, doctor_id=None):
        """Get all system activities or for specific doctor"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if doctor_id:
                query = '''
                    SELECT dal.*, u.full_name as doctor_name, p.name as patient_name
                    FROM doctor_activity_logs dal
                    LEFT JOIN doctors d ON dal.doctor_id = d.id
                    LEFT JOIN users u ON d.user_id = u.id
                    LEFT JOIN patients p ON dal.patient_id = p.id
                    WHERE dal.doctor_id = ?
                    ORDER BY dal.timestamp DESC
                    LIMIT ?
                '''
                cursor.execute(query, (doctor_id, limit))
            else:
                query = '''
                    SELECT dal.*, u.full_name as doctor_name, p.name as patient_name
                    FROM doctor_activity_logs dal
                    LEFT JOIN doctors d ON dal.doctor_id = d.id
                    LEFT JOIN users u ON d.user_id = u.id
                    LEFT JOIN patients p ON dal.patient_id = p.id
                    ORDER BY dal.timestamp DESC
                    LIMIT ?
                '''
                cursor.execute(query, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching all activities: {str(e)}")
            return []
        finally:
            conn.close()


class DoctorPatientAssignment:
    """Manage doctor-patient relationships"""
    
    def __init__(self, db_path='hospital.db'):
        self.db_path = db_path
    
    def assign_patient(self, doctor_id, patient_id, notes=None):
        """Assign patient to doctor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO doctor_patient_assignments (doctor_id, patient_id, notes)
                VALUES (?, ?, ?)
            ''', (doctor_id, patient_id, notes))
            conn.commit()
            logger.info(f"Assigned patient {patient_id} to doctor {doctor_id}")
            return True
        except Exception as e:
            logger.error(f"Error assigning patient: {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_doctor_patients(self, doctor_id):
        """Get all patients assigned to a doctor"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT p.*, dpa.assignment_date, dpa.notes
                FROM doctor_patient_assignments dpa
                JOIN patients p ON dpa.patient_id = p.id
                WHERE dpa.doctor_id = ? AND dpa.status = 'active'
                ORDER BY p.name
            ''', (doctor_id,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching doctor patients: {str(e)}")
            return []
        finally:
            conn.close()
    
    def get_patient_doctors(self, patient_id):
        """Get all doctors assigned to a patient"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT d.*, u.full_name, u.email,
                    dpa.assignment_date, dpa.notes
                FROM doctor_patient_assignments dpa
                JOIN doctors d ON dpa.doctor_id = d.id
                JOIN users u ON d.user_id = u.id
                WHERE dpa.patient_id = ? AND dpa.status = 'active'
                ORDER BY u.full_name
            ''', (patient_id,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching patient doctors: {str(e)}")
            return []
        finally:
            conn.close()
    
    def unassign_patient(self, doctor_id, patient_id):
        """Remove patient assignment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE doctor_patient_assignments
                SET status = 'inactive'
                WHERE doctor_id = ? AND patient_id = ?
            ''', (doctor_id, patient_id))
            conn.commit()
            logger.info(f"Unassigned patient {patient_id} from doctor {doctor_id}")
            return True
        except Exception as e:
            logger.error(f"Error unassigning patient: {str(e)}")
            return False
        finally:
            conn.close()
