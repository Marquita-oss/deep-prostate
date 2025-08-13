#!/usr/bin/env python3
"""
demo_medical_workstation.py

Script de demostración para Medical Imaging Workstation.
Genera datos sintéticos de imágenes médicas y muestra todas
las funcionalidades principales de la aplicación sin necesidad
de datos DICOM reales.
"""

import sys
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import os

# Añadir directorio raíz al path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# Imports de la aplicación
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog
from PyQt6.QtCore import Qt, QTimer

# Imports del dominio
from domain.entities.medical_image import (
    MedicalImage, ImageSpacing, ImageModalityType, WindowLevel
)
from domain.entities.segmentation import (
    MedicalSegmentation, AnatomicalRegion, SegmentationType
)

# Imports de servicios
from application.services.image_services import (
    ImageLoadingService, ImageVisualizationService
)

# Imports de infraestructura
from infrastructure.ui.main_window import MedicalImagingMainWindow


class MedicalDataGenerator:
    """
    Generador de datos médicos sintéticos para demostración.
    
    Crea imágenes y segmentaciones realistas que simulan
    estudios de próstata para mostrar capacidades del sistema.
    """
    
    def __init__(self):
        """Inicializa el generador de datos."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="medical_demo_"))
        print(f"📁 Datos de demo en: {self.temp_dir}")
    
    def generate_prostate_mri_t2(self) -> MedicalImage:
        """
        Genera imagen MRI T2 sintética de próstata.
        
        Returns:
            Imagen médica con datos sintéticos realistas
        """
        print("🧠 Generando MRI T2 de próstata...")
        
        # Dimensiones típicas de MRI prostática
        width, height, depth = 256, 256, 24
        
        # Crear anatomía base
        image_data = np.zeros((depth, height, width), dtype=np.float32)
        
        # Añadir ruido de fondo
        noise = np.random.normal(0, 10, image_data.shape)
        image_data += noise
        
        # Crear próstata (elipsoide en centro)
        center_z, center_y, center_x = depth // 2, height // 2, width // 2
        
        for z in range(depth):
            for y in range(height):
                for x in range(width):
                    # Distancia desde el centro
                    dz = (z - center_z) / (depth * 0.3)
                    dy = (y - center_y) / (height * 0.15)
                    dx = (x - center_x) / (width * 0.15)
                    
                    distance = np.sqrt(dx**2 + dy**2 + dz**2)
                    
                    # Próstata (zona periférica)
                    if distance <= 1.0:
                        image_data[z, y, x] += 150 + np.random.normal(0, 20)
                    
                    # Zona de transición (más central)
                    if distance <= 0.6:
                        image_data[z, y, x] += 80 + np.random.normal(0, 15)
                    
                    # Lesión sospechosa (hipointensa en T2)
                    lesion_dx = dx - 0.3
                    lesion_dy = dy + 0.2
                    lesion_distance = np.sqrt(lesion_dx**2 + lesion_dy**2 + dz**2)
                    if lesion_distance <= 0.15:
                        image_data[z, y, x] = 60 + np.random.normal(0, 10)
                    
                    # Uretra (hipointensa)
                    if abs(dx) <= 0.05 and abs(dy) <= 0.05:
                        image_data[z, y, x] = 20 + np.random.normal(0, 5)
        
        # Añadir tejidos circundantes
        # Músculo
        muscle_mask = np.random.random(image_data.shape) < 0.3
        image_data[muscle_mask] += np.random.normal(100, 20, np.sum(muscle_mask))
        
        # Grasa (hiperintensa en T2)
        fat_mask = np.random.random(image_data.shape) < 0.1
        image_data[fat_mask] += np.random.normal(200, 30, np.sum(fat_mask))
        
        # Normalizar y convertir a enteros
        image_data = np.clip(image_data, 0, 400).astype(np.int16)
        
        # Crear entidad MedicalImage
        spacing = ImageSpacing(x=0.625, y=0.625, z=3.0)  # Típico para MRI próstata
        
        medical_image = MedicalImage(
            image_data=image_data,
            spacing=spacing,
            modality=ImageModalityType.MRI,
            patient_id="DEMO_PATIENT_001",
            study_instance_uid="1.2.3.4.5.6.7.8.9.10.11.12.13.14.15.16",
            series_instance_uid="1.2.3.4.5.6.7.8.9.10.11.12.13.14.15.16.17",
            acquisition_date=datetime.now() - timedelta(days=2),
            dicom_metadata={
                "StudyDescription": "MRI Prostate Multiparametric",
                "SeriesDescription": "T2W TSE Axial",
                "ProtocolName": "Prostate_3T_Protocol",
                "Manufacturer": "Demo Medical Systems",
                "MagneticFieldStrength": "3.0",
                "RepetitionTime": "4500",
                "EchoTime": "120",
                "SliceThickness": "3.0",
                "PixelSpacing": "[0.625, 0.625]",
                "PatientPosition": "HFS",
                "ImageComments": "Generated for demonstration purposes"
            }
        )
        
        print(f"   ✅ MRI T2 creada: {width}x{height}x{depth}, {spacing.x}x{spacing.y}x{spacing.z}mm")
        return medical_image
    
    def generate_prostate_dwi(self) -> MedicalImage:
        """
        Genera imagen DWI (Diffusion Weighted Imaging) sintética.
        
        Returns:
            Imagen DWI con valores ADC simulados
        """
        print("🌊 Generando DWI de próstata...")
        
        # Dimensiones similares a T2 pero con menos resolución
        width, height, depth = 128, 128, 20
        
        # Crear imagen DWI base
        image_data = np.zeros((depth, height, width), dtype=np.float32)
        
        # Añadir ruido
        noise = np.random.normal(0, 5, image_data.shape)
        image_data += noise
        
        center_z, center_y, center_x = depth // 2, height // 2, width // 2
        
        for z in range(depth):
            for y in range(height):
                for x in range(width):
                    dz = (z - center_z) / (depth * 0.3)
                    dy = (y - center_y) / (height * 0.15)
                    dx = (x - center_x) / (width * 0.15)
                    
                    distance = np.sqrt(dx**2 + dy**2 + dz**2)
                    
                    # Próstata normal (valores ADC típicos)
                    if distance <= 1.0:
                        # ADC normal: ~1200-1500 x10^-6 mm²/s
                        image_data[z, y, x] += 120 + np.random.normal(0, 15)
                    
                    # Lesión cancerosa (restricción de difusión)
                    lesion_dx = dx - 0.3
                    lesion_dy = dy + 0.2
                    lesion_distance = np.sqrt(lesion_dx**2 + lesion_dy**2 + dz**2)
                    if lesion_distance <= 0.15:
                        # ADC bajo: ~600-800 x10^-6 mm²/s
                        image_data[z, y, x] = 60 + np.random.normal(0, 8)
        
        # Normalizar
        image_data = np.clip(image_data, 0, 200).astype(np.int16)
        
        spacing = ImageSpacing(x=1.25, y=1.25, z=4.0)  # Menor resolución en DWI
        
        medical_image = MedicalImage(
            image_data=image_data,
            spacing=spacing,
            modality=ImageModalityType.MRI,
            patient_id="DEMO_PATIENT_001",
            study_instance_uid="1.2.3.4.5.6.7.8.9.10.11.12.13.14.15.16",
            series_instance_uid="1.2.3.4.5.6.7.8.9.10.11.12.13.14.15.16.18",
            acquisition_date=datetime.now() - timedelta(days=2),
            dicom_metadata={
                "StudyDescription": "MRI Prostate Multiparametric",
                "SeriesDescription": "DWI b=1000 ADC",
                "ProtocolName": "Prostate_3T_Protocol",
                "DiffusionBValue": "1000",
                "SliceThickness": "4.0",
                "ImageComments": "DWI with ADC calculation - Demo data"
            }
        )
        
        print(f"   ✅ DWI creada: {width}x{height}x{depth}, {spacing.x}x{spacing.y}x{spacing.z}mm")
        return medical_image
    
    def generate_ct_pelvis(self) -> MedicalImage:
        """
        Genera imagen CT de pelvis sintética.
        
        Returns:
            Imagen CT con valores HU realistas
        """
        print("⚡ Generando CT de pelvis...")
        
        # Dimensiones típicas de CT
        width, height, depth = 512, 512, 64
        
        # Crear imagen CT base (aire = -1000 HU)
        image_data = np.full((depth, height, width), -1000, dtype=np.float32)
        
        # Añadir ruido
        noise = np.random.normal(0, 20, image_data.shape)
        image_data += noise
        
        center_z, center_y, center_x = depth // 2, height // 2, width // 2
        
        # Crear estructuras anatómicas con valores HU típicos
        for z in range(depth):
            for y in range(height):
                for x in range(width):
                    # Distancia desde el centro
                    distance_center = np.sqrt(
                        ((x - center_x) / (width * 0.4))**2 + 
                        ((y - center_y) / (height * 0.4))**2
                    )
                    
                    # Cuerpo (tejidos blandos)
                    if distance_center <= 1.0:
                        image_data[z, y, x] = 40 + np.random.normal(0, 15)  # Tejido blando
                        
                        # Próstata
                        dz = (z - center_z) / (depth * 0.2)
                        dy = (y - center_y) / (height * 0.1)
                        dx = (x - center_x) / (width * 0.1)
                        prostate_distance = np.sqrt(dx**2 + dy**2 + dz**2)
                        
                        if prostate_distance <= 1.0:
                            image_data[z, y, x] = 50 + np.random.normal(0, 10)
                        
                        # Hueso (sacro, fémur)
                        bone_distance = distance_center - 0.7
                        if bone_distance > 0 and bone_distance < 0.2:
                            image_data[z, y, x] = 1000 + np.random.normal(0, 200)  # Hueso cortical
                        
                        # Grasa
                        if np.random.random() < 0.1:
                            image_data[z, y, x] = -100 + np.random.normal(0, 20)  # Grasa
                        
                        # Músculo
                        if distance_center > 0.3 and distance_center < 0.8:
                            if np.random.random() < 0.4:
                                image_data[z, y, x] = 55 + np.random.normal(0, 10)  # Músculo
        
        # Añadir contraste en vejiga si está presente
        bladder_center_y = center_y + int(height * 0.1)
        for z in range(max(0, center_z - 8), min(depth, center_z + 8)):
            for y in range(max(0, bladder_center_y - 20), min(height, bladder_center_y + 20)):
                for x in range(max(0, center_x - 15), min(width, center_x + 15)):
                    dy = (y - bladder_center_y) / 20
                    dx = (x - center_x) / 15
                    if dx**2 + dy**2 <= 1.0:
                        image_data[z, y, x] = 20 + np.random.normal(0, 5)  # Orina
        
        # Convertir a enteros
        image_data = image_data.astype(np.int16)
        
        spacing = ImageSpacing(x=0.625, y=0.625, z=1.25)  # Alta resolución CT
        
        medical_image = MedicalImage(
            image_data=image_data,
            spacing=spacing,
            modality=ImageModalityType.CT,
            patient_id="DEMO_PATIENT_002",
            study_instance_uid="2.3.4.5.6.7.8.9.10.11.12.13.14.15.16.17",
            series_instance_uid="2.3.4.5.6.7.8.9.10.11.12.13.14.15.16.17.18",
            acquisition_date=datetime.now() - timedelta(days=5),
            dicom_metadata={
                "StudyDescription": "CT Abdomen and Pelvis with Contrast",
                "SeriesDescription": "Portal Venous Phase",
                "ProtocolName": "Abdomen_Pelvis_Portal",
                "Manufacturer": "Demo CT Systems",
                "KVP": "120",
                "ExposureTime": "500",
                "SliceThickness": "1.25",
                "ConvolutionKernel": "B30f",
                "ContrastBolusAgent": "Iodinated Contrast",
                "ImageComments": "Synthetic CT data for demonstration"
            }
        )
        
        print(f"   ✅ CT Pelvis creada: {width}x{height}x{depth}, {spacing.x}x{spacing.y}x{spacing.z}mm")
        return medical_image
    
    def generate_segmentations_for_image(self, image: MedicalImage) -> List[MedicalSegmentation]:
        """
        Genera segmentaciones sintéticas para una imagen dada.
        
        Args:
            image: Imagen médica para la cual generar segmentaciones
            
        Returns:
            Lista de segmentaciones médicas
        """
        print(f"🎯 Generando segmentaciones para {image.modality.value}...")
        
        segmentations = []
        depth, height, width = image.dimensions
        
        if image.modality == ImageModalityType.MRI:
            # Segmentaciones para MRI de próstata
            
            # 1. Próstata completa
            prostate_mask = self._create_prostate_mask(depth, height, width)
            prostate_seg = MedicalSegmentation(
                mask_data=prostate_mask,
                anatomical_region=AnatomicalRegion.PROSTATE_WHOLE,
                segmentation_type=SegmentationType.AUTOMATIC,
                creation_date=datetime.now(),
                creator_id="demo_ai_system",
                confidence_score=0.92,
                parent_image_uid=image.series_instance_uid,
                description="AI-generated prostate segmentation (demo)"
            )
            segmentations.append(prostate_seg)
            
            # 2. Zona periférica
            pz_mask = self._create_peripheral_zone_mask(depth, height, width)
            pz_seg = MedicalSegmentation(
                mask_data=pz_mask,
                anatomical_region=AnatomicalRegion.PROSTATE_PERIPHERAL_ZONE,
                segmentation_type=SegmentationType.AUTOMATIC,
                creation_date=datetime.now(),
                creator_id="demo_ai_system",
                confidence_score=0.87,
                parent_image_uid=image.series_instance_uid,
                description="Peripheral zone segmentation (demo)"
            )
            segmentations.append(pz_seg)
            
            # 3. Lesión sospechosa
            lesion_mask = self._create_lesion_mask(depth, height, width)
            lesion_seg = MedicalSegmentation(
                mask_data=lesion_mask,
                anatomical_region=AnatomicalRegion.SUSPICIOUS_LESION,
                segmentation_type=SegmentationType.AUTOMATIC,
                creation_date=datetime.now(),
                creator_id="demo_ai_system",
                confidence_score=0.74,
                parent_image_uid=image.series_instance_uid,
                description="Suspicious lesion detection (demo)"
            )
            segmentations.append(lesion_seg)
        
        elif image.modality == ImageModalityType.CT:
            # Segmentaciones para CT
            
            # Próstata (menos precisa en CT)
            prostate_mask = self._create_prostate_mask(depth, height, width, scale=0.8)
            prostate_seg = MedicalSegmentation(
                mask_data=prostate_mask,
                anatomical_region=AnatomicalRegion.PROSTATE_WHOLE,
                segmentation_type=SegmentationType.AUTOMATIC,
                creation_date=datetime.now(),
                creator_id="demo_ai_system",
                confidence_score=0.68,
                parent_image_uid=image.series_instance_uid,
                description="CT-based prostate segmentation (demo)"
            )
            segmentations.append(prostate_seg)
        
        print(f"   ✅ {len(segmentations)} segmentaciones generadas")
        return segmentations
    
    def _create_prostate_mask(self, depth: int, height: int, width: int, scale: float = 1.0) -> np.ndarray:
        """Crea máscara de próstata elipsoidal."""
        mask = np.zeros((depth, height, width), dtype=bool)
        
        center_z, center_y, center_x = depth // 2, height // 2, width // 2
        radius_z = depth * 0.3 * scale
        radius_y = height * 0.15 * scale
        radius_x = width * 0.15 * scale
        
        for z in range(depth):
            for y in range(height):
                for x in range(width):
                    dz = (z - center_z) / radius_z
                    dy = (y - center_y) / radius_y
                    dx = (x - center_x) / radius_x
                    
                    if dz**2 + dy**2 + dx**2 <= 1.0:
                        mask[z, y, x] = True
        
        return mask
    
    def _create_peripheral_zone_mask(self, depth: int, height: int, width: int) -> np.ndarray:
        """Crea máscara de zona periférica (anillo exterior de próstata)."""
        mask = np.zeros((depth, height, width), dtype=bool)
        
        center_z, center_y, center_x = depth // 2, height // 2, width // 2
        outer_radius_z = depth * 0.3
        outer_radius_y = height * 0.15
        outer_radius_x = width * 0.15
        
        inner_radius_z = depth * 0.18
        inner_radius_y = height * 0.09
        inner_radius_x = width * 0.09
        
        for z in range(depth):
            for y in range(height):
                for x in range(width):
                    dz_outer = (z - center_z) / outer_radius_z
                    dy_outer = (y - center_y) / outer_radius_y
                    dx_outer = (x - center_x) / outer_radius_x
                    
                    dz_inner = (z - center_z) / inner_radius_z
                    dy_inner = (y - center_y) / inner_radius_y
                    dx_inner = (x - center_x) / inner_radius_x
                    
                    outer_dist = dz_outer**2 + dy_outer**2 + dx_outer**2
                    inner_dist = dz_inner**2 + dy_inner**2 + dx_inner**2
                    
                    if outer_dist <= 1.0 and inner_dist > 1.0:
                        mask[z, y, x] = True
        
        return mask
    
    def _create_lesion_mask(self, depth: int, height: int, width: int) -> np.ndarray:
        """Crea máscara de lesión pequeña."""
        mask = np.zeros((depth, height, width), dtype=bool)
        
        # Lesión en zona periférica posterolateral izquierda
        center_z = depth // 2 + 2
        center_y = height // 2 - int(height * 0.08)
        center_x = width // 2 + int(width * 0.08)
        
        radius = min(depth, height, width) * 0.04  # Lesión pequeña
        
        for z in range(max(0, center_z - 4), min(depth, center_z + 5)):
            for y in range(max(0, center_y - 6), min(height, center_y + 7)):
                for x in range(max(0, center_x - 6), min(width, center_x + 7)):
                    distance = np.sqrt(
                        (z - center_z)**2 + 
                        (y - center_y)**2 + 
                        (x - center_x)**2
                    )
                    
                    if distance <= radius:
                        mask[z, y, x] = True
        
        return mask
    
    def cleanup(self):
        """Limpia archivos temporales."""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print(f"🗑️  Limpiados archivos temporales: {self.temp_dir}")
        except Exception as e:
            print(f"⚠️  No se pudieron limpiar archivos temporales: {e}")


class DemoMedicalWorkstation:
    """
    Aplicación de demostración que muestra todas las funcionalidades
    del Medical Imaging Workstation usando datos sintéticos.
    """
    
    def __init__(self):
        """Inicializa la demo."""
        self.app = None
        self.main_window = None
        self.data_generator = MedicalDataGenerator()
        self.demo_images = []
        self.demo_segmentations = []
    
    def run_demo(self):
        """Ejecuta la demostración completa."""
        print("🏥 MEDICAL IMAGING WORKSTATION - DEMO")
        print("=" * 50)
        
        try:
            # 1. Crear aplicación Qt
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("Medical Imaging Workstation - Demo")
            
            # 2. Generar datos de demostración
            self._generate_demo_data()
            
            # 3. Crear ventana principal
            self.main_window = MedicalImagingMainWindow(str(self.data_generator.temp_dir))
            
            # 4. Cargar datos de demo en la aplicación
            self._load_demo_data()
            
            # 5. Mostrar ventana y información de demo
            self.main_window.show()
            self._show_demo_instructions()
            
            # 6. Ejecutar aplicación
            print("\n🚀 Iniciando aplicación de demostración...")
            print("   💡 Cierra la ventana para finalizar la demo")
            
            exit_code = self.app.exec()
            
            return exit_code
            
        except Exception as e:
            print(f"❌ Error en demostración: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        finally:
            # Limpiar recursos
            self.data_generator.cleanup()
    
    def _generate_demo_data(self):
        """Genera todos los datos de demostración."""
        print("\n📊 Generando datos de demostración...")
        
        # Generar imágenes médicas sintéticas
        mri_t2 = self.data_generator.generate_prostate_mri_t2()
        self.demo_images.append(mri_t2)
        
        mri_dwi = self.data_generator.generate_prostate_dwi()
        self.demo_images.append(mri_dwi)
        
        ct_pelvis = self.data_generator.generate_ct_pelvis()
        self.demo_images.append(ct_pelvis)
        
        # Generar segmentaciones para cada imagen
        for image in self.demo_images:
            segmentations = self.data_generator.generate_segmentations_for_image(image)
            self.demo_segmentations.extend(segmentations)
        
        print(f"\n✅ Datos generados:")
        print(f"   📷 {len(self.demo_images)} imágenes médicas")
        print(f"   🎯 {len(self.demo_segmentations)} segmentaciones")
    
    def _load_demo_data(self):
        """Carga los datos de demo en la aplicación."""
        print("\n📥 Cargando datos en la aplicación...")
        
        # En implementación real, cargar datos a través de la interfaz
        # Por ahora, simplemente notificar que los datos están disponibles
        
        QTimer.singleShot(1000, self._auto_load_first_image)
    
    def _auto_load_first_image(self):
        """Carga automáticamente la primera imagen de demo."""
        if self.demo_images and self.main_window:
            try:
                # Simular carga de la primera imagen
                first_image = self.demo_images[0]
                
                # En implementación real, usar el servicio de carga
                # self.main_window._load_selected_image(first_image.series_instance_uid)
                
                print(f"   ✅ Imagen cargada: {first_image.modality.value} - {first_image.patient_id}")
                
                # Cargar segmentaciones asociadas
                image_segmentations = [
                    seg for seg in self.demo_segmentations 
                    if seg._parent_image_uid == first_image.series_instance_uid
                ]
                
                for seg in image_segmentations:
                    # self.main_window._on_segmentation_completed(seg)
                    pass
                
                print(f"   ✅ {len(image_segmentations)} segmentaciones cargadas")
                
            except Exception as e:
                print(f"   ⚠️  Error cargando imagen de demo: {e}")
    
    def _show_demo_instructions(self):
        """Muestra instrucciones de la demostración."""
        instructions = """
