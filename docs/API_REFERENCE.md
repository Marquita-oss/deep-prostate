# 📚 API Reference - Medical Imaging Workstation

## Documentación Completa de APIs

Esta documentación cubre todas las APIs públicas del sistema, tanto para desarrollo interno como para integración externa.

---

## 🏗️ Arquitectura de APIs

### Niveles de API

```mermaid
graph TB
    subgraph "External APIs"
        REST[REST API]
        WS[WebSocket API]
        CLI[CLI Interface]
    end
    
    subgraph "Public Python APIs"
        SERV[Service APIs]
        REPO[Repository APIs]
        ENTITY[Entity APIs]
    end
    
    subgraph "Internal APIs"
        UI[UI Component APIs]
        UTIL[Utility APIs]
        AI[AI Adapter APIs]
    end
    
    REST --> SERV
    WS --> SERV
    CLI --> SERV
    SERV --> REPO
    SERV --> ENTITY
    UI --> SERV
    AI --> SERV
```

---

## 🌐 REST API

### Base Configuration

#### **Endpoint Base**
```
Base URL: http://localhost:8080/api/v1
Content-Type: application/json
Authentication: Bearer Token (para producción)
```

#### **Standard Response Format**
```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

#### **Error Response Format**
```json
{
  "success": false,
  "error": {
    "code": "MEDICAL_IMAGE_NOT_FOUND",
    "message": "Medical image with UID 1.2.3.4.5 not found",
    "details": {
      "series_uid": "1.2.3.4.5",
      "search_attempted": true
    }
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

### Authentication

#### **POST /auth/login**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "radiologist_user",
  "password": "secure_password",
  "institution": "hospital_id_123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600,
    "user_info": {
      "id": "user_123",
      "username": "radiologist_user",
      "role": "radiologist",
      "institution": "hospital_id_123",
      "permissions": ["read_images", "create_segmentations", "generate_reports"]
    }
  }
}
```

### Medical Images

#### **GET /images**
Obtiene lista de imágenes médicas con filtros opcionales.

```http
GET /api/v1/images?patient_id=PAT001&modality=MRI_T2&limit=20&offset=0
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `patient_id` | string | No | ID del paciente |
| `study_uid` | string | No | UID del estudio |
| `modality` | string | No | Modalidad de imagen (CT, MRI_T2, etc.) |
| `date_from` | string | No | Fecha desde (ISO 8601) |
| `date_to` | string | No | Fecha hasta (ISO 8601) |
| `limit` | integer | No | Límite de resultados (default: 50) |
| `offset` | integer | No | Offset para paginación (default: 0) |

**Response:**
```json
{
  "success": true,
  "data": {
    "images": [
      {
        "series_uid": "1.2.826.0.1.3680043.8.498.12345",
        "study_uid": "1.2.826.0.1.3680043.8.498.12340",
        "patient_id": "PAT001",
        "patient_name": "DOE^JOHN",
        "modality": "MRI_T2",
        "acquisition_date": "2024-01-15T08:30:00Z",
        "institution": "HOSPITAL_A",
        "dimensions": [30, 256, 256],
        "spacing": [2.0, 0.938, 0.938],
        "file_size_mb": 15.2,
        "created_at": "2024-01-15T09:00:00Z"
      }
    ],
    "total_count": 145,
    "page_count": 8,
    "current_page": 1
  }
}
```

#### **GET /images/{series_uid}**
Obtiene detalles de una imagen específica.

```http
GET /api/v1/images/1.2.826.0.1.3680043.8.498.12345
```

