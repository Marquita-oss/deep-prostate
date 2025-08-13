#!/usr/bin/env python3
"""
infrastructure/coordination/workflow_coordinator.py

Coordinador de flujos de trabajo médicos complejos.
Este componente orquesta secuencias de operaciones médicas que involucran
múltiples servicios, asegurando que cada paso se ejecute en el orden correcto
con las validaciones médicas apropiadas.

Responsabilidades:
- Orquestar flujos de trabajo médicos complejos
- Coordinar comunicación entre servicios especializados
- Gestionar estado y progreso de operaciones de larga duración
- Implementar validaciones médicas en cada paso crítico
- Proporcionar feedback detallado al usuario médico
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Callable
from enum import Enum
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
from PyQt6.QtWidgets import QMessageBox

# Imports del dominio médico
from domain.entities.medical_image import MedicalImage, ImageModalityType
from domain.entities.segmentation import MedicalSegmentation, SegmentationType

# Imports de servicios de aplicación
from application.services.image_services import ImageLoadingService
from application.services.segmentation_services import AISegmentationService

# Import del contenedor de servicios
from infrastructure.di.medical_service_container import MedicalServiceContainer


class WorkflowState(Enum):
    """Estados posibles de los flujos de trabajo médicos."""
    IDLE = "idle"
    LOADING_IMAGE = "loading_image"
    VALIDATING_IMAGE = "validating_image"
    PREPARING_AI_ANALYSIS = "preparing_ai_analysis"
    RUNNING_AI_ANALYSIS = "running_ai_analysis"
    VALIDATING_AI_RESULTS = "validating_ai_results"
    PRESENTING_RESULTS = "presenting_results"
    ERROR = "error"
    COMPLETED = "completed"


class WorkflowEvent:
    """Representa un evento en el flujo de trabajo médico."""
    
    def __init__(self, event_type: str, data: Dict[str, Any], timestamp: Optional[datetime] = None):
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.now()
        self.workflow_id = data.get('workflow_id', 'unknown')


class MedicalWorkflowCoordinator(QObject):
    """
    Coordinador principal de flujos de trabajo médicos.
    
    Este coordinador implementa el patrón Orchestrator, encargándose de dirigir
    secuencias complejas de operaciones médicas. Piensa en él como el coordinador
    de cuidados del paciente en un hospital: se asegura de que cada paso del 
    proceso se ejecute correctamente, en el orden apropiado, y con todas las
    validaciones médicas necesarias.
    
    Ventajas de este patrón:
    - Centraliza la lógica de coordinación compleja
    - Separa orquestación de implementación de servicios individuales
    - Facilita auditoría médica del flujo completo
    - Permite manejo sofisticado de errores y recuperación
    - Simplifica testing de flujos de trabajo complejos
    """
    
    # Señales para comunicar progreso y eventos a la UI
    workflow_started = pyqtSignal(str, str)  # workflow_type, workflow_id
    workflow_progress = pyqtSignal(str, int, str)  # workflow_id, progress_percent, message
    workflow_completed = pyqtSignal(str, dict)  # workflow_id, results
    workflow_error = pyqtSignal(str, str)  # workflow_id, error_message
    
    # Señales específicas para eventos médicos importantes
    image_loaded = pyqtSignal(object)  # MedicalImage
    ai_analysis_completed = pyqtSignal(list)  # List[MedicalSegmentation]
    medical_validation_required = pyqtSignal(str, dict)  # validation_type, data
    
    def __init__(self, service_container: MedicalServiceContainer):
        """
        Inicializa el coordinador con acceso a servicios médicos.
        
        Args:
            service_container: Contenedor con todos los servicios médicos configurados
        """
        super().__init__()
        
        self._services = service_container
        self._logger = logging.getLogger(__name__)
        
        # Estado del coordinador
        self._current_state = WorkflowState.IDLE
        self._active_workflows: Dict[str, Dict[str, Any]] = {}
        self._workflow_counter = 0
        
        # Configuración de timeouts médicos (crítico para seguridad)
        self._ai_analysis_timeout_minutes = 15  # Timeout para análisis de IA
        self._image_loading_timeout_minutes = 5   # Timeout para carga de imágenes
        
        self._logger.info("Coordinador de flujos de trabajo médicos inicializado")
    
    def start_image_loading_workflow(self, file_path: Optional[str] = None) -> str:
        """
        Inicia el flujo de trabajo completo para cargar una imagen médica.
        
        Este flujo incluye:
        1. Selección de archivo (si no se proporciona path)
        2. Validación de formato DICOM
        3. Carga y parsing de metadatos médicos
        4. Validación de integridad de imagen
        5. Preparación para visualización
        6. Notificación de imagen lista para análisis
        
        Args:
            file_path: Ruta opcional al archivo DICOM a cargar
            
        Returns:
            ID único del flujo de trabajo iniciado
            
        Note:
            En aplicaciones médicas, la carga de imágenes requiere validaciones
            estrictas para garantizar que los datos sean válidos para diagnóstico.
        """
        workflow_id = self._generate_workflow_id("image_loading")
        
        self._logger.info(f"Iniciando flujo de carga de imagen médica: {workflow_id}")
        
        # Registrar nuevo flujo de trabajo
        self._active_workflows[workflow_id] = {
            'type': 'image_loading',
            'state': WorkflowState.LOADING_IMAGE,
            'start_time': datetime.now(),
            'file_path': file_path,
            'progress': 0
        }
        
        # Emitir señal de inicio
        self.workflow_started.emit("image_loading", workflow_id)
        
        # Ejecutar flujo de manera asíncrona para no bloquear UI
        QTimer.singleShot(0, lambda: self._execute_image_loading_workflow(workflow_id))
        
        return workflow_id
    
    def start_ai_analysis_workflow(self, image: MedicalImage, analysis_type: str = "full") -> str:
        """
        Inicia el flujo de trabajo completo para análisis de IA médica.
        
        Este flujo incluye:
        1. Validación de prerrequisitos (imagen válida, modalidad soportada)
        2. Preparación de datos para análisis de IA
        3. Ejecución de modelos de IA (nnUNet)
        4. Validación médica de resultados
        5. Conversión a entidades del dominio
        6. Presentación de resultados al médico
        
        Args:
            image: Imagen médica a analizar
            analysis_type: Tipo de análisis ("full", "prostate_only", "lesions_only")
            
        Returns:
            ID único del flujo de trabajo iniciado
            
        Note:
            El análisis de IA en aplicaciones médicas requiere validaciones
            especiales para asegurar que los resultados sean clínicamente útiles.
        """
        workflow_id = self._generate_workflow_id("ai_analysis")
        
        self._logger.info(f"Iniciando flujo de análisis de IA médica: {workflow_id}")
        
        # Validación previa crítica para aplicaciones médicas
        if not self._validate_image_for_ai_analysis(image):
            error_msg = "Imagen no válida para análisis de IA médica"
            self._logger.error(f"{workflow_id}: {error_msg}")
            self.workflow_error.emit(workflow_id, error_msg)
            return workflow_id
        
        # Registrar nuevo flujo de trabajo
        self._active_workflows[workflow_id] = {
            'type': 'ai_analysis',
            'state': WorkflowState.PREPARING_AI_ANALYSIS,
            'start_time': datetime.now(),
            'image': image,
            'analysis_type': analysis_type,
            'progress': 0
        }
        
        # Emitir señal de inicio
        self.workflow_started.emit("ai_analysis", workflow_id)
        
        # Ejecutar flujo de manera asíncrona
        QTimer.singleShot(0, lambda: self._execute_ai_analysis_workflow(workflow_id))
        
        return workflow_id
    
    def _execute_image_loading_workflow(self, workflow_id: str) -> None:
        """
        Ejecuta el flujo completo de carga de imagen médica.
        
        Este método implementa la orquestación paso a paso del proceso de carga,
        asegurando que cada validación médica se complete antes de proceder
        al siguiente paso.
        """
        try:
            workflow = self._active_workflows[workflow_id]
            
            # Paso 1: Seleccionar archivo si no se proporcionó
            self._update_workflow_progress(workflow_id, 10, "Seleccionando archivo DICOM...")
            file_path = workflow['file_path']
            if not file_path:
                file_path = self._prompt_for_dicom_file()
                if not file_path:
                    self._complete_workflow_with_error(workflow_id, "Selección de archivo cancelada")
                    return
            
            # Paso 2: Validar formato DICOM
            self._update_workflow_progress(workflow_id, 25, "Validando formato DICOM...")
            if not self._validate_dicom_format(file_path):
                self._complete_workflow_with_error(workflow_id, "Archivo no es un DICOM válido")
                return
            
            # Paso 3: Cargar imagen usando servicio especializado
            self._update_workflow_progress(workflow_id, 50, "Cargando imagen médica...")
            image_loading_service = self._services.image_loading_service
            
            # Simular carga asíncrona (en implementación real, usar async/await)
            QTimer.singleShot(1000, lambda: self._complete_image_loading(workflow_id, file_path))
            
        except Exception as e:
            self._complete_workflow_with_error(workflow_id, f"Error durante carga: {str(e)}")
    
    def _complete_image_loading(self, workflow_id: str, file_path: str) -> None:
        """Completa el proceso de carga de imagen médica."""
        try:
            # Paso 4: Validar integridad médica
            self._update_workflow_progress(workflow_id, 75, "Validando integridad médica...")
            
            # TODO: Integrar con servicio real de carga
            # Por ahora, simular carga exitosa
            # image = await image_loading_service.load_image_from_file(file_path)
            
            # Paso 5: Preparar para visualización
            self._update_workflow_progress(workflow_id, 90, "Preparando visualización...")
            
            # Simular imagen cargada exitosamente
            # En implementación real, esta sería la imagen real cargada
            mock_image = self._create_mock_loaded_image(file_path)
            
            # Paso 6: Completar flujo exitosamente
            self._update_workflow_progress(workflow_id, 100, "Imagen cargada exitosamente")
            
            results = {
                'image': mock_image,
                'file_path': file_path,
                'load_time': datetime.now()
            }
            
            self._complete_workflow_successfully(workflow_id, results)
            
            # Emitir señal específica para imagen cargada
            self.image_loaded.emit(mock_image)
            
        except Exception as e:
            self._complete_workflow_with_error(workflow_id, f"Error completando carga: {str(e)}")
    
    def _execute_ai_analysis_workflow(self, workflow_id: str) -> None:
        """
        Ejecuta el flujo completo de análisis de IA médica.
        
        Este flujo es particularmente crítico en aplicaciones médicas porque
        los resultados de IA pueden influir en decisiones diagnósticas.
        Cada paso incluye validaciones médicas específicas.
        """
        try:
            workflow = self._active_workflows[workflow_id]
            image = workflow['image']
            analysis_type = workflow['analysis_type']
            
            # Paso 1: Preparar datos para IA
            self._update_workflow_progress(workflow_id, 15, "Preparando datos para análisis de IA...")
            
            # Paso 2: Validar prerrequisitos de IA
            self._update_workflow_progress(workflow_id, 25, "Validando prerrequisitos médicos...")
            if not self._validate_ai_prerequisites(image, analysis_type):
                self._complete_workflow_with_error(workflow_id, "Prerrequisitos de IA no cumplidos")
                return
            
            # Paso 3: Ejecutar análisis de IA
            self._update_workflow_progress(workflow_id, 40, "Ejecutando modelos de IA médica...")
            
            # Simular análisis de IA de larga duración
            QTimer.singleShot(3000, lambda: self._complete_ai_analysis(workflow_id))
            
        except Exception as e:
            self._complete_workflow_with_error(workflow_id, f"Error durante análisis de IA: {str(e)}")
    
    def _complete_ai_analysis(self, workflow_id: str) -> None:
        """Completa el proceso de análisis de IA médica."""
        try:
            workflow = self._active_workflows[workflow_id]
            
            # Paso 4: Validar resultados de IA
            self._update_workflow_progress(workflow_id, 70, "Validando resultados de IA...")
            
            # TODO: Integrar con servicio real de IA
            # Por ahora, simular resultados de IA
            mock_segmentations = self._create_mock_ai_results(workflow['image'])
            
            # Paso 5: Validación médica de calidad
            self._update_workflow_progress(workflow_id, 85, "Validación médica de resultados...")
            if not self._validate_ai_results_quality(mock_segmentations):
                # En caso de baja calidad, alertar al médico
                self.medical_validation_required.emit("low_quality_ai_results", {
                    'workflow_id': workflow_id,
                    'segmentations': mock_segmentations
                })
            
            # Paso 6: Preparar presentación de resultados
            self._update_workflow_progress(workflow_id, 95, "Preparando presentación médica...")
            
            # Paso 7: Completar flujo exitosamente
            self._update_workflow_progress(workflow_id, 100, "Análisis de IA completado")
            
            results = {
                'segmentations': mock_segmentations,
                'analysis_type': workflow['analysis_type'],
                'completion_time': datetime.now(),
                'quality_score': self._calculate_quality_score(mock_segmentations)
            }
            
            self._complete_workflow_successfully(workflow_id, results)
            
            # Emitir señal específica para análisis completado
            self.ai_analysis_completed.emit(mock_segmentations)
            
        except Exception as e:
            self._complete_workflow_with_error(workflow_id, f"Error completando análisis de IA: {str(e)}")
    
    # Métodos de utilidad para gestión de flujos de trabajo
    
    def _generate_workflow_id(self, workflow_type: str) -> str:
        """Genera un ID único para el flujo de trabajo."""
        self._workflow_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{workflow_type}_{timestamp}_{self._workflow_counter:03d}"
    
    def _update_workflow_progress(self, workflow_id: str, progress: int, message: str) -> None:
        """Actualiza el progreso de un flujo de trabajo."""
        if workflow_id in self._active_workflows:
            self._active_workflows[workflow_id]['progress'] = progress
            self.workflow_progress.emit(workflow_id, progress, message)
            self._logger.debug(f"{workflow_id}: {progress}% - {message}")
    
    def _complete_workflow_successfully(self, workflow_id: str, results: Dict[str, Any]) -> None:
        """Marca un flujo de trabajo como completado exitosamente."""
        if workflow_id in self._active_workflows:
            self._active_workflows[workflow_id]['state'] = WorkflowState.COMPLETED
            self._active_workflows[workflow_id]['results'] = results
            self.workflow_completed.emit(workflow_id, results)
            self._logger.info(f"Flujo de trabajo {workflow_id} completado exitosamente")
    
    def _complete_workflow_with_error(self, workflow_id: str, error_message: str) -> None:
        """Marca un flujo de trabajo como completado con error."""
        if workflow_id in self._active_workflows:
            self._active_workflows[workflow_id]['state'] = WorkflowState.ERROR
            self._active_workflows[workflow_id]['error'] = error_message
            self.workflow_error.emit(workflow_id, error_message)
            self._logger.error(f"Flujo de trabajo {workflow_id} falló: {error_message}")
    
    # Métodos de validación médica específicos
    
    def _validate_image_for_ai_analysis(self, image: MedicalImage) -> bool:
        """
        Valida que una imagen sea apropiada para análisis de IA médica.
        
        En aplicaciones médicas reales, esto incluiría validaciones como:
        - Modalidad soportada por el modelo de IA
        - Calidad de imagen suficiente
        - Metadatos DICOM completos
        - Orientación y espaciado apropiados
        """
        if not image:
            return False
        
        # Validar modalidad soportada
        supported_modalities = [ImageModalityType.MRI, ImageModalityType.CT]
        if image.modality not in supported_modalities:
            self._logger.warning(f"Modalidad {image.modality} no soportada para IA")
            return False
        
        # Validar dimensiones mínimas
        if any(dim < 32 for dim in image.dimensions):
            self._logger.warning("Dimensiones de imagen demasiado pequeñas para IA")
            return False
        
        return True
    
    def _validate_ai_prerequisites(self, image: MedicalImage, analysis_type: str) -> bool:
        """Valida prerrequisitos específicos para el tipo de análisis de IA."""
        # Implementar validaciones específicas por tipo de análisis
        if analysis_type == "prostate_analysis" and image.modality != ImageModalityType.MRI:
            return False
        
        return True
    
    def _validate_ai_results_quality(self, segmentations: List[MedicalSegmentation]) -> bool:
        """
        Valida la calidad de los resultados de IA desde una perspectiva médica.
        
        En aplicaciones médicas reales, esto incluiría:
        - Verificar que las segmentaciones tengan sentido anatómico
        - Validar que los niveles de confianza estén dentro de rangos aceptables
        - Comprobar consistencia entre diferentes estructuras segmentadas
        """
        if not segmentations:
            return False
        
        # Validar que todas las segmentaciones tengan confianza mínima
        min_confidence = 0.7
        for seg in segmentations:
            if seg.confidence_score and seg.confidence_score < min_confidence:
                return False
        
        return True
    
    def _calculate_quality_score(self, segmentations: List[MedicalSegmentation]) -> float:
        """Calcula un score de calidad general para los resultados de IA."""
        if not segmentations:
            return 0.0
        
        scores = [seg.confidence_score for seg in segmentations if seg.confidence_score]
        return sum(scores) / len(scores) if scores else 0.0
    
    # Métodos de utilidad para simulación (en implementación real, remover)
    
    def _prompt_for_dicom_file(self) -> Optional[str]:
        """Simula selección de archivo DICOM."""
        # En implementación real, usar QFileDialog
        return "/path/to/sample_dicom.dcm"
    
    def _validate_dicom_format(self, file_path: str) -> bool:
        """Simula validación de formato DICOM."""
        return file_path.endswith(('.dcm', '.dicom'))
    
    def _create_mock_loaded_image(self, file_path: str) -> MedicalImage:
        """Crea una imagen mock para simulación."""
        # En implementación real, esto vendría del servicio de carga
        import numpy as np
        from ...domain.entities.medical_image import ImageSpacing
        
        mock_data = np.random.randint(0, 1000, (64, 64, 32), dtype=np.int16)
        return MedicalImage(
            image_data=mock_data,
            spacing=ImageSpacing(1.0, 1.0, 3.0),
            modality=ImageModalityType.MRI,
            patient_id="DEMO_PATIENT",
            study_instance_uid="1.2.3.4.5",
            series_instance_uid="1.2.3.4.5.6",
            acquisition_date=datetime.now()
        )
    
    def _create_mock_ai_results(self, image: MedicalImage) -> List[MedicalSegmentation]:
        """Crea resultados mock de IA para simulación."""
        # En implementación real, esto vendría del servicio de IA
        from ...domain.entities.segmentation import AnatomicalRegion
        
        mock_segmentations = []
        # Simular segmentación de próstata
        # En implementación real, estas serían las masks reales del modelo de IA
        
        return mock_segmentations
    
    def get_active_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Retorna información sobre flujos de trabajo activos."""
        return self._active_workflows.copy()
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancela un flujo de trabajo activo."""
        if workflow_id in self._active_workflows:
            self._complete_workflow_with_error(workflow_id, "Cancelado por usuario")
            return True
        return False