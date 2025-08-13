#!/usr/bin/env python3
"""
infrastructure/utils/demo_data_generator.py

Generador de datos médicos sintéticos para demostración.
Este módulo crea datos médicos realistas pero sintéticos
que permiten demostrar todas las funcionalidades del sistema
sin requerir datos médicos reales.

IMPORTANTE: Todos los datos generados son sintéticos y solo
para demostración. No representan casos médicos reales.
"""

import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import tempfile
import shutil
import uuid


def create_demo_medical_data() -> Dict[str, Any]:
    """
    Crea conjunto completo de datos médicos sintéticos para demostración.
    
    Esta función genera todo lo necesario para demostrar el sistema
    médico refactorizado sin requerir datos médicos reales.
    
    Returns:
        Diccionario con datos médicos sintéticos organizados
    """
    generator = MedicalDemoDataGenerator()
    return generator.generate_complete_demo_dataset()


class MedicalDemoDataGenerator:
    """
    Generador completo de datos médicos sintéticos.
    
    Esta clase crea datos médicos realistas pero completamente
    sintéticos que pueden ser usados para demostrar todas las
    funcionalidades del sistema médico sin comprometer la
    privacidad de pacientes reales.
    
    Piensa en esta clase como un "simulador médico" que crea
    escenarios médicos convincentes pero completamente ficticios
    para propósitos educativos y de demostración.
    """
    
    def __init__(self):
        """
        Inicializa el generador con configuraciones médicas realistas.
        """
        # Configuración para generar datos médicos realistas
        self.patient_count = 5
        self.studies_per_patient = 2
        self.series_per_study = 3
        
        # Modalidades médicas que podemos simular
        self.available_modalities = ['MRI', 'CT', 'ULTRASOUND']
        
        # Regiones anatómicas para simulación
        self.anatomical_regions = [
            'PROSTATE_WHOLE',
            'PROSTATE_PERIPHERAL_ZONE', 
            'PROSTATE_TRANSITION_ZONE',
            'SUSPICIOUS_LESION',
            'CONFIRMED_CANCER'
        ]
        
        # Directorio temporal para datos de demostración
        self.temp_dir = None
        self._setup_temp_environment()
    
    def _setup_temp_environment(self) -> None:
        """Configura entorno temporal para datos de demostración."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix='medical_demo_'))
        
        # Crear estructura de directorios médicos
        demo_dirs = [
            'patients',
            'studies', 
            'series',
            'images',
            'segmentations',
            'reports'
        ]
        
        for dir_name in demo_dirs:
            (self.temp_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    def generate_complete_demo_dataset(self) -> Dict[str, Any]:
        """
        Genera conjunto completo de datos médicos para demostración.
        
        Este método orquesta la creación de un dataset médico completo
        que incluye pacientes, estudios, imágenes, segmentaciones,
        y reportes - todo sintético pero médicamente plausible.
        
        Returns:
            Diccionario con dataset médico completo
        """
        print("🏥 Generando dataset médico sintético completo...")
        
        # Generar pacientes sintéticos
        patients = self._generate_synthetic_patients()
        print(f"   ✅ {len(patients)} pacientes sintéticos generados")
        
        # Generar estudios médicos para cada paciente
        studies = self._generate_medical_studies(patients)
        print(f"   ✅ {len(studies)} estudios médicos generados")
        
        # Generar series de imágenes para cada estudio
        series = self._generate_image_series(studies)
        print(f"   ✅ {len(series)} series de imágenes generadas")
        
        # Generar imágenes médicas sintéticas
        images = self._generate_synthetic_medical_images(series)
        print(f"   ✅ {len(images)} imágenes médicas sintéticas generadas")
        
        # Generar segmentaciones para las imágenes
        segmentations = self._generate_synthetic_segmentations(images)
        print(f"   ✅ {len(segmentations)} segmentaciones sintéticas generadas")
        
        # Generar reportes médicos sintéticos
        reports = self._generate_medical_reports(patients, studies)
        print(f"   ✅ {len(reports)} reportes médicos generados")
        
        # Compilar dataset completo
        complete_dataset = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'dataset_type': 'synthetic_medical_demo',
                'patient_count': len(patients),
                'study_count': len(studies),
                'image_count': len(images),
                'segmentation_count': len(segmentations),
                'temp_directory': str(self.temp_dir)
            },
            'patients': patients,
            'studies': studies,
            'series': series,
            'images': images,
            'segmentations': segmentations,
            'reports': reports,
            'paths': {
                'temp_dir': str(self.temp_dir),
                'patients_dir': str(self.temp_dir / 'patients'),
                'images_dir': str(self.temp_dir / 'images'),
                'segmentations_dir': str(self.temp_dir / 'segmentations')
            }
        }
        
        # Guardar dataset para referencia
        self._save_dataset_metadata(complete_dataset)
        
        print("🎉 Dataset médico sintético completo generado exitosamente!")
        return complete_dataset
    
    def _generate_synthetic_patients(self) -> List[Dict[str, Any]]:
        """
        Genera información de pacientes sintéticos.
        
        Crea pacientes ficticios con información médica realista
        pero completamente sintética que respeta la privacidad.
        
        Returns:
            Lista de diccionarios con información de pacientes sintéticos
        """
        patients = []
        
        # Nombres ficticios para demostración
        demo_names = [
            "DEMO_PATIENT_ALPHA",
            "DEMO_PATIENT_BETA", 
            "DEMO_PATIENT_GAMMA",
            "DEMO_PATIENT_DELTA",
            "DEMO_PATIENT_EPSILON"
        ]
        
        for i in range(self.patient_count):
            # Generar fecha de nacimiento realista (45-75 años para casos prostáticos)
            age_years = np.random.randint(45, 76)
            birth_date = datetime.now() - timedelta(days=age_years*365)
            
            patient = {
                'patient_id': f"DEMO_P_{i+1:03d}",
                'patient_name': demo_names[i] if i < len(demo_names) else f"DEMO_PATIENT_{i+1}",
                'birth_date': birth_date.strftime('%Y%m%d'),
                'age_years': age_years,
                'sex': 'M',  # Masculino para casos prostáticos
                'medical_record_number': f"MRN_{uuid.uuid4().hex[:8].upper()}",
                'referring_physician': f"Dr. Demo Physician {chr(65+i)}",
                'created_at': datetime.now().isoformat(),
                'demo_case_type': self._assign_demo_case_type(),
                'medical_history': self._generate_synthetic_medical_history()
            }
            
            patients.append(patient)
        
        return patients
    
    def _assign_demo_case_type(self) -> str:
        """Asigna tipo de caso de demostración."""
        case_types = [
            'normal_prostate',
            'benign_hyperplasia', 
            'suspicious_lesion',
            'confirmed_cancer',
            'post_treatment_followup'
        ]
        return np.random.choice(case_types)
    
    def _generate_synthetic_medical_history(self) -> Dict[str, Any]:
        """Genera historial médico sintético."""
        return {
            'psa_level': round(np.random.uniform(0.5, 15.0), 2),
            'previous_biopsies': np.random.randint(0, 3),
            'family_history_prostate_cancer': np.random.choice([True, False]),
            'medications': ['Demo Medication A', 'Demo Medication B'],
            'allergies': ['None known'],
            'previous_imaging_dates': [
                (datetime.now() - timedelta(days=np.random.randint(30, 365))).strftime('%Y%m%d')
            ]
        }
    
    def _generate_medical_studies(self, patients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Genera estudios médicos para los pacientes sintéticos.
        
        Cada estudio representa una sesión de imagen médica,
        como una resonancia magnética o tomografía computarizada.
        
        Args:
            patients: Lista de pacientes sintéticos
            
        Returns:
            Lista de estudios médicos sintéticos
        """
        studies = []
        
        for patient in patients:
            for study_num in range(self.studies_per_patient):
                # Generar fecha de estudio realista
                study_date = datetime.now() - timedelta(days=np.random.randint(1, 365))
                
                study = {
                    'study_instance_uid': f"1.2.3.4.5.{patient['patient_id']}.{study_num+1}.{int(study_date.timestamp())}",
                    'patient_id': patient['patient_id'],
                    'study_date': study_date.strftime('%Y%m%d'),
                    'study_time': study_date.strftime('%H%M%S'),
                    'study_description': self._generate_study_description(),
                    'referring_physician': patient['referring_physician'],
                    'study_id': f"STUDY_{patient['patient_id']}_{study_num+1:02d}",
                    'accession_number': f"ACC_{uuid.uuid4().hex[:8].upper()}",
                    'institution_name': "Demo Medical Center",
                    'department_name': "Radiology - Prostate Imaging",
                    'modalities_in_study': self._select_study_modalities(),
                    'number_of_series': self.series_per_study,
                    'clinical_indication': self._generate_clinical_indication(patient),
                    'created_at': datetime.now().isoformat()
                }
                
                studies.append(study)
        
        return studies
    
    def _generate_study_description(self) -> str:
        """Genera descripción de estudio médico."""
        descriptions = [
            "MRI PROSTATE WITH AND WITHOUT CONTRAST",
            "CT PELVIS WITH CONTRAST", 
            "MRI PROSTATE MULTIPARAMETRIC",
            "ULTRASOUND PROSTATE TRANSRECTAL",
            "MRI PROSTATE DWI SEQUENCE"
        ]
        return np.random.choice(descriptions)
    
    def _select_study_modalities(self) -> List[str]:
        """Selecciona modalidades para el estudio."""
        # La mayoría de estudios prostáticos son MRI
        if np.random.random() < 0.7:
            return ['MRI']
        elif np.random.random() < 0.5:
            return ['CT']
        else:
            return ['ULTRASOUND']
    
    def _generate_clinical_indication(self, patient: Dict[str, Any]) -> str:
        """Genera indicación clínica basada en el tipo de caso."""
        case_type = patient['demo_case_type']
        
        indications = {
            'normal_prostate': "Routine prostate screening",
            'benign_hyperplasia': "Evaluate enlarged prostate",
            'suspicious_lesion': "Evaluate abnormal PSA levels",
            'confirmed_cancer': "Staging of known prostate cancer",
            'post_treatment_followup': "Post-treatment surveillance"
        }
        
        return indications.get(case_type, "Prostate evaluation")
    
    def _generate_image_series(self, studies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Genera series de imágenes para cada estudio.
        
        Una serie es un conjunto de imágenes tomadas con los mismos
        parámetros de adquisición, como una secuencia T2 en MRI.
        
        Args:
            studies: Lista de estudios médicos
            
        Returns:
            Lista de series de imágenes
        """
        series_list = []
        
        for study in studies:
            modalities = study['modalities_in_study']
            
            for series_num in range(self.series_per_study):
                modality = np.random.choice(modalities)
                
                series = {
                    'series_instance_uid': f"{study['study_instance_uid']}.{series_num+1}",
                    'study_instance_uid': study['study_instance_uid'],
                    'patient_id': study['patient_id'],
                    'series_number': series_num + 1,
                    'series_description': self._generate_series_description(modality),
                    'modality': modality,
                    'body_part_examined': 'PROSTATE',
                    'patient_position': 'HFS',  # Head First Supine
                    'slice_thickness': self._get_typical_slice_thickness(modality),
                    'spacing_between_slices': self._get_typical_spacing(modality),
                    'repetition_time': self._get_typical_tr(modality) if modality == 'MRI' else None,
                    'echo_time': self._get_typical_te(modality) if modality == 'MRI' else None,
                    'number_of_images': np.random.randint(20, 50),
                    'acquisition_date': study['study_date'],
                    'acquisition_time': study['study_time'],
                    'protocol_name': self._generate_protocol_name(modality),
                    'created_at': datetime.now().isoformat()
                }
                
                series_list.append(series)
        
        return series_list
    
    def _generate_series_description(self, modality: str) -> str:
        """Genera descripción de serie según modalidad."""
        descriptions = {
            'MRI': [
                'T2 WEIGHTED AXIAL',
                'T1 WEIGHTED POST CONTRAST',
                'DWI DIFFUSION WEIGHTED',
                'T2 WEIGHTED SAGITTAL',
                'DYNAMIC CONTRAST ENHANCED'
            ],
            'CT': [
                'CT PELVIS AXIAL',
                'CT PELVIS CORONAL',
                'CT PELVIS SAGITTAL'
            ],
            'ULTRASOUND': [
                'TRANSRECTAL ULTRASOUND',
                'DOPPLER ULTRASOUND',
                'ELASTOGRAPHY'
            ]
        }
        
        return np.random.choice(descriptions.get(modality, ['UNKNOWN SERIES']))
    
    def _get_typical_slice_thickness(self, modality: str) -> float:
        """Obtiene grosor de corte típico por modalidad."""
        typical_thickness = {
            'MRI': np.random.uniform(2.0, 4.0),
            'CT': np.random.uniform(1.0, 3.0),
            'ULTRASOUND': np.random.uniform(1.0, 2.0)
        }
        return round(typical_thickness.get(modality, 3.0), 2)
    
    def _get_typical_spacing(self, modality: str) -> float:
        """Obtiene espaciado típico entre cortes."""
        typical_spacing = {
            'MRI': np.random.uniform(3.0, 5.0),
            'CT': np.random.uniform(2.0, 4.0),
            'ULTRASOUND': np.random.uniform(1.0, 3.0)
        }
        return round(typical_spacing.get(modality, 3.0), 2)
    
    def _get_typical_tr(self, modality: str) -> Optional[float]:
        """Obtiene tiempo de repetición típico para MRI."""
        if modality == 'MRI':
            return round(np.random.uniform(3000, 6000), 1)
        return None
    
    def _get_typical_te(self, modality: str) -> Optional[float]:
        """Obtiene tiempo de eco típico para MRI."""
        if modality == 'MRI':
            return round(np.random.uniform(80, 120), 1)
        return None
    
    def _generate_protocol_name(self, modality: str) -> str:
        """Genera nombre de protocolo médico."""
        protocols = {
            'MRI': [
                'PROSTATE_MULTIPARAMETRIC',
                'PROSTATE_T2_PROTOCOL',
                'PROSTATE_DWI_PROTOCOL'
            ],
            'CT': [
                'PELVIS_CONTRAST_PROTOCOL',
                'PROSTATE_CT_PROTOCOL'
            ],
            'ULTRASOUND': [
                'TRANSRECTAL_PROTOCOL',
                'PROSTATE_ULTRASOUND_PROTOCOL'
            ]
        }
        
        return np.random.choice(protocols.get(modality, ['STANDARD_PROTOCOL']))
    
    def _generate_synthetic_medical_images(self, series_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Genera imágenes médicas sintéticas para cada serie.
        
        Crea datos de imagen que parecen realistas pero son
        completamente sintéticos para propósitos de demostración.
        
        Args:
            series_list: Lista de series de imágenes
            
        Returns:
            Lista de imágenes médicas sintéticas
        """
        images = []
        
        for series in series_list:
            num_images = series['number_of_images']
            
            for image_num in range(num_images):
                # Generar dimensiones típicas según modalidad
                dimensions = self._get_typical_image_dimensions(series['modality'])
                
                # Crear datos de imagen sintéticos
                image_data = self._create_synthetic_image_data(
                    dimensions, 
                    series['modality'],
                    image_num,
                    num_images
                )
                
                # Guardar imagen sintética en archivo temporal
                image_filename = f"image_{series['series_instance_uid']}_{image_num+1:03d}.npy"
                image_path = self.temp_dir / 'images' / image_filename
                np.save(image_path, image_data)
                
                image = {
                    'sop_instance_uid': f"{series['series_instance_uid']}.{image_num+1}",
                    'series_instance_uid': series['series_instance_uid'],
                    'study_instance_uid': series['study_instance_uid'],
                    'patient_id': series['patient_id'],
                    'image_number': image_num + 1,
                    'slice_location': image_num * series['spacing_between_slices'],
                    'image_position': [0.0, 0.0, image_num * series['spacing_between_slices']],
                    'image_orientation': [1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                    'pixel_spacing': self._get_pixel_spacing(series['modality']),
                    'slice_thickness': series['slice_thickness'],
                    'rows': dimensions[0],
                    'columns': dimensions[1],
                    'bits_allocated': 16,
                    'bits_stored': 16,
                    'high_bit': 15,
                    'pixel_representation': 1,
                    'modality': series['modality'],
                    'body_part_examined': series['body_part_examined'],
                    'acquisition_date': series['acquisition_date'],
                    'acquisition_time': series['acquisition_time'],
                    'file_path': str(image_path),
                    'image_data_shape': dimensions,
                    'created_at': datetime.now().isoformat()
                }
                
                images.append(image)
        
        return images
    
    def _get_typical_image_dimensions(self, modality: str) -> Tuple[int, int]:
        """Obtiene dimensiones típicas de imagen por modalidad."""
        typical_dimensions = {
            'MRI': (512, 512),
            'CT': (512, 512),
            'ULTRASOUND': (256, 256)
        }
        return typical_dimensions.get(modality, (512, 512))
    
    def _get_pixel_spacing(self, modality: str) -> List[float]:
        """Obtiene espaciado de píxeles típico."""
        typical_spacing = {
            'MRI': [0.5, 0.5],
            'CT': [0.6, 0.6],
            'ULTRASOUND': [0.3, 0.3]
        }
        return typical_spacing.get(modality, [0.5, 0.5])
    
    def _create_synthetic_image_data(
        self, 
        dimensions: Tuple[int, int], 
        modality: str,
        slice_number: int,
        total_slices: int
    ) -> np.ndarray:
        """
        Crea datos de imagen médica sintéticos pero realistas.
        
        Esta función genera imágenes que se parecen a datos médicos
        reales pero son completamente sintéticos.
        
        Args:
            dimensions: Dimensiones de la imagen (filas, columnas)
            modality: Modalidad médica (MRI, CT, ULTRASOUND)
            slice_number: Número de corte actual
            total_slices: Total de cortes en la serie
            
        Returns:
            Array numpy con datos de imagen sintéticos
        """
        rows, cols = dimensions
        
        # Crear imagen base con ruido realista
        if modality == 'MRI':
            # MRI típicamente tiene valores de 0-4000
            base_intensity = np.random.randint(500, 2000)
            noise_level = 100
        elif modality == 'CT':
            # CT típicamente tiene valores de -1000 a 3000 (unidades Hounsfield)
            base_intensity = np.random.randint(-200, 200)
            noise_level = 50
        else:  # ULTRASOUND
            # Ultrasonido típicamente 0-255
            base_intensity = np.random.randint(50, 200)
            noise_level = 30
        
        # Crear imagen base
        image = np.full((rows, cols), base_intensity, dtype=np.int16)
        
        # Agregar ruido realista
        noise = np.random.normal(0, noise_level, (rows, cols))
        image = image + noise.astype(np.int16)
        
        # Agregar estructura anatómica sintética (próstata)
        if slice_number > total_slices * 0.2 and slice_number < total_slices * 0.8:
            # Simular próstata en cortes centrales
            center_x, center_y = rows // 2, cols // 2
            
            # Crear forma ovalada para próstata
            y, x = np.ogrid[:rows, :cols]
            prostate_mask = ((x - center_x)**2 / (30**2) + (y - center_y)**2 / (25**2)) <= 1
            
            # Intensidad diferente para próstata
            prostate_intensity = base_intensity + np.random.randint(200, 500)
            image[prostate_mask] = prostate_intensity
            
            # Agregar algunas estructuras internas
            if np.random.random() < 0.3:  # 30% chance de lesión
                lesion_x = center_x + np.random.randint(-15, 15)
                lesion_y = center_y + np.random.randint(-10, 10)
                lesion_mask = ((x - lesion_x)**2 + (y - lesion_y)**2) <= (5**2)
                lesion_intensity = base_intensity + np.random.randint(300, 800)
                image[lesion_mask] = lesion_intensity
        
        # Aplicar suavizado realista
        from scipy import ndimage
        image = ndimage.gaussian_filter(image, sigma=0.5)
        
        # Asegurar rango de valores apropiado
        if modality == 'CT':
            image = np.clip(image, -1024, 3071)
        else:
            image = np.clip(image, 0, 4095)
        
        return image.astype(np.int16)
    
    def _generate_synthetic_segmentations(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Genera segmentaciones sintéticas para las imágenes.
        
        Crea máscaras de segmentación que simulan resultados
        de análisis de IA o segmentación manual.
        
        Args:
            images: Lista de imágenes médicas
            
        Returns:
            Lista de segmentaciones sintéticas
        """
        segmentations = []
        
        # Agrupar imágenes por serie para crear segmentaciones coherentes
        series_groups = {}
        for image in images:
            series_uid = image['series_instance_uid']
            if series_uid not in series_groups:
                series_groups[series_uid] = []
            series_groups[series_uid].append(image)
        
        # Generar segmentaciones por serie
        for series_uid, series_images in series_groups.items():
            # Decidir qué regiones anatómicas segmentar
            regions_to_segment = self._select_regions_for_segmentation()
            
            for region in regions_to_segment:
                segmentation = self._create_segmentation_for_region(
                    series_images, 
                    region
                )
                segmentations.append(segmentation)
        
        return segmentations
    
    def _select_regions_for_segmentation(self) -> List[str]:
        """Selecciona regiones anatómicas para segmentar."""
        # La mayoría de casos tendrán segmentación de próstata completa
        regions = ['PROSTATE_WHOLE']
        
        # Algunas veces agregar zonas específicas
        if np.random.random() < 0.6:
            regions.append('PROSTATE_PERIPHERAL_ZONE')
        
        if np.random.random() < 0.4:
            regions.append('PROSTATE_TRANSITION_ZONE')
        
        # Algunas veces agregar lesiones
        if np.random.random() < 0.3:
            regions.append('SUSPICIOUS_LESION')
        
        return regions
    
    def _create_segmentation_for_region(
        self, 
        series_images: List[Dict[str, Any]], 
        region: str
    ) -> Dict[str, Any]:
        """
        Crea segmentación sintética para una región específica.
        
        Args:
            series_images: Imágenes de la serie
            region: Región anatómica a segmentar
            
        Returns:
            Diccionario con información de segmentación
        """
        # Crear máscara de segmentación sintética
        mask_data = self._generate_segmentation_mask(series_images, region)
        
        # Guardar máscara en archivo temporal
        mask_filename = f"seg_{series_images[0]['series_instance_uid']}_{region}.npy"
        mask_path = self.temp_dir / 'segmentations' / mask_filename
        np.save(mask_path, mask_data)
        
        # Calcular métricas de la segmentación
        volume_ml = self._calculate_segmentation_volume(mask_data, series_images[0])
        confidence_score = np.random.uniform(0.7, 0.95)
        
        segmentation = {
            'segmentation_id': f"SEG_{uuid.uuid4().hex[:8].upper()}",
            'series_instance_uid': series_images[0]['series_instance_uid'],
            'patient_id': series_images[0]['patient_id'],
            'anatomical_region': region,
            'segmentation_type': 'AUTOMATIC',  # Simular resultado de IA
            'creation_date': datetime.now().isoformat(),
            'creator_id': 'AI_DEMO_SYSTEM',
            'confidence_score': round(confidence_score, 3),
            'confidence_level': self._determine_confidence_level(confidence_score),
            'volume_ml': round(volume_ml, 2),
            'number_of_slices': len([img for img in series_images if self._slice_contains_region(img, region)]),
            'file_path': str(mask_path),
            'mask_dimensions': mask_data.shape,
            'validation_status': 'PENDING_REVIEW',
            'created_at': datetime.now().isoformat(),
            'metadata': {
                'algorithm_version': 'nnUNet_v2_demo',
                'preprocessing_applied': True,
                'postprocessing_applied': True,
                'manual_corrections': 0
            }
        }
        
        return segmentation
    
    def _generate_segmentation_mask(
        self, 
        series_images: List[Dict[str, Any]], 
        region: str
    ) -> np.ndarray:
        """Genera máscara de segmentación sintética."""
        # Obtener dimensiones de la primera imagen
        first_image = series_images[0]
        rows, cols = first_image['rows'], first_image['columns']
        num_slices = len(series_images)
        
        # Crear máscara 3D
        mask = np.zeros((num_slices, rows, cols), dtype=bool)
        
        # Definir región central donde aparece la anatomía
        start_slice = max(0, num_slices // 4)
        end_slice = min(num_slices, 3 * num_slices // 4)
        
        for slice_idx in range(start_slice, end_slice):
            # Crear máscara 2D para este corte
            slice_mask = self._create_region_mask_2d(rows, cols, region, slice_idx, num_slices)
            mask[slice_idx] = slice_mask
        
        return mask
    
    def _create_region_mask_2d(
        self, 
        rows: int, 
        cols: int, 
        region: str, 
        slice_idx: int, 
        total_slices: int
    ) -> np.ndarray:
        """Crea máscara 2D para una región específica."""
        mask = np.zeros((rows, cols), dtype=bool)
        center_x, center_y = rows // 2, cols // 2
        
        y, x = np.ogrid[:rows, :cols]
        
        if region == 'PROSTATE_WHOLE':
            # Próstata completa - forma ovalada
            mask = ((x - center_x)**2 / (35**2) + (y - center_y)**2 / (30**2)) <= 1
        
        elif region == 'PROSTATE_PERIPHERAL_ZONE':
            # Zona periférica - anillo externo de la próstata
            outer_mask = ((x - center_x)**2 / (35**2) + (y - center_y)**2 / (30**2)) <= 1
            inner_mask = ((x - center_x)**2 / (20**2) + (y - center_y)**2 / (15**2)) <= 1
            mask = outer_mask & ~inner_mask
        
        elif region == 'PROSTATE_TRANSITION_ZONE':
            # Zona de transición - parte central
            mask = ((x - center_x)**2 / (20**2) + (y - center_y)**2 / (15**2)) <= 1
        
        elif region == 'SUSPICIOUS_LESION':
            # Lesión sospechosa - pequeña región
            if np.random.random() < 0.7:  # No todas las imágenes tienen lesión
                lesion_x = center_x + np.random.randint(-20, 20)
                lesion_y = center_y + np.random.randint(-15, 15)
                lesion_radius = np.random.randint(3, 8)
                mask = ((x - lesion_x)**2 + (y - lesion_y)**2) <= (lesion_radius**2)
        
        return mask
    
    def _slice_contains_region(self, image: Dict[str, Any], region: str) -> bool:
        """Determina si un corte contiene la región especificada."""
        # Simplificación: asumimos que la región está en cortes centrales
        return True  # En implementación real, analizaríamos la imagen
    
    def _calculate_segmentation_volume(
        self, 
        mask_data: np.ndarray, 
        reference_image: Dict[str, Any]
    ) -> float:
        """Calcula volumen de segmentación en mililitros."""
        # Obtener espaciado de píxeles y grosor de corte
        pixel_spacing = reference_image['pixel_spacing']
        slice_thickness = reference_image['slice_thickness']
        
        # Calcular volumen de vóxel en mm³
        voxel_volume_mm3 = pixel_spacing[0] * pixel_spacing[1] * slice_thickness
        
        # Contar vóxeles en la máscara
        num_voxels = np.sum(mask_data)
        
        # Convertir a mililitros (1 ml = 1000 mm³)
        volume_ml = (num_voxels * voxel_volume_mm3) / 1000.0
        
        return volume_ml
    
    def _determine_confidence_level(self, confidence_score: float) -> str:
        """Determina nivel de confianza basado en el score."""
        if confidence_score >= 0.9:
            return 'VERY_HIGH'
        elif confidence_score >= 0.8:
            return 'HIGH'
        elif confidence_score >= 0.7:
            return 'MODERATE'
        elif confidence_score >= 0.6:
            return 'LOW'
        else:
            return 'VERY_LOW'
    
    def _generate_medical_reports(
        self, 
        patients: List[Dict[str, Any]], 
        studies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Genera reportes médicos sintéticos.
        
        Args:
            patients: Lista de pacientes
            studies: Lista de estudios
            
        Returns:
            Lista de reportes médicos sintéticos
        """
        reports = []
        
        for study in studies:
            patient = next(p for p in patients if p['patient_id'] == study['patient_id'])
            
            report = {
                'report_id': f"RPT_{uuid.uuid4().hex[:8].upper()}",
                'study_instance_uid': study['study_instance_uid'],
                'patient_id': study['patient_id'],
                'report_date': datetime.now().strftime('%Y%m%d'),
                'report_time': datetime.now().strftime('%H%M%S'),
                'radiologist': "Dr. Demo Radiologist",
                'report_status': 'FINAL',
                'clinical_indication': study['clinical_indication'],
                'technique': self._generate_technique_description(study),
                'findings': self._generate_findings_description(patient),
                'impression': self._generate_impression(patient),
                'pi_rads_score': self._generate_pi_rads_score(patient),
                'recommendations': self._generate_recommendations(patient),
                'created_at': datetime.now().isoformat()
            }
            
            reports.append(report)
        
        return reports
    
    def _generate_technique_description(self, study: Dict[str, Any]) -> str:
        """Genera descripción de técnica médica."""
        return f"Multiparametric MRI of the prostate was performed using {study['modalities_in_study'][0]} sequences including T2-weighted, diffusion-weighted, and dynamic contrast-enhanced imaging."
    
    def _generate_findings_description(self, patient: Dict[str, Any]) -> str:
        """Genera descripción de hallazgos basados en el tipo de caso."""
        case_type = patient['demo_case_type']
        
        findings = {
            'normal_prostate': "The prostate demonstrates normal size and signal characteristics. No focal lesions are identified.",
            'benign_hyperplasia': "The prostate is enlarged with homogeneous signal characteristics consistent with benign prostatic hyperplasia.",
            'suspicious_lesion': "A focal area of restricted diffusion is identified in the peripheral zone, measuring approximately 8mm.",
            'confirmed_cancer': "Multiple areas of restricted diffusion are present with corresponding low signal on T2-weighted images.",
            'post_treatment_followup': "Post-treatment changes are present with no evidence of residual or recurrent disease."
        }
        
        return findings.get(case_type, "Normal prostate examination.")
    
    def _generate_impression(self, patient: Dict[str, Any]) -> str:
        """Genera impresión médica."""
        case_type = patient['demo_case_type']
        
        impressions = {
            'normal_prostate': "Normal prostate examination.",
            'benign_hyperplasia': "Benign prostatic hyperplasia.",
            'suspicious_lesion': "PI-RADS 4 lesion in the peripheral zone. Recommend biopsy.",
            'confirmed_cancer': "Multifocal prostate cancer. Recommend staging studies.",
            'post_treatment_followup': "Stable post-treatment appearance."
        }
        
        return impressions.get(case_type, "Normal study.")
    
    def _generate_pi_rads_score(self, patient: Dict[str, Any]) -> Optional[int]:
        """Genera score PI-RADS sintético."""
        case_type = patient['demo_case_type']
        
        if case_type in ['suspicious_lesion', 'confirmed_cancer']:
            return np.random.randint(3, 6)  # PI-RADS 3-5
        elif case_type == 'benign_hyperplasia':
            return 2
        else:
            return 1
    
    def _generate_recommendations(self, patient: Dict[str, Any]) -> str:
        """Genera recomendaciones médicas."""
        case_type = patient['demo_case_type']
        
        recommendations = {
            'normal_prostate': "Routine follow-up as clinically indicated.",
            'benign_hyperplasia': "Clinical correlation. Consider urological consultation if symptomatic.",
            'suspicious_lesion': "Recommend targeted biopsy of the identified lesion.",
            'confirmed_cancer': "Recommend multidisciplinary team discussion and staging studies.",
            'post_treatment_followup': "Continue routine surveillance imaging."
        }
        
        return recommendations.get(case_type, "Clinical correlation.")
    
    def _save_dataset_metadata(self, dataset: Dict[str, Any]) -> None:
        """Guarda metadata del dataset para referencia."""
        metadata_file = self.temp_dir / 'dataset_metadata.json'
        
        # Crear versión serializable del dataset (sin datos numpy)
        serializable_metadata = {
            'metadata': dataset['metadata'],
            'summary': {
                'patients': len(dataset['patients']),
                'studies': len(dataset['studies']),
                'series': len(dataset['series']),
                'images': len(dataset['images']),
                'segmentations': len(dataset['segmentations']),
                'reports': len(dataset['reports'])
            },
            'paths': dataset['paths']
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_metadata, f, indent=2, ensure_ascii=False)
    
    def cleanup(self) -> None:
        """Limpia archivos temporales."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                print(f"🗑️ Archivos temporales limpiados: {self.temp_dir}")
            except Exception as e:
                print(f"⚠️ Error limpiando archivos temporales: {e}")


# Función de conveniencia para importación directa
def create_demo_medical_data() -> Dict[str, Any]:
    """
    Función de conveniencia para crear datos médicos de demostración.
    
    Returns:
        Dataset médico completo para demostración
    """
    generator = MedicalDemoDataGenerator()
    return generator.generate_complete_demo_dataset()


# Ejemplo de uso
if __name__ == "__main__":
    print("🏥 GENERADOR DE DATOS MÉDICOS SINTÉTICOS - PRUEBA")
    print("=" * 60)
    
    # Generar dataset completo
    dataset = create_demo_medical_data()
    
    print("\n📊 DATASET GENERADO:")
    print(f"   Pacientes: {len(dataset['patients'])}")
    print(f"   Estudios: {len(dataset['studies'])}")
    print(f"   Series: {len(dataset['series'])}")
    print(f"   Imágenes: {len(dataset['images'])}")
    print(f"   Segmentaciones: {len(dataset['segmentations'])}")
    print(f"   Reportes: {len(dataset['reports'])}")
    
    print(f"\n📁 Archivos guardados en: {dataset['paths']['temp_dir']}")
    
    # Mostrar ejemplo de paciente
    example_patient = dataset['patients'][0]
    print(f"\n👤 EJEMPLO DE PACIENTE:")
    print(f"   ID: {example_patient['patient_id']}")
    print(f"   Nombre: {example_patient['patient_name']}")
    print(f"   Edad: {example_patient['age_years']} años")
    print(f"   Tipo de caso: {example_patient['demo_case_type']}")
    
    print("\n🎉 Generación de datos médicos sintéticos completada!")