**Response:**
```json
{
  "success": true,
  "data": {
    "series_uid": "1.2.826.0.1.3680043.8.498.12345",
    "study_uid": "1.2.826.0.1.3680043.8.498.12340",
    "patient_id": "PAT001",
    "patient_name": "DOE^JOHN",
    "modality": "MRI_T2",
    "acquisition_date": "2024-01-15T08:30:00Z",
    "institution": "HOSPITAL_A",
    "dimensions": [30, 256, 256],
    "spacing": [2.0, 0.938, 0.938],
    "orientation": [1, 0, 0, 0, 1, 0],
    "window_level": {
      "default_window": 1000,
      "default_level": 500
    },
    "dicom_metadata": {
      "StudyDescription": "MRI PROSTATE WITH AND WITHOUT CONTRAST",
      "SeriesDescription": "T2W TSE AX",
      "SliceThickness": "2.0",
      "RepetitionTime": "4000",
      "EchoTime": "100"
    },
    "file_path": "/medical_data/studies/PAT001/...",
    "file_size_mb": 15.2,
    "created_at": "2024-01-15T09:00:00Z",
    "last_accessed": "2024-01-15T14:30:00Z"
  }
}
```

#### **POST /images/upload**
Sube nueva imagen médica al sistema.

```http
POST /api/v1/images/upload
Content-Type: multipart/form-data

FormData:
- file: [DICOM file]
- metadata: {
    "patient_id": "PAT001",
    "study_description": "MRI PROSTATE",
    "override_patient_info": false
  }
```

**Response:**
```json
{
  "success": true,
  "data": {
    "series_uid": "1.2.826.0.1.3680043.8.498.12346",
    "upload_id": "upload_789123",
    "processing_status": "processing",
    "estimated_completion": "2024-01-15T10:35:00Z"
  }
}
```

#### **DELETE /images/{series_uid}**
Elimina imagen del sistema (requiere permisos especiales).

```http
DELETE /api/v1/images/1.2.826.0.1.3680043.8.498.12345
```

**Response:**
```json
{
  "success": true,
  "data": {
    "deleted": true,
    "series_uid": "1.2.826.0.1.3680043.8.498.12345",
    "backup_location": "/backups/deleted/2024-01-15/...",
    "retention_until": "2024-07-15T10:30:00Z"
  }
}
```

### AI Analysis

#### **POST /ai/analyze**
Ejecuta análisis completo con IA sobre una imagen.

```http
POST /api/v1/ai/analyze
Content-Type: application/json

{
  "series_uid": "1.2.826.0.1.3680043.8.498.12345",
  "analysis_type": "prostate_comprehensive",
  "config": {
    "confidence_threshold": 0.75,
    "target_regions": ["prostate", "lesions"],
    "include_pi_rads": true,
    "generate_report": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "analysis_id": "analysis_456789",
    "status": "processing",
    "estimated_completion": "2024-01-15T10:35:00Z",
    "progress_url": "/api/v1/ai/analyze/analysis_456789/progress"
  }
}
```

#### **GET /ai/analyze/{analysis_id}**
Obtiene resultado de análisis de IA.

```http
GET /api/v1/ai/analyze/analysis_456789
```

**Response:**
```json
{
  "success": true,
  "data": {
    "analysis_id": "analysis_456789",
    "series_uid": "1.2.826.0.1.3680043.8.498.12345",
    "status": "completed",
    "created_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:33:45Z",
    "processing_time_seconds": 225,
    "results": {
      "segmentations": [
        {
          "segmentation_id": "seg_123456",
          "region_type": "prostate",
          "confidence": 0.89,
          "volume_ml": 42.3,
          "pi_rads_score": 2,
          "bounding_box": {
            "min": [8, 45, 67],
            "max": [22, 189, 205]
          }
        },
        {
          "segmentation_id": "seg_123457", 
          "region_type": "lesion",
          "confidence": 0.76,
          "volume_ml": 1.8,
          "pi_rads_score": 4,
          "anatomical_location": "peripheral_zone_left_base"
        }
      ],
      "metrics": {
        "prostate_volume_ml": 42.3,
        "prostate_psa_density": 0.142,
        "total_lesions": 1,
        "highest_pi_rads": 4,
        "overall_assessment": "clinically_significant_disease_detected"
      },
      "report": {
        "structured_report_url": "/api/v1/reports/report_789123",
        "pdf_url": "/api/v1/reports/report_789123.pdf"
      }
    }
  }
}
```

