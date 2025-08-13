#!/usr/bin/env python3
"""
infrastructure/ui/simplified_main_window.py

Ventana principal simplificada de la aplicación médica.
Esta versión refactorizada demuestra cómo eliminar un God Object manteniendo
toda la funcionalidad. Se enfoca únicamente en coordinación de alto nivel
y delegación apropiada, siguiendo el principio de responsabilidad única.

Responsabilidades ÚNICAS:
- Coordinar flujos de trabajo médicos de alto nivel
- Responder a eventos de usuario estratégicos
- Mantener estado global de la aplicación médica
- Delegar operaciones complejas a coordinadores especializados

Responsabilidades ELIMINADAS (ahora delegadas):
- Crear o configurar servicios médicos ❌
- Configurar widgets de UI individualmente ❌  
- Manejar threads de IA directamente ❌
- Aplicar estilos y temas manualmente ❌
- Gestionar detalles de visualización ❌
- Coordinar comunicación entre componentes ❌
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QStatusBar, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QCloseEvent

# Imports de nuestros componentes especializados
from infrastructure.di.medical_service_container import MedicalServiceContainer
from infrastructure.coordination.workflow_coordinator import MedicalWorkflowCoordinator
from infrastructure.ui.factories.ui_component_factory import (
    MedicalUIComponentFactory, WorkstationUIComponents
)

# Imports del dominio médico
from domain.entities.medical_image import MedicalImage
from domain.entities.segmentation import MedicalSegmentation


class SimplifiedMedicalMainWindow(QMainWindow):
    """
    Ventana principal simplificada para aplicación médica.
    
    Esta clase demuestra cómo un God Object puede ser refactorizado en un
    componente enfocado y mantenible. En lugar de manejar docenas de 
    responsabilidades diferentes, esta ventana actúa como un verdadero
    coordinador de alto nivel.
    
    Piensa en esta clase como el director médico de un hospital moderno:
    no realiza procedimientos médicos directamente, no configura equipos
    personalmente, no gestiona el inventario. En su lugar, toma decisiones
    estratégicas y delega apropiadamente a especialistas.
    
    Arquitectura de la simplicidad:
    - Recibe dependencias ya configuradas (no las crea)
    - Delega operaciones complejas (no las implementa)
    - Coordina flujos de trabajo (no maneja detalles)
    - Responde a eventos estratégicos (no a micro-eventos)
    """
    
    # Señales para comunicación de alto nivel solamente
    application_closing = pyqtSignal()
    patient_context_changed = pyqtSignal(str)  # patient_id
    
    def __init__(
        self, 
        service_container: MedicalServiceContainer,
        workflow_coordinator: MedicalWorkflowCoordinator,
        ui_components: WorkstationUIComponents
    ):
        """
        Inicializa la ventana principal con dependencias ya configuradas.
        
        Observa cómo esta ventana NO crea nada por sí misma. En su lugar,
        recibe todo lo que necesita ya configurado desde el exterior.
        Esto es la aplicación práctica del principio de Inversión de 
        Dependencias en acción.
        
        Args:
            service_container: Servicios médicos ya configurados
            workflow_coordinator: Coordinador de flujos de trabajo ya inicializado
            ui_components: Componentes de UI ya creados y conectados
        """
        super().__init__()
        
        # Dependencias inyectadas (no creadas internamente)
        self._services = service_container
        self._coordinator = workflow_coordinator
        self._ui_components = ui_components
        
        # Estado de alto nivel de la aplicación médica
        self._current_patient_id: Optional[str] = None
        self._current_image: Optional[MedicalImage] = None
        self._application_state = "idle"
        self._workflow_history: list = []
        
        # Logger para auditoría médica
        self._logger = logging.getLogger(__name__)
        
        # Configurar ventana principal (delegando los detalles)
        self._setup_main_window()
        self._setup_menu_system()
        self._setup_status_system()
        self._setup_high_level_coordination()
        
        self._logger.info("Ventana principal médica simplificada inicializada")
    
    def _setup_main_window(self) -> None:
        """
        Configura la ventana principal de manera simple y directa.
        
        Observa la simplicidad aquí comparada con el método original.
        No hay configuración detallada de widgets, no hay aplicación
        manual de estilos, no hay gestión de layouts complejos.
        Todo eso ya fue manejado por el UIComponentFactory.
        """
        # Configuración básica de ventana
        self.setWindowTitle("Medical Imaging Workstation - Simplified Architecture")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 1000)
        
        # Crear layout principal usando componentes ya configurados
        self._create_main_layout()
        
        # Aplicar tema médico (delegado al factory, solo activamos aquí)
        self._apply_medical_window_theme()
    
    def _create_main_layout(self) -> None:
        """
        Crea el layout principal usando componentes UI ya preparados.
        
        Esta es una demostración perfecta de cómo la simplicidad emerge
        cuando cada componente tiene responsabilidades claras. En lugar
        de crear y configurar docenas de widgets, simplemente organizamos
        componentes ya listos para usar.
        """
        # Widget central principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal horizontal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Crear splitter principal para organizar paneles
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Añadir componentes ya configurados al layout
        # Cada componente ya está internamente configurado y conectado
        if self._ui_components.left_panel:
            main_splitter.addWidget(self._ui_components.left_panel)
        
        if self._ui_components.central_viewer:
            main_splitter.addWidget(self._ui_components.central_viewer)
        
        if self._ui_components.right_panel:
            main_splitter.addWidget(self._ui_components.right_panel)
        
        # Configurar proporciones apropiadas para uso médico
        main_splitter.setSizes([300, 800, 350])  # left, center, right
        
        # Permitir que el panel central se expanda preferentemente
        main_splitter.setStretchFactor(1, 1)  # El panel central es expandible
    
    def _setup_menu_system(self) -> None:
        """
        Configura el sistema de menús enfocado en acciones de alto nivel.
        
        Los menús solo contienen acciones estratégicas que requieren
        decisión del coordinador principal. Acciones detalladas están
        delegadas a los widgets especializados.
        """
        menubar = self.menuBar()
        
        # Menú File - Solo acciones de archivo de alto nivel
        file_menu = menubar.addMenu("&File")
        
        # Acción para abrir estudio completo (no archivo individual)
        open_study_action = QAction("&Open Medical Study...", self)
        open_study_action.setShortcut("Ctrl+O")
        open_study_action.triggered.connect(self._on_open_medical_study)
        file_menu.addAction(open_study_action)
        
        file_menu.addSeparator()
        
        # Acción para cerrar aplicación
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Analysis - Acciones médicas de alto nivel
        analysis_menu = menubar.addMenu("&Analysis")
        
        # Análisis completo de IA
        full_ai_analysis_action = QAction("&Run Full AI Analysis", self)
        full_ai_analysis_action.setShortcut("Ctrl+A")
        full_ai_analysis_action.triggered.connect(self._on_run_full_ai_analysis)
        analysis_menu.addAction(full_ai_analysis_action)
        
        # Menú View - Configuraciones de visualización de alto nivel
        view_menu = menubar.addMenu("&View")
        
        # Toggle para vista de desarrollo (útil para debugging)
        dev_view_action = QAction("&Development View", self)
        dev_view_action.setCheckable(True)
        dev_view_action.triggered.connect(self._on_toggle_development_view)
        view_menu.addAction(dev_view_action)
        
        # Menú Help - Información del sistema
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_show_about)
        help_menu.addAction(about_action)
    
    def _setup_status_system(self) -> None:
        """
        Configura sistema de estado enfocado en información de alto nivel.
        
        La barra de estado muestra únicamente información estratégica
        relevante para el coordinador médico. Detalles específicos son
        manejados por widgets especializados.
        """
        # Crear barra de estado
        status_bar = self.statusBar()
        
        # Configurar timer para actualizaciones periódicas de estado
        self._status_update_timer = QTimer()
        self._status_update_timer.timeout.connect(self._update_high_level_status)
        self._status_update_timer.start(2000)  # Actualizar cada 2 segundos
        
        # Estado inicial
        self._update_high_level_status()
    
    def _setup_high_level_coordination(self) -> None:
        """
        Configura coordinación de alto nivel entre componentes principales.
        
        Este método establece las conexiones estratégicas entre el coordinador
        de flujos de trabajo y los componentes de UI. Solo maneja eventos
        que requieren decisión o conocimiento del coordinador principal.
        """
        # Conectar eventos estratégicos del coordinador de flujos de trabajo
        self._coordinator.workflow_completed.connect(self._on_workflow_completed)
        self._coordinator.workflow_error.connect(self._on_workflow_error)
        self._coordinator.medical_validation_required.connect(
            self._on_medical_validation_required
        )
        
        # Conectar eventos estratégicos de imagen cargada
        self._coordinator.image_loaded.connect(self._on_image_loaded_strategically)
        
        # Conectar eventos de cambio de paciente
        if self._ui_components.patient_browser:
            self._ui_components.patient_browser.patient_changed.connect(
                self._on_patient_context_changed
            )
        
        self._logger.debug("Coordinación de alto nivel configurada")
    
    def _apply_medical_window_theme(self) -> None:
        """
        Aplica tema médico a nivel de ventana principal.
        
        Solo configuraciones que afectan la ventana como un todo.
        Los temas de widgets individuales ya fueron aplicados por el Factory.
        """
        # Tema oscuro profesional para uso médico prolongado
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
                color: #dcdcdc;
            }
            QMenuBar {
                background-color: #2d2d30;
                color: #dcdcdc;
                border-bottom: 1px solid #666;
            }
            QMenuBar::item:selected {
                background-color: #0078d4;
            }
            QStatusBar {
                background-color: #2d2d30;
                color: #dcdcdc;
                border-top: 1px solid #666;
            }
        """)
    
    # Métodos de respuesta a eventos de alto nivel
    
    def _on_open_medical_study(self) -> None:
        """
        Responde a solicitud de apertura de estudio médico.
        
        Este método demuestra el patrón de delegación: la ventana principal
        no maneja los detalles de selección de archivos o validación DICOM.
        En su lugar, delega inmediatamente al coordinador especializado.
        """
        self._logger.info("Usuario solicitó apertura de estudio médico")
        
        # Delegar inmediatamente al coordinador de flujos de trabajo
        # No manejamos detalles de selección de archivos aquí
        workflow_id = self._coordinator.start_image_loading_workflow()
        
        # Registrar la solicitud para auditoría médica
        self._workflow_history.append({
            'action': 'open_study_requested',
            'timestamp': datetime.now(),
            'workflow_id': workflow_id,
            'user_initiated': True
        })
        
        # Actualizar estado de alto nivel
        self._application_state = "loading_study"
        self._update_high_level_status()
    
    def _on_run_full_ai_analysis(self) -> None:
        """
        Responde a solicitud de análisis completo de IA.
        
        Otro ejemplo de delegación apropiada: validamos prerrequisitos
        de alto nivel y delegamos la operación compleja al coordinador.
        """
        self._logger.info("Usuario solicitó análisis completo de IA")
        
        # Validación de prerrequisitos de alto nivel
        if not self._current_image:
            self._show_user_message(
                "No Image Loaded", 
                "Please load a medical image before running AI analysis.",
                "warning"
            )
            return
        
        if not self._validate_ai_analysis_prerequisites():
            return
        
        # Delegar al coordinador especializado
        workflow_id = self._coordinator.start_ai_analysis_workflow(
            self._current_image, 
            analysis_type="full"
        )
        
        # Registrar para auditoría
        self._workflow_history.append({
            'action': 'ai_analysis_requested',
            'timestamp': datetime.now(),
            'workflow_id': workflow_id,
            'image_id': self._current_image.series_instance_uid if self._current_image else None,
            'analysis_type': 'full'
        })
        
        # Actualizar estado
        self._application_state = "running_ai_analysis"
        self._update_high_level_status()
    
    def _on_toggle_development_view(self, checked: bool) -> None:
        """Activa/desactiva vista de desarrollo para debugging."""
        if checked:
            self._show_development_info()
        else:
            self._hide_development_info()
    
    def _on_show_about(self) -> None:
        """Muestra información sobre la aplicación."""
        about_text = """
        Medical Imaging Workstation
        Simplified Architecture Demonstration
        
        This version demonstrates how to eliminate God Objects
        while maintaining full functionality through proper
        separation of concerns and dependency injection.
        
        Architecture Components:
        • Medical Service Container
        • Workflow Coordinator  
        • UI Component Factory
        • Simplified Main Window
        
        Built with Clean Architecture principles
        for medical software development.
        """
        
        QMessageBox.about(self, "About Medical Workstation", about_text.strip())
    
    # Métodos de respuesta a eventos del coordinador
    
    def _on_workflow_completed(self, workflow_id: str, results: Dict[str, Any]) -> None:
        """
        Responde a finalización exitosa de flujo de trabajo.
        
        Solo maneja aspectos estratégicos de la finalización.
        Los detalles específicos ya fueron manejados por el coordinador.
        """
        self._logger.info(f"Flujo de trabajo completado: {workflow_id}")
        
        # Actualizar estado de alto nivel basado en tipo de workflow
        workflow_info = next(
            (w for w in self._workflow_history if w.get('workflow_id') == workflow_id),
            None
        )
        
        if workflow_info:
            if workflow_info['action'] == 'open_study_requested':
                self._application_state = "study_loaded"
            elif workflow_info['action'] == 'ai_analysis_requested':
                self._application_state = "ai_analysis_completed"
        
        self._update_high_level_status()
    
    def _on_workflow_error(self, workflow_id: str, error_message: str) -> None:
        """
        Responde a errores en flujos de trabajo.
        
        Maneja solo la respuesta estratégica a errores. Los detalles
        del manejo de errores específicos están en el coordinador.
        """
        self._logger.error(f"Error en flujo de trabajo {workflow_id}: {error_message}")
        
        # Mostrar error al usuario de manera apropiada para aplicación médica
        self._show_user_message(
            "Medical Workflow Error",
            f"An error occurred during medical workflow:\n{error_message}\n\n"
            f"Please check the logs for detailed information.",
            "error"
        )
        
        # Revertir estado de aplicación
        self._application_state = "error"
        self._update_high_level_status()
    
    def _on_medical_validation_required(self, validation_type: str, data: Dict[str, Any]) -> None:
        """
        Responde a solicitudes de validación médica.
        
        Este método maneja situaciones donde el coordinador necesita
        intervención o decisión médica de alto nivel.
        """
        self._logger.warning(f"Validación médica requerida: {validation_type}")
        
        if validation_type == "low_quality_ai_results":
            self._handle_low_quality_ai_results(data)
        elif validation_type == "ambiguous_findings":
            self._handle_ambiguous_medical_findings(data)
        else:
            self._handle_generic_medical_validation(validation_type, data)
    
    def _on_image_loaded_strategically(self, image: MedicalImage) -> None:
        """
        Responde a imagen cargada desde perspectiva estratégica.
        
        Solo maneja aspectos de alto nivel. Los detalles de actualización
        de UI ya fueron manejados por el coordinador y los widgets.
        """
        self._current_image = image
        self._logger.info(f"Imagen cargada estratégicamente: {image.series_instance_uid}")
        
        # Actualizar contexto de aplicación
        self._application_state = "image_ready"
        self._update_high_level_status()
        
        # Registrar para auditoría médica
        self._workflow_history.append({
            'action': 'image_loaded',
            'timestamp': datetime.now(),
            'image_id': image.series_instance_uid,
            'patient_id': image.patient_id,
            'modality': image.modality.value
        })
    
    def _on_patient_context_changed(self, patient_id: str) -> None:
        """Responde a cambio de contexto de paciente."""
        self._current_patient_id = patient_id
        self._logger.info(f"Contexto de paciente cambiado: {patient_id}")
        
        # Emitir señal para otros componentes que puedan necesitar saberlo
        self.patient_context_changed.emit(patient_id)
        
        self._update_high_level_status()
    
    # Métodos de utilidad de alto nivel
    
    def _validate_ai_analysis_prerequisites(self) -> bool:
        """
        Valida prerrequisitos de alto nivel para análisis de IA.
        
        Solo validaciones estratégicas. Validaciones técnicas detalladas
        están en el coordinador de flujos de trabajo.
        """
        if not self._current_image:
            return False
        
        # Validar que tengamos contexto de paciente apropiado
        if not self._current_patient_id:
            self._show_user_message(
                "Missing Patient Context",
                "Patient context is required for AI analysis.\n"
                "Please ensure proper patient selection.",
                "warning"
            )
            return False
        
        return True
    
    def _update_high_level_status(self) -> None:
        """
        Actualiza información de estado de alto nivel.
        
        Solo muestra información estratégicamente relevante para
        el coordinador médico principal.
        """
        status_parts = []
        
        # Estado de aplicación
        status_parts.append(f"Status: {self._application_state.replace('_', ' ').title()}")
        
        # Contexto de paciente actual
        if self._current_patient_id:
            status_parts.append(f"Patient: {self._current_patient_id}")
        else:
            status_parts.append("No patient selected")
        
        # Información de imagen actual
        if self._current_image:
            modality = self._current_image.modality.value
            status_parts.append(f"Image: {modality}")
        
        # Workflows activos
        active_workflows = self._coordinator.get_active_workflows()
        if active_workflows:
            status_parts.append(f"Active workflows: {len(active_workflows)}")
        
        self.statusBar().showMessage(" | ".join(status_parts))
    
    def _show_user_message(self, title: str, message: str, message_type: str = "info") -> None:
        """
        Muestra mensaje al usuario de manera apropiada para aplicación médica.
        
        Centraliza el manejo de mensajes para consistencia y auditoría.
        """
        if message_type == "error":
            QMessageBox.critical(self, title, message)
        elif message_type == "warning":
            QMessageBox.warning(self, title, message)
        else:
            QMessageBox.information(self, title, message)
        
        # Log para auditoría médica
        self._logger.info(f"Mensaje mostrado al usuario: {title} - {message_type}")
    
    def _handle_low_quality_ai_results(self, data: Dict[str, Any]) -> None:
        """Maneja resultados de IA de baja calidad."""
        message = (
            "The AI analysis has produced results with lower confidence scores.\n\n"
            "Medical recommendation:\n"
            "• Review results carefully with clinical context\n"
            "• Consider manual verification of segmentations\n"
            "• Evaluate need for additional imaging\n\n"
            "Would you like to proceed with these results?"
        )
        
        # En aplicación real, esto podría abrir un diálogo especializado
        # para revisión médica detallada
        self._show_user_message("AI Quality Alert", message, "warning")
    
    def _handle_ambiguous_medical_findings(self, data: Dict[str, Any]) -> None:
        """Maneja hallazgos médicos ambiguos."""
        # Implementar manejo específico para hallazgos ambiguos
        self._show_user_message(
            "Medical Review Required",
            "Ambiguous findings detected. Medical review recommended.",
            "warning"
        )
    
    def _handle_generic_medical_validation(self, validation_type: str, data: Dict[str, Any]) -> None:
        """Maneja validaciones médicas genéricas."""
        self._show_user_message(
            "Medical Validation",
            f"Medical validation required: {validation_type}",
            "info"
        )
    
    def _show_development_info(self) -> None:
        """Muestra información de desarrollo para debugging."""
        # Información útil para desarrollo y debugging
        dev_info = f"""
        Development Information:
        
        Service Container: {type(self._services).__name__}
        Workflow Coordinator: {type(self._coordinator).__name__}
        UI Components: {type(self._ui_components).__name__}
        
        Current State: {self._application_state}
        Patient ID: {self._current_patient_id or 'None'}
        Current Image: {self._current_image.series_instance_uid if self._current_image else 'None'}
        
        Active Workflows: {len(self._coordinator.get_active_workflows())}
        Workflow History: {len(self._workflow_history)} events
        """
        
        QMessageBox.information(self, "Development View", dev_info.strip())
    
    def _hide_development_info(self) -> None:
        """Oculta información de desarrollo."""
        # Por ahora, solo log que se desactivó
        self._logger.debug("Vista de desarrollo desactivada")
    
    # Manejo de cierre de aplicación
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Maneja cierre de aplicación de manera segura para uso médico.
        
        En aplicaciones médicas, el cierre debe ser controlado para
        asegurar que todos los datos se guarden y auditorías se completen.
        """
        self._logger.info("Iniciando cierre de aplicación médica")
        
        # Verificar si hay workflows activos
        active_workflows = self._coordinator.get_active_workflows()
        if active_workflows:
            reply = QMessageBox.question(
                self,
                "Active Medical Workflows",
                f"There are {len(active_workflows)} active medical workflows.\n\n"
                "Closing now may interrupt medical processes.\n"
                "Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        # Emitir señal de cierre para cleanup coordinado
        self.application_closing.emit()
        
        # Shutdown ordenado de servicios (delegado al contenedor)
        try:
            self._services.shutdown()
            self._logger.info("Servicios médicos cerrados correctamente")
        except Exception as e:
            self._logger.error(f"Error durante cierre de servicios: {e}")
        
        # Aceptar cierre
        event.accept()
        self._logger.info("Aplicación médica cerrada exitosamente")