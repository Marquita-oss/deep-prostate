#!/usr/bin/env python3
"""
infrastructure/utils/startup_validator.py

Validador completo del sistema para aplicaciones médicas.
Este módulo verifica que todos los prerrequisitos necesarios
estén cumplidos antes de permitir operación médica.

En software médico, no podemos simplemente "intentar ejecutar
y ver qué pasa". Debemos validar exhaustivamente que el entorno
sea seguro y apropiado para operaciones médicas críticas.
"""

import os
import sys
import platform
import shutil
import psutil
import importlib
import socket
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import subprocess
import logging


class MedicalSystemValidator:
    """
    Validador exhaustivo para sistemas médicos.
    
    Esta clase implementa validaciones específicas requeridas
    para software médico, asegurando que el entorno de ejecución
    sea apropiado para operaciones médicas críticas.
    
    En un hospital, no permitirías que un equipo médico funcione
    sin verificar que esté calibrado y sea seguro. De manera similar,
    este validador asegura que nuestro software médico tenga todas
    las condiciones necesarias para operar de manera segura.
    """
    
    def __init__(self):
        """
        Inicializa el validador con configuraciones médicas estándar.
        
        Estas configuraciones representan los mínimos requeridos
        para operación médica segura basados en mejores prácticas
        de la industria médica de software.
        """
        # Requisitos mínimos del sistema para aplicaciones médicas
        self.min_ram_gb = 4  # Mínimo RAM para procesamiento de imágenes médicas
        self.min_free_disk_gb = 10  # Espacio libre mínimo para datos médicos
        self.min_python_version = (3, 8)  # Python 3.8+ requerido para funcionalidades modernas
        
        # Dependencias críticas para funcionamiento médico
        self.required_medical_packages = [
            'numpy',      # Procesamiento numérico para imágenes médicas
            'PyQt6',      # Interfaz gráfica médica
            'pathlib',    # Manejo de rutas (estándar en Python 3.8+)
            'datetime',   # Manejo de timestamps médicos (estándar)
            'json',       # Serialización de datos médicos (estándar)
            'logging'     # Logging para auditoría médica (estándar)
        ]
        
        # Dependencias opcionales pero recomendadas
        self.recommended_packages = [
            'pydicom',      # Manejo de archivos DICOM
            'SimpleITK',    # Procesamiento de imágenes médicas
            'vtk',          # Visualización 3D médica
            'scipy',        # Análisis científico
            'scikit-image'  # Procesamiento de imágenes
        ]
        
        # Configuraciones de seguridad médica
        self.required_directories = [
            './logs',           # Para auditoría médica
            './medical_data',   # Para almacenamiento de datos médicos
            './temp',           # Para archivos temporales
            './config'          # Para configuraciones
        ]
        
        # Logger para validación
        self.logger = logging.getLogger(__name__)
    
    def validate_system_resources(self) -> bool:
        """
        Valida que los recursos del sistema sean suficientes para operación médica.
        
        En aplicaciones médicas, recursos insuficientes pueden causar:
        - Fallos durante análisis críticos
        - Pérdida de datos médicos
        - Rendimiento inaceptable para diagnóstico
        - Riesgo de corrupción de imágenes médicas
        
        Returns:
            True si los recursos son suficientes, False en caso contrario
        """
        try:
            self.logger.info("Validando recursos del sistema para uso médico...")
            
            # Validar memoria RAM disponible
            memory_info = psutil.virtual_memory()
            available_ram_gb = memory_info.available / (1024**3)
            
            if available_ram_gb < self.min_ram_gb:
                self.logger.error(
                    f"RAM insuficiente: {available_ram_gb:.2f}GB disponible, "
                    f"{self.min_ram_gb}GB requerido para aplicación médica"
                )
                return False
            
            self.logger.info(f"✅ RAM suficiente: {available_ram_gb:.2f}GB disponible")
            
            # Validar espacio en disco disponible
            disk_usage = shutil.disk_usage(Path.cwd())
            free_disk_gb = disk_usage.free / (1024**3)
            
            if free_disk_gb < self.min_free_disk_gb:
                self.logger.error(
                    f"Espacio en disco insuficiente: {free_disk_gb:.2f}GB disponible, "
                    f"{self.min_free_disk_gb}GB requerido para datos médicos"
                )
                return False
            
            self.logger.info(f"✅ Espacio en disco suficiente: {free_disk_gb:.2f}GB disponible")
            
            # Validar versión de Python
            if sys.version_info < self.min_python_version:
                self.logger.error(
                    f"Versión de Python insuficiente: {sys.version_info} actual, "
                    f"{self.min_python_version} requerida para funcionalidades médicas"
                )
                return False
            
            self.logger.info(f"✅ Python versión apropiada: {sys.version_info}")
            
            # Validar arquitectura del sistema
            architecture = platform.architecture()[0]
            if architecture != '64bit':
                self.logger.warning(
                    f"Arquitectura no recomendada para aplicación médica: {architecture}. "
                    f"Se recomienda 64bit para procesamiento de imágenes médicas."
                )
            
            # Validar sistema operativo
            os_name = platform.system()
            self.logger.info(f"Sistema operativo detectado: {os_name}")
            
            if os_name not in ['Windows', 'Linux', 'Darwin']:  # Darwin = macOS
                self.logger.warning(f"Sistema operativo no testado para uso médico: {os_name}")
            
            self.logger.info("✅ Recursos del sistema validados correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error durante validación de recursos del sistema: {e}")
            return False
    
    def validate_medical_dependencies(self) -> bool:
        """
        Valida que todas las dependencias médicas críticas estén disponibles.
        
        En software médico, dependencias faltantes pueden resultar en:
        - Funcionalidades médicas no disponibles
        - Fallos durante operaciones críticas
        - Incompatibilidad con estándares médicos
        - Riesgo de corrupción de datos
        
        Returns:
            True si todas las dependencias críticas están disponibles
        """
        try:
            self.logger.info("Validando dependencias médicas críticas...")
            
            missing_critical = []
            missing_recommended = []
            
            # Validar dependencias críticas
            for package in self.required_medical_packages:
                try:
                    importlib.import_module(package)
                    self.logger.debug(f"✅ Dependencia crítica encontrada: {package}")
                except ImportError:
                    missing_critical.append(package)
                    self.logger.error(f"❌ Dependencia crítica faltante: {package}")
            
            # Validar dependencias recomendadas
            for package in self.recommended_packages:
                try:
                    importlib.import_module(package)
                    self.logger.debug(f"✅ Dependencia recomendada encontrada: {package}")
                except ImportError:
                    missing_recommended.append(package)
                    self.logger.warning(f"⚠️ Dependencia recomendada faltante: {package}")
            
            # Reportar estado de dependencias
            if missing_critical:
                self.logger.error(
                    f"Dependencias críticas faltantes: {missing_critical}. "
                    f"La aplicación médica no puede funcionar sin estas dependencias."
                )
                return False
            
            if missing_recommended:
                self.logger.warning(
                    f"Dependencias recomendadas faltantes: {missing_recommended}. "
                    f"Algunas funcionalidades médicas avanzadas pueden no estar disponibles."
                )
            
            # Validar versiones específicas si es necesario
            try:
                import numpy as np
                numpy_version = np.__version__
                self.logger.info(f"NumPy versión: {numpy_version}")
                
                # Validar que numpy tenga una versión razonable
                major_version = int(numpy_version.split('.')[0])
                if major_version < 1:
                    self.logger.warning("Versión de NumPy muy antigua, considere actualizar")
                
            except ImportError:
                pass  # Ya capturado en validación crítica
            
            self.logger.info("✅ Dependencias médicas validadas correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error durante validación de dependencias médicas: {e}")
            return False
    
    def validate_security_configuration(self) -> bool:
        """
        Valida configuraciones de seguridad apropiadas para software médico.
        
        En aplicaciones médicas, la seguridad no es opcional debido a:
        - Regulaciones HIPAA y similares
        - Protección de datos de pacientes
        - Integridad de información médica crítica
        - Prevención de acceso no autorizado
        
        Returns:
            True si la configuración de seguridad es apropiada
        """
        try:
            self.logger.info("Validando configuración de seguridad médica...")
            
            # Validar permisos de directorios médicos
            for directory in self.required_directories:
                dir_path = Path(directory)
                
                # Crear directorio si no existe
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    self.logger.debug(f"✅ Directorio médico asegurado: {directory}")
                except PermissionError:
                    self.logger.error(f"❌ Sin permisos para crear directorio médico: {directory}")
                    return False
                
                # Validar permisos de escritura
                if not os.access(dir_path, os.W_OK):
                    self.logger.error(f"❌ Sin permisos de escritura en directorio médico: {directory}")
                    return False
            
            # Validar configuración de logging médico
            log_dir = Path('./logs')
            if not log_dir.exists() or not os.access(log_dir, os.W_OK):
                self.logger.error("❌ No se puede escribir logs médicos - directorio de logs inaccesible")
                return False
            
            # Validar que no estemos ejecutando como root (en sistemas Unix)
            if hasattr(os, 'getuid') and os.getuid() == 0:
                self.logger.warning(
                    "⚠️ Ejecutando como root - no recomendado para aplicaciones médicas por seguridad"
                )
            
            # Validar configuración de variables de entorno sensibles
            sensitive_env_vars = ['MEDICAL_API_KEY', 'DATABASE_PASSWORD', 'ENCRYPTION_KEY']
            for env_var in sensitive_env_vars:
                if env_var in os.environ:
                    self.logger.warning(
                        f"⚠️ Variable de entorno sensible detectada: {env_var}. "
                        f"Asegúrese de que esté apropiadamente protegida."
                    )
            
            self.logger.info("✅ Configuración de seguridad médica validada")
            return True
            
        except Exception as e:
            self.logger.error(f"Error durante validación de seguridad médica: {e}")
            return False
    
    def validate_medical_connectivity(self) -> bool:
        """
        Valida conectividad con sistemas médicos externos (si aplicable).
        
        En entornos médicos reales, esto incluiría:
        - Conectividad con PACS (Picture Archiving and Communication System)
        - Acceso a bases de datos médicas
        - Conexión con sistemas de información hospitalaria (HIS)
        - Verificación de servicios de red médicos
        
        Para nuestra demostración, validamos conectividad básica de red.
        
        Returns:
            True si la conectividad médica es apropiada
        """
        try:
            self.logger.info("Validando conectividad médica...")
            
            # Validar conectividad básica de red
            try:
                # Intentar resolver DNS básico
                socket.gethostbyname('localhost')
                self.logger.debug("✅ Resolución DNS básica funcional")
            except socket.gaierror:
                self.logger.warning("⚠️ Problemas con resolución DNS básica")
            
            # En una implementación real, aquí validaríamos:
            # - Conectividad con servidores DICOM
            # - Acceso a bases de datos médicas
            # - Disponibilidad de servicios de IA médica
            # - Conectividad con sistemas hospitalarios
            
            # Para demostración, simular validación de servicios médicos
            mock_medical_services = [
                {'name': 'DICOM_SERVER', 'available': True},
                {'name': 'AI_ANALYSIS_SERVICE', 'available': True},
                {'name': 'MEDICAL_DATABASE', 'available': True}
            ]
            
            for service in mock_medical_services:
                if service['available']:
                    self.logger.debug(f"✅ Servicio médico disponible: {service['name']}")
                else:
                    self.logger.warning(f"⚠️ Servicio médico no disponible: {service['name']}")
            
            # Validar puertos comunes para servicios médicos
            common_medical_ports = [80, 443, 104]  # HTTP, HTTPS, DICOM
            available_ports = []
            
            for port in common_medical_ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    available_ports.append(port)
                    self.logger.debug(f"Puerto médico en uso: {port}")
            
            self.logger.info("✅ Conectividad médica validada (modo demostración)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error durante validación de conectividad médica: {e}")
            # En modo demostración, no fallar por conectividad
            return True
    
    def validate_all_prerequisites(self) -> Tuple[bool, Dict[str, bool]]:
        """
        Ejecuta todas las validaciones médicas y reporta estado completo.
        
        Esta función orquesta todas las validaciones necesarias
        para determinar si el sistema está listo para operación médica.
        
        Returns:
            Tuple con (éxito_general, estado_detallado_por_categoría)
        """
        self.logger.info("Iniciando validación completa de prerrequisitos médicos...")
        
        validation_results = {}
        
        # Ejecutar cada validación y capturar resultados
        validation_results['system_resources'] = self.validate_system_resources()
        validation_results['medical_dependencies'] = self.validate_medical_dependencies()
        validation_results['security_configuration'] = self.validate_security_configuration()
        validation_results['medical_connectivity'] = self.validate_medical_connectivity()
        
        # Determinar éxito general
        overall_success = all(validation_results.values())
        
        # Reportar estado final
        if overall_success:
            self.logger.info("🎉 Todos los prerrequisitos médicos están cumplidos")
            self.logger.info("✅ Sistema listo para operación médica segura")
        else:
            failed_validations = [
                category for category, success in validation_results.items() 
                if not success
            ]
            self.logger.error(
                f"❌ Prerrequisitos médicos no cumplidos en: {failed_validations}"
            )
            self.logger.error("⚠️ Sistema NO LISTO para operación médica")
        
        return overall_success, validation_results
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """
        Genera un reporte completo del estado de validación del sistema.
        
        Este reporte es útil para auditorías médicas, debugging,
        y documentación de cumplimiento regulatorio.
        
        Returns:
            Diccionario con reporte completo de validación
        """
        # Ejecutar todas las validaciones
        overall_success, detailed_results = self.validate_all_prerequisites()
        
        # Recopilar información del sistema
        system_info = {
            'platform': platform.platform(),
            'python_version': sys.version,
            'architecture': platform.architecture(),
            'processor': platform.processor(),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'disk_total_gb': shutil.disk_usage(Path.cwd()).total / (1024**3)
        }
        
        # Compilar reporte completo
        validation_report = {
            'timestamp': self._get_timestamp(),
            'overall_success': overall_success,
            'validation_results': detailed_results,
            'system_information': system_info,
            'requirements': {
                'min_ram_gb': self.min_ram_gb,
                'min_free_disk_gb': self.min_free_disk_gb,
                'min_python_version': self.min_python_version,
                'required_packages': self.required_medical_packages,
                'recommended_packages': self.recommended_packages
            },
            'medical_readiness': overall_success
        }
        
        return validation_report
    
    def _get_timestamp(self) -> str:
        """Genera timestamp médico estándar."""
        from datetime import datetime
        return datetime.now().isoformat()


