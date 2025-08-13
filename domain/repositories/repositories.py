"""
domain/repositories/repositories.py

Interfaces abstractas que definen cómo el dominio interactúa con el almacenamiento.
Estas interfaces permiten que la lógica de negocio sea independiente de la 
implementación específica de almacenamiento (archivos, base de datos, etc.).

Siguiendo el principio de inversión de dependencias de SOLID.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.medical_image import MedicalImage
from ..entities.segmentation import MedicalSegmentation


class MedicalImageRepository(ABC):
    """
    Interfaz abstracta para el repositorio de imágenes médicas.
    
    Define todas las operaciones de persistencia necesarias para imágenes
    sin especificar cómo se implementan. Esto permite cambiar entre diferentes
    sistemas de almacenamiento sin afectar la lógica de negocio.
    """
    
    @abstractmethod
    async def save_image(self, image: MedicalImage) -> bool:
        """
        Persiste una imagen médica en el sistema de almacenamiento.
        
        Args:
            image: Imagen médica a guardar
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
            
        Raises:
            RepositoryError: Si ocurre un error durante el guardado
        """
        pass
    
    @abstractmethod
    async def find_by_study_uid(self, study_uid: str) -> List[MedicalImage]:
        """
        Busca todas las imágenes pertenecientes a un estudio específico.
        
        Args:
            study_uid: Identificador único del estudio DICOM
            
        Returns:
            Lista de imágenes médicas del estudio
        """
        pass
    
    @abstractmethod
    async def find_by_series_uid(self, series_uid: str) -> Optional[MedicalImage]:
        """
        Busca una imagen específica por su serie DICOM.
        
        Args:
            series_uid: Identificador único de la serie DICOM
            
        Returns:
            Imagen médica si existe, None en caso contrario
        """
        pass
    
    @abstractmethod
    async def find_by_patient_id(self, patient_id: str) -> List[MedicalImage]:
        """
        Busca todas las imágenes de un paciente específico.
        
        Args:
            patient_id: Identificador del paciente
            
        Returns:
            Lista de imágenes médicas del paciente
        """
        pass
    
    @abstractmethod
    async def find_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[MedicalImage]:
        """
        Busca imágenes dentro de un rango de fechas de adquisición.
        
        Args:
            start_date: Fecha de inicio del rango
            end_date: Fecha de fin del rango
            
        Returns:
            Lista de imágenes en el rango especificado
        """
        pass
    
    @abstractmethod
    async def delete_image(self, series_uid: str) -> bool:
        """
        Elimina una imagen del sistema de almacenamiento.
        
        Args:
            series_uid: Identificador de la serie a eliminar
            
        Returns:
            True si se eliminó exitosamente, False en caso contrario
        """
        pass
    
    @abstractmethod
    async def update_image_metadata(
        self, 
        series_uid: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Actualiza los metadatos de una imagen existente.
        
        Args:
            series_uid: Identificador de la serie
            metadata: Nuevos metadatos a actualizar
            
        Returns:
            True si se actualizó exitosamente, False en caso contrario
        """
        pass
    
    @abstractmethod
    async def exists_image(self, series_uid: str) -> bool:
        """
        Verifica si una imagen existe en el repositorio.
        
        Args:
            series_uid: Identificador de la serie
            
        Returns:
            True si la imagen existe, False en caso contrario
        """
        pass