### Segmentations

#### **GET /segmentations**
Obtiene lista de segmentaciones.

```http
GET /api/v1/segmentations?image_uid=1.2.826.0.1.3680043.8.498.12345
```

**Response:**
```json
{
  "success": true,
  "data": {
    "segmentations": [
      {
        "segmentation_id": "seg_123456",
        "image_uid": "1.2.826.0.1.3680043.8.498.12345",
        "region_type": "prostate", 
        "creation_method": "ai_automatic",
        "confidence": 0.89,
        "created_by": "user_123",
        "created_at": "2024-01-15T10:33:00Z",
        "last_modified": "2024-01-15T11:15:00Z",
        "volume_ml": 42.3,
        "pi_rads_score": 2,
        "validated": true,
        "validated_by": "radiologist_456",
        "validation_date": "2024-01-15T14:20:00Z"
      }
    ]
  }
}
```

#### **POST /segmentations**
Crea nueva segmentación manual.

```http
POST /api/v1/segmentations
Content-Type: application/json

{
  "image_uid": "1.2.826.0.1.3680043.8.498.12345",
  "region_type": "lesion",
  "creation_method": "manual",
  "mask_data": "base64_encoded_mask_data",
  "metadata": {
    "anatomical_location": "peripheral_zone_right_apex",
    "pi_rads_assessment": 3,
    "radiologist_notes": "Hyperintense focus on T2W, mild restriction on DWI"
  }
}
```

#### **PUT /segmentations/{segmentation_id}**
Actualiza segmentación existente.

```http
PUT /api/v1/segmentations/seg_123456
Content-Type: application/json

{
  "pi_rads_score": 4,
  "validated": true,
  "radiologist_notes": "Updated assessment after DCE review"
}
```

### Reports

#### **POST /reports/generate**
Genera reporte médico estructurado.

```http
POST /api/v1/reports/generate
Content-Type: application/json

{
  "study_uid": "1.2.826.0.1.3680043.8.498.12340",
  "template": "pi_rads_structured_report",
  "include_images": true,
  "include_measurements": true,
  "radiologist_signature": {
    "radiologist_id": "rad_123",
    "digital_signature": "signature_hash_456"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "report_id": "report_789123",
    "study_uid": "1.2.826.0.1.3680043.8.498.12340", 
    "template_used": "pi_rads_structured_report",
    "generated_at": "2024-01-15T15:30:00Z",
    "formats": {
      "pdf_url": "/api/v1/reports/report_789123.pdf",
      "html_url": "/api/v1/reports/report_789123.html",
      "json_url": "/api/v1/reports/report_789123.json",
      "dicom_sr_url": "/api/v1/reports/report_789123.dcm"
    },
    "status": "finalized",
    "digital_signature": {
      "signed": true,
      "signature_timestamp": "2024-01-15T15:30:15Z",
      "certificate_serial": "cert_456789"
    }
  }
}
```

---

## 🔌 WebSocket API

### Real-time Updates

#### **Connection**
```javascript
const ws = new WebSocket('ws://localhost:8080/ws/v1?token=your_jwt_token');

ws.onopen = function(event) {
    console.log('Connected to Medical Imaging WebSocket');
    
    // Subscribe to specific events
    ws.send(JSON.stringify({
        action: 'subscribe',
        events: ['ai_analysis_progress', 'image_uploads', 'system_alerts']
    }));
};
```

#### **AI Analysis Progress**
```javascript
ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    
    if (message.event === 'ai_analysis_progress') {
        console.log(`Analysis ${message.data.analysis_id}: ${message.data.progress}%`);
        
        // Update progress bar
        updateProgressBar(message.data.analysis_id, message.data.progress);
        
        if (message.data.status === 'completed') {
            // Fetch final results
            fetchAnalysisResults(message.data.analysis_id);
        }
    }
};
```