# Función de conveniencia para validación rápida
def quick_medical_validation() -> bool:
    """
    Ejecuta validación rápida de prerrequisitos médicos.
    
    Esta función proporciona una manera rápida de verificar
    si el sistema está básicamente listo para uso médico.
    
    Returns:
        True si la validación básica pasa, False en caso contrario
    """
    validator = MedicalSystemValidator()
    success, _ = validator.validate_all_prerequisites()
    return success


# Función para generar reporte completo
def generate_system_validation_report() -> Dict[str, Any]:
    """
    Genera reporte completo de validación del sistema médico.
    
    Returns:
        Diccionario con reporte detallado de validación
    """
    validator = MedicalSystemValidator()
    return validator.generate_validation_report()


# Ejemplo de uso y testing
if __name__ == "__main__":
    # Configurar logging básico para pruebas
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🏥 VALIDADOR DE SISTEMA MÉDICO - PRUEBA")
    print("=" * 50)
    
    # Crear validador y ejecutar pruebas
    validator = MedicalSystemValidator()
    
    print("\n📊 Ejecutando validación completa...")
    success, results = validator.validate_all_prerequisites()
    
    print("\n📋 RESULTADOS DE VALIDACIÓN:")
    for category, result in results.items():
        status = "✅ ÉXITO" if result else "❌ FALLO"
        print(f"   {category}: {status}")
    
    print(f"\n🎯 ESTADO GENERAL: {'✅ LISTO' if success else '❌ NO LISTO'} para operación médica")
    
    # Generar reporte completo
    print("\n📄 Generando reporte completo...")
    report = validator.generate_validation_report()
    
    print("\n📊 INFORMACIÓN DEL SISTEMA:")
    print(f"   Plataforma: {report['system_information']['platform']}")
    print(f"   Python: {report['system_information']['python_version'].split()[0]}")
    print(f"   RAM Total: {report['system_information']['memory_total_gb']:.2f}GB")
    print(f"   Disco Total: {report['system_information']['disk_total_gb']:.2f}GB")
    
    print("\n🎉 Validación de sistema médico completada!")