class SegmentationRepository(ABC):
    """
    Interfaz abstracta para el repositorio de segmentaciones médicas.
    
    Maneja la persistencia de máscaras de segmentación y sus metadatos
    asociados, incluyendo métricas calculadas y historiales de modificación.
    """
    
    @abstractmethod
    async def save_segmentation(self, segmentation: MedicalSegmentation) -> bool:
        """
        Persiste una segmentación médica en el sistema de almacenamiento.
        
        Args:
            segmentation: Segmentación a guardar
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        pass
    
    @abstractmethod
    async def find_by_image_uid(self, image_uid: str) -> List[MedicalSegmentation]:
        """
        Busca todas las segmentaciones asociadas a una imagen específica.
        
        Args:
            image_uid: Identificador de la imagen padre
            
        Returns:
            Lista de segmentaciones de la imagen
        """
        pass
    
    @abstractmethod
    async def find_by_segmentation_id(self, segmentation_id: str) -> Optional[MedicalSegmentation]:
        """
        Busca una segmentación específica por su ID único.
        
        Args:
            segmentation_id: Identificador único de la segmentación
            
        Returns:
            Segmentación si existe, None en caso contrario
        """
        pass
    
    @abstractmethod
    async def find_by_anatomical_region(
        self, 
        region: 'AnatomicalRegion',
        image_uid: Optional[str] = None
    ) -> List[MedicalSegmentation]:
        """
        Busca segmentaciones por región anatómica.
        
        Args:
            region: Región anatómica a buscar
            image_uid: Filtrar por imagen específica (opcional)
            
        Returns:
            Lista de segmentaciones de la región especificada
        """
        pass
    
    @abstractmethod
    async def find_by_creator(self, creator_id: str) -> List[MedicalSegmentation]:
        """
        Busca todas las segmentaciones creadas por un usuario específico.
        
        Args:
            creator_id: Identificador del creador
            
        Returns:
            Lista de segmentaciones del creador
        """
        pass
    
    @abstractmethod
    async def find_automatic_segmentations(
        self, 
        confidence_threshold: float = 0.5
    ) -> List[MedicalSegmentation]:
        """
        Busca segmentaciones automáticas con confianza superior al umbral.
        
        Args:
            confidence_threshold: Umbral mínimo de confianza
            
        Returns:
            Lista de segmentaciones automáticas de alta confianza
        """
        pass
    
    @abstractmethod
    async def update_segmentation(self, segmentation: MedicalSegmentation) -> bool:
        """
        Actualiza una segmentación existente en el repositorio.
        
        Args:
            segmentation: Segmentación con cambios a guardar
            
        Returns:
            True si se actualizó exitosamente, False en caso contrario
        """
        pass
    
    @abstractmethod
    async def delete_segmentation(self, segmentation_id: str) -> bool:
        """
        Elimina una segmentación del sistema de almacenamiento.
        
        Args:
            segmentation_id: Identificador de la segmentación
            
        Returns:
            True si se eliminó exitosamente, False en caso contrario
        """
        pass
    
    @abstractmethod
    async def save_segmentation_metrics(
        self, 
        segmentation_id: str, 
        metrics: 'SegmentationMetrics'
    ) -> bool:
        """
        Guarda las métricas calculadas de una segmentación por separado.
        
        Args:
            segmentation_id: ID de la segmentación
            metrics: Métricas calculadas a guardar
            
        Returns:
            True si se guardaron exitosamente, False en caso contrario
        """
        pass
    
    @abstractmethod
    async def get_segmentation_history(
        self, 
        segmentation_id: str
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de modificaciones de una segmentación.
        
        Args:
            segmentation_id: ID de la segmentación
            
        Returns:
            Lista de eventos del historial de la segmentación
        """
        pass


