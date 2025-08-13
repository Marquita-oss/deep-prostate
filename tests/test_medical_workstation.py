#!/usr/bin/env python3
"""
tests/test_medical_workstation.py

Suite de tests básicos para Medical Imaging Workstation.
Verifica funcionalidad crítica de componentes principales,
entidades del dominio, servicios y integración básica.
"""

import sys
import pytest
import numpy as np
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Añadir directorio raíz para imports
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Imports de la aplicación médica
from domain.entities.medical_image import (
    MedicalImage, ImageSpacing, WindowLevel, ImageModalityType
)
from domain.entities.segmentation import (
    MedicalSegmentation, AnatomicalRegion, SegmentationType
)


class TestMedicalImageEntity:
    """Tests para la entidad MedicalImage del dominio."""
    
    def setup_method(self):
        """Configuración para cada test."""
        # Crear imagen de prueba
        self.test_image_data = np.random.randint(0, 1000, (64, 64, 32), dtype=np.int16)
        self.test_spacing = ImageSpacing(x=1.0, y=1.0, z=3.0)
        self.test_modality = ImageModalityType.MRI
        self.test_patient_id = "TEST_PATIENT_001"
        self.test_study_uid = "1.2.3.4.5.6.7.8.9.10.11"
        self.test_series_uid = "1.2.3.4.5.6.7.8.9.10.11.12"
        self.test_acquisition_date = datetime(2024, 1, 15, 14, 30, 0)
        
        self.medical_image = MedicalImage(
            image_data=self.test_image_data,
            spacing=self.test_spacing,
            modality=self.test_modality,
            patient_id=self.test_patient_id,
            study_instance_uid=self.test_study_uid,
            series_instance_uid=self.test_series_uid,
            acquisition_date=self.test_acquisition_date
        )
    
    def test_medical_image_creation(self):
        """Test creación básica de imagen médica."""
        assert self.medical_image is not None
        assert self.medical_image.patient_id == self.test_patient_id
        assert self.medical_image.modality == self.test_modality
        assert np.array_equal(self.medical_image.image_data, self.test_image_data)
    
    def test_image_dimensions(self):
        """Test obtención de dimensiones."""
        dimensions = self.medical_image.dimensions
        assert dimensions == (64, 64, 32)
    
    def test_physical_dimensions(self):
        """Test cálculo de dimensiones físicas."""
        physical_dims = self.medical_image.get_physical_dimensions()
        expected = (64.0, 64.0, 96.0)  # 64*1.0, 64*1.0, 32*3.0
        assert physical_dims == expected
    
    def test_slice_extraction_axial(self):
        """Test extracción de slice axial."""
        slice_data = self.medical_image.get_slice(ImagePlaneType.AXIAL, 16)
        assert slice_data.shape == (64, 64)
        assert np.array_equal(slice_data, self.test_image_data[16, :, :])
    
    def test_slice_extraction_sagittal(self):
        """Test extracción de slice sagital."""
        slice_data = self.medical_image.get_slice(ImagePlaneType.SAGITTAL, 32)
        assert slice_data.shape == (64, 32)
        assert np.array_equal(slice_data, self.test_image_data[:, :, 32])
    
    def test_slice_extraction_out_of_bounds(self):
        """Test extracción de slice fuera de límites."""
        with pytest.raises(ValueError):
            self.medical_image.get_slice(ImagePlaneType.AXIAL, 100)
    
    def test_window_level_configuration(self):
        """Test configuración de ventana/nivel."""
        self.medical_image.set_window_level(500, 100)
        wl = self.medical_image.current_window_level
        assert wl.window == 500
        assert wl.level == 100
    
    def test_window_level_invalid(self):
        """Test configuración inválida de ventana/nivel."""
        with pytest.raises(ValueError):
            self.medical_image.set_window_level(-100, 50)  # Ventana negativa
    
    def test_intensity_statistics(self):
        """Test cálculo de estadísticas de intensidad."""
        stats = self.medical_image.get_intensity_statistics()
        
        assert 'min' in stats
        assert 'max' in stats 
        assert 'mean' in stats
        assert 'std' in stats
        assert 'median' in stats
        
        assert stats['min'] >= 0
        assert stats['max'] < 1000
        assert stats['min'] <= stats['mean'] <= stats['max']
    
    def test_invalid_image_data(self):
        """Test validación de datos de imagen inválidos."""
        with pytest.raises(TypeError):
            MedicalImage(
                image_data="invalid",  # No es numpy array
                spacing=self.test_spacing,
                modality=self.test_modality,
                patient_id=self.test_patient_id,
                study_instance_uid=self.test_study_uid,
                series_instance_uid=self.test_series_uid,
                acquisition_date=self.test_acquisition_date
            )
    
    def test_invalid_patient_id(self):
        """Test validación de ID de paciente inválido."""
        with pytest.raises(ValueError):
            MedicalImage(
                image_data=self.test_image_data,
                spacing=self.test_spacing,
                modality=self.test_modality,
                patient_id="",  # ID vacío
                study_instance_uid=self.test_study_uid,
                series_instance_uid=self.test_series_uid,
                acquisition_date=self.test_acquisition_date
            )


