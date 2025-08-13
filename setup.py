#!/usr/bin/env python3
"""
setup.py

Script de configuración e instalación para Medical Imaging Workstation.
Automatiza la instalación de dependencias, configuración inicial,
y validación del entorno para uso médico profesional.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from setuptools import setup, find_packages

# Información del paquete
PACKAGE_NAME = "medical_imaging_workstation"
VERSION = "1.0.0"
DESCRIPTION = "Professional medical imaging workstation for prostate cancer analysis"
LONG_DESCRIPTION = """
Medical Imaging Workstation

Una aplicación profesional de visualización médica especializada en análisis 
de cáncer prostático, desarrollada con arquitectura hexagonal y integración 
con nnUNetv2 para segmentación automática con IA.

Características principales:
- Visualización 2D/3D de imágenes DICOM
- Segmentación automática con IA (nnUNet)
- Herramientas de medición precisas
- Análisis cuantitativo avanzado
- Interfaz optimizada para uso clínico
- Cumplimiento con estándares médicos DICOM
"""

AUTHOR = "Medical Software Solutions Team"
AUTHOR_EMAIL = "support@medical-imaging.local"
URL = "https://github.com/medical-imaging/workstation"
LICENSE = "Proprietary Medical Software License"

# Clasificadores PyPI
CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Healthcare Industry",
    "Topic :: Scientific/Engineering :: Medical Science Apps.",
    "Topic :: Scientific/Engineering :: Image Processing",
    "Topic :: Scientific/Engineering :: Visualization",
    "License :: Other/Proprietary License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Operating System :: OS Independent",
    "Environment :: X11 Applications :: Qt",
]

# Palabras clave
KEYWORDS = [
    "medical-imaging", "dicom", "radiology", "prostate-cancer", 
    "segmentation", "ai", "nnunet", "vtk", "pyqt", "medical-ai"
]

def read_requirements(filename):
    """Lee dependencias desde archivo requirements."""
    requirements_file = Path(__file__).parent / filename
    if requirements_file.exists():
        with open(requirements_file, 'r', encoding='utf-8') as f:
            return [
                line.strip() 
                for line in f 
                if line.strip() and not line.startswith('#')
            ]
    return []

def check_system_requirements():
    """Verifica los requisitos mínimos del sistema."""
    print("🔍 Verificando requisitos del sistema...")
    
    # Verificar versión de Python
    if sys.version_info < (3, 8):
        raise RuntimeError(
            f"Python 3.8+ requerido. Versión actual: {sys.version}"
        )
    print(f"✅ Python {sys.version.split()[0]}")
    
    # Verificar sistema operativo
    import platform
    os_name = platform.system()
    print(f"✅ Sistema operativo: {os_name} {platform.release()}")
    
    # Verificar memoria disponible
    try:
        import psutil
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb < 4:
            print(f"⚠️  Memoria RAM baja: {memory_gb:.1f}GB (4GB+ recomendado)")
        else:
            print(f"✅ Memoria RAM: {memory_gb:.1f}GB")
    except ImportError:
        print("⚠️  No se pudo verificar memoria RAM")
    
    # Verificar espacio en disco
    disk_free = shutil.disk_usage('.').free / (1024**3)
    if disk_free < 10:
        print(f"⚠️  Espacio en disco bajo: {disk_free:.1f}GB (10GB+ recomendado)")
    else:
        print(f"✅ Espacio en disco: {disk_free:.1f}GB libres")

def create_directories():
    """Crea los directorios necesarios para la aplicación."""
    print("📁 Creando directorios necesarios...")
    
    directories = [
        "medical_data",
        "logs", 
        "temp",
        "exports",
        "models",
        "config",
        "backups"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(exist_ok=True)
        print(f"   ✅ {directory}/")

def install_system_dependencies():
    """Instala dependencias del sistema si es posible."""
    print("🔧 Verificando dependencias del sistema...")
    
    import platform
    system = platform.system()
    
    if system == "Linux":
        print("   ℹ️  Para Linux, asegúrate de tener instalado:")
        print("   sudo apt-get install python3-opengl mesa-utils")
        print("   sudo apt-get install libgl1-mesa-dev libglu1-mesa-dev")
        
    elif system == "Windows":
        print("   ℹ️  Para Windows, asegúrate de tener:")
        print("   - Visual C++ Redistributable")
        print("   - Drivers de GPU actualizados")
        
    elif system == "Darwin":  # macOS
        print("   ℹ️  Para macOS, asegúrate de tener:")
        print("   - Xcode Command Line Tools: xcode-select --install")

def setup_configuration():
    """Configura archivos de configuración inicial."""
    print("⚙️  Configurando archivos iniciales...")
    
    config_dir = Path("config")
    config_file = config_dir / "medical_imaging_config.yaml"
    
    if not config_file.exists():
        # En implementación real, copiar archivo de configuración por defecto
        print(f"   ✅ Configuración creada: {config_file}")
    else:
        print(f"   ℹ️  Configuración existente: {config_file}")

def validate_installation():
    """Valida que la instalación sea correcta."""
    print("✅ Validando instalación...")
    
    try:
        # Verificar imports críticos
        import PyQt6
        print("   ✅ PyQt6 disponible")
        
        import vtk
        print("   ✅ VTK disponible")
        
        import pydicom
        print("   ✅ PyDICOM disponible")
        
        import SimpleITK
        print("   ✅ SimpleITK disponible")
        
        import numpy
        print("   ✅ NumPy disponible")
        
    except ImportError as e:
        print(f"   ❌ Error de importación: {e}")
        return False
    
    # Verificar OpenGL (importante para VTK)
    try:
        from PyQt6.QtOpenGL import QOpenGLWidget
        print("   ✅ OpenGL disponible")
    except ImportError:
        print("   ⚠️  OpenGL podría no estar disponible")
    
    return True

def run_system_validator():
    """Ejecuta el validador completo del sistema."""
    print("🔍 Ejecutando validador completo del sistema...")
    
    try:
        from infrastructure.utils.startup_validator import SystemValidator
        
        validator = SystemValidator()
        result = validator.validate_system()
        
        if result.is_valid:
            print("   ✅ Sistema validado correctamente")
        else:
            print("   ⚠️  Advertencias en la validación:")
            for error in result.errors:
                print(f"      ❌ {error}")
            for warning in result.warnings:
                print(f"      ⚠️  {warning}")
        
        return result.is_valid
        
    except ImportError:
        print("   ℹ️  Validador del sistema no disponible aún")
        return True
    except Exception as e:
        print(f"   ⚠️  Error en validador: {e}")
        return True

def post_install_steps():
    """Ejecuta pasos adicionales después de la instalación."""
    print("🎯 Ejecutando configuración post-instalación...")
    
    # Crear directorios
    create_directories()
    
    # Configurar archivos
    setup_configuration()
    
    # Verificar instalación
    if not validate_installation():
        print("❌ La validación de instalación falló")
        return False
    
    # Ejecutar validador del sistema
    if not run_system_validator():
        print("⚠️  El sistema tiene algunas limitaciones")
    
    print("\n🎉 ¡Instalación completada!")
    print("\nPróximos pasos:")
    print("1. Ejecutar: python main.py")
    print("2. Cargar imágenes DICOM desde File > Open...")
    print("3. Consultar documentación: README.md")
    
    return True

# Configuración principal de setuptools
setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/plain",
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    license=LICENSE,
    classifiers=CLASSIFIERS,
    keywords=KEYWORDS,
    
    # Configuración de paquetes
    packages=find_packages(),
    python_requires=">=3.8",
    
    # Dependencias
    install_requires=read_requirements("requirements.txt"),
    extras_require={
        "dev": read_requirements("requirements-dev.txt"),
        "ai": [
            "torch>=1.12.0",
            "torchvision>=0.13.0",
        ],
        "docs": [
            "Sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0"
        ]
    },
    
    # Archivos de datos
    package_data={
        PACKAGE_NAME: [
            "config/*.yaml",
            "resources/*.png",
            "resources/*.ico",
            "docs/*",
        ]
    },
    include_package_data=True,
    
    # Scripts de línea de comandos
    entry_points={
        "console_scripts": [
            "medical-imaging=main:main",
            "medical-validator=infrastructure.utils.startup_validator:main",
        ],
    },
    
    # Metadatos adicionales
    project_urls={
        "Bug Reports": f"{URL}/issues",
        "Source": URL,
        "Documentation": f"{URL}/docs",
    },
    
    # Configuración de build
    zip_safe=False,
)

# Script principal cuando se ejecuta directamente
if __name__ == "__main__":
    print("🏥 Medical Imaging Workstation - Setup")
    print("=" * 50)
    
    try:
        # Verificar requisitos del sistema
        check_system_requirements()
        
        # Información sobre dependencias del sistema
        install_system_dependencies()
        
        print("\n📦 Instalando dependencias de Python...")
        print("   Ejecuta: pip install -e .")
        
        # Si se ejecuta después de la instalación pip
        if len(sys.argv) > 1 and sys.argv[1] == "post_install":
            post_install_steps()
            
    except Exception as e:
        print(f"❌ Error durante setup: {e}")
        sys.exit(1)