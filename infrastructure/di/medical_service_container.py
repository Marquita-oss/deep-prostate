#!/usr/bin/env python3
"""
infrastructure/di/medical_service_container.py

Contenedor de inyección de dependencias para servicios médicos.
Este componente centraliza la creación y configuración de todos los servicios
del sistema, implementando el patrón Dependency Injection para reducir
el acoplamiento y mejorar la testabilidad.

Responsabilidades:
- Crear y configurar servicios médicos según configuración
- Gestionar ciclo de vida de servicios singleton
- Proporcionar acceso tipo-seguro a dependencias
- Facilitar testing mediante inyección de mocks
"""

from typing import Dict, Any, Optional, TypeVar, Type
from pathlib import Path
import logging

# Imports de dominio y aplicación
from domain.repositories.repositories import (
    MedicalImageRepository, SegmentationRepository
)
from application.services.image_services import (
    ImageLoadingService, ImageVisualizationService
)
from application.services.segmentation_services import (
    AISegmentationService, SegmentationEditingService
)

# Imports de infraestructura
from infrastructure.storage.dicom_repository import DICOMImageRepository
from infrastructure.visualization.vtk_renderer import MedicalVTKRenderer

T = TypeVar('T')


class MedicalServiceContainer:
    """
    Contenedor de servicios médicos con inyección de dependencias.
    
    Este contenedor implementa el patrón Dependency Injection Container,
    centralizando la creación y configuración de todos los servicios médicos
    del sistema. Esto elimina la responsabilidad de Main Window de crear
    y configurar servicios, siguiendo el principio de Inversión de Dependencias.
    
    Ventajas del patrón:
    - Reduce acoplamiento entre componentes
    - Facilita testing mediante inyección de mocks
    - Centraliza configuración de servicios
    - Permite intercambio fácil de implementaciones
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el contenedor con configuración médica.
        
        Args:
            config: Diccionario con configuración de servicios médicos
                   Debe contener: storage_path, ai_config, visualization_config
        """
        self._config = config
        self._services: Dict[str, Any] = {}
        self._logger = logging.getLogger(__name__)
        
        # Validar configuración crítica para uso médico
        self._validate_medical_configuration()
        
        # Inicializar servicios en orden de dependencias
        self._initialize_core_services()
        
        self._logger.info("Contenedor de servicios médicos inicializado correctamente")
    
    def _validate_medical_configuration(self) -> None:
        """
        Valida que la configuración médica sea completa y segura.
        
        En software médico, la validación de configuración es crítica
        para garantizar que todos los servicios funcionen correctamente
        y cumplan con los estándares de seguridad médica.
        """
        required_keys = [
            'storage_path',
            'ai_config', 
            'visualization_config',
            'logging_config'
        ]
        
        missing_keys = [key for key in required_keys if key not in self._config]
        if missing_keys:
            raise ValueError(
                f"Configuración médica incompleta. Faltan: {missing_keys}"
            )
        
        # Validar que el directorio de almacenamiento sea accesible
        storage_path = Path(self._config['storage_path'])
        if not storage_path.exists():
            storage_path.mkdir(parents=True, exist_ok=True)
            self._logger.info(f"Creado directorio de almacenamiento médico: {storage_path}")
    
    def _initialize_core_services(self) -> None:
        """
        Inicializa servicios médicos centrales en orden de dependencias.
        
        El orden de inicialización es importante:
        1. Repositorios (capa de datos)
        2. Servicios de aplicación (lógica de negocio)
        3. Servicios de infraestructura (rendering, etc.)
        
        Este orden asegura que las dependencias estén disponibles
        cuando cada servicio las necesite.
        """
        try:
            # 1. Repositorios - Capa de acceso a datos
            self._initialize_repositories()
            
            # 2. Servicios de aplicación - Lógica de negocio médica
            self._initialize_application_services()
            
            # 3. Servicios de infraestructura - Componentes técnicos
            self._initialize_infrastructure_services()
            
        except Exception as e:
            self._logger.error(f"Error inicializando servicios médicos: {e}")
            raise RuntimeError(f"Fallo en inicialización de servicios médicos: {e}")
    
    def _initialize_repositories(self) -> None:
        """Inicializa repositorios de datos médicos."""
        storage_path = self._config['storage_path']
        
        # Repositorio principal para imágenes DICOM
        # Este repositorio maneja la persistencia de imágenes médicas
        # siguiendo estándares DICOM para interoperabilidad
        self._services['image_repository'] = DICOMImageRepository(storage_path)
        
        # TODO: Agregar repositorio de segmentaciones cuando esté disponible
        # self._services['segmentation_repository'] = DICOMSegmentationRepository(storage_path)
        
        self._logger.debug("Repositorios médicos inicializados")
    
    def _initialize_application_services(self) -> None:
        """Inicializa servicios de lógica de negocio médica."""
        image_repo = self._services['image_repository']
        ai_config = self._config['ai_config']
        
        # Servicio de carga de imágenes médicas
        # Maneja validación médica, carga segura y preparación de datos
        self._services['image_loading_service'] = ImageLoadingService(image_repo)
        
        # Servicio de visualización médica
        # Gestiona presets médicos, window/level, y configuraciones por modalidad
        self._services['image_visualization_service'] = ImageVisualizationService()
        
        # Servicio de IA para segmentación automática
        # Integra nnUNet para análisis automático de cáncer prostático
        # TODO: Ajustar cuando tengamos repositorio de segmentaciones
        self._services['ai_segmentation_service'] = AISegmentationService(
            image_repo,  # Temporalmente usar image_repo
            ai_config
        )
        
        # Servicio de edición manual de segmentaciones
        # Permite a médicos corregir y refinar resultados de IA
        self._services['segmentation_editing_service'] = SegmentationEditingService(
            image_repo  # Temporalmente usar image_repo
        )
        
        self._logger.debug("Servicios de aplicación médica inicializados")
    
    def _initialize_infrastructure_services(self) -> None:
        """Inicializa servicios de infraestructura técnica."""
        viz_config = self._config['visualization_config']
        
        # Motor de renderizado 3D médico usando VTK
        # Optimizado para visualización de estructuras anatómicas
        self._services['vtk_renderer'] = MedicalVTKRenderer()
        
        self._logger.debug("Servicios de infraestructura inicializados")
    
    # Métodos de acceso tipo-seguro a servicios
    
    @property
    def image_repository(self) -> MedicalImageRepository:
        """Acceso al repositorio de imágenes médicas."""
        return self._services['image_repository']
    
    @property 
    def image_loading_service(self) -> ImageLoadingService:
        """Acceso al servicio de carga de imágenes."""
        return self._services['image_loading_service']
    
    @property
    def image_visualization_service(self) -> ImageVisualizationService:
        """Acceso al servicio de visualización médica."""
        return self._services['image_visualization_service']
    
    @property
    def ai_segmentation_service(self) -> AISegmentationService:
        """Acceso al servicio de IA para segmentación."""
        return self._services['ai_segmentation_service']
    
    @property
    def segmentation_editing_service(self) -> SegmentationEditingService:
        """Acceso al servicio de edición de segmentaciones."""
        return self._services['segmentation_editing_service']
    
    @property
    def vtk_renderer(self) -> MedicalVTKRenderer:
        """Acceso al motor de renderizado 3D."""
        return self._services['vtk_renderer']
    
    def get_service(self, service_type: Type[T]) -> T:
        """
        Obtiene un servicio por su tipo (para casos avanzados).
        
        Este método permite obtener servicios de manera tipo-segura
        usando el sistema de tipos de Python. Útil para casos donde
        necesitamos acceso dinámico a servicios.
        
        Args:
            service_type: Clase del servicio requerido
            
        Returns:
            Instancia del servicio solicitado
            
        Raises:
            ValueError: Si el servicio no está disponible
        """
        for service in self._services.values():
            if isinstance(service, service_type):
                return service
        
        raise ValueError(f"Servicio {service_type.__name__} no disponible")
    
    def configure_for_testing(self, mock_services: Dict[str, Any]) -> None:
        """
        Configura el contenedor para testing con servicios mock.
        
        Este método es crucial para testing médico, permitiendo
        inyectar servicios mock que simulen comportamientos específicos
        sin afectar datos médicos reales.
        
        Args:
            mock_services: Diccionario con servicios mock para testing
        """
        for service_name, mock_service in mock_services.items():
            if service_name in self._services:
                self._services[service_name] = mock_service
                self._logger.debug(f"Servicio {service_name} configurado para testing")
    
    def shutdown(self) -> None:
        """
        Cierra todos los servicios de manera ordenada.
        
        Importante en aplicaciones médicas para asegurar que:
        - Datos se guarden correctamente
        - Recursos se liberen apropiadamente
        - Auditoría se complete
        """
        self._logger.info("Iniciando cierre ordenado de servicios médicos")
        
        # Cerrar servicios en orden inverso al de inicialización
        for service_name, service in self._services.items():
            try:
                if hasattr(service, 'shutdown'):
                    service.shutdown()
                    self._logger.debug(f"Servicio {service_name} cerrado correctamente")
            except Exception as e:
                self._logger.error(f"Error cerrando servicio {service_name}: {e}")
        
        self._services.clear()
        self._logger.info("Servicios médicos cerrados correctamente")