class TestMedicalSegmentationEntity:
    """Tests para la entidad MedicalSegmentation del dominio."""
    
    def setup_method(self):
        """Configuración para cada test."""
        # Crear máscara de prueba
        self.test_mask = np.zeros((64, 64, 32), dtype=bool)
        self.test_mask[20:40, 20:40, 10:20] = True  # Región rectangular
        
        self.segmentation = MedicalSegmentation(
            mask_data=self.test_mask,
            anatomical_region=AnatomicalRegion.PROSTATE_WHOLE,
            segmentation_type=SegmentationType.AUTOMATIC,
            creation_date=datetime.now(),
            creator_id="test_ai_system",
            confidence_score=0.85
        )
    
    def test_segmentation_creation(self):
        """Test creación básica de segmentación."""
        assert self.segmentation is not None
        assert self.segmentation.anatomical_region == AnatomicalRegion.PROSTATE_WHOLE
        assert self.segmentation.segmentation_type == SegmentationType.AUTOMATIC
        assert self.segmentation.confidence_level == ConfidenceLevel.HIGH
    
    def test_voxel_count(self):
        """Test conteo de voxels en segmentación."""
        expected_count = 20 * 20 * 10  # Región 20x20x10
        assert self.segmentation.voxel_count == expected_count
    
    def test_bounding_box(self):
        """Test cálculo de caja delimitadora."""
        bbox = self.segmentation.get_bounding_box()
        expected = ((10, 19), (20, 39), (20, 39))  # (z_min, z_max), (y_min, y_max), (x_min, x_max)
        assert bbox == expected
    
    def test_centroid(self):
        """Test cálculo de centroide."""
        centroid = self.segmentation.get_centroid()
        expected = (14.5, 29.5, 29.5)  # Centro de la región
        assert centroid == expected
    
    def test_empty_segmentation(self):
        """Test segmentación vacía."""
        empty_mask = np.zeros((64, 64, 32), dtype=bool)
        empty_seg = MedicalSegmentation(
            mask_data=empty_mask,
            anatomical_region=AnatomicalRegion.SUSPICIOUS_LESION,
            segmentation_type=SegmentationType.MANUAL,
            creation_date=datetime.now(),
            creator_id="test_user"
        )
        
        assert empty_seg.is_empty
        assert empty_seg.voxel_count == 0
    
    def test_segmentation_union(self):
        """Test unión de segmentaciones."""
        # Crear segunda segmentación
        mask2 = np.zeros((64, 64, 32), dtype=bool)
        mask2[30:50, 30:50, 15:25] = True
        
        seg2 = MedicalSegmentation(
            mask_data=mask2,
            anatomical_region=AnatomicalRegion.PROSTATE_PERIPHERAL_ZONE,
            segmentation_type=SegmentationType.MANUAL,
            creation_date=datetime.now(),
            creator_id="test_user"
        )
        
        # Calcular unión
        union_seg = self.segmentation.union_with(seg2)
        
        # Verificar que la unión contiene ambas regiones
        assert union_seg.voxel_count >= self.segmentation.voxel_count
        assert union_seg.voxel_count >= seg2.voxel_count
    
    def test_segmentation_intersection(self):
        """Test intersección de segmentaciones."""
        # Crear segmentación que se solapa parcialmente
        mask2 = np.zeros((64, 64, 32), dtype=bool)
        mask2[25:45, 25:45, 12:22] = True  # Se solapa con la original
        
        seg2 = MedicalSegmentation(
            mask_data=mask2,
            anatomical_region=AnatomicalRegion.PROSTATE_TRANSITION_ZONE,
            segmentation_type=SegmentationType.MANUAL,
            creation_date=datetime.now(),
            creator_id="test_user"
        )
        
        intersection_seg = self.segmentation.intersection_with(seg2)
        
        # La intersección debe ser menor que ambas segmentaciones originales
        assert intersection_seg.voxel_count <= self.segmentation.voxel_count
        assert intersection_seg.voxel_count <= seg2.voxel_count
        assert intersection_seg.voxel_count > 0  # Debe haber alguna intersección
    
    def test_confidence_level_mapping(self):
        """Test mapeo de niveles de confianza."""
        # Test diferentes niveles de confianza
        confidence_tests = [
            (0.2, ConfidenceLevel.VERY_LOW),
            (0.4, ConfidenceLevel.LOW),
            (0.6, ConfidenceLevel.MODERATE),
            (0.8, ConfidenceLevel.HIGH),
            (0.95, ConfidenceLevel.VERY_HIGH)
        ]
        
        for conf_score, expected_level in confidence_tests:
            seg = MedicalSegmentation(
                mask_data=self.test_mask,
                anatomical_region=AnatomicalRegion.SUSPICIOUS_LESION,
                segmentation_type=SegmentationType.AUTOMATIC,
                creation_date=datetime.now(),
                creator_id="test_ai",
                confidence_score=conf_score
            )
            assert seg.confidence_level == expected_level


