#!/usr/bin/env python3
"""
run_medical_workstation.py

Script de inicio inteligente para Medical Imaging Workstation.
Maneja validación del sistema, configuración automática, y inicio
de la aplicación médica con manejo robusto de errores.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import time

# Añadir directorio raíz al path para imports
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

def print_banner():
    """Muestra banner de la aplicación."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║             🏥 MEDICAL IMAGING WORKSTATION 🏥                ║
║                                                              ║
║            Professional Prostate Cancer Analysis             ║
║             Version 1.0.0 | Clean Architecture               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """Verifica la versión de Python."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 o superior requerido")
        print(f"   Versión actual: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]}")
    return True

def check_dependencies() -> Dict[str, bool]:
    """Verifica dependencias críticas."""
    print("🔍 Verificando dependencias críticas...")
    
    dependencies = {
        "PyQt6": False,
        "vtk": False,
        "pydicom": False,
        "SimpleITK": False,
        "numpy": False,
        "scipy": False
    }
    
    for package in dependencies:
        try:
            if package == "PyQt6":
                import PyQt6
                # Verificar submódulos críticos
                from PyQt6.QtWidgets import QApplication
                from PyQt6.QtCore import Qt
                dependencies[package] = True
                print(f"   ✅ {package} - OK")
                
            elif package == "vtk":
                import vtk
                # Verificar capacidades básicas
                vtk_version = vtk.vtkVersion.GetVTKVersion()
                dependencies[package] = True
                print(f"   ✅ {package} {vtk_version} - OK")
                
            elif package == "pydicom":
                import pydicom
                dependencies[package] = True
                print(f"   ✅ {package} {pydicom.__version__} - OK")
                
            elif package == "SimpleITK":
                import SimpleITK as sitk
                dependencies[package] = True
                print(f"   ✅ {package} {sitk.Version_GetITKVersion()} - OK")
                
            else:
                module = __import__(package)
                version = getattr(module, '__version__', 'unknown')
                dependencies[package] = True
                print(f"   ✅ {package} {version} - OK")
                
        except ImportError as e:
            dependencies[package] = False
            print(f"   ❌ {package} - FALTANTE")
            print(f"      Error: {e}")
        except Exception as e:
            dependencies[package] = False
            print(f"   ⚠️  {package} - ERROR")
            print(f"      Error: {e}")
    
    return dependencies

def check_optional_dependencies() -> Dict[str, bool]:
    """Verifica dependencias opcionales (IA)."""
    print("\n🤖 Verificando dependencias de IA (opcionales)...")
    
    ai_dependencies = {
        "torch": False,
        "nnunet": False
    }
    
    for package in ai_dependencies:
        try:
            if package == "torch":
                import torch
                ai_dependencies[package] = True
                print(f"   ✅ PyTorch {torch.__version__}")
                
                # Verificar CUDA
                if torch.cuda.is_available():
                    gpu_count = torch.cuda.device_count()
                    gpu_name = torch.cuda.get_device_name(0)
                    print(f"      🚀 CUDA disponible: {gpu_count} GPU(s)")
                    print(f"      📱 GPU: {gpu_name}")
                else:
                    print(f"      ⚠️  CUDA no disponible (solo CPU)")
                    
            elif package == "nnunet":
                import nnunet
                ai_dependencies[package] = True
                version = getattr(nnunet, '__version__', 'unknown')
                print(f"   ✅ nnUNet {version}")
                
        except ImportError:
            ai_dependencies[package] = False
            print(f"   ⚠️  {package} - No instalado (funcionalidad limitada)")
        except Exception as e:
            ai_dependencies[package] = False
            print(f"   ❌ {package} - Error: {e}")
    
    return ai_dependencies

def check_system_resources():
    """Verifica recursos del sistema."""
    print("\n💻 Verificando recursos del sistema...")
    
    try:
        import psutil
        
        # Memoria
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        memory_available = memory.available / (1024**3)
        
        if memory_gb < 4:
            print(f"   ⚠️  RAM: {memory_gb:.1f}GB (4GB+ recomendado)")
        else:
            print(f"   ✅ RAM: {memory_gb:.1f}GB ({memory_available:.1f}GB disponible)")
        
        # CPU
        cpu_count = psutil.cpu_count()
        print(f"   ✅ CPU: {cpu_count} núcleos")
        
        # Disco
        disk = psutil.disk_usage('.')
        disk_free = disk.free / (1024**3)
        if disk_free < 10:
            print(f"   ⚠️  Disco: {disk_free:.1f}GB libres (10GB+ recomendado)")
        else:
            print(f"   ✅ Disco: {disk_free:.1f}GB libres")
            
    except ImportError:
        print("   ⚠️  No se puede verificar recursos (psutil no disponible)")

def check_opengl():
    """Verifica soporte de OpenGL."""
    print("\n🎨 Verificando soporte gráfico...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtOpenGL import QOpenGLWidget
        
        # Crear aplicación temporal para verificar OpenGL
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
            created_app = True
        else:
            created_app = False
        
        try:
            widget = QOpenGLWidget()
            print("   ✅ OpenGL disponible")
            
        except Exception as e:
            print(f"   ⚠️  OpenGL limitado: {e}")
        finally:
            if created_app:
                app.quit()
                
    except ImportError:
        print("   ❌ No se puede verificar OpenGL")

def create_required_directories():
    """Crea directorios necesarios."""
    print("\n📁 Verificando directorios...")
    
    required_dirs = [
        "medical_data",
        "logs",
        "temp", 
        "exports",
        "config"
    ]
    
    for directory in required_dirs:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Creado: {directory}/")
        else:
            print(f"   ✅ Existe: {directory}/")

def install_missing_dependencies(missing_deps: List[str]):
    """Ofrece instalar dependencias faltantes."""
    if not missing_deps:
        return True
    
    print(f"\n❌ Dependencias faltantes: {', '.join(missing_deps)}")
    print("\nOpciones de instalación:")
    print("1. Instalar automáticamente con pip")
    print("2. Mostrar comandos de instalación manual")
    print("3. Continuar sin instalar (funcionalidad limitada)")
    print("4. Salir")
    
    while True:
        choice = input("\nElige una opción (1-4): ").strip()
        
        if choice == "1":
            return auto_install_dependencies(missing_deps)
        elif choice == "2":
            show_manual_install_commands(missing_deps)
            return False
        elif choice == "3":
            print("⚠️  Continuando con funcionalidad limitada...")
            return True
        elif choice == "4":
            return False
        else:
            print("❌ Opción inválida")

def auto_install_dependencies(deps: List[str]) -> bool:
    """Instala dependencias automáticamente."""
    print(f"\n📦 Instalando dependencias: {', '.join(deps)}")
    
    # Mapeo de nombres de paquetes
    package_map = {
        "PyQt6": "PyQt6",
        "vtk": "vtk",
        "pydicom": "pydicom",
        "SimpleITK": "SimpleITK",
        "numpy": "numpy",
        "scipy": "scipy"
    }
    
    try:
        for dep in deps:
            if dep in package_map:
                package_name = package_map[dep]
                print(f"   📥 Instalando {package_name}...")
                
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package_name],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print(f"   ✅ {package_name} instalado")
                else:
                    print(f"   ❌ Error instalando {package_name}")
                    print(f"      {result.stderr}")
                    return False
        
        print("\n✅ Todas las dependencias instaladas")
        return True
        
    except Exception as e:
        print(f"❌ Error durante instalación automática: {e}")
        return False

def show_manual_install_commands(deps: List[str]):
    """Muestra comandos de instalación manual."""
    print("\n📋 Comandos de instalación manual:")
    print("=" * 50)
    
    # Comandos básicos
    basic_deps = ["PyQt6", "vtk", "pydicom", "SimpleITK", "numpy", "scipy"]
    basic_missing = [dep for dep in deps if dep in basic_deps]
    
    if basic_missing:
        print("\n# Dependencias básicas:")
        basic_packages = " ".join(basic_missing)
        print(f"pip install {basic_packages}")
    
    # Comandos especiales
    if "torch" in deps:
        print("\n# PyTorch (CPU):")
        print("pip install torch torchvision")
        print("\n# PyTorch (GPU con CUDA):")
        print("pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
    
    if "nnunet" in deps:
        print("\n# nnUNet:")
        print("pip install git+https://github.com/MIC-DKFZ/nnUNet.git")
    
    print("\n# Todas las dependencias desde requirements:")
    print("pip install -r requirements.txt")

def run_application(args):
    """Ejecuta la aplicación principal."""
    print("\n🚀 Iniciando Medical Imaging Workstation...")
    
    try:
        # Importar y ejecutar aplicación principal
        from main import main
        
        # Preparar argumentos
        sys.argv = ["main.py"] + [
            arg for arg in [
                f"--storage={args.storage}" if args.storage else None,
                f"--config={args.config}" if args.config else None,
                "--debug" if args.debug else None,
                "--no-splash" if args.no_splash else None
            ] if arg is not None
        ]
        
        # Ejecutar aplicación
        exit_code = main()
        return exit_code
        
    except KeyboardInterrupt:
        print("\n👋 Aplicación interrumpida por el usuario")
        return 0
    except Exception as e:
        print(f"\n❌ Error ejecutando aplicación: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """Función principal del launcher."""
    # Parsear argumentos
    parser = argparse.ArgumentParser(
        description="Medical Imaging Workstation Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python run_medical_workstation.py                    # Inicio normal
  python run_medical_workstation.py --debug           # Con debug
  python run_medical_workstation.py --no-checks       # Sin verificaciones
  python run_medical_workstation.py --storage /data   # Directorio personalizado
        """
    )
    
    parser.add_argument(
        "--storage", 
        type=str,
        help="Directorio de datos médicos"
    )
    
    parser.add_argument(
        "--config",
        type=str, 
        help="Archivo de configuración personalizado"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Activar modo debug"
    )
    
    parser.add_argument(
        "--no-splash",
        action="store_true",
        help="Omitir splash screen"
    )
    
    parser.add_argument(
        "--no-checks",
        action="store_true",
        help="Omitir verificaciones del sistema"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Solo instalar dependencias y salir"
    )
    
    args = parser.parse_args()
    
    # Mostrar banner
    print_banner()
    
    # Verificación de Python
    if not check_python_version():
        return 1
    
    if not args.no_checks:
        # Verificar dependencias críticas
        deps_status = check_dependencies()
        missing_critical = [dep for dep, status in deps_status.items() if not status]
        
        if missing_critical:
            if args.install_deps:
                if not install_missing_dependencies(missing_critical):
                    return 1
            else:
                print(f"\n❌ Dependencias críticas faltantes: {', '.join(missing_critical)}")
                print("Ejecuta con --install-deps para instalación automática")
                print("O instala manualmente: pip install -r requirements.txt")
                return 1
        
        # Verificar dependencias opcionales
        check_optional_dependencies()
        
        # Verificar recursos del sistema
        check_system_resources()
        
        # Verificar OpenGL
        check_opengl()
    
    # Crear directorios necesarios
    create_required_directories()
    
    # Si solo se pidió instalar dependencias
    if args.install_deps:
        print("\n✅ Verificación e instalación completada")
        return 0
    
    # Ejecutar aplicación
    print("\n" + "="*60)
    exit_code = run_application(args)
    
    print(f"\n👋 Aplicación finalizada con código: {exit_code}")
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)