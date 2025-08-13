"""
domain/entities/medical_image.py

Entidad central que representa una imagen médica DICOM.
Esta clase encapsula toda la lógica de negocio relacionada con imágenes médicas,
incluyendo metadatos DICOM, validaciones y operaciones básicas.
No tiene dependencias externas, solo lógica pura de dominio.
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class ImageModalityType(Enum):
    """Tipos de modalidad de imagen médica soportados."""
    CT = "CT"
    MRI = "MRI"
    ULTRASOUND = "US"
    XRAY = "XR"
    PET = "PT"


class ImagePlaneType(Enum):
    """Planos anatómicos estándar para visualización médica."""
    AXIAL = "axial"
    SAGITTAL = "sagittal"
    CORONAL = "coronal"
    OBLIQUE = "oblique"


@dataclass
class ImageSpacing:
    """
    Representa el espaciado físico entre voxels en una imagen médica.
    Crítico para mediciones precisas y reconstrucciones 3D.
    """
    x: float  # Espaciado en mm en dirección X
    y: float  # Espaciado en mm en dirección Y
    z: float  # Espaciado en mm en dirección Z (grosor de corte)
    
    def get_voxel_volume(self) -> float:
        """Calcula el volumen de un voxel en mm³."""
        return self.x * self.y * self.z
    
    def is_isotropic(self, tolerance: float = 0.1) -> bool:
        """Determina si el espaciado es isotrópico dentro de una tolerancia."""
        return (abs(self.x - self.y) < tolerance and 
                abs(self.y - self.z) < tolerance and 
                abs(self.x - self.z) < tolerance)


@dataclass
class WindowLevel:
    """
    Configuración de ventana y nivel para visualización de imágenes médicas.
    Controla el contraste y brillo para resaltar diferentes tejidos.
    """
    window: float  # Ancho de la ventana
    level: float   # Centro de la ventana
    
    def get_display_range(self) -> Tuple[float, float]:
        """Retorna el rango de valores [min, max] para visualización."""
        min_val = self.level - (self.window / 2.0)
        max_val = self.level + (self.window / 2.0)
        return min_val, max_val
    
    def apply_to_array(self, image_array: np.ndarray) -> np.ndarray:
        """
        Aplica la configuración de ventana/nivel a un array de imagen.
        Normaliza los valores al rango [0, 1] para visualización.
        """
        min_val, max_val = self.get_display_range()
        # Clip values to window range
        clipped = np.clip(image_array, min_val, max_val)
        # Normalize to [0, 1]
        if max_val != min_val:
            normalized = (clipped - min_val) / (max_val - min_val)
        else:
            normalized = np.zeros_like(clipped)
        return normalized


class MedicalImage:
    """
    Entidad principal que representa una imagen médica completa.
    Encapsula todos los datos y metadatos DICOM con validaciones de negocio.
    
    Esta clase es el núcleo del dominio médico y no conoce nada sobre
    frameworks de visualización, almacenamiento o interfaces gráficas.
    """
    
    def __init__(
        self,
        image_data: np.ndarray,
        spacing: ImageSpacing,
        modality: ImageModalityType,
        patient_id: str,
        study_instance_uid: str,
        series_instance_uid: str,
        acquisition_date: datetime,
        dicom_metadata: Optional[Dict[str, Any]] = None
    ):
        # Validaciones críticas de negocio
        self._validate_image_data(image_data)
        self._validate_patient_id(patient_id)
        self._validate_uid(study_instance_uid, "Study Instance UID")
        self._validate_uid(series_instance_uid, "Series Instance UID")
        
        self._image_data = image_data.copy()  # Proteger datos originales
        self._spacing = spacing
        self._modality = modality
        self._patient_id = patient_id
        self._study_instance_uid = study_instance_uid
        self._series_instance_uid = series_instance_uid
        self._acquisition_date = acquisition_date
        self._dicom_metadata = dicom_metadata or {}
        
        # Configuración por defecto basada en modalidad
        self._default_window_level = self._get_default_window_level()
        self._current_window_level = self._default_window_level
    
    @property
    def image_data(self) -> np.ndarray:
        """Acceso de solo lectura a los datos de imagen."""
        return self._image_data.copy()
    
    @property
    def original_data_type(self) -> np.dtype:
        """Tipo de datos original de la imagen."""
        return self._image_data.dtype
    
    @property
    def dimensions(self) -> Tuple[int, ...]:
        """Dimensiones de la imagen (alto, ancho, profundidad)."""
        return self._image_data.shape
    
    @property
    def spacing(self) -> ImageSpacing:
        """Espaciado físico entre voxels."""
        return self._spacing
    
    @property
    def modality(self) -> ImageModalityType:
        """Modalidad de la imagen médica."""
        return self._modality
    
    @property
    def patient_id(self) -> str:
        """Identificador único del paciente."""
        return self._patient_id
    
    @property
    def study_instance_uid(self) -> str:
        """UID único del estudio DICOM."""
        return self._study_instance_uid
    
    @property
    def series_instance_uid(self) -> str:
        """UID único de la serie DICOM."""
        return self._series_instance_uid
    
    @property
    def acquisition_date(self) -> datetime:
        """Fecha de adquisición de la imagen."""
        return self._acquisition_date
    
    @property
    def current_window_level(self) -> WindowLevel:
        """Configuración actual de ventana y nivel."""
        return self._current_window_level
    
    def get_slice(self, plane: ImagePlaneType, index: int) -> np.ndarray:
        """
        Extrae un corte 2D específico de la imagen volumétrica.
        
        Args:
            plane: Plano anatómico del corte
            index: Índice del corte en el plano especificado
            
        Returns:
            Array 2D representando el corte
            
        Raises:
            ValueError: Si el índice está fuera de rango
        """
        if len(self._image_data.shape) != 3:
            raise ValueError("La extracción de cortes requiere datos 3D")
        
        depth, height, width = self._image_data.shape
        
        if plane == ImagePlaneType.AXIAL:
            if not 0 <= index < depth:
                raise ValueError(f"Índice axial {index} fuera de rango [0, {depth-1}]")
            return self._image_data[index, :, :]
        
        elif plane == ImagePlaneType.SAGITTAL:
            if not 0 <= index < width:
                raise ValueError(f"Índice sagital {index} fuera de rango [0, {width-1}]")
            return self._image_data[:, :, index]
        
        elif plane == ImagePlaneType.CORONAL:
            if not 0 <= index < height:
                raise ValueError(f"Índice coronal {index} fuera de rango [0, {height-1}]")
            return self._image_data[:, index, :]
        
        else:
            raise ValueError(f"Plano {plane} no soportado para extracción simple")
    
    def get_physical_dimensions(self) -> Tuple[float, float, float]:
        """
        Calcula las dimensiones físicas reales de la imagen en milímetros.
        
        Returns:
            Tupla (ancho_mm, alto_mm, profundidad_mm)
        """
        if len(self._image_data.shape) == 3:
            depth, height, width = self._image_data.shape
            return (
                width * self._spacing.x,
                height * self._spacing.y,
                depth * self._spacing.z
            )
        else:
            height, width = self._image_data.shape
            return (width * self._spacing.x, height * self._spacing.y, 0.0)
    
    def get_intensity_statistics(self) -> Dict[str, float]:
        """
        Calcula estadísticas básicas de intensidad de la imagen.
        
        Returns:
            Diccionario con estadísticas (min, max, mean, std, median)
        """
        return {
            'min': float(np.min(self._image_data)),
            'max': float(np.max(self._image_data)),
            'mean': float(np.mean(self._image_data)),
            'std': float(np.std(self._image_data)),
            'median': float(np.median(self._image_data))
        }
    
    def set_window_level(self, window: float, level: float) -> None:
        """
        Actualiza la configuración de ventana y nivel.
        
        Args:
            window: Nuevo ancho de ventana
            level: Nuevo centro de ventana
        """
        if window <= 0:
            raise ValueError("El ancho de ventana debe ser positivo")
        
        self._current_window_level = WindowLevel(window=window, level=level)
    
    def reset_window_level(self) -> None:
        """Restaura la configuración de ventana y nivel por defecto."""
        self._current_window_level = self._default_window_level
    
    def get_dicom_tag(self, tag_name: str) -> Any:
        """
        Obtiene un valor específico de los metadatos DICOM.
        
        Args:
            tag_name: Nombre del tag DICOM
            
        Returns:
            Valor del tag o None si no existe
        """
        return self._dicom_metadata.get(tag_name)
    
    def _validate_image_data(self, image_data: np.ndarray) -> None:
        """Valida que los datos de imagen sean válidos."""
        if not isinstance(image_data, np.ndarray):
            raise TypeError("Los datos de imagen deben ser un numpy array")
        
        if image_data.size == 0:
            raise ValueError("Los datos de imagen no pueden estar vacíos")
        
        if not (2 <= len(image_data.shape) <= 3):
            raise ValueError("La imagen debe ser 2D o 3D")
    
    def _validate_patient_id(self, patient_id: str) -> None:
        """Valida el ID del paciente."""
        if not isinstance(patient_id, str) or not patient_id.strip():
            raise ValueError("El ID del paciente debe ser una cadena no vacía")
    
    def _validate_uid(self, uid: str, uid_type: str) -> None:
        """Valida que un UID DICOM tenga formato correcto."""
        if not isinstance(uid, str) or not uid.strip():
            raise ValueError(f"{uid_type} debe ser una cadena no vacía")
        
        # Validación básica de formato UID DICOM
        if not all(c.isdigit() or c == '.' for c in uid):
            raise ValueError(f"{uid_type} debe contener solo dígitos y puntos")
    
    def _get_default_window_level(self) -> WindowLevel:
        """
        Calcula configuración de ventana/nivel por defecto basada en modalidad.
        
        Returns:
            WindowLevel apropiado para la modalidad
        """
        if self._modality == ImageModalityType.CT:
            # Ventana para tejidos blandos en CT
            return WindowLevel(window=400, level=40)
        
        elif self._modality == ImageModalityType.MRI:
            # Configuración adaptativa basada en estadísticas de imagen
            stats = self.get_intensity_statistics()
            window = (stats['max'] - stats['min']) * 0.8
            level = (stats['max'] + stats['min']) / 2
            return WindowLevel(window=window, level=level)
        
        else:
            # Configuración genérica basada en estadísticas
            stats = self.get_intensity_statistics()
            window = (stats['max'] - stats['min'])
            level = (stats['max'] + stats['min']) / 2
            return WindowLevel(window=window, level=level)