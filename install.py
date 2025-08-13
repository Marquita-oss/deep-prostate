#!/usr/bin/env python3
"""
install.py

Script de instalación completo para Medical Imaging Workstation.
Automatiza todo el proceso de configuración, instalación de dependencias,
validación del sistema, y preparación del entorno médico profesional.
"""

import os
import sys
import subprocess
import shutil
import urllib.request
import zipfile
from pathlib import Path
from typing import List, Dict, Optional
import platform
import json

class MedicalWorkstationInstaller:
    """
    Instalador automático para Medical Imaging Workstation.
    
    Maneja instalación completa desde cero, incluyendo:
    - Verificación de requisitos del sistema
    - Instalación de dependencias Python
    - Configuración de entorno virtual
    - Descarga de modelos de IA (opcional)
    - Configuración inicial de la aplicación
    - Validación post-instalación
    """
    
    def __init__(self):
        """Inicializa el instalador."""
        self.root_dir = Path(__file__).parent
        self.system_info = self._get_system_info()
        self.python_executable = sys.executable
        self.venv_path = self.root_dir / "medical_env"
        self.config_dir = self.root_dir / "config"
        self.data_dir = self.root_dir / "medical_data"
        
        # Estado de instalación
        self.installation_log = []
        self.errors = []
        self.warnings = []
        
    def _get_system_info(self) -> Dict[str, str]:
        """Obtiene información del sistema."""
        return {
            "os": platform.system(),
            "os_version": platform.release(),
            "architecture": platform.architecture()[0],
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "machine": platform.machine()
        }
    
    def print_banner(self):
        """Muestra banner de instalación."""
        banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║     🏥 MEDICAL IMAGING WORKSTATION - INSTALLER 🏥                   ║
║                                                                      ║
║           Professional Prostate Cancer Analysis Software            ║
║              Automatic Installation & Configuration                  ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

