#!/usr/bin/env python3
"""
infrastructure/utils/logging_config.py

Sistema de logging especializado para aplicaciones médicas.
Implementa logging compatible con HIPAA, auditoría médica, y 
trazabilidad completa requerida para software médico crítico.

Este módulo proporciona funcionalidad de logging que tu sistema
refactorizado necesita para operar correctamente.
"""

import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union
import sys


class MedicalLogFormatter(logging.Formatter):
    """
    Formateador especializado para logs médicos.
    
    Asegura que toda información médica esté apropiadamente
    formateada y sea compatible con auditorías HIPAA.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formatea logs con estructura médica estándar.
        
        Args:
            record: Registro de log a formatear
            
        Returns:
            String formateado para logging médico
        """
        # Crear timestamp médico estándar
        medical_timestamp = datetime.fromtimestamp(record.created).isoformat()
        
        # Estructura base del log médico
        log_data = {
            'timestamp': medical_timestamp,
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Agregar información de contexto médico si existe
        if hasattr(record, 'medical_context'):
            log_data['medical_context'] = record.medical_context
        
        if hasattr(record, 'patient_id'):
            # Nota: En implementación real, el patient_id debería estar
            # hasheado o encriptado para cumplimiento HIPAA
            log_data['patient_context'] = f"PATIENT_{hash(record.patient_id) % 10000:04d}"
        
        if hasattr(record, 'workflow_id'):
            log_data['workflow_id'] = record.workflow_id
        
        # Formatear como JSON para facilidad de parsing
        return json.dumps(log_data, ensure_ascii=False)


class HIPAACompliantFilter(logging.Filter):
    """
    Filtro que asegura cumplimiento HIPAA removiendo información sensible.
    
    En software médico real, este filtro sería mucho más sofisticado
    y estaría configurado según las regulaciones específicas aplicables.
    """
    
    def __init__(self):
        super().__init__()
        # Patrones que deben ser filtrados para cumplimiento HIPAA
        self.sensitive_patterns = [
            'ssn', 'social_security', 'birth_date', 
            'address', 'phone', 'email_personal'
        ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filtra logs para asegurar cumplimiento HIPAA.
        
        Args:
            record: Registro de log a evaluar
            
        Returns:
            True si el log puede ser registrado, False si debe ser filtrado
        """
        # En implementación real, aquí habría lógica sofisticada
        # para detectar y filtrar información médica sensible
        
        message = record.getMessage().lower()
        
        # Filtrar mensajes que contengan información potencialmente sensible
        for pattern in self.sensitive_patterns:
            if pattern in message:
                # En lugar de bloquear completamente, podríamos redactar
                record.msg = record.msg.replace(pattern, '[REDACTED_FOR_HIPAA]')
        
        return True


def setup_medical_logging(
    log_level: Union[str, int] = logging.INFO,
    log_file: Optional[str] = None,
    console_output: bool = True,
    medical_audit: bool = True,
    hipaa_compliant: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configura sistema de logging completo para aplicaciones médicas.
    
    Esta función establece un sistema de logging que cumple con
    los requisitos específicos de software médico, incluyendo
    auditoría, trazabilidad, y cumplimiento regulatorio.
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Ruta del archivo de log (opcional)
        console_output: Si mostrar logs en consola
        medical_audit: Si habilitar funciones de auditoría médica
        hipaa_compliant: Si aplicar filtros de cumplimiento HIPAA
        max_file_size: Tamaño máximo del archivo de log en bytes
        backup_count: Número de archivos de backup a mantener
        
    Returns:
        Logger configurado para uso médico
        
    Raises:
        OSError: Si no se puede crear directorio de logs
        PermissionError: Si no hay permisos para escribir logs
    """
    # Crear logger raíz para la aplicación médica
    logger = logging.getLogger('medical_workstation')
    
    # Limpiar handlers existentes para evitar duplicación
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Configurar nivel de logging
    if isinstance(log_level, str):
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    else:
        numeric_level = log_level
    
    logger.setLevel(numeric_level)
    
    # Configurar formateador médico
    if medical_audit:
        formatter = MedicalLogFormatter()
    else:
        # Formateador estándar para desarrollo
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Configurar handler de consola si se solicita
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        
        # Aplicar filtro HIPAA si está habilitado
        if hipaa_compliant:
            console_handler.addFilter(HIPAACompliantFilter())
        
        logger.addHandler(console_handler)
    
    # Configurar handler de archivo si se especifica
    if log_file:
        # Asegurar que el directorio existe
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Usar RotatingFileHandler para evitar archivos de log masivos
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        
        # Aplicar filtro HIPAA si está habilitado
        if hipaa_compliant:
            file_handler.addFilter(HIPAACompliantFilter())
        
        logger.addHandler(file_handler)
    
    # Configurar handler especial para auditoría médica
    if medical_audit and log_file:
        # Crear archivo separado para auditoría médica
        audit_file = str(log_path.parent / f"{log_path.stem}_audit.jsonl")
        
        audit_handler = logging.handlers.RotatingFileHandler(
            audit_file,
            maxBytes=max_file_size,
            backupCount=backup_count * 2,  # Mantener más auditorías
            encoding='utf-8'
        )
        
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(MedicalLogFormatter())
        
        # Filtro específico para auditoría médica
        if hipaa_compliant:
            audit_handler.addFilter(HIPAACompliantFilter())
        
        logger.addHandler(audit_handler)
    
    # Log inicial para confirmar configuración
    logger.info("Sistema de logging médico configurado correctamente", extra={
        'medical_context': 'system_initialization',
        'log_level': numeric_level,
        'medical_audit': medical_audit,
        'hipaa_compliant': hipaa_compliant,
        'log_file': log_file
    })
    
    return logger


def create_medical_log_entry(
    logger: logging.Logger,
    level: str,
    message: str,
    medical_context: Optional[str] = None,
    patient_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Crea entrada de log especializada para contexto médico.
    
    Esta función facilita la creación de logs médicos con toda
    la información de contexto necesaria para auditoría y trazabilidad.
    
    Args:
        logger: Logger a usar
        level: Nivel del log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Mensaje principal del log
        medical_context: Contexto médico específico
        patient_id: ID del paciente (será hasheado para HIPAA)
        workflow_id: ID del flujo de trabajo médico
        additional_data: Datos adicionales para el log
    """
    # Preparar información extra para el log
    extra_data = {}
    
    if medical_context:
        extra_data['medical_context'] = medical_context
    
    if patient_id:
        extra_data['patient_id'] = patient_id
    
    if workflow_id:
        extra_data['workflow_id'] = workflow_id
    
    if additional_data:
        extra_data.update(additional_data)
    
    # Obtener método de logging apropiado
    log_method = getattr(logger, level.lower(), logger.info)
    
    # Crear entrada de log con contexto médico
    log_method(message, extra=extra_data)


def setup_development_logging() -> logging.Logger:
    """
    Configuración de logging simplificada para desarrollo.
    
    Esta función proporciona una configuración de logging más simple
    y legible para uso durante desarrollo y debugging.
    
    Returns:
        Logger configurado para desarrollo
    """
    return setup_medical_logging(
        log_level=logging.DEBUG,
        log_file="./logs/development.log",
        console_output=True,
        medical_audit=False,
        hipaa_compliant=False
    )


# Función de conveniencia para compatibilidad con el código existente
def get_medical_logger(name: str = 'medical_workstation') -> logging.Logger:
    """
    Obtiene logger médico ya configurado.
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger configurado para uso médico
    """
    return logging.getLogger(name)


# Ejemplo de uso para testing
if __name__ == "__main__":
    # Configurar logging médico para pruebas
    logger = setup_medical_logging(
        log_level="DEBUG",
        log_file="./logs/test_medical.log",
        console_output=True,
        medical_audit=True,
        hipaa_compliant=True
    )
    
    # Probar diferentes tipos de logs médicos
    logger.info("Sistema médico iniciado")
    
    create_medical_log_entry(
        logger,
        "INFO",
        "Imagen médica cargada exitosamente",
        medical_context="image_loading",
        workflow_id="img_load_001",
        additional_data={
            "modality": "MRI",
            "image_size": "512x512x32"
        }
    )
    
    create_medical_log_entry(
        logger,
        "WARNING",
        "Análisis de IA completado con baja confianza",
        medical_context="ai_analysis",
        patient_id="PATIENT_12345",
        workflow_id="ai_analysis_002",
        additional_data={
            "confidence_score": 0.65,
            "requires_review": True
        }
    )
    
    logger.info("Prueba de logging médico completada")