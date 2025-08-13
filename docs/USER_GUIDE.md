# 📖 User Guide - Medical Imaging Workstation

## Guía Completa para Profesionales Médicos

Esta guía está diseñada para radiólogos, urólogos, oncólogos y técnicos en imaging médico que trabajen con diagnóstico de cáncer de próstata.

---

## 🎯 Objetivo y Alcance Médico

### Propósito Clínico
La **Medical Imaging Workstation** es una herramienta de **asistencia diagnóstica** que:
- Facilita la visualización avanzada de imágenes de próstata
- Proporciona segmentación automática con IA
- Calcula métricas cuantitativas PI-RADS
- Asiste en la planificación de biopsias
- Genera reportes estructurados

### ⚠️ Limitaciones y Responsabilidades
- **NO es un dispositivo médico certificado FDA/CE**
- **NO reemplaza el criterio clínico profesional**
- **Requiere validación médica** de todos los resultados
- **Usar únicamente como herramienta de segunda opinión**

---

## 🏥 Flujo de Trabajo Clínico

### Caso de Uso Típico: Evaluación de Próstata

#### **Paso 1: Preparación del Estudio** ⏱️ 5 minutos
```
1. Verificar calidad de imágenes MRI
   ✓ Secuencias T2W, DWI, DCE disponibles
   ✓ Resolución ≥ 1.5mm en plano axial
   ✓ Sin artefactos de movimiento significativos

2. Cargar estudio completo
   File > Import DICOM Directory > [Seleccionar carpeta del paciente]

3. Validar información del paciente
   ✓ Nombre, ID, fecha de nacimiento
   ✓ Fecha del estudio
   ✓ Secuencias correctamente etiquetadas
```

#### **Paso 2: Evaluación Visual Inicial** ⏱️ 10 minutos
```
1. Navegación por secuencias
   - T2W: Anatomía zonal de próstata
   - DWI: Restricción de difusión
   - DCE: Realce dinámico

2. Identificación manual de lesiones
   Tools > Measurement > ROI
   - Marcar regiones sospechosas
   - Anotar localización anatómica
   - Estimar tamaño preliminar

3. Aplicar presets optimizados
   Visualization > Window/Level Presets > Prostate T2W
```

#### **Paso 3: Análisis Automatizado con IA** ⏱️ 15 minutos
```
1. Configurar parámetros de IA
   AI Analysis Panel:
   - Target Region: "Prostate Gland"
   - Confidence Threshold: 0.7-0.8
   - Detection Mode: "Lesion Detection"

2. Ejecutar análisis completo
   [Run Full AI Analysis]
   - Segmentación de próstata completa
   - Detección de lesiones sospechosas
   - Cálculo de métricas automáticas

3. Revisar resultados automáticos
   ✓ Contornos de próstata anatómicamente correctos
   ✓ Lesiones detectadas corresponden a hallazgos visuales
   ✓ Métricas dentro de rangos fisiológicos
```

#### **Paso 4: Refinamiento Manual** ⏱️ 10 minutos
```
1. Editar segmentaciones si necesario
   Segmentation Tools:
   - Brush Tool: Agregar/quitar voxels
   - Morphological Operations: Suavizar contornos
   - Manual Correction: Ajustes precisos

2. Validar zonas anatómicas
   ✓ Zona periférica bien delimitada
   ✓ Zona de transición separada
   ✓ Cápsula prostática incluida

3. Marcar lesiones adicionales no detectadas
   Manual Segmentation > New Lesion
```

#### **Paso 5: Análisis Cuantitativo** ⏱️ 5 minutos
```
1. Revisar métricas automáticas
   Quantitative Analysis Panel:
   - Volumen prostático total
   - Volumen por zonas anatómicas
   - Métricas de lesiones individuales

2. Calcular scores PI-RADS
   - Evaluación DWI (score 1-5)
   - Evaluación DCE (score 1-5)
   - Score global integrado

3. Validar mediciones
   ✓ Volumen dentro de rango normal (20-80ml)
   ✓ Métricas de lesiones consistentes
```

#### **Paso 6: Generación de Reporte** ⏱️ 5 minutos
```
1. Compilar hallazgos estructurados
   Report Generator:
   - Datos demográficos del paciente
   - Técnica de adquisición
   - Hallazgos por zona anatómica
   - Clasificación PI-RADS

2. Exportar resultados
   File > Export > Medical Report (PDF)
   File > Export > DICOM SR (Structured Report)

3. Archivar caso
   Project > Save Complete Study
```