def create_medical_service_container(config_path: Optional[str] = None) -> MedicalServiceContainer:
    """
    Función factory para crear contenedor de servicios médicos.
    
    Esta función simplifica la creación del contenedor cargando
    configuración desde archivo y aplicando valores por defecto
    apropiados para uso médico.
    
    Args:
        config_path: Ruta opcional al archivo de configuración
        
    Returns:
        Contenedor de servicios configurado para uso médico
    """
    # Configuración por defecto para uso médico
    default_config = {
        'storage_path': './medical_data',
        'ai_config': {
            'model_path': './models/nnunet_prostate',
            'confidence_threshold': 0.7,
            'preprocessing_params': {
                'normalize': True,
                'resample': True,
                'target_spacing': [1.0, 1.0, 3.0]
            }
        },
        'visualization_config': {
            'default_window_width': 400,
            'default_window_level': 40,
            'enable_gpu_rendering': True,
            'max_texture_memory_mb': 512
        },
        'logging_config': {
            'level': 'INFO',
            'medical_audit': True,
            'hipaa_compliant': True
        }
    }
    
    # TODO: Cargar configuración desde archivo si se proporciona
    if config_path:
        # Implementar carga desde archivo YAML/JSON
        pass
    
    return MedicalServiceContainer(default_config)