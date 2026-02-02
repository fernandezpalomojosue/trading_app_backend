# app/utils/date_utils.py
"""
Utilidades para manejo de fechas de mercado
"""

from datetime import datetime, timedelta
from typing import Optional

def get_last_trading_day(target_date: Optional[datetime] = None) -> str:
    """
    Obtiene el último día hábil (no fin de semana) anterior a la fecha objetivo.
    
    Args:
        target_date: Fecha objetivo (por defecto: hoy)
        
    Returns:
        str: Fecha del último día hábil en formato YYYY-MM-DD
    """
    if target_date is None:
        target_date = datetime.utcnow()
    
    # Si es lunes (weekday()=0), el último día hábil fue el viernes pasado
    if target_date.weekday() == 0:  # Lunes
        last_trading_day = target_date - timedelta(days=3)  # Viernes
    # Si es domingo (weekday()=6), el último día hábil fue el viernes pasado  
    elif target_date.weekday() == 6:  # Domingo
        last_trading_day = target_date - timedelta(days=2)  # Viernes
    # Si es sábado (weekday()=5), el último día hábil fue el viernes pasado
    elif target_date.weekday() == 5:  # Sábado
        last_trading_day = target_date - timedelta(days=1)  # Viernes
    else:
        # Es día de semana (martes-viernes), usar día anterior
        last_trading_day = target_date - timedelta(days=1)
    
    return last_trading_day.strftime("%Y-%m-%d")