**Progress Message Format:**
```json
{
  "event": "ai_analysis_progress",
  "timestamp": "2024-01-15T10:32:30Z",
  "data": {
    "analysis_id": "analysis_456789",
    "series_uid": "1.2.826.0.1.3680043.8.498.12345",
    "status": "processing",
    "progress": 65,
    "current_step": "Segmenting prostate gland",
    "estimated_remaining_seconds": 45
  }
}
```

#### **System Alerts**
```json
{
  "event": "system_alert",
  "timestamp": "2024-01-15T10:35:00Z",
  "data": {
    "alert_id": "alert_123456",
    "severity": "warning",
    "category": "memory",
    "message": "System memory usage above 85%",
    "details": {
      "current_usage_percent": 87,
      "available_gb": 2.1,
      "recommendation": "Consider closing unused images or increasing system memory"
    },
    "auto_dismiss_seconds": 30
  }
}
```

---

## 🐍 Python API

### Domain Entities

#### **MedicalImage Class**

```python
from medical_imaging.domain.entities import MedicalImage, ImageModalityType, ImageSpacing
from datetime import datetime
import numpy as np

# Create medical image
image = MedicalImage(
    series_uid="1.2.826.0.1.3680043.8.498.12345",
    patient_id="PAT001",
    study_uid="1.2.826.0.1.3680043.8.498.12340",
    modality=ImageModalityType.MRI_T2,
    acquisition_date=datetime.now(),
    pixel_data=np.zeros((30, 256, 256), dtype=np.float32),
    spacing=ImageSpacing(x=0.938, y=0.938, z=2.0),
    orientation=np.array([1, 0, 0, 0, 1, 0, 0, 0, 1])
)

# Properties and methods
print(f"Image dimensions: {image.dimensions}")  # (30, 256, 256)
print(f"Voxel volume: {image.voxel_volume} mm³")  # 3.516 mm³

# Extract specific slice
slice_data = image.get_slice(15)
print(f"Slice shape: {slice_data.shape}")  # (256, 256)

# Apply window/level
windowed = image.apply_window_level(window=1000, level=500)
print(f"Windowed data type: {windowed.dtype}")  # uint8
```

#### **MedicalSegmentation Class**

```python
from medical_imaging.domain.entities import MedicalSegmentation, AnatomicalRegion

# Create segmentation
segmentation = MedicalSegmentation(
    segmentation_id="seg_123456",
    image_uid="1.2.826.0.1.3680043.8.498.12345",
    region_type=AnatomicalRegion.PROSTATE,
    mask_data=np.zeros((30, 256, 256), dtype=np.uint8),
    creation_method="ai_automatic",
    confidence_score=0.89,
    created_by="nnunet_v1",
    created_at=datetime.now()
)

# Calculate metrics
volume = segmentation.calculate_volume()
surface_area = segmentation.calculate_surface_area()
sphericity = segmentation.calculate_sphericity()

print(f"Volume: {volume:.2f} ml")
print(f"Surface area: {surface_area:.2f} mm²")
print(f"Sphericity: {sphericity:.3f}")

# Extract ROI from original image
roi_data = segmentation.extract_roi(image)
print(f"ROI shape: {roi_data.shape}")
```

### Service Layer

#### **ImageVisualizationService**

