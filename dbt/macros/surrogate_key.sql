{# Backend-portable surrogate key: md5 of concatenated, null-safe columns.
   Avoids a dbt_utils dependency while working on both DuckDB and BigQuery. #}
{% macro surrogate_key(columns) %}
    md5(
        {%- for col in columns %}
        coalesce(cast({{ col }} as varchar), ''){% if not loop.last %} || '-' ||{% endif %}
        {%- endfor %}
    )
{% endmacro %}