---

## 🔬 Herramientas Médicas Especializadas

### 1. Visualización Multimodal

#### **Secuencias MRI Soportadas**
```yaml
T2W (T2 Weighted):
  - Anatomía zonal
  - Detección de lesiones
  - Evaluación capsular
  - Window/Level: 400/200

DWI (Diffusion Weighted):
  - Restricción de difusión
  - Mapas ADC
  - Window/Level: 800/400

DCE (Dynamic Contrast Enhanced):
  - Cinética de realce
  - Curvas tiempo-intensidad
  - Análisis de perfusión
```

#### **Herramientas de Sincronización**
- **Cross-reference Cursor**: Localización automática entre secuencias
- **Multi-planar Reconstruction**: Vistas axial, sagital, coronal
- **Fusion Imaging**: Overlay de diferentes secuencias

### 2. Análisis Morfológico

#### **Mediciones Geométricas**
```
Herramientas disponibles:
✓ Distancia: Medición lineal precisa
✓ Área: Cálculo de superficies
✓ Volumen: Cálculo volumétrico 3D
✓ Ángulos: Medición angular
✓ Perímetro: Contorno de estructuras
```

#### **Métricas Prostáticas Específicas**
```python
# Métricas automáticamente calculadas:
- Volumen prostático total (ml)
- Volumen zona periférica (ml)
- Volumen zona transición (ml)
- Ratio PZ/TZ
- Índice de esfericidad
- Diámetro anteroposterior máximo
- Diámetro transversal máximo
- Diámetro cefalocaudal máximo
```

### 3. Evaluación PI-RADS v2.1

#### **Protocolo de Scoring Automático**
```yaml
Zona Periférica:
  Secuencia Dominante: DWI
  Score 1: Sin restricción difusión
  Score 2: Restricción leve/difusa
  Score 3: Restricción focal leve
  Score 4: Restricción focal marcada
  Score 5: Lesión claramente maligna

Zona Transición:
  Secuencia Dominante: T2W
  Score 1: Señal homogénea
  Score 2: Nódulos circunscritos
  Score 3: Heterogeneidad focal
  Score 4: Lesión sospechosa
  Score 5: Lesión claramente maligna
```

#### **Integración DCE**
```
Criterios de realce:
✓ Realce focal precoz
✓ Corresponde a lesión DWI/T2W
✓ Wash-out dinámico
→ Upgrade de score 3 a 4
```

### 4. Planificación de Biopsia

#### **Targeting de Lesiones**
```
1. Identificación de targets
   - Lesiones PI-RADS ≥ 3
   - Localización anatómica precisa
   - Coordenadas espaciales 3D

2. Cálculo de trayectorias
   - Approach transrectal vs transperineal
   - Avoiding de zonas críticas
   - Optimización de número de cores

3. Exportación para sistemas guiados
   - Formato compatible con Artemis
   - Formato compatible con UroNav
   - DICOM RT para planificación
```

---

## 📊 Interpretación de Resultados

### Valores de Referencia Normales

#### **Métricas Volumétricas**
| Parámetro | Rango Normal | Unidades |
|-----------|--------------|----------|
| Volumen prostático total | 20-80 | ml |
| Zona periférica | 40-60% del total | % |
| Zona transición | 35-55% del total | % |
| Densidad PSA | <0.15 | ng/ml/cc |

#### **Métricas de Lesiones**
| Característica | Benigno | Sospechoso | Maligno |
|----------------|---------|------------|---------|
| ADC medio | >1.2 | 0.8-1.2 | <0.8 | mm²/s × 10⁻³ |
| Volumen lesión | <0.5 | 0.5-1.5 | >1.5 | ml |
| Enhancement ratio | <1.5 | 1.5-2.0 | >2.0 | - |

### Clasificación de Hallazgos

#### **Lesiones por Localización**
```yaml
Zona Periférica:
  - Base lateral izquierda/derecha
  - Porción media lateral izq/der
  - Apex lateral izquierda/derecha
  - Base medial, porción media medial, apex medial

Zona Transición:
  - Nódulo anterior/posterior
  - Nódulo medial/lateral
  - Extensión a zona central

Zona Central:
  - Alrededor de conductos eyaculadores
  - Raramente sede de carcinoma
```