```python
from medical_imaging.application.services import ImageVisualizationService
from medical_imaging.infrastructure.storage import DICOMImageRepository
from medical_imaging.infrastructure.visualization import VTKRenderer

# Setup service
repository = DICOMImageRepository("/path/to/medical/data")
renderer = VTKRenderer()
service = ImageVisualizationService(repository, renderer)

# Load and display image
async def load_image_example():
    result = await service.load_and_display_image(
        series_uid="1.2.826.0.1.3680043.8.498.12345",
        window_level=WindowLevel(window=1000, level=500)
    )
    
    if result.success:
        print(f"Image loaded: {result.image.modality}")
        print(f"Render time: {result.render_time_ms}ms")
        return result.render_data
    else:
        print(f"Failed to load image: {result.error_message}")

# Run async
import asyncio
render_data = asyncio.run(load_image_example())
```

#### **AISegmentationService**

```python
from medical_imaging.application.services import AISegmentationService
from medical_imaging.infrastructure.ai import NNUNetAdapter

# Setup AI service
ai_adapter = NNUNetAdapter("/path/to/nnunet/model")
service = AISegmentationService(ai_adapter)

# Analyze prostate study
async def analyze_prostate():
    # Load images
    t2w_image = await repository.find_by_uid("t2w_series_uid")
    dwi_image = await repository.find_by_uid("dwi_series_uid")
    
    study_images = [t2w_image, dwi_image]
    
    # Configure analysis
    config = AnalysisConfig(
        confidence_threshold=0.75,
        target_regions=[AnatomicalRegion.PROSTATE, AnatomicalRegion.LESION],
        include_pi_rads=True,
        model_ensemble=True
    )
    
    # Run analysis
    result = await service.analyze_prostate_study(study_images, config)
    
    print(f"Analysis completed in {result.processing_time:.1f}s")
    print(f"Found {len(result.segmentations)} regions")
    
    for seg in result.segmentations:
        print(f"- {seg.region_type}: {seg.volume_ml:.1f}ml (confidence: {seg.confidence:.2f})")
    
    return result

# Execute analysis
analysis_result = asyncio.run(analyze_prostate())
```

### Repository Pattern

#### **DICOMImageRepository**

```python
from medical_imaging.infrastructure.storage import DICOMImageRepository

# Initialize repository
repository = DICOMImageRepository("/medical_data/storage")

# Save image
async def save_image_example():
    success = await repository.save_image(medical_image)
    if success:
        print(f"Image saved: {medical_image.series_uid}")
    
# Find images
async def search_images():
    # Find by UID
    image = await repository.find_by_uid("1.2.826.0.1.3680043.8.498.12345")
    
    # Find by patient
    patient_images = await repository.find_by_patient_id("PAT001")
    
    # Find by date range
    from datetime import datetime, timedelta
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    recent_images = await repository.find_by_date_range(start_date, end_date)
    
    print(f"Found {len(patient_images)} images for patient")
    print(f"Found {len(recent_images)} images in last 30 days")

# Query with filters
async def advanced_search():
    query = ImageQuery(
        modality=ImageModalityType.MRI_T2,
        institution="HOSPITAL_A",
        min_date=datetime(2024, 1, 1),
        max_date=datetime(2024, 12, 31)
    )
    
    images = await repository.find_by_query(query)
    return images
```

### Configuration Management

#### **ConfigManager**

```python
from medical_imaging.infrastructure.utils import ConfigManager

# Load configuration
config = ConfigManager.load_config("config/medical_imaging_config.yaml")

# Access configuration values
storage_path = config.get("storage_path", "/default/path")
ai_enabled = config.get("ai_models.nnunet_enabled", False)
memory_limit = config.get("visualization.max_memory_usage_gb", 4)

# Update configuration
config.set("ai_models.confidence_threshold", 0.8)
ConfigManager.save_config(config, "config/medical_imaging_config.yaml")

# Environment-specific configs
env_config = ConfigManager.load_env_config(
    base_config="config/base.yaml",
    env_config=f"config/{os.getenv('ENVIRONMENT', 'development')}.yaml"
)
```

### Error Handling

#### **Custom Exceptions**