🔧 Sistema detectado: {os} {architecture}
🐍 Python: {python_version}
📂 Directorio: {root_dir}

        """.format(
            os=self.system_info["os"],
            architecture=self.system_info["architecture"],
            python_version=self.system_info["python_version"],
            root_dir=self.root_dir
        )
        print(banner)
    
    def log(self, message: str, level: str = "info"):
        """Registra mensaje de instalación."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        if level == "info":
            print(f"ℹ️  {formatted_message}")
        elif level == "success":
            print(f"✅ {formatted_message}")
        elif level == "warning":
            print(f"⚠️  {formatted_message}")
            self.warnings.append(message)
        elif level == "error":
            print(f"❌ {formatted_message}")
            self.errors.append(message)
        
        self.installation_log.append({"timestamp": timestamp, "level": level, "message": message})
    
    def check_prerequisites(self) -> bool:
        """Verifica prerequisitos del sistema."""
        self.log("Verificando prerequisitos del sistema...")
        
        # Verificar versión de Python
        if sys.version_info < (3, 8):
            self.log(f"Python 3.8+ requerido. Actual: {self.system_info['python_version']}", "error")
            return False
        
        self.log(f"Python {self.system_info['python_version']} ✓", "success")
        
        # Verificar pip
        try:
            import pip
            self.log("pip disponible ✓", "success")
        except ImportError:
            self.log("pip no encontrado - requerido para instalación", "error")
            return False
        
        # Verificar espacio en disco
        free_space = shutil.disk_usage('.').free / (1024**3)
        if free_space < 5:
            self.log(f"Espacio insuficiente: {free_space:.1f}GB (5GB+ requerido)", "error")
            return False
        
        self.log(f"Espacio en disco: {free_space:.1f}GB ✓", "success")
        
        # Verificar memoria RAM
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            if memory_gb < 4:
                self.log(f"RAM limitada: {memory_gb:.1f}GB (4GB+ recomendado)", "warning")
            else:
                self.log(f"RAM: {memory_gb:.1f}GB ✓", "success")
        except ImportError:
            self.log("No se pudo verificar RAM (psutil no disponible)", "warning")
        
        return len(self.errors) == 0
    
    def create_virtual_environment(self) -> bool:
        """Crea entorno virtual para la aplicación."""
        self.log("Configurando entorno virtual...")
        
        try:
            if self.venv_path.exists():
                self.log("Entorno virtual existente encontrado", "warning")
                response = input("¿Recrear entorno virtual? (y/N): ").lower()
                if response == 'y':
                    shutil.rmtree(self.venv_path)
                else:
                    self.log("Usando entorno virtual existente", "info")
                    return True
            
            # Crear entorno virtual
            result = subprocess.run([
                self.python_executable, "-m", "venv", str(self.venv_path)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log(f"Error creando entorno virtual: {result.stderr}", "error")
                return False
            
            self.log("Entorno virtual creado exitosamente", "success")
            
            # Actualizar referencia al ejecutable de Python del venv
            if self.system_info["os"] == "Windows":
                self.python_executable = str(self.venv_path / "Scripts" / "python.exe")
                self.pip_executable = str(self.venv_path / "Scripts" / "pip.exe")
            else:
                self.python_executable = str(self.venv_path / "bin" / "python")
                self.pip_executable = str(self.venv_path / "bin" / "pip")
            
            return True
            
        except Exception as e:
            self.log(f"Error configurando entorno virtual: {e}", "error")
            return False
    
    def install_dependencies(self) -> bool:
        """Instala dependencias Python."""
        self.log("Instalando dependencias Python...")
        
        try:
            # Actualizar pip primero
            self.log("Actualizando pip...")
            result = subprocess.run([
                self.python_executable, "-m", "pip", "install", "--upgrade", "pip"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log(f"Advertencia actualizando pip: {result.stderr}", "warning")
            
            # Dependencias críticas
            critical_deps = [
                "PyQt6>=6.0.0",
                "numpy>=1.20.0", 
                "pydicom>=2.3.0",
                "SimpleITK>=2.2.0",
                "vtk>=9.2.0",
                "scipy>=1.9.0",
                "scikit-image>=0.19.0",
                "matplotlib>=3.5.0",
                "Pillow>=9.0.0",
                "PyYAML>=6.0",
                "psutil>=5.8.0"
            ]
            
            # Instalar dependencias críticas
            for dep in critical_deps:
                self.log(f"Instalando {dep.split('>=')[0]}...")
                result = subprocess.run([
                    self.pip_executable, "install", dep
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.log(f"Error instalando {dep}: {result.stderr}", "error")
                    return False
                else:
                    self.log(f"{dep.split('>=')[0]} instalado ✓", "success")
            
            # Dependencias de desarrollo/testing (opcionales)
            dev_deps = [
                "pytest>=7.0.0",
                "pytest-qt>=4.2.0",
                "black>=22.0.0"
            ]
            
            self.log("Instalando dependencias de desarrollo...")
            for dep in dev_deps:
                result = subprocess.run([
                    self.pip_executable, "install", dep
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.log(f"Dependencia opcional {dep} no instalada", "warning")
                else:
                    self.log(f"{dep.split('>=')[0]} instalado ✓", "success")
            
            return True
            
        except Exception as e:
            self.log(f"Error instalando dependencias: {e}", "error")
            return False
    
    def install_ai_dependencies(self) -> bool:
        """Instala dependencias de IA (PyTorch, nnUNet)."""
        self.log("Configurando dependencias de IA...")
        
        # Preguntar si instalar dependencias de IA
        response = input("¿Instalar dependencias de IA (PyTorch, nnUNet)? Requerido para segmentación automática (y/N): ").lower()
        
        if response != 'y':
            self.log("Saltando instalación de IA - funcionalidad limitada", "warning")
            return True
        
        try:
            # Detectar si hay GPU NVIDIA disponible
            gpu_available = self._detect_nvidia_gpu()
            
            if gpu_available:
                self.log("GPU NVIDIA detectada - instalando PyTorch con CUDA", "info")
                torch_cmd = [
                    self.pip_executable, "install", "torch", "torchvision", "torchaudio",
                    "--index-url", "https://download.pytorch.org/whl/cu118"
                ]
            else:
                self.log("GPU no detectada - instalando PyTorch para CPU", "info")
                torch_cmd = [
                    self.pip_executable, "install", "torch", "torchvision", "torchaudio"
                ]
            
            # Instalar PyTorch
            self.log("Instalando PyTorch (esto puede tomar varios minutos)...")
            result = subprocess.run(torch_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log(f"Error instalando PyTorch: {result.stderr}", "error")
                return False
            
            self.log("PyTorch instalado exitosamente ✓", "success")
            
            # Instalar nnUNet
            self.log("Instalando nnUNet...")
            result = subprocess.run([
                self.pip_executable, "install", 
                "git+https://github.com/MIC-DKFZ/nnUNet.git"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log(f"Error instalando nnUNet: {result.stderr}", "warning")
                self.log("nnUNet puede instalarse manualmente más tarde", "info")
            else:
                self.log("nnUNet instalado exitosamente ✓", "success")
            
            return True
            
        except Exception as e:
            self.log(f"Error configurando IA: {e}", "error")
            return False
    
    def _detect_nvidia_gpu(self) -> bool:
        """Detecta si hay GPU NVIDIA disponible."""
        try:
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def create_directory_structure(self) -> bool:
        """Crea estructura de directorios necesaria."""
        self.log("Creando estructura de directorios...")
        
        directories = [
            "medical_data",
            "medical_data/studies",
            "medical_data/exports", 
            "logs",
            "temp",
            "models",
            "models/nnunet_results",
            "config",
            "backups",
            "resources"
        ]
        
        try:
            for directory in directories:
                dir_path = self.root_dir / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                self.log(f"Directorio {directory}/ ✓", "success")
            
            return True
            
        except Exception as e:
            self.log(f"Error creando directorios: {e}", "error")
            return False
    
    def create_configuration_files(self) -> bool:
        """Crea archivos de configuración inicial."""
        self.log("Generando archivos de configuración...")
        
        try:
            # Configuración principal (simplificada para instalación)
            config_content = {
                "application": {
                    "name": "Medical Imaging Workstation",
                    "version": "1.0.0",
                    "first_run": True,
                    "installation_date": datetime.now().isoformat()
                },
                "storage_path": "./medical_data",
                "models_path": "./models", 
                "temp_path": "./temp",
                "logs_path": "./logs",
                "ai_models": {
                    "nnunet_model_path": "./models/nnunet_prostate",
                    "confidence_threshold": 0.7,
                    "use_gpu": self._detect_nvidia_gpu()
                },
                "visualization": {
                    "default_theme": "dark",
                    "max_memory_usage_gb": 4
                },
                "system_info": self.system_info
            }
            
            config_file = self.config_dir / "medical_imaging_config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_content, f, indent=2, ensure_ascii=False)
            
            self.log("Configuración principal creada ✓", "success")
            
            # Crear archivo de logging config
            log_config = {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "medical": {
                        "format": "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
                    }
                },
                "handlers": {
                    "console": {
                        "class": "logging.StreamHandler",
                        "formatter": "medical",
                        "level": "INFO"
                    },
                    "file": {
                        "class": "logging.handlers.RotatingFileHandler",
                        "filename": "./logs/medical_imaging.log",
                        "formatter": "medical",
                        "maxBytes": 10485760,
                        "backupCount": 5
                    }
                },
                "root": {
                    "level": "INFO",
                    "handlers": ["console", "file"]
                }
            }
            
            log_config_file = self.config_dir / "logging_config.json"
            with open(log_config_file, 'w', encoding='utf-8') as f:
                json.dump(log_config, f, indent=2)
            
            self.log("Configuración de logging creada ✓", "success")
            
            return True
            
        except Exception as e:
            self.log(f"Error creando configuración: {e}", "error")
            return False
    
    def create_launcher_scripts(self) -> bool:
        """Crea scripts de lanzamiento."""
        self.log("Creando scripts de lanzamiento...")
        
        try:
            # Script para Windows
            if self.system_info["os"] == "Windows":
                bat_content = f'''@echo off
echo Iniciando Medical Imaging Workstation...
cd /d "{self.root_dir}"
"{self.python_executable}" main.py %*
pause
'''
                bat_file = self.root_dir / "run_medical_workstation.bat"
                with open(bat_file, 'w', encoding='utf-8') as f:
                    f.write(bat_content)
                
                self.log("Script Windows (.bat) creado ✓", "success")
            
            # Script para Unix/Linux/macOS
            if self.system_info["os"] in ["Linux", "Darwin"]:
                sh_content = f'''#!/bin/bash
echo "Iniciando Medical Imaging Workstation..."
cd "{self.root_dir}"
"{self.python_executable}" main.py "$@"
'''
                sh_file = self.root_dir / "run_medical_workstation.sh"
                with open(sh_file, 'w', encoding='utf-8') as f:
                    f.write(sh_content)
                
                # Hacer ejecutable
                os.chmod(sh_file, 0o755)
                self.log("Script Unix (.sh) creado ✓", "success")
            
            # Script Python universal
            py_launcher = self.root_dir / "launch.py"
            launcher_content = f'''#!/usr/bin/env python3
"""
Launcher para Medical Imaging Workstation
Generado automáticamente por el instalador
"""
import sys
import subprocess
from pathlib import Path

# Configuración de la instalación
PYTHON_EXECUTABLE = r"{self.python_executable}"
ROOT_DIR = Path(r"{self.root_dir}")
MAIN_SCRIPT = ROOT_DIR / "main.py"

def main():
    import os
    os.chdir(ROOT_DIR)
    
    cmd = [PYTHON_EXECUTABLE, str(MAIN_SCRIPT)] + sys.argv[1:]
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
'''
            
            with open(py_launcher, 'w', encoding='utf-8') as f:
                f.write(launcher_content)
            
            self.log("Launcher Python creado ✓", "success")
            
            return True
            
        except Exception as e:
            self.log(f"Error creando launchers: {e}", "error")
            return False
    
    def run_post_install_validation(self) -> bool:
        """Ejecuta validación post-instalación."""
        self.log("Ejecutando validación post-instalación...")
        
        try:
            # Test de imports críticos
            test_script = f'''
import sys
sys.path.insert(0, r"{self.root_dir}")

try:
    # Test imports críticos
    import PyQt6
    print("✅ PyQt6")
    
    import vtk
    print("✅ VTK")
    
    import pydicom
    print("✅ PyDICOM") 
    
    import SimpleITK
    print("✅ SimpleITK")
    
    import numpy
    print("✅ NumPy")
    
    # Test entidades del dominio
    from domain.entities.medical_image import MedicalImage
    from domain.entities.segmentation import MedicalSegmentation
    print("✅ Entidades del dominio")
    
    print("🎉 Validación exitosa")
    
except ImportError as e:
    print(f"❌ Error de importación: {{e}}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {{e}}")
    sys.exit(1)
'''
            
            result = subprocess.run([
                self.python_executable, "-c", test_script
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("Validación exitosa ✓", "success")
                print(result.stdout)
                return True
            else:
                self.log(f"Validación falló: {result.stderr}", "error")
                return False
                
        except Exception as e:
            self.log(f"Error en validación: {e}", "error")
            return False
    
    def generate_installation_report(self):
        """Genera reporte de instalación."""
        report_content = f"""
# MEDICAL IMAGING WORKSTATION - INSTALLATION REPORT

## Información del Sistema
- SO: {self.system_info['os']} {self.system_info['os_version']}
- Arquitectura: {self.system_info['architecture']} 
- Python: {self.system_info['python_version']}
- Directorio: {self.root_dir}

## Estado de Instalación
- Errores: {len(self.errors)}
- Advertencias: {len(self.warnings)}
- Instalación exitosa: {"✅ SÍ" if len(self.errors) == 0 else "❌ NO"}

## Errores Encontrados
"""
        
        for error in self.errors:
            report_content += f"- ❌ {error}\n"
        
        report_content += "\n## Advertencias\n"
        for warning in self.warnings:
            report_content += f"- ⚠️  {warning}\n"
        
        report_content += f"""
## Log de Instalación
"""
        
        for entry in self.installation_log:
            icon = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
            report_content += f"{icon.get(entry['level'], 'ℹ️')} [{entry['timestamp']}] {entry['message']}\n"
        
        report_content += f"""
## Próximos Pasos

1. **Ejecutar la aplicación:**
   - Windows: Doble click en `run_medical_workstation.bat`
   - Linux/macOS: `./run_medical_workstation.sh`
   - Universal: `python launch.py`

2. **Cargar imágenes DICOM:**
   - File > Open Image/Study...
   - Soporta archivos .dcm, .dicom, directorios DICOM

3. **Probar segmentación con IA:**
   - Cargar imagen de próstata
   - Panel derecho > AI Analysis > Run Full Analysis

4. **Documentación:**
   - README.md para guía completa
   - Panel Help > About para información de versión

## Soporte
- Revisar logs en: ./logs/medical_imaging.log
- Configuración en: ./config/medical_imaging_config.json
- Datos médicos en: ./medical_data/

¡Instalación completada! 🏥
"""
        
        report_file = self.root_dir / "INSTALLATION_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        self.log(f"Reporte guardado en: {report_file}", "info")
    
    def run_installation(self):
        """Ejecuta instalación completa."""
        from datetime import datetime
        
        self.print_banner()
        
        start_time = datetime.now()
        
        try:
            # Paso 1: Verificar prerequisitos
            if not self.check_prerequisites():
                self.log("Prerequisitos no cumplidos - abortando instalación", "error")
                return False
            
            # Paso 2: Crear entorno virtual
            if not self.create_virtual_environment():
                self.log("Error configurando entorno virtual", "error")
                return False
            
            # Paso 3: Instalar dependencias críticas
            if not self.install_dependencies():
                self.log("Error instalando dependencias", "error")
                return False
            
            # Paso 4: Instalar dependencias de IA (opcional)
            if not self.install_ai_dependencies():
                self.log("Error configurando IA - continuando sin funcionalidad de IA", "warning")
            
            # Paso 5: Crear estructura de directorios
            if not self.create_directory_structure():
                self.log("Error creando directorios", "error")
                return False
            
            # Paso 6: Crear archivos de configuración
            if not self.create_configuration_files():
                self.log("Error creando configuración", "error")
                return False
            
            # Paso 7: Crear scripts de lanzamiento
            if not self.create_launcher_scripts():
                self.log("Error creando launchers", "error")
                return False
            
            # Paso 8: Validación post-instalación
            if not self.run_post_install_validation():
                self.log("Validación post-instalación falló", "warning")
            
            # Paso 9: Generar reporte
            self.generate_installation_report()
            
            # Resumen final
            end_time = datetime.now()
            duration = end_time - start_time
            
            print("\n" + "="*70)
            if len(self.errors) == 0:
                print("🎉 ¡INSTALACIÓN COMPLETADA EXITOSAMENTE! 🎉")
                print(f"⏱️  Tiempo total: {duration.total_seconds():.1f} segundos")
                print(f"📊 Errores: {len(self.errors)} | Advertencias: {len(self.warnings)}")
                
                print("\n🚀 Para iniciar la aplicación:")
                if self.system_info["os"] == "Windows":
                    print("   📝 Ejecutar: run_medical_workstation.bat")
                else:
                    print("   📝 Ejecutar: ./run_medical_workstation.sh")
                print("   📝 O usar: python launch.py")
                
                print("\n📚 Documentación:")
                print("   📖 README.md - Guía completa")
                print("   📋 INSTALLATION_REPORT.md - Detalles de instalación")
                
                return True
            else:
                print("❌ INSTALACIÓN FALLÓ")
                print(f"📊 Errores: {len(self.errors)} | Advertencias: {len(self.warnings)}")
                print("\n🔍 Revisar errores:")
                for error in self.errors:
                    print(f"   ❌ {error}")
                
                return False
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Instalación interrumpida por el usuario")
            return False
        except Exception as e:
            self.log(f"Error inesperado durante instalación: {e}", "error")
            return False


def main():
    """Función principal del instalador."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Medical Imaging Workstation - Instalador Automático"
    )
    
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Saltar instalación de dependencias de IA"
    )
    
    parser.add_argument(
        "--force",
        action="store_true", 
        help="Forzar reinstalación completa"
    )
    
    args = parser.parse_args()
    
    # Crear instalador y ejecutar
    installer = MedicalWorkstationInstaller()
    
    success = installer.run_installation()
    
    if success:
        sys.exit(0)
    else:
        print("\n❌ Instalación falló. Revisar errores arriba.")
        sys.exit(1)


if __name__ == "__main__":
    main()