#### **Criterios de Malignidad**
```
Alta sospecha (PI-RADS 4-5):
✓ Restricción marcada difusión (ADC <0.8)
✓ Lesión hipointensa T2W bien definida
✓ Realce focal precoz y wash-out
✓ Volumen >1.5 ml
✓ Contacto capsular extenso

Baja sospecha (PI-RADS 1-2):
✓ Sin restricción difusión (ADC >1.2)
✓ Señal homogénea o cambios benignos
✓ Sin realce focal
✓ Cambios post-biopsia
```

---

## 🛠️ Herramientas Avanzadas

### 1. Análisis de Textura

#### **Radiomics Features**
```python
# Features automáticamente extraídos:
First Order Statistics:
- Mean, Median, Standard Deviation
- Skewness, Kurtosis
- Energy, Entropy

Gray Level Co-occurrence Matrix (GLCM):
- Contrast, Dissimilarity
- Homogeneity, Angular Second Moment
- Correlation, Energy

Gray Level Run Length Matrix (GLRLM):
- Short/Long Run Emphasis
- Gray Level Non-uniformity
- Run Length Non-uniformity
```

#### **Machine Learning Predictions**
```
Modelos disponibles:
✓ Gleason Score Prediction
✓ Tumor Volume Estimation  
✓ Extracapsular Extension Risk
✓ Biochemical Recurrence Risk
```

### 2. Análisis Temporal (DCE)

#### **Curvas de Perfusión**
```
Parámetros farmacocinéticos:
- Ktrans: Permeabilidad vascular
- Ve: Volumen extracelular
- Kep: Constante de retorno
- iAUC: Área bajo curva inicial

Tipos de curvas:
- Tipo I: Progresivo (benigno)
- Tipo II: Plateau (intermedio)  
- Tipo III: Wash-out (maligno)
```

### 3. Fusión Multimodal

#### **Registro de Imágenes**
```
Secuencias fusionadas:
✓ T2W + DWI overlay
✓ T2W + DCE parametric maps
✓ Todas las secuencias + mapas ADC
✓ MRI + Ultrasound (si disponible)
✓ Pre/post biopsia comparison
```

---

## 📋 Protocolos Clínicos

### Protocolo Screening

#### **Pacientes Asintomáticos PSA Elevado**
```yaml
Objetivo: Detección lesiones clínicamente significativas
Threshold: PI-RADS ≥ 3
Seguimiento: 
  - PI-RADS 1-2: PSA monitoring
  - PI-RADS 3: Considerar biopsia/seguimiento
  - PI-RADS 4-5: Biopsia dirigida

Frecuencia:
  - Inicial: Baseline MRI
  - Seguimiento: Cada 1-2 años si negativo
```

### Protocolo Active Surveillance

#### **Pacientes con Cáncer Bajo Riesgo**
```yaml
Criterios inclusión:
  - Gleason ≤ 6
  - PSA <10 ng/ml
  - cT1c-T2a
  - <3 cores positivos
  - <50% involucro por core

Protocolo seguimiento:
  - MRI cada 6-12 meses
  - Comparación con estudios previos
  - Detección de progresión
  - Trigger para re-biopsia
```

### Protocolo Post-tratamiento

#### **Evaluación Recurrencia**
```yaml
Post-prostatectomía:
  - Evaluación lecho prostático
  - Detección recurrencia local
  - PSA >0.2 ng/ml

Post-radioterapia:
  - Cambios post-RT vs recurrencia
  - Fibrosis vs tumor viable
  - PSA nadir + 2 ng/ml
```

---

## 🚨 Alertas y Controles de Calidad

### Validaciones Automáticas

#### **Control de Calidad de Imagen**
```
Verificaciones automáticas:
⚠️ Resolución insuficiente (<1.5mm)
⚠️ Artefactos de movimiento detectados
⚠️ Secuencias incompletas
⚠️ Contraste inadecuado T2W
⚠️ Mapas ADC corruptos
⚠️ Timing DCE incorrecto
```