```python
from medical_imaging.domain.repositories import (
    ImageNotFoundError,
    SegmentationNotFoundError,
    RepositoryError
)
from medical_imaging.application.services import (
    ImageVisualizationError,
    AISegmentationError
)

# Exception handling examples
async def robust_image_loading():
    try:
        image = await repository.find_by_uid("invalid_uid")
        
    except ImageNotFoundError as e:
        logger.warning(f"Image not found: {e}")
        return None
        
    except RepositoryError as e:
        logger.error(f"Repository error: {e}")
        # Maybe try backup repository
        return await backup_repository.find_by_uid("invalid_uid")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

async def robust_ai_analysis():
    try:
        result = await ai_service.segment_image(image, config)
        
    except AISegmentationError as e:
        if "out_of_memory" in str(e):
            # Retry with reduced resolution
            reduced_config = config.copy()
            reduced_config.resolution_factor = 0.5
            result = await ai_service.segment_image(image, reduced_config)
        else:
            raise
            
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        # Fallback to manual segmentation workflow
        return None
```

---

## 💾 Database Schema API

### SQLAlchemy Models

#### **Medical Image Model**
```python
from sqlalchemy import Column, String, DateTime, Integer, Float, LargeBinary, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MedicalImageModel(Base):
    __tablename__ = 'medical_images'
    
    # Primary identifiers
    series_uid = Column(String(128), primary_key=True)
    study_uid = Column(String(128), nullable=False, index=True)
    patient_id = Column(String(64), nullable=False, index=True)
    
    # Medical metadata
    modality = Column(String(32), nullable=False, index=True)
    acquisition_date = Column(DateTime, nullable=False, index=True)
    institution = Column(String(128))
    
    # Image properties
    dimensions_x = Column(Integer, nullable=False)
    dimensions_y = Column(Integer, nullable=False)
    dimensions_z = Column(Integer, nullable=False)
    spacing_x = Column(Float, nullable=False)
    spacing_y = Column(Float, nullable=False)
    spacing_z = Column(Float, nullable=False)
    
    # File information
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer)
    
    # Extended metadata
    dicom_metadata = Column(JSON)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False)
    last_accessed = Column(DateTime)
    access_count = Column(Integer, default=0)

class SegmentationModel(Base):
    __tablename__ = 'segmentations'
    
    # Primary identifier
    segmentation_id = Column(String(128), primary_key=True)
    
    # Foreign keys
    image_uid = Column(String(128), nullable=False, index=True)
    
    # Segmentation properties
    region_type = Column(String(64), nullable=False)
    creation_method = Column(String(32), nullable=False)
    confidence_score = Column(Float)
    
    # Medical validation
    validated = Column(Boolean, default=False)
    validated_by = Column(String(64))
    validation_date = Column(DateTime)
    
    # Calculated metrics
    volume_ml = Column(Float)
    surface_area_mm2 = Column(Float)
    sphericity = Column(Float)
    pi_rads_score = Column(Integer)
    
    # Mask storage
    mask_file_path = Column(String(512))
    
    # Audit fields
    created_by = Column(String(64), nullable=False)
    created_at = Column(DateTime, nullable=False)
    last_modified = Column(DateTime)
```

#### **Database Operations**
```python
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Database connection
engine = create_engine('postgresql://user:pass@localhost/medical_imaging')
Session = sessionmaker(bind=engine)

class DatabaseRepository:
    def __init__(self):
        self.session = Session()
    
    async def save_medical_image(self, image: MedicalImage) -> bool:
        try:
            model = MedicalImageModel(
                series_uid=image.series_uid,
                study_uid=image.study_uid,
                patient_id=image.patient_id,
                modality=image.modality.value,
                acquisition_date=image.acquisition_date,
                dimensions_x=image.dimensions[2],
                dimensions_y=image.dimensions[1], 
                dimensions_z=image.dimensions[0],
                spacing_x=image.spacing.x,
                spacing_y=image.spacing.y,
                spacing_z=image.spacing.z,
                file_path=str(image.file_path),
                created_at=datetime.utcnow()
            )
            
            self.session.add(model)
            self.session.commit()
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to save image to database: {e}")
            return False
    
    async def find_images_by_patient(self, patient_id: str) -> List[MedicalImageModel]:
        return self.session.query(MedicalImageModel)\
            .filter(MedicalImageModel.patient_id == patient_id)\
            .order_by(MedicalImageModel.acquisition_date.desc())\
            .all()
```

