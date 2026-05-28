{# Generic test: fails for any row where the column is <= 0. #}
{% test positive(model, column_name) %}
select *
from {{ model }}
where {{ column_name }} <= 0
{% endtest %}
