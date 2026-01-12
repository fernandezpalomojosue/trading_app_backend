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

def is_trading_day(date: datetime) -> bool:
    """
    Verifica si una fecha es día hábil (lunes-viernes).
    
    Args:
        date: Fecha a verificar
        
    Returns:
        bool: True si es día hábil, False si es fin de semana
    """
    return date.weekday() < 5  # 0-4 = lunes-viernes

def get_previous_trading_days(days: int, end_date: Optional[datetime] = None) -> list:
    """
    Obtiene los últimos N días hábiles.
    
    Args:
        days: Número de días hábiles a obtener
        end_date: Fecha final (por defecto: hoy)
        
    Returns:
        list: Lista de fechas en formato YYYY-MM-DD
    """
    if end_date is None:
        end_date = datetime.utcnow()
    
    trading_days = []
    current_date = end_date
    
    while len(trading_days) < days:
        current_date -= timedelta(days=1)
        if is_trading_day(current_date):
            trading_days.append(current_date.strftime("%Y-%m-%d"))
    
    return trading_days