---

## 🔧 Utility APIs

### Logging System

#### **Medical Audit Logger**
```python
from medical_imaging.infrastructure.utils import MedicalAuditLogger

# Initialize audit logger
audit_logger = MedicalAuditLogger()

# Log medical actions
audit_logger.log_image_access(
    user_id="radiologist_123",
    patient_id="PAT001",
    series_uid="1.2.826.0.1.3680043.8.498.12345",
    action="view",
    timestamp=datetime.utcnow()
)

audit_logger.log_diagnosis_event(
    user_id="radiologist_123",
    patient_id="PAT001", 
    diagnosis_type="ai_assisted_segmentation",
    pi_rads_score=4,
    confidence=0.87,
    validated=True,
    timestamp=datetime.utcnow()
)

# Query audit logs
recent_access = audit_logger.get_patient_access_history(
    patient_id="PAT001",
    start_date=datetime.now() - timedelta(days=30)
)

for access in recent_access:
    print(f"{access.timestamp}: {access.user_id} {access.action}")
```

### System Monitoring

#### **Performance Monitor**
```python
from medical_imaging.infrastructure.utils import PerformanceMonitor

# Initialize monitor
monitor = PerformanceMonitor()

# Monitor method execution
@monitor.track_performance
async def expensive_ai_operation(image: MedicalImage):
    # AI processing...
    result = await ai_model.predict(image)
    return result

# Monitor memory usage
with monitor.memory_context("image_loading"):
    large_image = await repository.find_by_uid("large_series_uid")

# Get performance metrics
metrics = monitor.get_metrics()
print(f"Average AI processing time: {metrics.avg_ai_time}ms")
print(f"Peak memory usage: {metrics.peak_memory_mb}MB")
print(f"Cache hit rate: {metrics.cache_hit_rate}%")

# System health check
health = monitor.get_system_health()
if health.memory_usage > 0.9:
    logger.warning("High memory usage detected")
    
if health.disk_usage > 0.95:
    logger.critical("Disk space critical")
```

### File Validation

#### **DICOM Validator**
```python
from medical_imaging.infrastructure.utils import DICOMValidator

validator = DICOMValidator()

# Validate single file
validation_result = validator.validate_file("/path/to/image.dcm")

if validation_result.is_valid:
    print(f"Valid DICOM file: {validation_result.series_uid}")
else:
    print(f"Invalid DICOM: {validation_result.errors}")

# Validate directory
batch_result = validator.validate_directory("/path/to/study/")

print(f"Valid files: {batch_result.valid_count}")
print(f"Invalid files: {batch_result.invalid_count}")

for error in batch_result.errors:
    print(f"Error in {error.filename}: {error.message}")

# Medical compliance check
compliance_result = validator.check_medical_compliance(
    dicom_file="/path/to/image.dcm",
    required_tags=["PatientID", "StudyInstanceUID", "SeriesInstanceUID"],
    anonymization_check=True
)

if not compliance_result.compliant:
    print(f"Compliance issues: {compliance_result.violations}")
```

---

## 📊 Data Export APIs

### Report Generation