class TestImageSpacingEntity:
    """Tests para la entidad ImageSpacing."""
    
    def test_voxel_volume_calculation(self):
        """Test cálculo de volumen de voxel."""
        spacing = ImageSpacing(x=1.0, y=1.0, z=3.0)
        volume = spacing.get_voxel_volume()
        assert volume == 3.0
    
    def test_isotropic_detection(self):
        """Test detección de espaciado isotrópico."""
        # Espaciado isotrópico
        iso_spacing = ImageSpacing(x=1.0, y=1.0, z=1.0)
        assert iso_spacing.is_isotropic()
        
        # Espaciado no isotrópico
        aniso_spacing = ImageSpacing(x=0.5, y=0.5, z=3.0)
        assert not aniso_spacing.is_isotropic()
        
        # Espaciado casi isotrópico (dentro de tolerancia)
        almost_iso = ImageSpacing(x=1.0, y=1.05, z=0.98)
        assert almost_iso.is_isotropic(tolerance=0.1)


class TestWindowLevelEntity:
    """Tests para la entidad WindowLevel."""
    
    def test_display_range_calculation(self):
        """Test cálculo de rango de visualización."""
        wl = WindowLevel(window=400, level=40)
        min_val, max_val = wl.get_display_range()
        
        assert min_val == -160  # 40 - 400/2
        assert max_val == 240   # 40 + 400/2
    
    def test_window_level_application(self):
        """Test aplicación de ventana/nivel a array."""
        wl = WindowLevel(window=100, level=50)
        test_array = np.array([0, 25, 50, 75, 100], dtype=np.float32)
        
        normalized = wl.apply_to_array(test_array)
        
        # Verificar que el resultado está en rango [0, 1]
        assert np.all(normalized >= 0)
        assert np.all(normalized <= 1)
        
        # Verificar que el valor central se mapea cerca de 0.5
        assert abs(normalized[2] - 0.5) < 0.1  # Valor 50 (nivel) -> ~0.5


