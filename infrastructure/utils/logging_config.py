"""
infrastructure/utils/logging_config.py

Configuración profesional de logging para aplicación médica.
Maneja logs estructurados, rotación de archivos, y diferentes
niveles de logging para auditoría y depuración médica.
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import json


class MedicalFormatter(logging.Formatter):
    """
    Formateador personalizado para logs médicos.
    
    Incluye información relevante para auditoría médica:
    - Timestamp preciso
    - Nivel de criticidad
    - Contexto médico cuando está disponible
    - Información de usuario/sesión
    """
    
    def __init__(self):
        # Formato base para logs médicos
        super().__init__(
            fmt='%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def format(self, record):
        """Formato personalizado para diferentes tipos de log."""
        # Añadir contexto médico si está disponible
        if hasattr(record, 'patient_id'):
            record.message = f"[Patient: {record.patient_id}] {record.getMessage()}"
        elif hasattr(record, 'study_uid'):
            record.message = f"[Study: {record.study_uid}] {record.getMessage()}"
        else:
            record.message = record.getMessage()
        
        # Formatear según nivel de criticidad
        if record.levelno >= logging.CRITICAL:
            # Logs críticos con más detalle
            record.message = f"🚨 CRITICAL: {record.message}"
        elif record.levelno >= logging.ERROR:
            record.message = f"❌ ERROR: {record.message}"
        elif record.levelno >= logging.WARNING:
            record.message = f"⚠️  WARNING: {record.message}"
        elif record.levelno >= logging.INFO:
            record.message = f"ℹ️  INFO: {record.message}"
        else:
            record.message = f"🔍 DEBUG: {record.message}"
        
        return super().format(record)


class AuditFormatter(logging.Formatter):
    """
    Formateador para logs de auditoría médica.
    Genera logs estructurados en formato JSON para compliance.
    """
    
    def format(self, record):
        """Genera log estructurado para auditoría."""
        audit_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'module': record.name,
            'message': record.getMessage(),
            'thread': record.thread,
            'process': record.process
        }
        
        # Añadir contexto médico específico
        medical_context = {}
        for attr in ['patient_id', 'study_uid', 'series_uid', 'user_id', 
                     'action_type', 'anatomical_region', 'ai_model']:
            if hasattr(record, attr):
                medical_context[attr] = getattr(record, attr)
        
        if medical_context:
            audit_entry['medical_context'] = medical_context
        
        # Añadir información de excepción si existe
        if record.exc_info:
            audit_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        return json.dumps(audit_entry, ensure_ascii=False)


class SecurityFilter(logging.Filter):
    """
    Filtro de seguridad para logs médicos.
    Remueve información sensible antes del logging.
    """
    
    def __init__(self):
        super().__init__()
        # Patrones de información sensible a filtrar
        self.sensitive_patterns = [
            r'\b\d{4}-\d{4}-\d{4}-\d{4}\b',  # Números de tarjeta
            r'\b\d{3}-\d{2}-\d{4}\b',        # SSN
            r'\bpassword\s*[=:]\s*\S+\b',    # Passwords
        ]
    
    def filter(self, record):
        """Filtra información sensible del mensaje."""
        import re
        
        message = record.getMessage()
        
        # Aplicar filtros de seguridad
        for pattern in self.sensitive_patterns:
            message = re.sub(pattern, '[REDACTED]', message, flags=re.IGNORECASE)
        
        # Actualizar mensaje filtrado
        record.msg = message
        record.args = ()
        
        return True


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    console_output: bool = True,
    enable_audit_log: bool = True,
    max_file_size_mb: int = 10,
    backup_count: int = 5
) -> logging.Logger:
    """
    Configura el sistema de logging para la aplicación médica.
    
    Args:
        log_level: Nivel mínimo de logging
        log_file: Ruta del archivo de log principal
        console_output: Si mostrar logs en consola
        enable_audit_log: Si crear log de auditoría separado
        max_file_size_mb: Tamaño máximo de archivo antes de rotación
        backup_count: Número de archivos de backup a mantener
        
    Returns:
        Logger principal configurado
    """
    # Crear directorio de logs si no existe
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Limpiar handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Crear formatters
    medical_formatter = MedicalFormatter()
    audit_formatter = AuditFormatter()
    
    # Crear filtro de seguridad
    security_filter = SecurityFilter()
    
    # 1. Handler para consola (si está habilitado)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(medical_formatter)
        console_handler.addFilter(security_filter)
        root_logger.addHandler(console_handler)
    
    # 2. Handler para archivo principal (con rotación)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(medical_formatter)
        file_handler.addFilter(security_filter)
        root_logger.addHandler(file_handler)
    
    # 3. Handler para errores críticos (archivo separado)
    if log_file:
        error_log_file = str(Path(log_file).with_suffix('.errors.log'))
        error_handler = logging.handlers.RotatingFileHandler(
            filename=error_log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(medical_formatter)
        error_handler.addFilter(security_filter)
        root_logger.addHandler(error_handler)
    
    # 4. Handler para auditoría médica (si está habilitado)
    if enable_audit_log and log_file:
        audit_log_file = str(Path(log_file).with_suffix('.audit.jsonl'))
        audit_handler = logging.handlers.RotatingFileHandler(
            filename=audit_log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count * 2,  # Mantener más auditoría
            encoding='utf-8'
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(audit_formatter)
        
        # Crear logger específico para auditoría
        audit_logger = logging.getLogger('medical_audit')
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.INFO)
        audit_logger.propagate = False  # No propagar a root logger
    
    # 5. Configurar loggers específicos de terceros
    _configure_third_party_loggers(log_level)
    
    # Log inicial del sistema
    main_logger = logging.getLogger('medical_imaging')
    main_logger.info("Sistema de logging médico inicializado")
    main_logger.info(f"Nivel de log: {logging.getLevelName(log_level)}")
    main_logger.info(f"Archivo principal: {log_file or 'No configurado'}")
    main_logger.info(f"Auditoría habilitada: {enable_audit_log}")
    
    return main_logger


def _configure_third_party_loggers(log_level: int) -> None:
    """Configura niveles de log para librerías de terceros."""
    # Reducir verbosidad de librerías externas
    third_party_loggers = {
        'vtk': logging.WARNING,
        'SimpleITK': logging.WARNING,
        'pydicom': logging.WARNING,
        'matplotlib': logging.WARNING,
        'PIL': logging.WARNING,
        'urllib3': logging.WARNING,
        'requests': logging.WARNING,
        'asyncio': logging.WARNING,
        'PyQt6': logging.WARNING
    }
    
    for logger_name, level in third_party_loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(max(level, log_level))


class MedicalLogger:
    """
    Logger especializado para contexto médico.
    Facilita el logging con información de contexto médico automática.
    """
    
    def __init__(self, name: str):
        """
        Inicializa logger médico.
        
        Args:
            name: Nombre del logger
        """
        self.logger = logging.getLogger(name)
        self.audit_logger = logging.getLogger('medical_audit')
        self._medical_context = {}
    
    def set_medical_context(
        self,
        patient_id: Optional[str] = None,
        study_uid: Optional[str] = None,
        series_uid: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Establece contexto médico para logs subsecuentes.
        
        Args:
            patient_id: ID del paciente
            study_uid: UID del estudio
            series_uid: UID de la serie
            user_id: ID del usuario
            **kwargs: Contexto adicional
        """
        self._medical_context = {
            'patient_id': patient_id,
            'study_uid': study_uid,
            'series_uid': series_uid,
            'user_id': user_id,
            **kwargs
        }
    
    def clear_context(self) -> None:
        """Limpia el contexto médico."""
        self._medical_context.clear()
    
    def _log_with_context(self, level: int, message: str, **kwargs) -> None:
        """Log con contexto médico automático."""
        # Crear record con contexto
        record = self.logger.makeRecord(
            self.logger.name, level, '', 0, message, (), None
        )
        
        # Añadir contexto médico
        for key, value in self._medical_context.items():
            if value is not None:
                setattr(record, key, value)
        
        # Añadir contexto adicional
        for key, value in kwargs.items():
            setattr(record, key, value)
        
        # Enviar log
        self.logger.handle(record)
    
    def info(self, message: str, **kwargs) -> None:
        """Log nivel INFO con contexto médico."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log nivel WARNING con contexto médico."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log nivel ERROR con contexto médico."""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log nivel CRITICAL con contexto médico."""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log nivel DEBUG con contexto médico."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def audit(
        self, 
        action: str, 
        outcome: str = "success",
        details: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log de auditoría médica.
        
        Args:
            action: Acción realizada
            outcome: Resultado de la acción
            details: Detalles adicionales
            **kwargs: Contexto adicional
        """
        audit_message = f"Action: {action} | Outcome: {outcome}"
        if details:
            audit_message += f" | Details: {details}"
        
        # Crear record de auditoría
        record = self.audit_logger.makeRecord(
            self.audit_logger.name, logging.INFO, '', 0, audit_message, (), None
        )
        
        # Añadir contexto médico y adicional
        for key, value in {**self._medical_context, **kwargs}.items():
            if value is not None:
                setattr(record, key, value)
        
        # Marcar como auditoría
        setattr(record, 'action_type', action)
        
        # Enviar a auditoría
        self.audit_logger.handle(record)