#### **Validaciones Clínicas**
```
Alerts médicos:
🔍 Lesión >2cm sin evaluación
🔍 PI-RADS 5 no confirmado
🔍 Volumen prostático >100ml
🔍 Hallazgos extrprostáticos
🔍 Adenopatías significativas
🔍 Invasion vesical/rectal
```

### Límites de Seguridad

#### **Thresholds Críticos**
```python
CRITICAL_ALERTS = {
    'prostate_volume_max': 150,  # ml
    'lesion_volume_max': 10,     # ml  
    'pi_rads_5_confirm': True,   # Requiere validación
    'extracapsular_extension': True,  # Alert automático
    'seminal_vesicle_invasion': True, # Alert automático
}
```

---

## 📈 Casos de Uso Específicos

### Caso 1: Paciente 65 años, PSA 8.5 ng/ml

#### **Hallazgos Típicos**
```
Imagen: MRI próstata multiparamétrica
Secuencias: T2W, DWI, DCE

Hallazgos:
- Volumen prostático: 45 ml
- Zona periférica base izquierda:
  * Lesión hipointensa T2W
  * Restricción marcada DWI (ADC 0.6)
  * Realce precoz DCE
  * Volumen: 1.2 ml
  * PI-RADS: 4

Recomendación: Biopsia dirigida
```

### Caso 2: Active Surveillance

#### **Seguimiento Longitudinal**
```
Baseline:
- Gleason 6 (3+3)
- 2/12 cores positivos
- PI-RADS 3

Seguimiento 12 meses:
- Nueva lesión PZ derecha
- PI-RADS 4  
- Volumen incrementado 0.8→1.4 ml

Acción: Re-estadificación
```

### Caso 3: Post-tratamiento

#### **Evaluación Post-RT**
```
48 meses post-EBRT:
- PSA: 4.2 ng/ml (nadir 0.8)
- Fibrosis difusa
- Área focal T2W hipointensa
- Sin restricción DWI significativa
- PI-RADS: 2

Interpretación: Fibrosis post-RT
Seguimiento: PSA + MRI 6 meses
```

---

## 📚 Educación y Entrenamiento

### Curva de Aprendizaje Recomendada

#### **Nivel Básico** (1-2 semanas)
```
Objetivos:
✓ Navegación fluida interfaz
✓ Carga e interpretación DICOM
✓ Uso herramientas medición básicas
✓ Entendimiento PI-RADS básico
✓ Generación reportes simples

Casos práctica: 20-30 estudios normales
```

#### **Nivel Intermedio** (1-2 meses)
```
Objetivos:
✓ Análisis multiparamétrico avanzado
✓ Detección lesiones complejas
✓ Uso eficiente herramientas IA
✓ Correlación con hallazgos histológicos
✓ Protocolos seguimiento

Casos práctica: 50-100 casos variados
```

#### **Nivel Avanzado** (3-6 meses)
```
Objetivos:
✓ Casos complejos post-tratamiento
✓ Personalización workflows
✓ Investigación y radiomics
✓ Training modelos IA locales
✓ Control calidad departamental

Casos práctica: >200 casos + investigación
```

### Recursos Educativos

#### **Material de Referencia**
- **PI-RADS v2.1**: Guía oficial ACR/ESUR
- **Casos interactivos**: Biblioteca integrada
- **Videos tutoriales**: Workflows específicos
- **Webinars**: Actualizaciones técnicas

---

## ⚖️ Aspectos Legales y Éticos

### Responsabilidad Médica

#### **Uso Apropiado**
```
✅ Como herramienta de segunda opinión
✅ Para educación y entrenamiento  
✅ Para investigación con IRB apropiado
✅ Con supervisión médica calificada

❌ Como diagnóstico definitivo único
❌ En pacientes críticos sin validación
❌ Sin entrenamiento apropiado
❌ Como reemplazo del criterio clínico
```

#### **Documentación Requerida**
```
Registros obligatorios:
📋 Usuario que realizó análisis
📋 Fecha y hora de evaluación
📋 Versión software utilizada
📋 Parámetros IA empleados
📋 Modificaciones manuales realizadas
📋 Validación médica final
```

### Privacidad y Seguridad

#### **Protección Datos Paciente**
```yaml
Cumplimiento HIPAA/GDPR:
  - Anonimización automática
  - Encriptación datos en reposo
  - Logs de acceso completos
  - Backup seguro automatizado
  - Purga automática datos temporales
```