@pytest.mark.skipif(
    sys.platform.startswith("win") and "CI" in os.environ,
    reason="GUI tests pueden fallar en CI de Windows"
)
class TestApplicationLaunch:
    """Tests de integración para lanzamiento de aplicación."""
    
    @patch('PyQt6.QtWidgets.QApplication')
    def test_application_can_be_imported(self, mock_qapp):
        """Test que la aplicación principal puede ser importada."""
        try:
            from main import MedicalImagingApplication
            assert MedicalImagingApplication is not None
        except ImportError as e:
            pytest.skip(f"No se puede importar aplicación principal: {e}")
    
    def test_config_manager_initialization(self):
        """Test inicialización del gestor de configuración."""
        try:
            from infrastructure.utils.config_manager import ConfigurationManager
            
            config_manager = ConfigurationManager()
            assert config_manager is not None
            
            # Test obtención de valor por defecto
            default_value = config_manager.get("nonexistent_key", "default")
            assert default_value == "default"
            
        except ImportError as e:
            pytest.skip(f"No se puede importar ConfigurationManager: {e}")
    
    def test_system_validator(self):
        """Test validador del sistema."""
        try:
            from infrastructure.utils.startup_validator import SystemValidator
            
            validator = SystemValidator()
            result = validator.validate_system()
            
            assert hasattr(result, 'is_valid')
            assert hasattr(result, 'errors')
            assert hasattr(result, 'warnings')
            assert hasattr(result, 'system_info')
            
        except ImportError as e:
            pytest.skip(f"No se puede importar SystemValidator: {e}")


class TestImageServices:
    """Tests para servicios de aplicación de imágenes."""
    
    def test_image_loading_service_creation(self):
        """Test creación del servicio de carga de imágenes."""
        try:
            from application.services.image_services import ImageLoadingService
            
            # Mock del repositorio
            mock_repo = Mock()
            service = ImageLoadingService(mock_repo)
            
            assert service is not None
            
        except ImportError as e:
            pytest.skip(f"No se puede importar ImageLoadingService: {e}")
    
    def test_image_visualization_service_creation(self):
        """Test creación del servicio de visualización."""
        try:
            from application.services.image_services import ImageVisualizationService
            
            service = ImageVisualizationService()
            assert service is not None
            
        except ImportError as e:
            pytest.skip(f"No se puede importar ImageVisualizationService: {e}")


def run_basic_smoke_test():
    """Test básico de humo para verificar imports principales."""
    print("🧪 Ejecutando test básico de humo...")
    
    try:
        # Test imports críticos
        import numpy as np
        print("   ✅ NumPy")
        
        from domain.entities.medical_image import MedicalImage
        print("   ✅ MedicalImage")
        
        from domain.entities.segmentation import MedicalSegmentation
        print("   ✅ MedicalSegmentation")
        
        # Test creación básica de entidades
        test_data = np.random.rand(10, 10, 5)
        from domain.entities.medical_image import ImageSpacing, ImageModalityType
        
        spacing = ImageSpacing(1.0, 1.0, 1.0)
        image = MedicalImage(
            image_data=test_data,
            spacing=spacing,
            modality=ImageModalityType.CT,
            patient_id="TEST_001",
            study_instance_uid="1.2.3",
            series_instance_uid="1.2.3.4",
            acquisition_date=datetime.now()
        )
        print("   ✅ Creación de MedicalImage")
        
        # Test estadísticas básicas
        stats = image.get_intensity_statistics()
        assert 'mean' in stats
        print("   ✅ Estadísticas de imagen")
        
        print("✅ Test de humo completado exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Test de humo falló: {e}")
        return False


if __name__ == "__main__":
    """Ejecutar tests básicos si se llama directamente."""
    import os
    
    print("🏥 Medical Imaging Workstation - Basic Tests")
    print("=" * 50)
    
    # Test de humo básico
    if not run_basic_smoke_test():
        sys.exit(1)
    
    # Ejecutar tests con pytest si está disponible
    try:
        pytest_exit_code = pytest.main([
            __file__,
            "-v",
            "--tb=short",
            "--no-header"
        ])
        
        if pytest_exit_code == 0:
            print("\n✅ Todos los tests básicos pasaron")
        else:
            print(f"\n⚠️  Algunos tests fallaron (código: {pytest_exit_code})")
            
    except ImportError:
        print("\n⚠️  pytest no disponible, solo test de humo ejecutado")
        pytest_exit_code = 0
    
    sys.exit(pytest_exit_code)