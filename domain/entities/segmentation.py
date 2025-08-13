"""
domain/entities/segmentation.py

Entidad que representa segmentaciones médicas y regiones de interés.
Encapsula la lógica de negocio para máscaras binarias, contornos y análisis
de regiones anatómicas, especialmente para detección de cáncer prostático.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import uuid


class SegmentationType(Enum):
    """Tipos de segmentación médica soportados."""
    MANUAL = "manual"           # Dibujada manualmente por el médico
    AUTOMATIC = "automatic"     # Generada por IA (nnUNet)
    SEMI_AUTOMATIC = "semi_automatic"  # IA + correcciones manuales
    IMPORTED = "imported"       # Importada de otro sistema


class AnatomicalRegion(Enum):
    """Regiones anatómicas específicas para próstata."""
    PROSTATE_WHOLE = "prostate_whole"
    PROSTATE_PERIPHERAL_ZONE = "prostate_peripheral_zone"
    PROSTATE_TRANSITION_ZONE = "prostate_transition_zone"
    PROSTATE_CENTRAL_ZONE = "prostate_central_zone"
    SUSPICIOUS_LESION = "suspicious_lesion"
    CONFIRMED_CANCER = "confirmed_cancer"
    BENIGN_HYPERPLASIA = "benign_hyperplasia"
    URETHRA = "urethra"
    SEMINAL_VESICLES = "seminal_vesicles"


class ConfidenceLevel(Enum):
    """Niveles de confianza para segmentaciones automáticas."""
    VERY_LOW = "very_low"      # < 0.3
    LOW = "low"                # 0.3 - 0.5
    MODERATE = "moderate"      # 0.5 - 0.7
    HIGH = "high"              # 0.7 - 0.9
    VERY_HIGH = "very_high"    # > 0.9


@dataclass
class SegmentationMetrics:
    """
    Métricas cuantitativas de una segmentación.
    Críticas para análisis clínico y seguimiento de lesiones.
    """
    volume_mm3: float           # Volumen en milímetros cúbicos
    surface_area_mm2: float     # Área de superficie en mm²
    max_diameter_mm: float      # Diámetro máximo en mm
    sphericity: float           # Qué tan esférica es la región [0-1]
    compactness: float          # Compacidad de la forma [0-1]
    voxel_count: int           # Número de voxels en la segmentación
    
    def get_equivalent_sphere_diameter(self) -> float:
        """Calcula el diámetro de una esfera equivalente en volumen."""
        if self.volume_mm3 <= 0:
            return 0.0
        return 2.0 * ((3.0 * self.volume_mm3) / (4.0 * np.pi)) ** (1.0/3.0)


@dataclass
class IntensityStatistics:
    """
    Estadísticas de intensidad dentro de una región segmentada.
    Útil para caracterización de tejidos y diagnóstico diferencial.
    """
    mean_intensity: float
    std_intensity: float
    min_intensity: float
    max_intensity: float
    median_intensity: float
    percentile_25: float
    percentile_75: float
    entropy: float              # Entropía de Shannon
    uniformity: float           # Uniformidad de intensidades
    
    def get_intensity_range(self) -> float:
        """Calcula el rango de intensidades."""
        return self.max_intensity - self.min_intensity


class MedicalSegmentation:
    """
    Entidad que representa una segmentación médica completa.
    
    Una segmentación es una máscara que identifica una región específica
    en una imagen médica, como un tumor o un órgano. Esta clase encapsula
    toda la lógica de negocio relacionada con análisis de regiones.
    """
    
    def __init__(
        self,
        mask_data: np.ndarray,
        anatomical_region: AnatomicalRegion,
        segmentation_type: SegmentationType,
        creation_date: datetime,
        creator_id: str,
        confidence_score: Optional[float] = None,
        parent_image_uid: Optional[str] = None,
        description: Optional[str] = None
    ):
        # Validaciones de negocio
        self._validate_mask_data(mask_data)
        self._validate_confidence_score(confidence_score)
        
        self._segmentation_id = str(uuid.uuid4())
        self._mask_data = mask_data.astype(bool)  # Asegurar máscara binaria
        self._anatomical_region = anatomical_region
        self._segmentation_type = segmentation_type
        self._creation_date = creation_date
        self._creator_id = creator_id
        self._confidence_score = confidence_score
        self._parent_image_uid = parent_image_uid
        self._description = description or f"{anatomical_region.value} segmentation"
        
        # Estado mutable para edición
        self._is_locked = False
        self._modification_history: List[Dict] = []
        
        # Cache para métricas calculadas
        self._cached_metrics: Optional[SegmentationMetrics] = None
        self._cached_intensity_stats: Optional[IntensityStatistics] = None
        self._cache_invalidated = True
    
    @property
    def segmentation_id(self) -> str:
        """Identificador único de la segmentación."""
        return self._segmentation_id
    
    @property
    def mask_data(self) -> np.ndarray:
        """Máscara binaria de la segmentación (solo lectura)."""
        return self._mask_data.copy()
    
    @property
    def dimensions(self) -> Tuple[int, ...]:
        """Dimensiones de la máscara de segmentación."""
        return self._mask_data.shape
    
    @property
    def anatomical_region(self) -> AnatomicalRegion:
        """Región anatómica que representa esta segmentación."""
        return self._anatomical_region
    
    @property
    def segmentation_type(self) -> SegmentationType:
        """Tipo de segmentación (manual, automática, etc.)."""
        return self._segmentation_type
    
    @property
    def confidence_level(self) -> Optional[ConfidenceLevel]:
        """Nivel de confianza categórico basado en el score numérico."""
        if self._confidence_score is None:
            return None
        
        if self._confidence_score < 0.3:
            return ConfidenceLevel.VERY_LOW
        elif self._confidence_score < 0.5:
            return ConfidenceLevel.LOW
        elif self._confidence_score < 0.7:
            return ConfidenceLevel.MODERATE
        elif self._confidence_score < 0.9:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.VERY_HIGH
    
    @property
    def is_locked(self) -> bool:
        """Indica si la segmentación está bloqueada para edición."""
        return self._is_locked
    
    @property
    def voxel_count(self) -> int:
        """Número total de voxels en la segmentación."""
        return int(np.sum(self._mask_data))
    
    @property
    def is_empty(self) -> bool:
        """Determina si la segmentación está vacía."""
        return self.voxel_count == 0
    
    def get_bounding_box(self) -> Tuple[Tuple[int, int], ...]:
        """
        Calcula la caja delimitadora mínima que contiene la segmentación.
        
        Returns:
            Tupla de tuplas ((min_dim, max_dim), ...) para cada dimensión
        """
        if self.is_empty:
            return tuple((0, 0) for _ in self._mask_data.shape)
        
        indices = np.where(self._mask_data)
        bounding_box = []
        
        for i in range(len(indices)):
            min_idx = int(np.min(indices[i]))
            max_idx = int(np.max(indices[i]))
            bounding_box.append((min_idx, max_idx))
        
        return tuple(bounding_box)
    
    def get_centroid(self) -> Tuple[float, ...]:
        """
        Calcula el centroide (centro de masa) de la segmentación.
        
        Returns:
            Coordenadas del centroide en cada dimensión
        """
        if self.is_empty:
            return tuple(0.0 for _ in self._mask_data.shape)
        
        indices = np.where(self._mask_data)
        centroid = []
        
        for i in range(len(indices)):
            centroid.append(float(np.mean(indices[i])))
        
        return tuple(centroid)
    
    def calculate_metrics(self, spacing: 'ImageSpacing') -> SegmentationMetrics:
        """
        Calcula métricas geométricas de la segmentación.
        
        Args:
            spacing: Espaciado físico de la imagen para cálculos métricos
            
        Returns:
            Objeto con todas las métricas calculadas
        """
        if self._cached_metrics is not None and not self._cache_invalidated:
            return self._cached_metrics
        
        if self.is_empty:
            self._cached_metrics = SegmentationMetrics(
                volume_mm3=0.0, surface_area_mm2=0.0, max_diameter_mm=0.0,
                sphericity=0.0, compactness=0.0, voxel_count=0
            )
            return self._cached_metrics
        
        # Calcular volumen
        voxel_volume = spacing.get_voxel_volume()
        volume_mm3 = self.voxel_count * voxel_volume
        
        # Calcular diámetro máximo
        max_diameter_mm = self._calculate_max_diameter(spacing)
        
        # Calcular área de superficie (aproximada)
        surface_area_mm2 = self._calculate_surface_area(spacing)
        
        # Calcular esfericidad y compacidad
        sphericity = self._calculate_sphericity(volume_mm3, surface_area_mm2)
        compactness = self._calculate_compactness(volume_mm3, surface_area_mm2)
        
        self._cached_metrics = SegmentationMetrics(
            volume_mm3=volume_mm3,
            surface_area_mm2=surface_area_mm2,
            max_diameter_mm=max_diameter_mm,
            sphericity=sphericity,
            compactness=compactness,
            voxel_count=self.voxel_count
        )
        
        self._cache_invalidated = False
        return self._cached_metrics
    
    def calculate_intensity_statistics(self, image_data: np.ndarray) -> IntensityStatistics:
        """
        Calcula estadísticas de intensidad dentro de la región segmentada.
        
        Args:
            image_data: Array de imagen original
            
        Returns:
            Estadísticas de intensidad de la región
        """
        if image_data.shape != self._mask_data.shape:
            raise ValueError("Las dimensiones de imagen y máscara deben coincidir")
        
        if self.is_empty:
            # Retornar estadísticas vacías
            return IntensityStatistics(
                mean_intensity=0.0, std_intensity=0.0, min_intensity=0.0,
                max_intensity=0.0, median_intensity=0.0, percentile_25=0.0,
                percentile_75=0.0, entropy=0.0, uniformity=0.0
            )
        
        # Extraer valores de intensidad dentro de la máscara
        masked_values = image_data[self._mask_data]
        
        # Calcular estadísticas básicas
        mean_intensity = float(np.mean(masked_values))
        std_intensity = float(np.std(masked_values))
        min_intensity = float(np.min(masked_values))
        max_intensity = float(np.max(masked_values))
        median_intensity = float(np.median(masked_values))
        percentile_25 = float(np.percentile(masked_values, 25))
        percentile_75 = float(np.percentile(masked_values, 75))
        
        # Calcular entropía y uniformidad
        entropy = self._calculate_entropy(masked_values)
        uniformity = self._calculate_uniformity(masked_values)
        
        self._cached_intensity_stats = IntensityStatistics(
            mean_intensity=mean_intensity,
            std_intensity=std_intensity,
            min_intensity=min_intensity,
            max_intensity=max_intensity,
            median_intensity=median_intensity,
            percentile_25=percentile_25,
            percentile_75=percentile_75,
            entropy=entropy,
            uniformity=uniformity
        )
        
        return self._cached_intensity_stats
    
    def union_with(self, other: 'MedicalSegmentation') -> 'MedicalSegmentation':
        """
        Crea una nueva segmentación que es la unión de esta con otra.
        
        Args:
            other: Otra segmentación para unir
            
        Returns:
            Nueva segmentación con la unión de ambas máscaras
        """
        if self._mask_data.shape != other._mask_data.shape:
            raise ValueError("Las segmentaciones deben tener las mismas dimensiones")
        
        union_mask = np.logical_or(self._mask_data, other._mask_data)
        
        return MedicalSegmentation(
            mask_data=union_mask,
            anatomical_region=self._anatomical_region,  # Mantener región original
            segmentation_type=SegmentationType.MANUAL,  # Marcar como manual al ser editada
            creation_date=datetime.now(),
            creator_id="system_union",
            parent_image_uid=self._parent_image_uid,
            description=f"Union of {self._description} and {other._description}"
        )
    
    def intersection_with(self, other: 'MedicalSegmentation') -> 'MedicalSegmentation':
        """
        Crea una nueva segmentación que es la intersección de esta con otra.
        
        Args:
            other: Otra segmentación para intersectar
            
        Returns:
            Nueva segmentación con la intersección de ambas máscaras
        """
        if self._mask_data.shape != other._mask_data.shape:
            raise ValueError("Las segmentaciones deben tener las mismas dimensiones")
        
        intersection_mask = np.logical_and(self._mask_data, other._mask_data)
        
        return MedicalSegmentation(
            mask_data=intersection_mask,
            anatomical_region=self._anatomical_region,
            segmentation_type=SegmentationType.MANUAL,
            creation_date=datetime.now(),
            creator_id="system_intersection",
            parent_image_uid=self._parent_image_uid,
            description=f"Intersection of {self._description} and {other._description}"
        )
    
    def apply_morphological_operation(self, operation: str, iterations: int = 1) -> 'MedicalSegmentation':
        """
        Aplica operaciones morfológicas a la segmentación.
        
        Args:
            operation: Tipo de operación ('erode', 'dilate', 'open', 'close')
            iterations: Número de iteraciones
            
        Returns:
            Nueva segmentación con la operación aplicada
        """
        from scipy import ndimage
        
        if operation == 'erode':
            processed_mask = ndimage.binary_erosion(self._mask_data, iterations=iterations)
        elif operation == 'dilate':
            processed_mask = ndimage.binary_dilation(self._mask_data, iterations=iterations)
        elif operation == 'open':
            processed_mask = ndimage.binary_opening(self._mask_data, iterations=iterations)
        elif operation == 'close':
            processed_mask = ndimage.binary_closing(self._mask_data, iterations=iterations)
        else:
            raise ValueError(f"Operación morfológica '{operation}' no reconocida")
        
        return MedicalSegmentation(
            mask_data=processed_mask,
            anatomical_region=self._anatomical_region,
            segmentation_type=SegmentationType.MANUAL,
            creation_date=datetime.now(),
            creator_id="system_morphology",
            parent_image_uid=self._parent_image_uid,
            description=f"{operation.capitalize()} of {self._description}"
        )
    
    def lock(self) -> None:
        """Bloquea la segmentación para evitar modificaciones accidentales."""
        self._is_locked = True
    
    def unlock(self) -> None:
        """Desbloquea la segmentación para permitir edición."""
        self._is_locked = False
    
    def _validate_mask_data(self, mask_data: np.ndarray) -> None:
        """Valida que los datos de máscara sean válidos."""
        if not isinstance(mask_data, np.ndarray):
            raise TypeError("La máscara debe ser un numpy array")
        
        if mask_data.size == 0:
            raise ValueError("La máscara no puede estar vacía")
        
        if not (2 <= len(mask_data.shape) <= 3):
            raise ValueError("La máscara debe ser 2D o 3D")
    
    def _validate_confidence_score(self, confidence_score: Optional[float]) -> None:
        """Valida que el score de confianza esté en rango válido."""
        if confidence_score is not None:
            if not (0.0 <= confidence_score <= 1.0):
                raise ValueError("El score de confianza debe estar entre 0.0 y 1.0")
    
    def _calculate_max_diameter(self, spacing: 'ImageSpacing') -> float:
        """Calcula el diámetro máximo de la segmentación."""
        if self.is_empty:
            return 0.0
        
        # Obtener coordenadas de todos los puntos en la segmentación
        indices = np.where(self._mask_data)
        if len(indices[0]) < 2:
            return 0.0
        
        # Calcular distancia máxima entre cualquier par de puntos
        max_distance = 0.0
        coords = list(zip(*indices))
        
        # Para eficiencia, muestrear puntos si hay demasiados
        if len(coords) > 1000:
            step = len(coords) // 1000
            coords = coords[::step]
        
        for i, coord1 in enumerate(coords):
            for coord2 in coords[i+1:]:
                # Calcular distancia euclidiana en espacio físico
                distance = 0.0
                if len(coord1) == 3:  # 3D
                    dx = (coord1[2] - coord2[2]) * spacing.x
                    dy = (coord1[1] - coord2[1]) * spacing.y
                    dz = (coord1[0] - coord2[0]) * spacing.z
                    distance = np.sqrt(dx*dx + dy*dy + dz*dz)
                else:  # 2D
                    dx = (coord1[1] - coord2[1]) * spacing.x
                    dy = (coord1[0] - coord2[0]) * spacing.y
                    distance = np.sqrt(dx*dx + dy*dy)
                
                max_distance = max(max_distance, distance)
        
        return max_distance
    
    def _calculate_surface_area(self, spacing: 'ImageSpacing') -> float:
        """Calcula el área de superficie aproximada de la segmentación."""
        if self.is_empty:
            return 0.0
        
        # Usar gradiente para encontrar bordes
        if len(self._mask_data.shape) == 3:
            # 3D: usar gradiente en las 3 direcciones
            grad_x = np.gradient(self._mask_data.astype(float), axis=2)
            grad_y = np.gradient(self._mask_data.astype(float), axis=1)
            grad_z = np.gradient(self._mask_data.astype(float), axis=0)
            
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
            
            # Área de superficie aproximada considerando el espaciado
            surface_voxels = np.sum(gradient_magnitude > 0)
            avg_voxel_face_area = (spacing.x * spacing.y + 
                                 spacing.y * spacing.z + 
                                 spacing.x * spacing.z) / 3.0
            return surface_voxels * avg_voxel_face_area
        
        else:
            # 2D: calcular perímetro
            grad_x = np.gradient(self._mask_data.astype(float), axis=1)
            grad_y = np.gradient(self._mask_data.astype(float), axis=0)
            
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            # Perímetro aproximado considerando el espaciado
            perimeter_pixels = np.sum(gradient_magnitude > 0)
            avg_pixel_length = (spacing.x + spacing.y) / 2.0
            return perimeter_pixels * avg_pixel_length
    
    def _calculate_sphericity(self, volume: float, surface_area: float) -> float:
        """Calcula la esfericidad de la segmentación."""
        if volume <= 0 or surface_area <= 0:
            return 0.0
        
        if len(self._mask_data.shape) == 3:
            # Esfericidad 3D: π^(1/3) * (6V)^(2/3) / A
            sphere_surface_area = np.pi**(1.0/3.0) * (6.0 * volume)**(2.0/3.0)
            return sphere_surface_area / surface_area
        else:
            # Circularidad 2D: 4πA / P²
            return (4.0 * np.pi * volume) / (surface_area ** 2)
    
    def _calculate_compactness(self, volume: float, surface_area: float) -> float:
        """Calcula la compacidad de la segmentación."""
        if volume <= 0 or surface_area <= 0:
            return 0.0
        
        if len(self._mask_data.shape) == 3:
            # Compacidad 3D: V / (A^(3/2))
            return volume / (surface_area ** 1.5)
        else:
            # Compacidad 2D: A / P²
            return volume / (surface_area ** 2)
    
    def _calculate_entropy(self, values: np.ndarray) -> float:
        """Calcula la entropía de Shannon de los valores de intensidad."""
        if len(values) == 0:
            return 0.0
        
        # Crear histograma normalizado
        hist, _ = np.histogram(values, bins=256, density=True)
        hist = hist[hist > 0]  # Eliminar ceros para evitar log(0)
        
        if len(hist) == 0:
            return 0.0
        
        # Calcular entropía: -Σ(p * log2(p))
        return -np.sum(hist * np.log2(hist))
    
    def _calculate_uniformity(self, values: np.ndarray) -> float:
        """Calcula la uniformidad (energía) de los valores de intensidad."""
        if len(values) == 0:
            return 0.0
        
        # Crear histograma normalizado
        hist, _ = np.histogram(values, bins=256, density=True)
        
        # Uniformidad: Σ(p²)
        return np.sum(hist ** 2)