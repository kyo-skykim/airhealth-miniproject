{# Use the configured +schema verbatim (bronze/silver/gold) instead of dbt's
   default "<target_schema>_<custom>" concatenation, so medallion layers map to
   clean schema names across DuckDB / BigQuery / Databricks. #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
