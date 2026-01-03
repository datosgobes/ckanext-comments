# ckanext-comments

`ckanext-comments` es una extensión para CKAN utilizada en la plataforma [datos.gob.es](https://datos.gob.es/) para permitir la creación y gestión de hilos de comentarios en las diferentes entidades del portal (conjuntos de datos, recursos, etc.).

> [!TIP]
> Guía base y contexto del proyecto: https://github.com/datosgobes/datos.gob.es

## Descripción general

Esta extensión permite hilos de comentarios vinculados a las principales entidades de CKAN:
- Conjuntos de datos (*datasets*)
- Recursos
- Grupos
- Organizaciones
- Usuarios

## Requisitos

- Una instancia de CKAN.
- Librerías Python adicionales ([`requirements`](requirements.txt))/[`setup.py.install_requires`](setup.py)

### Compatibilidad

Compatibilidad con versiones de CKAN:

| Versión de CKAN | ¿Compatible?                                                              |
|--------------|-----------------------------------------------------------------------------|
| 2.8          | ❌ No                                                                        |
| 2.9          | ✅ Sí                                                                        |
| 2.10         | ✅ Sí                                                                        |
| 2.11         | ❓ Desconocido                                                               |

## Instalación

```sh
pip install -r requirements.txt
pip install -e .
```

## Configuración

### Plugins

Activa el plugin en tu configuración de CKAN:

```ini
ckan.plugins = … comments
```

### Configuración en `ckan.ini`

> [!NOTE]
> La configuración específica de [datos.gob.es](https://datos.gob.es/) está documentada en:
> https://github.com/datosgobes/datos.gob.es/blob/master/docs/202512_datosgobes-ckan-doc_es.pdf (sección correspondiente a extensiones).

Parámetros disponibles para configurar el comportamiento de los comentarios:

```ini
# Requerir aprobación de comentarios para que sean visibles
# (opcional, por defecto: true).
ckanext.comments.require_approval = false

# Editor (admin) puede editar borradores de comentarios
# (opcional, por defecto: true).
ckanext.comments.draft_edits = true

# El autor puede editar sus propios borradores
# (opcional, por defecto: true).
ckanext.comments.draft_edits_by_author = false

# Editor (admin) puede editar comentarios ya aprobados
# (opcional, por defecto: false).
ckanext.comments.approved_edits = false

# El autor puede editar sus propios comentarios aprobados
# (opcional, por defecto: false).
ckanext.comments.approved_edits_by_author = false

# Niveles de anidamiento mostrados en diseño móvil
# (opcional, por defecto: 3).
ckanext.comments.mobile_depth_threshold = 3

# Incluir implementación por defecto de hilos en la página del dataset
# Si se activa, no es necesario editar las plantillas manualmente para datasets.
# (opcional, por defecto: false).
ckanext.comments.enable_default_dataset_comments = true

# Registrar un getter personalizado para un sujeto proporcionando la ruta a una función
# ckanext.comments.subject.{self.subject_type}_getter = path
# La función debe aceptar un ID y devolver un objeto del modelo.
# Ejemplo:
# ckanext.comments.subject.question_getter = ckanext.msf_ask_question.model.question_getter
```

### Integración en Plantillas (Templates)

Si no se usa la opción automática para datasets (`enable_default_dataset_comments`), es necesario incluir el *snippet* en las plantillas Jinja2 donde se quieran mostrar los comentarios.

Ejemplo para `package/read.html`:

```jinja2
{% ckan_extends %}

{% block primary_content_inner %}
  {{ super() }}
  {# subject_type := package | group | resource | user #}
  {% snippet 'comments/snippets/thread.html', subject_id=pkg.id, subject_type='package' %}
{% endblock primary_content_inner %}
```

### Migraciones de base de datos

Para crear/actualizar el modelo de datos de comentarios:

```sh
ckan -c /etc/ckan/default/ckan.ini db upgrade -p comments
```

## API

La extensión personalizada para [datos.gob.es](https://datos.gob.es/) bloquea los endpoints de la API para la gestión de hilos y comentarios.

## Tests

```sh
pytest --ckan-ini=test.ini
```

## Licencia

Este proyecto se distribuye bajo licencia **GNU Affero General Public License (AGPL) v3.0**. Consulta el fichero [LICENSE](LICENSE).

De acuerdo con los términos de la licencia AGPL-3.0, se mantiene el reconocimiento al proyecto original ([DataShades/ckanext-comments](https://github.com/DataShades/ckanext-comments)) y la redistribución del código derivado bajo la misma licencia.
