## Documentación actual de endpoints YAML para PPTX y DOCX

### 1. Endpoint DOCX desde YAML

- Endpoint: `POST /generate_word_structured_yaml`
- Ruta en código: `server.py` -> `generate_word_structured_yaml`

#### Flujo jerárquico de invocación

1. `server.py:generate_word_structured_yaml`
   - recibe `file_name` y `document_yaml` desde la petición.
   - llama a `parse_yaml_to_docx_body(document_yaml, file_name)`.
   - llama a `generate_word_template_body_check(body)`.
   - llama a `tools.docx_tool.generate_word_from_template(...)`.

2. `utils.yaml_docx_parser.parse_yaml_to_docx_body`
   - parsea YAML con `yaml.safe_load`.
   - valida la estructura top-level: `cover`, `columns_body`, `body`.
   - valida `cover` con `utils.pydantic_models_arguments.Cover`.
   - valida cada elemento de `body` con `_validate_element`.
   - `_validate_element` normaliza el campo `type` y lo mapea a modelos Pydantic:
     - `ElemHeader`
     - `ElemParagraph`
     - `ElemList`
     - `ElemTable`
     - `ElemImage`
     - `ElemEquation`
     - `ElemPageBreak`
   - devuelve `utils.pydantic_models_endpoints.DocxBodyElements`.

3. `utils.generate_word_template_body_check.generate_word_template_body_check`
   - revisa/normaliza los elementos validados antes de pasarlos al builder.
   - si hay errores devuelve un dict con `error`.

4. `tools.docx_tool.generate_word_from_template`
   - convierte metadatos y elementos a diccionario.
   - construye `doc_full` con `metadata`, `sections`, `font`, `columns_body`.
   - crea buffer `BytesIO` con nombre `file_name.docx`.
   - llama a `utils.document_builder.build_docx_from_dict(doc_full, buffer, request, URL)`.
   - obtiene token con `utils.authorization._get_bearer_token(request)`.
   - obtiene `user_id` con `utils.get_user_id.get_user_id(URL, bearer_token)`.
   - sube el archivo con `utils.upload_file.upload_file(...)`.
   - si `ENABLE_CREATE_KNOWLEDGE` es verdadero, llama a `utils.knowledge.create_knowledge(...)`.

#### Módulos implicados

- `server.py`
- `utils.yaml_docx_parser.py`
- `utils.pydantic_models_arguments.py`
- `utils.pydantic_models_endpoints.py`
- `utils.generate_word_template_body_check.py`
- `tools.docx_tool.py`
- `utils.document_builder.py`
- `utils.authorization.py`
- `utils.get_user_id.py`
- `utils.upload_file.py`
- `utils.knowledge.py`

---

### 2. Endpoint PPTX desde YAML

- Endpoint: `POST /generate_powerpoint_structured_yaml`
- Ruta en código: `server.py` -> `generate_powerpoint_structured_yaml`

#### Flujo jerárquico de invocación

1. `server.py:generate_powerpoint_structured_yaml`
   - recibe `file_name` y `document_yaml` desde la petición.
   - construye `request_context`.
   - llama a `tools.powerpoint_tool.generate_powerpoint_structured_yaml(...)`.

2. `tools.powerpoint_tool.generate_powerpoint_structured_yaml`
   - parsea YAML con `yaml.safe_load`.
   - extrae `image_id` del YAML con `_extract_image_ids_from_yaml`.
   - descarga imágenes referenciadas con `utils.download_file.download_file(...)`.
   - construye `image_registry`.
   - crea buffer `BytesIO` con nombre `file_name.pptx`.
   - llama a `create_presentation_from_yaml(document_yaml, buffer, image_registry)`.
   - obtiene token con `utils.authorization._get_bearer_token(request)`.
   - obtiene `user_id` con `utils.get_user_id.get_user_id(URL, bearer_token)`.
   - sube el PPTX con `utils.upload_file.upload_file(...)`.
   - si `ENABLE_CREATE_KNOWLEDGE` es verdadero y hay `user_id`, llama a `utils.knowledge.create_knowledge(...)`.

3. `tools.powerpoint_tool.create_presentation_from_yaml`
   - parsea de nuevo YAML y valida con `PPTXSchema`.
   - construye la presentación `Presentation()`.
   - para cada slide invoca el constructor correcto desde `BUILDERS` según `slide_data.type`.
   - funciones auxiliares usadas en la construcción:
     - `hex_to_rgb`
     - `set_slide_background`
     - `add_text_box`
     - `add_header_bar`
     - `place_image_centered`
     - `add_chart`
     - `add_table`
   - guarda el buffer de PowerPoint.

#### Módulos implicados

- `server.py`
- `tools.powerpoint_tool.py`
- `utils.download_file.py`
- `utils.authorization.py`
- `utils.get_user_id.py`
- `utils.upload_file.py`
- `utils.knowledge.py`

---

### 3. Estado actual y recomendaciones para refactorización

- El flujo DOCX YAML es principalmente:
  - parseo YAML -> validación Pydantic -> build dict -> `build_docx_from_dict` -> subida.
- El flujo PPTX YAML es principalmente:
  - parseo YAML -> extracción de imágenes -> build PPTX -> subida.
- Ambos flujos repiten pasos comunes de autorización, token, usuario y subida.
- Para refactorizar, considera separar:
  1. parseo/validación YAML
  2. construcción de documento en memoria
  3. subida y conocimiento
  4. manejo de tokens/usuario

### 4. Componentes candidatos para extraer

- validación YAML genérica (un parser común para `yaml.safe_load` + errores claros)
- manejo de imágenes compartido entre PPTX y DOCX si se usan `image_id`
- función de subida/creación de conocimiento común para todos los endpoints
- abstraer el paso de `request_context` -> `bearer_token` -> `user_id`
