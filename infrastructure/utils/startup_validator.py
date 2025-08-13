"""
infrastructure/utils/startup_validator.py

Validador de sistema para aplicación médica.
Verifica dependencias, hardware, y configuraciones necesarias
antes del inicio de la aplicación médica.
"""

import sys
import os
import platform
import psutil
import importlib
from pathlib import Path
from typing import List, Dict, Any, Optional, NamedTuple
import subprocess
import logging


class ValidationResult(NamedTuple):
    """Resultado de validación del sistema."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    system_info: Dict[str, Any]


class SystemValidator:
    """
    Validador completo del sistema para aplicación médica.
    
    Verifica:
    - Versión de Python y dependencias
    - Recursos de hardware disponibles
    - Bibliotecas gráficas y de visualización
    - Permisos y configuraciones de sistema
    - Disponibilidad de GPU para IA (opcional)
    """
    
    def __init__(self):
        """Inicializa el validador de sistema."""
        self.logger = logging.getLogger(__name__)
        
        # Dependencias críticas requeridas
        self.critical_dependencies = {
            'PyQt6': '6.0.0',
            'numpy': '1.20.0',
            'pydicom': '2.0.0',
            'SimpleITK': '2.0.0'
        }
        
        # Dependencias opcionales pero recomendadas
        self.optional_dependencies = {
            'vtk': '9.0.0',
            'scipy': '1.7.0',
            'scikit-image': '0.18.0',
            'matplotlib': '3.5.0',
            'Pillow': '8.0.0'
        }
        
        # Dependencias de IA (opcionales)
        self.ai_dependencies = {
            'torch': '1.10.0',
            'torchvision': '0.11.0',
            'nnunet': '1.0.0'
        }
        
        # Requisitos mínimos de hardware
        self.min_requirements = {
            'ram_gb': 4,
            'disk_space_gb': 10,
            'python_version': (3, 8, 0)
        }
        
        # Requisitos recomendados
        self.recommended_requirements = {
            'ram_gb': 16,
            'disk_space_gb': 100,
            'cpu_cores': 4
        }
    
    def validate_system(self) -> ValidationResult:
        """
        Ejecuta validación completa del sistema.
        
        Returns:
            Resultado de validación con errores y advertencias
        """
        errors = []
        warnings = []
        system_info = {}
        
        try:
            # 1. Validar versión de Python
            python_result = self._validate_python_version()
            system_info.update(python_result['info'])
            errors.extend(python_result['errors'])
            warnings.extend(python_result['warnings'])
            
            # 2. Validar dependencias críticas
            deps_result = self._validate_dependencies()
            system_info.update(deps_result['info'])
            errors.extend(deps_result['errors'])
            warnings.extend(deps_result['warnings'])
            
            # 3. Validar recursos de hardware
            hardware_result = self._validate_hardware()
            system_info.update(hardware_result['info'])
            errors.extend(hardware_result['errors'])
            warnings.extend(hardware_result['warnings'])
            
            # 4. Validar sistema gráfico
            graphics_result = self._validate_graphics_system()
            system_info.update(graphics_result['info'])
            errors.extend(graphics_result['errors'])
            warnings.extend(graphics_result['warnings'])
            
            # 5. Validar permisos y acceso a archivos
            permissions_result = self._validate_file_permissions()
            system_info.update(permissions_result['info'])
            errors.extend(permissions_result['errors'])
            warnings.extend(permissions_result['warnings'])
            
            # 6. Validar capacidades de IA (opcional)
            ai_result = self._validate_ai_capabilities()
            system_info.update(ai_result['info'])
            # Las capacidades de IA son opcionales, solo warnings
            warnings.extend(ai_result['errors'])
            warnings.extend(ai_result['warnings'])
            
            # 7. Validar configuración del sistema operativo
            os_result = self._validate_operating_system()
            system_info.update(os_result['info'])
            errors.extend(os_result['errors'])
            warnings.extend(os_result['warnings'])
            
        except Exception as e:
            errors.append(f"Error crítico durante validación: {e}")
        
        # Determinar si el sistema es válido
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            system_info=system_info
        )
    
    def _validate_python_version(self) -> Dict[str, Any]:
        """Valida la versión de Python."""
        result = {'errors': [], 'warnings': [], 'info': {}}
        
        current_version = sys.version_info[:3]
        min_version = self.min_requirements['python_version']
        
        result['info']['python_version'] = '.'.join(map(str, current_version))
        result['info']['python_executable'] = sys.executable
        
        if current_version < min_version:
            result['errors'].append(
                f"Python {'.'.join(map(str, min_version))} o superior requerido. "
                f"Versión actual: {'.'.join(map(str, current_version))}"
            )
        
        # Verificar si es una versión muy nueva que podría tener problemas
        if current_version >= (3, 12):
            result['warnings'].append(
                f"Python {'.'.join(map(str, current_version))} es muy reciente. "
                "Algunas dependencias podrían no ser compatibles."
            )
        
        return result
    
    def _validate_dependencies(self) -> Dict[str, Any]:
        """Valida dependencias de Python."""
        result = {'errors': [], 'warnings': [], 'info': {}}
        installed_packages = {}
        
        # Validar dependencias críticas
        for package, min_version in self.critical_dependencies.items():
            try:
                module = importlib.import_module(package.lower().replace('-', '_'))
                version = getattr(module, '__version__', 'unknown')
                installed_packages[package] = version
                
                if not self._version_compatible(version, min_version):
                    result['errors'].append(
                        f"{package} {min_version}+ requerido. Instalado: {version}"
                    )
                
            except ImportError:
                result['errors'].append(f"Dependencia crítica faltante: {package}")
                installed_packages[package] = 'not_installed'
        
        # Validar dependencias opcionales
        for package, min_version in self.optional_dependencies.items():
            try:
                module_name = package.lower().replace('-', '_')
                if package == 'Pillow':
                    module_name = 'PIL'
                elif package == 'scikit-image':
                    module_name = 'skimage'
                
                module = importlib.import_module(module_name)
                version = getattr(module, '__version__', 'unknown')
                installed_packages[package] = version
                
                if not self._version_compatible(version, min_version):
                    result['warnings'].append(
                        f"{package} {min_version}+ recomendado. Instalado: {version}"
                    )
                
            except ImportError:
                result['warnings'].append(f"Dependencia opcional faltante: {package}")
                installed_packages[package] = 'not_installed'
        
        result['info']['installed_packages'] = installed_packages
        return result
    
    def _validate_hardware(self) -> Dict[str, Any]:
        """Valida recursos de hardware."""
        result = {'errors': [], 'warnings': [], 'info': {}}
        
        # Memoria RAM
        memory = psutil.virtual_memory()
        ram_gb = memory.total / (1024**3)
        result['info']['ram_gb'] = round(ram_gb, 2)
        result['info']['ram_available_gb'] = round(memory.available / (1024**3), 2)
        
        if ram_gb < self.min_requirements['ram_gb']:
            result['errors'].append(
                f"RAM insuficiente: {ram_gb:.1f}GB disponible, "
                f"{self.min_requirements['ram_gb']}GB mínimo requerido"
            )
        elif ram_gb < self.recommended_requirements['ram_gb']:
            result['warnings'].append(
                f"RAM baja: {ram_gb:.1f}GB disponible, "
                f"{self.recommended_requirements['ram_gb']}GB recomendado para mejor rendimiento"
            )
        
        # CPU
        cpu_count = psutil.cpu_count(logical=False)
        cpu_count_logical = psutil.cpu_count(logical=True)
        result['info']['cpu_cores_physical'] = cpu_count
        result['info']['cpu_cores_logical'] = cpu_count_logical
        result['info']['cpu_freq_mhz'] = psutil.cpu_freq().current if psutil.cpu_freq() else 'unknown'
        
        if cpu_count < self.recommended_requirements.get('cpu_cores', 4):
            result['warnings'].append(
                f"CPU: {cpu_count} núcleos físicos disponibles, "
                f"{self.recommended_requirements['cpu_cores']} recomendados"
            )
        
        # Espacio en disco
        disk_usage = psutil.disk_usage('.')
        free_space_gb = disk_usage.free / (1024**3)
        result['info']['disk_free_gb'] = round(free_space_gb, 2)
        result['info']['disk_total_gb'] = round(disk_usage.total / (1024**3), 2)
        
        if free_space_gb < self.min_requirements['disk_space_gb']:
            result['errors'].append(
                f"Espacio en disco insuficiente: {free_space_gb:.1f}GB libres, "
                f"{self.min_requirements['disk_space_gb']}GB mínimo requerido"
            )
        elif free_space_gb < self.recommended_requirements['disk_space_gb']:
            result['warnings'].append(
                f"Espacio en disco bajo: {free_space_gb:.1f}GB libres, "
                f"{self.recommended_requirements['disk_space_gb']}GB recomendado"
            )
        
        return result
    
    def _validate_graphics_system(self) -> Dict[str, Any]:
        """Valida sistema gráfico y capacidades de visualización."""
        result = {'errors': [], 'warnings': [], 'info': {}}
        
        # Información básica del sistema gráfico
        try:
            if platform.system() == "Linux":
                # En Linux, verificar X11 o Wayland
                display = os.environ.get('DISPLAY')
                wayland_display = os.environ.get('WAYLAND_DISPLAY')
                
                if not display and not wayland_display:
                    result['errors'].append(
                        "No se detectó sistema gráfico (X11/Wayland). "
                        "Se requiere entorno gráfico para la aplicación."
                    )
                
                result['info']['display_server'] = 'X11' if display else 'Wayland' if wayland_display else 'none'
                
            elif platform.system() == "Windows":
                # En Windows, verificar DirectX/OpenGL
                result['info']['display_server'] = 'Windows Graphics'
                
            elif platform.system() == "Darwin":
                # En macOS
                result['info']['display_server'] = 'Quartz'
        
        except Exception as e:
            result['warnings'].append(f"No se pudo verificar sistema gráfico: {e}")
        
        # Verificar capacidades de OpenGL (importante para VTK)
        try:
            # Intentar importar PyQt6 y verificar OpenGL
            from PyQt6.QtOpenGL import QOpenGLWidget
            from PyQt6.QtWidgets import QApplication
            
            # Si llegamos aquí, OpenGL está disponible
            result['info']['opengl_support'] = True
            
        except ImportError as e:
            result['warnings'].append(
                "OpenGL no disponible o PyQt6 no instalado. "
                "El renderizado 3D podría estar limitado."
            )
            result['info']['opengl_support'] = False
        
        return result
    
    def _validate_file_permissions(self) -> Dict[str, Any]:
        """Valida permisos de archivos y directorios."""
        result = {'errors': [], 'warnings': [], 'info': {}}
        
        # Directorios que necesitan ser escribibles
        required_directories = [
            './medical_data',
            './logs',
            './temp',
            './exports'
        ]
        
        permissions_ok = True
        
        for directory in required_directories:
            dir_path = Path(directory)
            
            try:
                # Crear directorio si no existe
                dir_path.mkdir(parents=True, exist_ok=True)
                
                # Verificar permisos de escritura
                test_file = dir_path / 'test_write_permission.tmp'
                test_file.write_text('test')
                test_file.unlink()
                
            except PermissionError:
                result['errors'].append(
                    f"Sin permisos de escritura en directorio: {directory}"
                )
                permissions_ok = False
            except Exception as e:
                result['warnings'].append(
                    f"No se pudo verificar permisos en {directory}: {e}"
                )
        
        result['info']['file_permissions_ok'] = permissions_ok
        
        return result
    
    def _validate_ai_capabilities(self) -> Dict[str, Any]:
        """Valida capacidades de IA (GPU, PyTorch, etc.)."""
        result = {'errors': [], 'warnings': [], 'info': {}}
        
        # Verificar PyTorch
        try:
            import torch
            result['info']['pytorch_version'] = torch.__version__
            result['info']['pytorch_available'] = True
            
            # Verificar CUDA
            cuda_available = torch.cuda.is_available()
            result['info']['cuda_available'] = cuda_available
            
            if cuda_available:
                result['info']['cuda_device_count'] = torch.cuda.device_count()
                result['info']['cuda_device_name'] = torch.cuda.get_device_name(0)
                result['info']['cuda_memory_gb'] = round(
                    torch.cuda.get_device_properties(0).total_memory / (1024**3), 2
                )
            else:
                result['warnings'].append(
                    "CUDA no disponible. La inferencia de IA será más lenta en CPU."
                )
                
        except ImportError:
            result['warnings'].append(
                "PyTorch no instalado. Las funciones de IA no estarán disponibles."
            )
            result['info']['pytorch_available'] = False
        
        # Verificar nnUNet
        try:
            import nnunet
            result['info']['nnunet_available'] = True
            result['info']['nnunet_version'] = getattr(nnunet, '__version__', 'unknown')
        except ImportError:
            result['warnings'].append(
                "nnUNet no instalado. Se requiere para segmentación automática."
            )
            result['info']['nnunet_available'] = False
        
        return result
    
    def _validate_operating_system(self) -> Dict[str, Any]:
        """Valida configuración del sistema operativo."""
        result = {'errors': [], 'warnings': [], 'info': {}}
        
        system = platform.system()
        release = platform.release()
        version = platform.version()
        
        result['info']['os_system'] = system
        result['info']['os_release'] = release
        result['info']['os_version'] = version
        result['info']['architecture'] = platform.architecture()[0]
        
        # Verificaciones específicas por OS
        if system == "Windows":
            # Verificar versión de Windows
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                   r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
                build = winreg.QueryValueEx(key, "CurrentBuild")[0]
                result['info']['windows_build'] = build
                
                # Windows 10 build 1903+ recomendado
                if int(build) < 18362:
                    result['warnings'].append(
                        f"Windows build {build} detectado. "
                        "Build 18362+ recomendado para mejor compatibilidad."
                    )
                    
            except Exception:
                result['warnings'].append("No se pudo verificar build de Windows")
        
        elif system == "Linux":
            # Verificar distribución
            try:
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('PRETTY_NAME='):
                            distro = line.split('=')[1].strip('"')
                            result['info']['linux_distribution'] = distro
                            break
            except Exception:
                result['info']['linux_distribution'] = 'unknown'
        
        elif system == "Darwin":
            # macOS
            mac_version = platform.mac_ver()[0]
            result['info']['macos_version'] = mac_version
            
            # macOS 10.15+ recomendado
            if mac_version and tuple(map(int, mac_version.split('.'))) < (10, 15):
                result['warnings'].append(
                    f"macOS {mac_version} detectado. "
                    "macOS 10.15+ recomendado."
                )
        
        return result
    
    def _version_compatible(self, installed: str, required: str) -> bool:
        """
        Verifica si una versión instalada es compatible con la requerida.
        
        Args:
            installed: Versión instalada
            required: Versión mínima requerida
            
        Returns:
            True si es compatible
        """
        try:
            if installed == 'unknown':
                return True  # Asumir compatible si no se puede determinar
            
            # Parsear versiones
            installed_parts = [int(x) for x in installed.split('.') if x.isdigit()]
            required_parts = [int(x) for x in required.split('.') if x.isdigit()]
            
            # Normalizar longitudes
            max_len = max(len(installed_parts), len(required_parts))
            installed_parts.extend([0] * (max_len - len(installed_parts)))
            required_parts.extend([0] * (max_len - len(required_parts)))
            
            return installed_parts >= required_parts
            
        except Exception:
            return True  # En caso de error, asumir compatible
    
    def generate_system_report(self, validation_result: ValidationResult) -> str:
        """
        Genera un reporte detallado del sistema.
        
        Args:
            validation_result: Resultado de validación
            
        Returns:
            Reporte del sistema en formato texto
        """
        report = []
        report.append("=== MEDICAL IMAGING WORKSTATION - SYSTEM REPORT ===")
        report.append("")
        
        # Estado general
        status = "✅ VÁLIDO" if validation_result.is_valid else "❌ INVÁLIDO"
        report.append(f"Estado del sistema: {status}")
        report.append("")
        
        # Información del sistema
        report.append("--- INFORMACIÓN DEL SISTEMA ---")
        info = validation_result.system_info
        
        if 'python_version' in info:
            report.append(f"Python: {info['python_version']}")
        if 'os_system' in info:
            report.append(f"Sistema Operativo: {info['os_system']} {info.get('os_release', '')}")
        if 'architecture' in info:
            report.append(f"Arquitectura: {info['architecture']}")
        if 'ram_gb' in info:
            report.append(f"RAM: {info['ram_gb']}GB ({info.get('ram_available_gb', 0):.1f}GB disponible)")
        if 'cpu_cores_physical' in info:
            report.append(f"CPU: {info['cpu_cores_physical']} núcleos físicos")
        if 'disk_free_gb' in info:
            report.append(f"Disco: {info['disk_free_gb']:.1f}GB libres de {info.get('disk_total_gb', 0):.1f}GB")
        
        report.append("")
        
        # Errores
        if validation_result.errors:
            report.append("--- ERRORES CRÍTICOS ---")
            for error in validation_result.errors:
                report.append(f"❌ {error}")
            report.append("")
        
        # Advertencias
        if validation_result.warnings:
            report.append("--- ADVERTENCIAS ---")
            for warning in validation_result.warnings:
                report.append(f"⚠️  {warning}")
            report.append("")
        
        # Capacidades de IA
        if 'pytorch_available' in info:
            report.append("--- CAPACIDADES DE IA ---")
            if info['pytorch_available']:
                report.append(f"✅ PyTorch {info.get('pytorch_version', 'unknown')}")
                if info.get('cuda_available'):
                    report.append(f"✅ CUDA - {info.get('cuda_device_name', 'GPU disponible')}")
                    report.append(f"   Memoria GPU: {info.get('cuda_memory_gb', 0):.1f}GB")
                else:
                    report.append("⚠️  CUDA no disponible (CPU solamente)")
            else:
                report.append("❌ PyTorch no instalado")
            
            if info.get('nnunet_available'):
                report.append(f"✅ nnUNet {info.get('nnunet_version', 'unknown')}")
            else:
                report.append("❌ nnUNet no instalado")
        
        report.append("")
        report.append("=== FIN DEL REPORTE ===")
        
        return "\n".join(report)