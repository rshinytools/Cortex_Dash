# ABOUTME: Clinical calculation functions for medical/pharmaceutical calculations
# ABOUTME: Includes BMI, BSA, eGFR, CTCAE grading, and other clinical formulas

import math
from typing import Optional, Union, Literal
from datetime import datetime, date, timedelta
from enum import Enum


class ClinicalFunctions:
    """Library of clinical calculation functions"""
    
    @staticmethod
    def calculate_bmi(
        weight_kg: float,
        height_cm: float
    ) -> float:
        """
        Calculate Body Mass Index (BMI).
        
        Formula: BMI = weight (kg) / height (m)²
        
        Args:
            weight_kg: Weight in kilograms
            height_cm: Height in centimeters
            
        Returns:
            BMI value
        """
        if height_cm <= 0 or weight_kg <= 0:
            return 0
        
        height_m = height_cm / 100
        return round(weight_kg / (height_m ** 2), 1)
    
    @staticmethod
    def calculate_bsa_dubois(
        weight_kg: float,
        height_cm: float
    ) -> float:
        """
        Calculate Body Surface Area using DuBois formula.
        
        Formula: BSA = 0.007184 × weight^0.425 × height^0.725
        
        Args:
            weight_kg: Weight in kilograms
            height_cm: Height in centimeters
            
        Returns:
            BSA in m²
        """
        if height_cm <= 0 or weight_kg <= 0:
            return 0
        
        return round(0.007184 * (weight_kg ** 0.425) * (height_cm ** 0.725), 2)
    
    @staticmethod
    def calculate_bsa_mosteller(
        weight_kg: float,
        height_cm: float
    ) -> float:
        """
        Calculate Body Surface Area using Mosteller formula.
        
        Formula: BSA = √((height × weight) / 3600)
        
        Args:
            weight_kg: Weight in kilograms
            height_cm: Height in centimeters
            
        Returns:
            BSA in m²
        """
        if height_cm <= 0 or weight_kg <= 0:
            return 0
        
        return round(math.sqrt((height_cm * weight_kg) / 3600), 2)
    
    @staticmethod
    def calculate_egfr_ckd_epi(
        creatinine_mg_dl: float,
        age_years: int,
        sex: Literal['M', 'F'],
        race: Literal['black', 'other'] = 'other'
    ) -> float:
        """
        Calculate estimated Glomerular Filtration Rate using CKD-EPI equation.
        
        Args:
            creatinine_mg_dl: Serum creatinine in mg/dL
            age_years: Age in years
            sex: Sex (M or F)
            race: Race (black or other)
            
        Returns:
            eGFR in mL/min/1.73m²
        """
        if creatinine_mg_dl <= 0 or age_years <= 0:
            return 0
        
        # CKD-EPI constants
        if sex == 'F':
            kappa = 0.7
            alpha = -0.329
            sex_factor = 1.018
        else:
            kappa = 0.9
            alpha = -0.411
            sex_factor = 1.0
        
        race_factor = 1.159 if race == 'black' else 1.0
        
        min_cr_kappa = min(creatinine_mg_dl / kappa, 1)
        max_cr_kappa = max(creatinine_mg_dl / kappa, 1)
        
        egfr = 141 * (min_cr_kappa ** alpha) * (max_cr_kappa ** -1.209) * \
               (0.993 ** age_years) * sex_factor * race_factor
        
        return round(egfr, 1)
    
    @staticmethod
    def calculate_egfr_mdrd(
        creatinine_mg_dl: float,
        age_years: int,
        sex: Literal['M', 'F'],
        race: Literal['black', 'other'] = 'other'
    ) -> float:
        """
        Calculate eGFR using MDRD equation.
        
        Formula: 175 × Cr^-1.154 × age^-0.203 × (0.742 if female) × (1.212 if black)
        
        Args:
            creatinine_mg_dl: Serum creatinine in mg/dL
            age_years: Age in years
            sex: Sex (M or F)
            race: Race (black or other)
            
        Returns:
            eGFR in mL/min/1.73m²
        """
        if creatinine_mg_dl <= 0 or age_years <= 0:
            return 0
        
        sex_factor = 0.742 if sex == 'F' else 1.0
        race_factor = 1.212 if race == 'black' else 1.0
        
        egfr = 175 * (creatinine_mg_dl ** -1.154) * (age_years ** -0.203) * \
               sex_factor * race_factor
        
        return round(egfr, 1)
    
    @staticmethod
    def calculate_creatinine_clearance(
        creatinine_mg_dl: float,
        age_years: int,
        weight_kg: float,
        sex: Literal['M', 'F']
    ) -> float:
        """
        Calculate Creatinine Clearance using Cockcroft-Gault equation.
        
        Formula: ((140 - age) × weight × (0.85 if female)) / (72 × Cr)
        
        Args:
            creatinine_mg_dl: Serum creatinine in mg/dL
            age_years: Age in years
            weight_kg: Weight in kilograms
            sex: Sex (M or F)
            
        Returns:
            Creatinine clearance in mL/min
        """
        if creatinine_mg_dl <= 0 or age_years <= 0 or weight_kg <= 0:
            return 0
        
        sex_factor = 0.85 if sex == 'F' else 1.0
        
        crcl = ((140 - age_years) * weight_kg * sex_factor) / (72 * creatinine_mg_dl)
        
        return round(crcl, 1)
    
    @staticmethod
    def calculate_child_pugh_score(
        bilirubin_mg_dl: float,
        albumin_g_dl: float,
        inr: float,
        ascites: Literal['none', 'mild', 'moderate_severe'],
        encephalopathy: Literal['none', 'grade_1_2', 'grade_3_4']
    ) -> dict:
        """
        Calculate Child-Pugh Score for liver disease severity.
        
        Args:
            bilirubin_mg_dl: Total bilirubin in mg/dL
            albumin_g_dl: Albumin in g/dL
            inr: INR value
            ascites: Ascites severity
            encephalopathy: Hepatic encephalopathy grade
            
        Returns:
            Dictionary with score and class
        """
        score = 0
        
        # Bilirubin
        if bilirubin_mg_dl < 2:
            score += 1
        elif bilirubin_mg_dl <= 3:
            score += 2
        else:
            score += 3
        
        # Albumin
        if albumin_g_dl > 3.5:
            score += 1
        elif albumin_g_dl >= 2.8:
            score += 2
        else:
            score += 3
        
        # INR
        if inr < 1.7:
            score += 1
        elif inr <= 2.3:
            score += 2
        else:
            score += 3
        
        # Ascites
        if ascites == 'none':
            score += 1
        elif ascites == 'mild':
            score += 2
        else:
            score += 3
        
        # Encephalopathy
        if encephalopathy == 'none':
            score += 1
        elif encephalopathy == 'grade_1_2':
            score += 2
        else:
            score += 3
        
        # Determine class
        if score <= 6:
            child_class = 'A'
        elif score <= 9:
            child_class = 'B'
        else:
            child_class = 'C'
        
        return {
            'score': score,
            'class': child_class,
            'description': f'Child-Pugh Class {child_class} (Score: {score})'
        }
    
    @staticmethod
    def calculate_meld_score(
        creatinine_mg_dl: float,
        bilirubin_mg_dl: float,
        inr: float,
        dialysis: bool = False
    ) -> int:
        """
        Calculate MELD Score for liver disease.
        
        Formula: 10 × (0.957 × ln(Cr) + 0.378 × ln(bili) + 1.12 × ln(INR)) + 6.43
        
        Args:
            creatinine_mg_dl: Serum creatinine in mg/dL
            bilirubin_mg_dl: Total bilirubin in mg/dL
            inr: INR value
            dialysis: Whether patient is on dialysis
            
        Returns:
            MELD score
        """
        # Apply minimum values
        creatinine = max(creatinine_mg_dl, 1.0)
        bilirubin = max(bilirubin_mg_dl, 1.0)
        inr_val = max(inr, 1.0)
        
        # Cap creatinine at 4.0 if on dialysis
        if dialysis:
            creatinine = min(creatinine, 4.0)
        
        meld = 10 * (0.957 * math.log(creatinine) + 
                    0.378 * math.log(bilirubin) + 
                    1.12 * math.log(inr_val)) + 6.43
        
        # Round and cap between 6 and 40
        meld = round(meld)
        return max(6, min(40, meld))
    
    @staticmethod
    def calculate_sofa_score(
        pao2_fio2: float,
        platelets: float,
        bilirubin_mg_dl: float,
        map_or_vasopressors: Union[float, str],
        gcs: int,
        creatinine_mg_dl: float,
        urine_output_ml_day: Optional[float] = None
    ) -> dict:
        """
        Calculate SOFA (Sequential Organ Failure Assessment) Score.
        
        Args:
            pao2_fio2: PaO2/FiO2 ratio
            platelets: Platelet count (×10³/μL)
            bilirubin_mg_dl: Total bilirubin in mg/dL
            map_or_vasopressors: MAP value or vasopressor type
            gcs: Glasgow Coma Scale
            creatinine_mg_dl: Serum creatinine in mg/dL
            urine_output_ml_day: Urine output in mL/day
            
        Returns:
            Dictionary with component scores and total
        """
        scores = {}
        
        # Respiration
        if pao2_fio2 >= 400:
            scores['respiration'] = 0
        elif pao2_fio2 >= 300:
            scores['respiration'] = 1
        elif pao2_fio2 >= 200:
            scores['respiration'] = 2
        elif pao2_fio2 >= 100:
            scores['respiration'] = 3
        else:
            scores['respiration'] = 4
        
        # Coagulation
        if platelets >= 150:
            scores['coagulation'] = 0
        elif platelets >= 100:
            scores['coagulation'] = 1
        elif platelets >= 50:
            scores['coagulation'] = 2
        elif platelets >= 20:
            scores['coagulation'] = 3
        else:
            scores['coagulation'] = 4
        
        # Liver
        if bilirubin_mg_dl < 1.2:
            scores['liver'] = 0
        elif bilirubin_mg_dl < 2.0:
            scores['liver'] = 1
        elif bilirubin_mg_dl < 6.0:
            scores['liver'] = 2
        elif bilirubin_mg_dl < 12.0:
            scores['liver'] = 3
        else:
            scores['liver'] = 4
        
        # Cardiovascular
        if isinstance(map_or_vasopressors, float):
            if map_or_vasopressors >= 70:
                scores['cardiovascular'] = 0
            else:
                scores['cardiovascular'] = 1
        else:
            # Vasopressor scoring would need more detailed implementation
            scores['cardiovascular'] = 3  # Placeholder
        
        # CNS
        if gcs >= 15:
            scores['cns'] = 0
        elif gcs >= 13:
            scores['cns'] = 1
        elif gcs >= 10:
            scores['cns'] = 2
        elif gcs >= 6:
            scores['cns'] = 3
        else:
            scores['cns'] = 4
        
        # Renal
        if creatinine_mg_dl < 1.2:
            scores['renal'] = 0
        elif creatinine_mg_dl < 2.0:
            scores['renal'] = 1
        elif creatinine_mg_dl < 3.5:
            scores['renal'] = 2
        elif creatinine_mg_dl < 5.0:
            scores['renal'] = 3
        else:
            scores['renal'] = 4
        
        # Adjust renal score based on urine output if provided
        if urine_output_ml_day is not None:
            if urine_output_ml_day < 200:
                scores['renal'] = max(scores['renal'], 4)
            elif urine_output_ml_day < 500:
                scores['renal'] = max(scores['renal'], 3)
        
        total_score = sum(scores.values())
        
        return {
            'total': total_score,
            'components': scores,
            'mortality_risk': self._sofa_mortality_risk(total_score)
        }
    
    @staticmethod
    def _sofa_mortality_risk(score: int) -> str:
        """Get mortality risk based on SOFA score"""
        if score <= 1:
            return '<10%'
        elif score <= 3:
            return '10-20%'
        elif score <= 6:
            return '20-40%'
        elif score <= 9:
            return '40-50%'
        elif score <= 12:
            return '50-60%'
        else:
            return '>80%'
    
    @staticmethod
    def calculate_study_day(
        event_date: Union[datetime, date],
        reference_date: Union[datetime, date]
    ) -> int:
        """
        Calculate study day based on reference date.
        
        ICH E9 convention:
        - Day before reference date = -1
        - Reference date = 1
        - Day after reference date = 2
        
        Args:
            event_date: Date of the event
            reference_date: Reference date (e.g., first dose date)
            
        Returns:
            Study day
        """
        if isinstance(event_date, datetime):
            event_date = event_date.date()
        if isinstance(reference_date, datetime):
            reference_date = reference_date.date()
        
        delta_days = (event_date - reference_date).days
        
        if delta_days >= 0:
            return delta_days + 1
        else:
            return delta_days  # Negative days remain negative
    
    @staticmethod
    def calculate_age(
        birth_date: Union[datetime, date],
        reference_date: Optional[Union[datetime, date]] = None
    ) -> int:
        """
        Calculate age in years.
        
        Args:
            birth_date: Date of birth
            reference_date: Reference date (default: today)
            
        Returns:
            Age in years
        """
        if isinstance(birth_date, datetime):
            birth_date = birth_date.date()
        
        if reference_date is None:
            reference_date = date.today()
        elif isinstance(reference_date, datetime):
            reference_date = reference_date.date()
        
        age = reference_date.year - birth_date.year
        
        # Adjust if birthday hasn't occurred this year
        if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
            age -= 1
        
        return age
    
    @staticmethod
    def map_ctcae_grade(
        value: float,
        parameter: str,
        unit: str = None
    ) -> int:
        """
        Map laboratory values to CTCAE v5.0 grades.
        
        This is a simplified example - full implementation would need
        complete CTCAE grading criteria.
        
        Args:
            value: Lab value
            parameter: Lab parameter name
            unit: Unit of measurement
            
        Returns:
            CTCAE grade (0-5)
        """
        # Example grading for common parameters
        # This would need to be expanded with full CTCAE criteria
        
        grades = {
            'hemoglobin': [
                (10, 0),  # >= 10 g/dL: Grade 0
                (8, 1),   # 8-10: Grade 1
                (7, 2),   # 7-8: Grade 2
                (6.5, 3), # 6.5-7: Grade 3
                (0, 4),   # < 6.5: Grade 4
            ],
            'neutrophils': [
                (1.5, 0),  # >= 1.5 × 10⁹/L: Grade 0
                (1.0, 1),  # 1.0-1.5: Grade 1
                (0.5, 2),  # 0.5-1.0: Grade 2
                (0.2, 3),  # 0.2-0.5: Grade 3
                (0, 4),    # < 0.2: Grade 4
            ],
            'platelets': [
                (75, 0),   # >= 75 × 10⁹/L: Grade 0
                (50, 1),   # 50-75: Grade 1
                (25, 2),   # 25-50: Grade 2
                (10, 3),   # 10-25: Grade 3
                (0, 4),    # < 10: Grade 4
            ],
        }
        
        param_lower = parameter.lower()
        if param_lower in grades:
            for threshold, grade in grades[param_lower]:
                if value >= threshold:
                    return grade
        
        return 0  # Default to Grade 0 if parameter not found