def get_medical_logger(name: str) -> MedicalLogger:
    """
    Obtiene un logger médico para un módulo específico.
    
    Args:
        name: Nombre del módulo/componente
        
    Returns:
        Logger médico configurado
    """
    return MedicalLogger(name)


# Configuración de excepciones no capturadas
def log_uncaught_exceptions(exc_type, exc_value, exc_traceback):
    """
    Handler para excepciones no capturadas.
    
    Args:
        exc_type: Tipo de excepción
        exc_value: Valor de la excepción
        exc_traceback: Traceback de la excepción
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # Permitir KeyboardInterrupt normal
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Log de excepción crítica
    logger = logging.getLogger('uncaught_exceptions')
    logger.critical(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    
    # Auditoría de error crítico
    audit_logger = logging.getLogger('medical_audit')
    audit_record = audit_logger.makeRecord(
        audit_logger.name, logging.CRITICAL, '', 0,
        f"Uncaught exception: {exc_type.__name__}: {exc_value}", (), 
        (exc_type, exc_value, exc_traceback)
    )
    setattr(audit_record, 'action_type', 'system_error')
    setattr(audit_record, 'error_severity', 'critical')
    audit_logger.handle(audit_record)


# Instalar handler de excepciones no capturadas
sys.excepthook = log_uncaught_exceptions