class ProjectRepository(ABC):
    """
    Interfaz abstracta para el repositorio de proyectos médicos.
    
    Un proyecto agrupa imágenes y segmentaciones relacionadas, típicamente
    correspondientes a un estudio clínico o caso diagnóstico específico.
    """
    
    @abstractmethod
    async def create_project(
        self, 
        name: str, 
        description: str,
        creator_id: str
    ) -> str:
        """
        Crea un nuevo proyecto médico.
        
        Args:
            name: Nombre del proyecto
            description: Descripción del proyecto
            creator_id: ID del usuario creador
            
        Returns:
            ID único del proyecto creado
        """
        pass
    
    @abstractmethod
    async def add_image_to_project(self, project_id: str, image_uid: str) -> bool:
        """
        Asocia una imagen médica a un proyecto.
        
        Args:
            project_id: ID del proyecto
            image_uid: UID de la imagen a agregar
            
        Returns:
            True si se agregó exitosamente, False en caso contrario
        """
        pass
    
    @abstractmethod
    async def get_project_images(self, project_id: str) -> List[str]:
        """
        Obtiene todas las imágenes asociadas a un proyecto.
        
        Args:
            project_id: ID del proyecto
            
        Returns:
            Lista de UIDs de imágenes del proyecto
        """
        pass
    
    @abstractmethod
    async def get_project_segmentations(self, project_id: str) -> List[str]:
        """
        Obtiene todas las segmentaciones asociadas a un proyecto.
        
        Args:
            project_id: ID del proyecto
            
        Returns:
            Lista de IDs de segmentaciones del proyecto
        """
        pass
    
    @abstractmethod
    async def delete_project(self, project_id: str) -> bool:
        """
        Elimina un proyecto y todas sus asociaciones.
        
        Args:
            project_id: ID del proyecto a eliminar
            
        Returns:
            True si se eliminó exitosamente, False en caso contrario
        """
        pass
    
    @abstractmethod
    async def get_user_projects(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los proyectos de un usuario específico.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de diccionarios con información de proyectos
        """
        pass


class ConfigurationRepository(ABC):
    """
    Interfaz abstracta para el repositorio de configuraciones del sistema.
    
    Maneja persistencia de configuraciones de usuario, preferencias de
    visualización, configuraciones de IA y parámetros del sistema.
    """
    
    @abstractmethod
    async def save_user_preferences(
        self, 
        user_id: str, 
        preferences: Dict[str, Any]
    ) -> bool:
        """
        Guarda las preferencias específicas de un usuario.
        
        Args:
            user_id: ID del usuario
            preferences: Diccionario con preferencias del usuario
            
        Returns:
            True si se guardaron exitosamente, False en caso contrario
        """
        pass
    
    @abstractmethod
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene las preferencias de un usuario específico.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Diccionario con preferencias del usuario
        """
        pass
    
    @abstractmethod
    async def save_ai_model_config(
        self, 
        model_name: str, 
        config: Dict[str, Any]
    ) -> bool:
        """
        Guarda la configuración de un modelo de IA.
        
        Args:
            model_name: Nombre identificador del modelo
            config: Configuración del modelo
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        pass
    
    @abstractmethod
    async def get_ai_model_config(self, model_name: str) -> Dict[str, Any]:
        """
        Obtiene la configuración de un modelo de IA específico.
        
        Args:
            model_name: Nombre del modelo
            
        Returns:
            Diccionario con configuración del modelo
        """
        pass
    
    @abstractmethod
    async def save_visualization_presets(
        self, 
        preset_name: str, 
        settings: Dict[str, Any]
    ) -> bool:
        """
        Guarda presets de configuración de visualización.
        
        Args:
            preset_name: Nombre del preset
            settings: Configuraciones de visualización
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        pass
    
    @abstractmethod
    async def get_visualization_presets(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene todos los presets de visualización disponibles.
        
        Returns:
            Diccionario con todos los presets de visualización
        """
        pass


class RepositoryError(Exception):
    """
    Excepción base para errores del repositorio.
    
    Permite manejar errores específicos de la capa de persistencia
    sin exponer detalles de implementación al dominio.
    """
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ImageNotFoundError(RepositoryError):
    """Excepción cuando una imagen solicitada no existe."""
    pass


class SegmentationNotFoundError(RepositoryError):
    """Excepción cuando una segmentación solicitada no existe."""
    pass


class ProjectNotFoundError(RepositoryError):
    """Excepción cuando un proyecto solicitado no existe.""" 
    pass


class DuplicateEntityError(RepositoryError):
    """Excepción cuando se intenta crear una entidad que ya existe."""
    pass


class InvalidQueryError(RepositoryError):
    """Excepción cuando los parámetros de consulta son inválidos."""
    pass