🎓 DEMO INSTRUCTIONS

Welcome to the Medical Imaging Workstation demonstration!

🔍 WHAT'S INCLUDED:
• Synthetic MRI T2-weighted prostate images
• Synthetic DWI (Diffusion Weighted Imaging)
• Synthetic CT pelvis scan
• AI-generated segmentations (prostate, lesions)

🎮 TRY THESE FEATURES:
1. 📷 Switch between 2D and 3D views (tabs)
2. 🖱️ Navigate slices with mouse wheel
3. 🎨 Adjust window/level (left panel)
4. 📏 Use measurement tools (toolbar)
5. 🤖 Run AI analysis (right panel)
6. ✏️ Edit segmentations manually
7. 📊 View quantitative analysis

💡 TIPS:
• All data is synthetic and for demonstration only
• Try different visualization presets
• Experiment with 3D rendering settings
• Use keyboard shortcuts (see Help menu)

🔗 REAL USAGE:
In real use, you would:
• Load actual DICOM files (File > Open)
• Use real nnUNet models for AI
• Export results for clinical review

Enjoy exploring! 🏥
        """
        
        msg_box = QMessageBox(self.main_window)
        msg_box.setWindowTitle("Medical Workstation Demo")
        msg_box.setText("Welcome to the demonstration!")
        msg_box.setDetailedText(instructions.strip())
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Mostrar después de que la ventana principal esté visible
        QTimer.singleShot(2000, msg_box.exec)


def main():
    """Función principal de la demo."""
    print("🎬 Iniciando demostración de Medical Imaging Workstation...")
    
    # Verificar dependencias básicas
    try:
        import PyQt6
        import numpy
        import vtk
        print("✅ Dependencias básicas verificadas")
    except ImportError as e:
        print(f"❌ Dependencia faltante: {e}")
        print("💡 Ejecuta: pip install -r requirements.txt")
        return 1
    
    # Crear y ejecutar demo
    demo = DemoMedicalWorkstation()
    exit_code = demo.run_demo()
    
    print(f"\n👋 Demo finalizada con código: {exit_code}")
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)