#### **PDF Report Generator**
```python
from medical_imaging.infrastructure.reporting import PDFReportGenerator

generator = PDFReportGenerator()

# Generate PI-RADS structured report
report_data = {
    "patient_info": {
        "patient_id": "PAT001",
        "patient_name": "DOE^JOHN",
        "date_of_birth": "1965-05-15",
        "study_date": "2024-01-15"
    },
    "findings": [
        {
            "region": "Peripheral Zone",
            "location": "Left base", 
            "pi_rads_score": 4,
            "size_mm": [15, 12, 8],
            "volume_ml": 1.8,
            "adc_value": 0.65,
            "description": "Hypointense lesion on T2W with marked restriction on DWI"
        }
    ],
    "overall_assessment": "Clinically significant disease likely present",
    "recommendations": "MRI-guided biopsy recommended"
}

pdf_path = await generator.generate_pi_rads_report(
    data=report_data,
    template="pi_rads_v2_1",
    include_images=True,
    radiologist_signature="Dr. Smith, MD"
)

print(f"Report generated: {pdf_path}")
```

#### **DICOM SR Export**
```python
from medical_imaging.infrastructure.export import DICOMSRExporter

exporter = DICOMSRExporter()

# Create structured report
sr_dataset = exporter.create_structured_report(
    template_id="PI-RADS_v2.1_Template",
    study_uid="1.2.826.0.1.3680043.8.498.12340",
    findings=findings_data,
    radiologist_info={
        "name": "Dr. Smith",
        "institution": "HOSPITAL_A",
        "license_number": "MD12345"
    }
)

# Save as DICOM file
sr_path = exporter.save_sr(sr_dataset, "/export/path/")
print(f"DICOM SR saved: {sr_path}")
```

### Data Anonymization

#### **DICOM Anonymizer**
```python
from medical_imaging.infrastructure.utils import DICOMAnonymizer

anonymizer = DICOMAnonymizer()

# Anonymize single file
anonymized_path = anonymizer.anonymize_file(
    input_path="/path/to/original.dcm",
    output_path="/path/to/anonymized.dcm", 
    patient_mapping={
        "original_id": "PAT001",
        "anonymized_id": "ANON_001"
    }
)

# Batch anonymization
batch_result = anonymizer.anonymize_directory(
    input_dir="/study/original/",
    output_dir="/study/anonymized/",
    preserve_structure=True,
    anonymization_level="full"  # "partial", "full", "research"
)

print(f"Anonymized {batch_result.processed_count} files")
```

---

## 🧪 Testing APIs

### Test Utilities

#### **Medical Image Test Factory**
```python
from medical_imaging.testing import MedicalImageTestFactory

factory = MedicalImageTestFactory()

# Create test prostate MRI
test_image = factory.create_prostate_mri_t2(
    dimensions=(30, 256, 256),
    spacing=(2.0, 0.938, 0.938),
    with_lesion=True,
    lesion_pi_rads=4
)

# Create test segmentation
test_segmentation = factory.create_prostate_segmentation(
    image=test_image,
    region_type=AnatomicalRegion.PROSTATE,
    realistic_shape=True
)

# Generate test DICOM
dicom_file = factory.save_as_dicom(
    image=test_image,
    output_path="/tmp/test_prostate.dcm",
    patient_id="TEST_PAT_001"
)
```

#### **Mock AI Services**
```python
from medical_imaging.testing.mocks import MockAIService

# Create mock AI service for testing
mock_ai = MockAIService(
    response_time_ms=500,
    confidence_range=(0.7, 0.95),
    success_rate=0.9
)

# Configure mock responses
mock_ai.configure_response(
    input_modality=ImageModalityType.MRI_T2,
    expected_output={
        "prostate_volume": 45.2,
        "lesions_detected": 1,
        "highest_pi_rads": 4
    }
)

# Use in tests
result = await mock_ai.segment_image(test_image, config)
assert result.confidence > 0.7
```

---

Esta documentación de APIs proporciona una referencia completa para desarrolladores, usuarios avanzados y sistemas que necesiten integrar con la Medical Imaging Workstation. Incluye tanto APIs REST para integraciones externas como APIs Python para desarrollo interno.
