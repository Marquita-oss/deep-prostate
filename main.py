#!/usr/bin/env python3
"""
main.py

Punto de entrada principal para la aplicación de visualización médica.
Configura el entorno, inicializa servicios, y lanza la interfaz gráfica
con arquitectura hexagonal para análisis de cáncer prostático.

Autor: Sistema de Visualización Médica
Versión: 1.0.0
Arquitectura: Clean Architecture / Hexagonal
Framework UI: PyQt6
Motor 3D: VTK
IA: nnUNetv2 Integration
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional

# PyQt6 imports
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt6.QtCore import Qt, QTimer, QThread
from PyQt6.QtGui import QPixmap, QFont, QPalette, QColor

# Importar componentes de la aplicación
from infrastructure.ui.main_window import MedicalImagingMainWindow
from infrastructure.storage.dicom_repository import DICOMImageRepository
from infrastructure.visualization.vtk_renderer import MedicalVTKRenderer

# Configuración de logging
from infrastructure.utils.logging_config import setup_logging
from infrastructure.utils.config_manager import ConfigurationManager
from infrastructure.utils.startup_validator import SystemValidator


class MedicalImagingApplication:
    """
    Clase principal de la aplicación médica.
    
    Gestiona el ciclo de vida completo de la aplicación, desde la inicialización
    de servicios hasta el manejo de errores globales y cierre limpio.
    """
    
    def __init__(self):
        """Inicializa la aplicación médica."""
        self._app: Optional[QApplication] = None
        self._main_window: Optional[MedicalImagingMainWindow] = None
        self._config_manager: Optional[ConfigurationManager] = None
        self._logger: Optional[logging.Logger] = None
        self._startup_successful = False
        
        # Configuraciones por defecto
        self._default_storage_path = "./medical_data"
        self._default_models_path = "./models"
        self._default_temp_path = "./temp"
        
    def initialize(self) -> bool:
        """
        Inicializa todos los componentes de la aplicación.
        
        Returns:
            True si la inicialización fue exitosa, False en caso contrario
        """
        try:
            # 1. Configurar logging
            self._setup_logging()
            self._logger.info("Iniciando Medical Imaging Workstation v1.0.0")
            
            # 2. Crear aplicación Qt
            self._create_qt_application()
            
            # 3. Mostrar splash screen
            splash = self._create_splash_screen()
            splash.show()
            self._app.processEvents()
            
            # 4. Cargar configuración
            splash.showMessage("Loading configuration...", Qt.AlignmentFlag.AlignBottom, Qt.GlobalColor.white)
            self._app.processEvents()
            
            self._config_manager = ConfigurationManager()
            config_loaded = self._config_manager.load_configuration()
            
            if not config_loaded:
                self._logger.warning("Using default configuration")
            
            # 5. Validar sistema
            splash.showMessage("Validating system requirements...", Qt.AlignmentFlag.AlignBottom, Qt.GlobalColor.white)
            self._app.processEvents()
            
            validator = SystemValidator()
            validation_result = validator.validate_system()
            
            if not validation_result.is_valid:
                self._show_validation_errors(validation_result)
                return False
            
            # 6. Crear directorios necesarios
            splash.showMessage("Creating directories...", Qt.AlignmentFlag.AlignBottom, Qt.GlobalColor.white)
            self._app.processEvents()
            
            self._create_required_directories()
            
            # 7. Inicializar servicios de infraestructura
            splash.showMessage("Initializing medical services...", Qt.AlignmentFlag.AlignBottom, Qt.GlobalColor.white)
            self._app.processEvents()
            
            storage_path = self._config_manager.get("storage_path", self._default_storage_path)
            
            # 8. Crear ventana principal
            splash.showMessage("Creating main interface...", Qt.AlignmentFlag.AlignBottom, Qt.GlobalColor.white)
            self._app.processEvents()
            
            self._main_window = MedicalImagingMainWindow(storage_path)
            
            # 9. Configurar manejo de errores globales
            self._setup_error_handling()
            
            # 10. Finalizar inicialización
            splash.showMessage("Ready!", Qt.AlignmentFlag.AlignBottom, Qt.GlobalColor.white)
            self._app.processEvents()
            
            # Cerrar splash después de un momento
            QTimer.singleShot(1000, splash.close)
            
            self._startup_successful = True
            self._logger.info("Aplicación inicializada exitosamente")
            
            return True
            
        except Exception as e:
            self._logger.error(f"Error durante la inicialización: {e}")
            self._show_startup_error(str(e))
            return False
    
    def run(self) -> int:
        """
        Ejecuta la aplicación.
        
        Returns:
            Código de salida de la aplicación
        """
        if not self._startup_successful:
            self._logger.error("No se puede ejecutar: inicialización fallida")
            return 1
        
        try:
            # Mostrar ventana principal
            self._main_window.show()
            
            # Configurar autosave periódico
            self._setup_autosave()
            
            # Log de inicio exitoso
            self._logger.info("Aplicación iniciada - Lista para uso médico")
            
            # Ejecutar loop principal
            return self._app.exec()
            
        except Exception as e:
            self._logger.critical(f"Error crítico en ejecución: {e}")
            return 1
        
        finally:
            self._cleanup()
    
    def _setup_logging(self) -> None:
        """Configura el sistema de logging."""
        self._logger = setup_logging(
            log_level=logging.INFO,
            log_file="./logs/medical_imaging.log",
            console_output=True
        )
    
    def _create_qt_application(self) -> None:
        """Crea y configura la aplicación Qt."""
        # Configurar atributos de aplicación antes de crear QApplication
        QApplication.setApplicationName("Medical Imaging Workstation")
        QApplication.setApplicationVersion("1.0.0")
        QApplication.setOrganizationName("Medical Software Solutions")
        QApplication.setOrganizationDomain("medical-imaging.local")
        
        # Crear aplicación
        self._app = QApplication(sys.argv)
        
        # Configurar estilo y tema
        self._setup_application_style()
        
        # Configurar fuentes
        self._setup_fonts()
    
    def _setup_application_style(self) -> None:
        """Configura el estilo visual de la aplicación."""
        # Aplicar tema oscuro a nivel de aplicación
        self._app.setStyle("Fusion")
        
        # Configurar palette oscuro global
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        
        self._app.setPalette(dark_palette)
    
    def _setup_fonts(self) -> None:
        """Configura las fuentes de la aplicación."""
        # Fuente principal optimizada para interfaces médicas
        main_font = QFont("Segoe UI", 9)
        main_font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        self._app.setFont(main_font)
    
    def _create_splash_screen(self) -> QSplashScreen:
        """Crea la pantalla de splash de inicio."""
        # Crear imagen de splash simple
        splash_pixmap = QPixmap(400, 300)
        splash_pixmap.fill(QColor(45, 45, 48))
        
        # En implementación real, cargar imagen de splash profesional
        splash = QSplashScreen(splash_pixmap)
        splash.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        
        return splash
    
    def _create_required_directories(self) -> None:
        """Crea los directorios necesarios para la aplicación."""
        directories = [
            self._config_manager.get("storage_path", self._default_storage_path),
            self._config_manager.get("models_path", self._default_models_path),
            self._config_manager.get("temp_path", self._default_temp_path),
            "./logs",
            "./exports",
            "./backups"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            self._logger.debug(f"Directorio creado/verificado: {directory}")
    
    def _setup_error_handling(self) -> None:
        """Configura el manejo global de errores."""
        def handle_exception(exc_type, exc_value, exc_traceback):
            """Maneja excepciones no capturadas."""
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # Log del error
            self._logger.critical(
                "Excepción no capturada",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
            
            # Mostrar error al usuario (si hay interfaz disponible)
            if self._main_window:
                QMessageBox.critical(
                    self._main_window,
                    "Critical Error",
                    f"A critical error occurred:\n{exc_value}\n\nPlease check the logs for details."
                )
        
        sys.excepthook = handle_exception
    
    def _setup_autosave(self) -> None:
        """Configura guardado automático periódico."""
        autosave_timer = QTimer()
        autosave_timer.timeout.connect(self._perform_autosave)
        
        # Autosave cada 5 minutos
        autosave_interval = self._config_manager.get("autosave_interval_minutes", 5)
        autosave_timer.start(autosave_interval * 60 * 1000)
        
        self._logger.info(f"Autosave configurado cada {autosave_interval} minutos")
    
    def _perform_autosave(self) -> None:
        """Realiza guardado automático del estado de la aplicación."""
        try:
            if self._main_window and hasattr(self._main_window, '_current_image'):
                # En implementación real, guardar estado actual
                self._logger.debug("Autosave ejecutado")
        except Exception as e:
            self._logger.error(f"Error en autosave: {e}")
    
    def _show_validation_errors(self, validation_result) -> None:
        """Muestra errores de validación del sistema."""
        error_msg = "System validation failed:\n\n"
        for error in validation_result.errors:
            error_msg += f"• {error}\n"
        
        error_msg += "\nPlease fix these issues before running the application."
        
        QMessageBox.critical(None, "System Validation Failed", error_msg)
    
    def _show_startup_error(self, error_message: str) -> None:
        """Muestra error de inicialización."""
        QMessageBox.critical(
            None,
            "Startup Error",
            f"Failed to initialize application:\n\n{error_message}\n\nPlease check the logs for details."
        )
    
    def _cleanup(self) -> None:
        """Limpia recursos al cerrar la aplicación."""
        try:
            self._logger.info("Cerrando aplicación...")
            
            # Limpiar recursos VTK si existen
            if self._main_window and hasattr(self._main_window, '_vtk_renderer'):
                self._main_window._vtk_renderer.clear_all()
            
            # Guardar configuración
            if self._config_manager:
                self._config_manager.save_configuration()
            
            self._logger.info("Aplicación cerrada limpiamente")
            
        except Exception as e:
            self._logger.error(f"Error durante cleanup: {e}")


def main() -> int:
    """
    Función principal de entrada.
    
    Returns:
        Código de salida de la aplicación
    """
    # Configurar argumentos de línea de comandos si es necesario
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Medical Imaging Workstation for Prostate Cancer Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Start with default configuration
  python main.py --storage /path/data     # Use custom data directory
  python main.py --debug                  # Enable debug logging
  python main.py --config config.yaml    # Use custom configuration file
        """
    )
    
    parser.add_argument(
        "--storage",
        type=str,
        help="Path to medical data storage directory"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--no-splash",
        action="store_true",
        help="Skip splash screen"
    )
    
    args = parser.parse_args()
    
    # Crear y configurar aplicación
    medical_app = MedicalImagingApplication()
    
    # Aplicar argumentos de línea de comandos
    if args.storage:
        medical_app._default_storage_path = args.storage
    
    if args.debug:
        # Configurar logging debug
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Inicializar aplicación
    if not medical_app.initialize():
        print("Failed to initialize application. Check logs for details.")
        return 1
    
    # Ejecutar aplicación
    return medical_app.run()


if __name__ == "__main__":
    # Configurar path para imports relativos
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    # Ejecutar aplicación
    exit_code = main()
    sys.exit(exit_code)