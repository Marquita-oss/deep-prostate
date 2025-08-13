"""
application/services/image_services.py

Servicios de aplicación para gestión de imágenes médicas.
Estos servicios orquestan casos de uso complejos que involucran múltiples
entidades del dominio y repositorios, manteniendo la lógica de negocio
separada de los detalles de infraestructura.
"""

import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import asyncio
from pathlib import Path

from ...domain.entities.medical_image import (
    MedicalImage, ImageSpacing, WindowLevel, 
    ImageModalityType, ImagePlaneType
)
from ...domain.entities.segmentation import MedicalSegmentation
from ...domain.repositories.repositories import (
    MedicalImageRepository, SegmentationRepository, ProjectRepository,
    ImageNotFoundError, RepositoryError
)


class ImageLoadingService:
    """
    Servicio para carga y validación de imágenes médicas DICOM.
    
    Este servicio orquesta el proceso completo de cargar una imagen desde
    el almacenamiento, validar su integridad médica, y prepararla para
    su uso en el sistema.
    """
    
    def __init__(self, image_repository: MedicalImageRepository):
        self._image_repository = image_repository
        self._supported_modalities = {
            ImageModalityType.CT,
            ImageModalityType.MRI,
            ImageModalityType.ULTRASOUND
        }
    
    async def load_image_by_series_uid(self, series_uid: str) -> Optional[MedicalImage]:
        """
        Carga una imagen médica específica por su serie DICOM.
        
        Args:
            series_uid: Identificador único de la serie DICOM
            
        Returns:
            Imagen médica cargada o None si no existe
            
        Raises:
            ImageLoadingError: Si hay problemas durante la carga
        """
        try:
            image = await self._image_repository.find_by_series_uid(series_uid)
            
            if image is None:
                return None
            
            # Validar integridad de la imagen cargada
            await self._validate_image_integrity(image)
            
            return image
            
        except RepositoryError as e:
            raise ImageLoadingError(f"Error accediendo al repositorio: {e}") from e
        except Exception as e:
            raise ImageLoadingError(f"Error inesperado cargando imagen: {e}") from e
    
    async def load_study_images(self, study_uid: str) -> List[MedicalImage]:
        """
        Carga todas las imágenes pertenecientes a un estudio completo.
        
        Args:
            study_uid: Identificador único del estudio DICOM
            
        Returns:
            Lista de imágenes médicas del estudio ordenadas por serie
            
        Raises:
            ImageLoadingError: Si hay problemas durante la carga
        """
        try:
            images = await self._image_repository.find_by_study_uid(study_uid)
            
            if not images:
                raise ImageLoadingError(f"No se encontraron imágenes para el estudio {study_uid}")
            
            # Validar integridad de todas las imágenes
            validation_tasks = [self._validate_image_integrity(img) for img in images]
            await asyncio.gather(*validation_tasks)
            
            # Ordenar por número de serie si está disponible
            sorted_images = self._sort_images_by_series(images)
            
            return sorted_images
            
        except RepositoryError as e:
            raise ImageLoadingError(f"Error accediendo al repositorio: {e}") from e
        except Exception as e:
            raise ImageLoadingError(f"Error inesperado cargando estudio: {e}") from e
    
    async def load_patient_images(
        self, 
        patient_id: str,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[MedicalImage]:
        """
        Carga todas las imágenes de un paciente específico.
        
        Args:
            patient_id: Identificador del paciente
            date_range: Rango de fechas opcional para filtrar
            
        Returns:
            Lista de imágenes médicas del paciente ordenadas por fecha
        """
        try:
            if date_range:
                start_date, end_date = date_range
                images = await self._image_repository.find_by_date_range(start_date, end_date)
                # Filtrar por paciente
                images = [img for img in images if img.patient_id == patient_id]
            else:
                images = await self._image_repository.find_by_patient_id(patient_id)
            
            # Ordenar por fecha de adquisición
            sorted_images = sorted(images, key=lambda img: img.acquisition_date)
            
            return sorted_images
            
        except RepositoryError as e:
            raise ImageLoadingError(f"Error accediendo al repositorio: {e}") from e
    
    async def validate_modality_support(self, image: MedicalImage) -> bool:
        """
        Valida si la modalidad de imagen es soportada por el sistema.
        
        Args:
            image: Imagen médica a validar
            
        Returns:
            True si la modalidad es soportada, False en caso contrario
        """
        return image.modality in self._supported_modalities
    
    async def _validate_image_integrity(self, image: MedicalImage) -> None:
        """
        Valida la integridad médica de una imagen cargada.
        
        Args:
            image: Imagen a validar
            
        Raises:
            ImageValidationError: Si la imagen no pasa las validaciones
        """
        # Validar dimensiones mínimas
        if any(dim < 32 for dim in image.dimensions):
            raise ImageValidationError(
                f"Dimensiones de imagen demasiado pequeñas: {image.dimensions}"
            )
        
        # Validar espaciado físico razonable
        spacing = image.spacing
        if spacing.x <= 0 or spacing.y <= 0 or spacing.z <= 0:
            raise ImageValidationError(
                f"Espaciado de imagen inválido: {spacing}"
            )
        
        # Validar modalidad soportada
        if not await self.validate_modality_support(image):
            raise ImageValidationError(
                f"Modalidad {image.modality} no soportada"
            )
        
        # Validar rango de intensidades
        stats = image.get_intensity_statistics()
        if stats['min'] == stats['max']:
            raise ImageValidationError("Imagen con intensidad uniforme detectada")
    
    def _sort_images_by_series(self, images: List[MedicalImage]) -> List[MedicalImage]:
        """
        Ordena las imágenes por número de serie DICOM.
        
        Args:
            images: Lista de imágenes a ordenar
            
        Returns:
            Lista ordenada de imágenes
        """
        def get_series_number(image: MedicalImage) -> int:
            series_number = image.get_dicom_tag("SeriesNumber")
            return int(series_number) if series_number else 0
        
        return sorted(images, key=get_series_number)


class ImageVisualizationService:
    """
    Servicio para preparación y optimización de imágenes para visualización.
    
    Maneja la lógica de negocio relacionada con ventana/nivel, extracción
    de cortes, y preparación de datos para diferentes tipos de visualización.
    """
    
    def __init__(self):
        # Presets predefinidos de ventana/nivel por modalidad y región
        self._window_level_presets = {
            ImageModalityType.CT: {
                "soft_tissue": WindowLevel(window=400, level=40),
                "bone": WindowLevel(window=1500, level=300),
                "lung": WindowLevel(window=1600, level=-600),
                "brain": WindowLevel(window=100, level=40),
                "liver": WindowLevel(window=150, level=60)
            },
            ImageModalityType.MRI: {
                "t1": WindowLevel(window=600, level=300),
                "t2": WindowLevel(window=1000, level=500),
                "flair": WindowLevel(window=800, level=400),
                "dwi": WindowLevel(window=1200, level=600)
            }
        }
    
    async def prepare_slice_for_display(
        self,
        image: MedicalImage,
        plane: ImagePlaneType,
        slice_index: int,
        window_level: Optional[WindowLevel] = None
    ) -> Dict[str, Any]:
        """
        Prepara un corte 2D específico para visualización en pantalla.
        
        Args:
            image: Imagen médica fuente
            plane: Plano anatómico del corte
            slice_index: Índice del corte
            window_level: Configuración de ventana/nivel (opcional)
            
        Returns:
            Diccionario con datos del corte preparados para visualización
        """
        try:
            # Extraer el corte específico
            slice_data = image.get_slice(plane, slice_index)
            
            # Usar configuración de ventana/nivel especificada o la actual de la imagen
            wl = window_level or image.current_window_level
            
            # Aplicar ventana/nivel para normalizar intensidades
            normalized_slice = wl.apply_to_array(slice_data)
            
            # Calcular información espacial del corte
            spatial_info = self._calculate_slice_spatial_info(image, plane, slice_index)
            
            # Preparar metadatos del corte
            slice_metadata = {
                "plane": plane.value,
                "slice_index": slice_index,
                "total_slices": self._get_total_slices(image, plane),
                "window_level": {"window": wl.window, "level": wl.level},
                "spatial_info": spatial_info,
                "intensity_range": wl.get_display_range()
            }
            
            return {
                "image_data": normalized_slice,
                "metadata": slice_metadata,
                "original_data": slice_data  # Para análisis adicional
            }
            
        except Exception as e:
            raise ImageVisualizationError(f"Error preparando corte para visualización: {e}")
    
    async def prepare_volume_for_3d(
        self,
        image: MedicalImage,
        downsample_factor: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Prepara los datos volumétricos completos para renderizado 3D.
        
        Args:
            image: Imagen médica volumétrica
            downsample_factor: Factor de submuestreo para optimización (opcional)
            
        Returns:
            Diccionario con datos volumétricos preparados para 3D
        """
        try:
            # Obtener datos volumétricos originales
            volume_data = image.image_data
            
            # Aplicar submuestreo si se especifica
            if downsample_factor and downsample_factor > 1:
                volume_data = self._downsample_volume(volume_data, downsample_factor)
            
            # Aplicar ventana/nivel al volumen completo
            wl = image.current_window_level
            normalized_volume = wl.apply_to_array(volume_data)
            
            # Calcular información espacial
            spacing = image.spacing
            if downsample_factor:
                spacing = ImageSpacing(
                    x=spacing.x * downsample_factor,
                    y=spacing.y * downsample_factor,
                    z=spacing.z * downsample_factor
                )
            
            # Preparar metadatos volumétricos
            volume_metadata = {
                "original_dimensions": image.dimensions,
                "current_dimensions": volume_data.shape,
                "spacing": {
                    "x": spacing.x,
                    "y": spacing.y,
                    "z": spacing.z
                },
                "downsample_factor": downsample_factor or 1,
                "window_level": {"window": wl.window, "level": wl.level},
                "modality": image.modality.value,
                "intensity_statistics": image.get_intensity_statistics()
            }
            
            return {
                "volume_data": normalized_volume,
                "metadata": volume_metadata,
                "original_spacing": image.spacing
            }
            
        except Exception as e:
            raise ImageVisualizationError(f"Error preparando volumen para 3D: {e}")
    
    async def apply_window_level_preset(
        self,
        image: MedicalImage,
        preset_name: str
    ) -> WindowLevel:
        """
        Aplica un preset predefinido de ventana/nivel basado en modalidad.
        
        Args:
            image: Imagen médica a la cual aplicar el preset
            preset_name: Nombre del preset a aplicar
            
        Returns:
            Configuración WindowLevel aplicada
            
        Raises:
            PresetNotFoundError: Si el preset no existe para la modalidad
        """
        modality_presets = self._window_level_presets.get(image.modality)
        
        if not modality_presets:
            raise PresetNotFoundError(
                f"No hay presets disponibles para modalidad {image.modality}"
            )
        
        if preset_name not in modality_presets:
            available_presets = list(modality_presets.keys())
            raise PresetNotFoundError(
                f"Preset '{preset_name}' no encontrado. "
                f"Presets disponibles: {available_presets}"
            )
        
        preset_wl = modality_presets[preset_name]
        image.set_window_level(preset_wl.window, preset_wl.level)
        
        return preset_wl
    
    async def get_available_presets(self, modality: ImageModalityType) -> List[str]:
        """
        Obtiene la lista de presets disponibles para una modalidad específica.
        
        Args:
            modality: Modalidad de imagen
            
        Returns:
            Lista de nombres de presets disponibles
        """
        presets = self._window_level_presets.get(modality, {})
        return list(presets.keys())
    
    async def calculate_optimal_window_level(
        self,
        image: MedicalImage,
        percentile_range: Tuple[float, float] = (5.0, 95.0)
    ) -> WindowLevel:
        """
        Calcula una configuración óptima de ventana/nivel basada en estadísticas.
        
        Args:
            image: Imagen médica para análisis
            percentile_range: Rango de percentiles para el cálculo
            
        Returns:
            Configuración WindowLevel optimizada
        """
        # Obtener estadísticas de intensidad
        image_data = image.image_data
        
        # Calcular percentiles para ventana robusta
        low_percentile, high_percentile = percentile_range
        min_intensity = np.percentile(image_data, low_percentile)
        max_intensity = np.percentile(image_data, high_percentile)
        
        # Calcular ventana y nivel
        window = max_intensity - min_intensity
        level = (max_intensity + min_intensity) / 2.0
        
        # Asegurar valores mínimos razonables
        if window < 1.0:
            window = np.std(image_data) * 3.0
        
        return WindowLevel(window=window, level=level)
    
    def _calculate_slice_spatial_info(
        self,
        image: MedicalImage,
        plane: ImagePlaneType,
        slice_index: int
    ) -> Dict[str, Any]:
        """
        Calcula información espacial específica de un corte.
        
        Args:
            image: Imagen médica fuente
            plane: Plano del corte
            slice_index: Índice del corte
            
        Returns:
            Diccionario con información espacial del corte
        """
        spacing = image.spacing
        dimensions = image.dimensions
        
        if plane == ImagePlaneType.AXIAL:
            pixel_spacing = (spacing.x, spacing.y)
            slice_thickness = spacing.z
            slice_dimensions = (dimensions[2], dimensions[1])  # width, height
            physical_position = slice_index * spacing.z
            
        elif plane == ImagePlaneType.SAGITTAL:
            pixel_spacing = (spacing.y, spacing.z)
            slice_thickness = spacing.x
            slice_dimensions = (dimensions[1], dimensions[0])  # height, depth
            physical_position = slice_index * spacing.x
            
        elif plane == ImagePlaneType.CORONAL:
            pixel_spacing = (spacing.x, spacing.z)
            slice_thickness = spacing.y
            slice_dimensions = (dimensions[2], dimensions[0])  # width, depth
            physical_position = slice_index * spacing.y
            
        else:
            raise ValueError(f"Plano {plane} no soportado para cálculo espacial")
        
        return {
            "pixel_spacing_mm": pixel_spacing,
            "slice_thickness_mm": slice_thickness,
            "slice_dimensions": slice_dimensions,
            "physical_position_mm": physical_position,
            "plane_normal": plane.value
        }
    
    def _get_total_slices(self, image: MedicalImage, plane: ImagePlaneType) -> int:
        """
        Obtiene el número total de cortes disponibles en un plano específico.
        
        Args:
            image: Imagen médica
            plane: Plano anatómico
            
        Returns:
            Número total de cortes en el plano
        """
        dimensions = image.dimensions
        
        if plane == ImagePlaneType.AXIAL:
            return dimensions[0]  # depth
        elif plane == ImagePlaneType.SAGITTAL:
            return dimensions[2]  # width
        elif plane == ImagePlaneType.CORONAL:
            return dimensions[1]  # height
        else:
            raise ValueError(f"Plano {plane} no soportado")
    
    def _downsample_volume(
        self,
        volume: np.ndarray,
        factor: int
    ) -> np.ndarray:
        """
        Submuestrea un volumen por un factor específico para optimización 3D.
        
        Args:
            volume: Array volumétrico original
            factor: Factor de submuestreo
            
        Returns:
            Volumen submuestreado
        """
        if len(volume.shape) != 3:
            raise ValueError("El submuestreo requiere un volumen 3D")
        
        # Submuestreo simple por salto de índices
        return volume[::factor, ::factor, ::factor]


# Excepciones específicas del servicio
class ImageLoadingError(Exception):
    """Excepción para errores durante la carga de imágenes."""
    pass


class ImageValidationError(Exception):
    """Excepción para errores de validación de imágenes médicas."""
    pass


class ImageVisualizationError(Exception):
    """Excepción para errores durante la preparación de visualización."""
    pass


class PresetNotFoundError(Exception):
    """Excepción cuando un preset de visualización no existe."""
    pass